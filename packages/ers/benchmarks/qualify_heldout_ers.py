"""Score production SDK outputs against a local, annotated held-out image set."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from eon_ers.evaluation.metrics import compute_classification_metrics
from eon_ers.types import ObservationStatus
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from qualify_desktop_sdk import Box, iou

from ovic_eon.ers import ERSClient, ERSConfig

LABELS = ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"]


Subject = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Sample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: Path
    box: Box | None
    subject: Subject | None = None
    expression: str | None = None

    @model_validator(mode="after")
    def validate_annotation(self) -> Sample:
        if self.box is None:
            if self.subject is not None or self.expression is not None:
                raise ValueError("Face-free images cannot have a subject or expression.")
            return self
        x1, y1, x2, y2 = self.box
        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
            raise ValueError("Expected an ordered, normalized face box.")
        if not self.subject or not self.subject.strip():
            raise ValueError("Each portrait needs a pseudonymous subject ID.")
        if self.expression is not None and self.expression not in LABELS:
            raise ValueError("Unsupported facial expression label.")
        return self


class Holdout(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(min_length=1)
    usage_reference: str = Field(min_length=1)
    training_subjects: set[Subject]
    validation_subjects: set[Subject]
    samples: list[Sample] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_leakage(self) -> Holdout:
        subjects = {sample.subject for sample in self.samples if sample.subject is not None}
        if self.training_subjects & self.validation_subjects:
            raise ValueError("Training and validation subjects overlap.")
        if subjects & (self.training_subjects | self.validation_subjects):
            raise ValueError("Held-out subject overlaps training or validation.")
        if not subjects or all(sample.box is not None for sample in self.samples):
            raise ValueError("Include both portraits and face-free controls.")
        return self


async def evaluate(path: Path, config: ERSConfig) -> dict[str, object]:
    manifest_bytes = path.read_bytes()
    data = Holdout.model_validate_json(manifest_bytes)
    seen: set[str] = set()
    counts: Counter[str] = Counter()
    expected: list[str] = []
    predicted: list[str] = []

    async with ERSClient(config=config) as sdk:
        for sample in data.samples:
            with (path.parent / sample.image).open("rb") as stream:
                payload = stream.read(config.max_image_bytes + 1)
            if len(payload) > config.max_image_bytes:
                raise ValueError(f"Image exceeds SDK size limit: {sample.image}")
            with Image.open(io.BytesIO(payload)) as image:
                if max(image.size) > config.max_image_dimension:
                    raise ValueError(
                        f"Image exceeds the configured resolution limit: {sample.image}"
                    )
                image.verify()
            digest = hashlib.sha256(payload).hexdigest()
            if digest in seen:
                raise ValueError("Duplicate image contents in the held-out manifest.")
            seen.add(digest)
            session = uuid4().hex
            await sdk.register_consent(session, session)
            try:
                result = await sdk.analyze_image(session, session, payload)
            finally:
                await sdk.revoke_consent(session)
            if isinstance(result, dict):
                raise RuntimeError("Expected a local SDK observation.")
            if result.status == ObservationStatus.FAILED:
                raise RuntimeError(f"SDK failed to process {sample.image}: {result.limitations}")
            if sample.box is None:
                counts["negative"] += 1
                counts["false_positive"] += result.face_bbox is not None
                continue
            counts["portrait"] += 1
            matched = result.face_bbox is not None and iou(sample.box, result.face_bbox) >= 0.5
            counts["localized"] += matched
            if sample.expression is not None:
                expected.append(sample.expression)
                if matched and result.is_validated and result.dominant_estimate in LABELS:
                    predicted.append(result.dominant_estimate)
                else:
                    predicted.append("unknown")

    classified = sum(label != "unknown" for label in predicted)
    expression_metrics = None
    if classified:
        present = sorted(set(expected) | (set(predicted) - {"unknown"}))
        summary, per_class, matrix = compute_classification_metrics(expected, predicted, present)
        correct = sum(a == b for a, b in zip(expected, predicted, strict=True))
        expression_metrics = {
            "summary": summary,
            "per_class": per_class,
            "labels": present,
            "confusion_matrix": matrix,
            "correct": correct,
            "meets_99_89_percent_point_target": correct * 10_000 >= len(expected) * 9_989,
        }

    return {
        "dataset_id": data.dataset_id,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "images_sha256": hashlib.sha256("".join(sorted(seen)).encode()).hexdigest(),
        "subjects": len({s.subject for s in data.samples if s.subject is not None}),
        "detector": config.face_detector,
        "portraits": counts["portrait"],
        "localized_iou_0_5": counts["localized"],
        "face_free_images": counts["negative"],
        "false_positive_images": counts["false_positive"],
        "labeled_images": len(expected),
        "classified_images": classified,
        "abstentions": len(expected) - classified,
        "expression_metrics": expression_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--facial-model", help="Local facial ONNX path for an approved runtime")
    args = parser.parse_args()
    config = ERSConfig(
        face_detector="opencv",
        facial_model_path=args.facial_model,
        enable_speech=False,
        enable_text=False,
        enable_video=False,
        enable_multimodal_fusion=False,
    )
    print(json.dumps(asyncio.run(evaluate(args.manifest, config)), indent=2))


if __name__ == "__main__":
    main()

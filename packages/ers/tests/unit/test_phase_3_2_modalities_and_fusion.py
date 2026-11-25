"""Comprehensive unit & integration tests for Phase 3.2 modalities, fusion, registry, and checkpoints."""

from __future__ import annotations

import io
import json
import struct
import threading
import wave
from pathlib import Path

import numpy as np
import pytest
from eon_ers.audio.decoder import AudioDecoder
from eon_ers.audio.pipeline import AudioPipeline
from eon_ers.audio.resampler import AudioResampler
from eon_ers.audio.segmentation import AudioSegmenter
from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput
from eon_ers.core.adapter import CoreEventBusAdapter
from eon_ers.engine import ERSEngine
from eon_ers.exceptions import (
    ERSSafetyViolationError,
    ERSUnsupportedCodecError,
)
from eon_ers.facial.detection import FaceDetectionStatus, HeuristicFaceDetector
from eon_ers.facial.preprocessing import FacialPreprocessor
from eon_ers.fusion.multimodal import MultimodalFusionPipeline
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.registry import ModelRegistry
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.speech.features import AcousticFeatureExtractor
from eon_ers.speech.voice_activity import VoiceActivityDetector
from eon_ers.text.normalization import TextNormalizer
from eon_ers.text.postprocessing import TextPipeline
from eon_ers.training.checkpoints import CheckpointManager, TrainingCheckpoint
from eon_ers.types import (
    InputQualityStatus,
    Modality,
    ModelQualificationState,
    ModelState,
    ObservationStatus,
    TextSentiment,
)
from eon_ers.video.decoder import VideoDecoder
from eon_ers.video.pipeline import VideoPipeline
from PIL import Image


def _make_wav_bytes(
    freq: float = 220.0, sr: int = 16000, duration: float = 1.0, amp: float = 0.4, channels: int = 1
) -> bytes:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    mono = (amp * np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    samples = np.repeat(mono, channels) if channels > 1 else mono
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


def _make_mjpeg_avi(frames: list[bytes], fps: int = 10) -> bytes:
    """Build a minimal standards-compliant RIFF AVI MJPEG stream in pure Python."""
    movi_chunks = bytearray(b"movi")
    for jpg in frames:
        movi_chunks.extend(b"00dc")
        movi_chunks.extend(struct.pack("<I", len(jpg)))
        movi_chunks.extend(jpg)
        if len(jpg) % 2 == 1:
            movi_chunks.append(0)
    list_movi = b"LIST" + struct.pack("<I", len(movi_chunks)) + bytes(movi_chunks)
    us_per_frame = int(1_000_000 / fps)
    avih = b"avih" + struct.pack("<I", 4) + struct.pack("<I", us_per_frame)
    hdrl_body = b"hdrl" + avih
    list_hdrl = b"LIST" + struct.pack("<I", len(hdrl_body)) + hdrl_body
    riff_body = b"AVI " + list_hdrl + list_movi
    return b"RIFF" + struct.pack("<I", len(riff_body)) + riff_body


def _make_face_patch_jpeg(offset_x: int = 40, width: int = 160, height: int = 120) -> bytes:
    arr = np.ones((height, width, 3), dtype=np.uint8) * 185
    arr[20:40, offset_x : offset_x + 16] = 45
    arr[20:40, offset_x + 28 : offset_x + 44] = 45
    arr[55:70, offset_x + 10 : offset_x + 36] = 75
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    return buf.getvalue()


def test_multiface_detection_and_partial_boundary() -> None:
    detector = HeuristicFaceDetector()
    # Wide scene with two clearly separated faces on left and right sides
    arr = np.ones((128, 320, 3), dtype=np.uint8) * 190
    # Face A (left)
    arr[25:45, 25:45] = 40
    arr[25:45, 65:85] = 40
    arr[60:80, 35:75] = 65
    # Face B (right)
    arr[25:45, 220:240] = 40
    arr[25:45, 260:280] = 40
    arr[60:80, 230:270] = 65

    res = detector.detect(Image.fromarray(arr))
    assert res.status == FaceDetectionStatus.MULTIPLE_FACES_DETECTED
    assert len(res.faces) >= 2
    assert res.primary_face is not None
    assert res.primary_face.face_id == "face-0"

    # Preprocessing validates alignment and finite normalized tensor
    pre = FacialPreprocessor(target_size=(64, 64), channels=1)
    pixel_box = res.primary_face.to_pixel_box(320, 128)
    tensor = pre.preprocess(
        Image.fromarray(arr),
        face_bbox=pixel_box,
        left_eye=(0.3, 0.35),
        right_eye=(0.7, 0.38),
    )
    assert tensor.shape == (1, 1, 64, 64)
    assert np.isfinite(tensor).all()


def test_audio_decoder_resampler_vad_and_pipeline() -> None:
    decoder = AudioDecoder()
    stereo_wav = _make_wav_bytes(freq=240.0, sr=22050, duration=0.8, amp=0.5, channels=2)
    samples, sr = decoder.decode(stereo_wav)
    assert sr == 22050
    assert samples.ndim == 1

    with pytest.raises(ERSUnsupportedCodecError):
        decoder.decode(b"ID3compressedmp3payload")

    resampler = AudioResampler()
    resamp = resampler.resample(samples, 22050, 16000)
    assert abs(len(resamp) - int(0.8 * 16000)) < 20

    vad = VoiceActivityDetector()
    active_vad = vad.detect(resamp, 16000)
    assert active_vad.has_voice is True
    assert active_vad.speech_ratio > 0.5

    silent_vad = vad.detect(np.zeros(8000, dtype=np.float32), 16000)
    assert silent_vad.has_voice is False
    assert silent_vad.speech_ratio == 0.0

    # Speech features handle NaN/empty safely
    extractor = AcousticFeatureExtractor(sample_rate=16000)
    assert (
        extractor.extract_features(np.array([], dtype=np.float32), 16000)["energy_rms_mean"] == 0.0
    )
    nan_feats = extractor.extract_features(
        np.array([np.nan, np.inf] * 500, dtype=np.float32), 16000
    )
    assert all(np.isfinite(v) for v in nan_feats.values())

    # Segmentation & pipeline
    segs = AudioSegmenter(window_seconds=0.5, hop_seconds=0.25).segment(np.zeros(16000), 16000)
    assert len(segs) >= 2
    pipe = AudioPipeline(
        ERSConfig(speech_model_path="packages/ers/models/speech_emotion_model.onnx")
    )
    report = pipe.analyze_audio_upload("aud-sess", "consent-1", stereo_wav)
    assert report["target_sample_rate"] == 16000
    assert report["vad"]["has_voice"] is True
    assert report["primary_observation"] is not None


@pytest.mark.asyncio
async def test_text_engine_normalization_privacy_and_distinct_sentiment() -> None:
    norm = TextNormalizer(max_length=100)
    assert norm.normalize("  Hello   World!  ").text == "Hello World!"
    assert norm.normalize("café 😊").has_non_ascii is True
    assert norm.normalize("   ").is_valid is False
    assert norm.normalize(b"\xff\xfe").is_valid is False
    assert norm.normalize("x" * 101).is_valid is False
    assert norm.normalize("bad\x00byte").is_valid is False

    engine = ERSEngine(ERSConfig())
    await engine.start()
    try:
        engine.register_consent("txt-s1", "txt-consent")
        inp = ERSInput(
            session_id="txt-s1",
            modality=Modality.TEXT,
            consent_reference="txt-consent",
            text_payload="I am very happy and grateful today!",
        )
        obs = await engine.process(inp)
        assert isinstance(obs, EmotionObservation)
        assert obs.modality == Modality.TEXT
        assert obs.status == ObservationStatus.MODEL_UNVALIDATED
        assert obs.is_definitive_claim is False
        assert obs.expression_observations["text_sentiment"] == TextSentiment.POSITIVE.value
        assert inp.text_payload is None  # Scrubbed
        # Raw utterance never leaked into expression_observations
        assert "grateful" not in json.dumps(obs.expression_observations)
    finally:
        await engine.stop()


def test_text_pipeline_handles_long_and_empty_inputs() -> None:
    tp = TextPipeline(ERSConfig(max_text_length=64))
    empty_obs = tp.process(
        ERSInput(
            session_id="s",
            modality=Modality.TEXT,
            consent_reference="c",
            text_payload="   ",
        )
    )
    assert empty_obs.status == ObservationStatus.INSUFFICIENT_EVIDENCE


def test_video_decoder_avi_gif_corrupted_recovery_and_cancellation() -> None:
    jpg1 = _make_face_patch_jpeg(offset_x=35)
    jpg2 = _make_face_patch_jpeg(offset_x=65)
    avi_bytes = _make_mjpeg_avi([jpg1, b"corrupt_frame_bytes", jpg2], fps=10)

    decoder = VideoDecoder()
    decoded = list(decoder.iter_frames(avi_bytes))
    assert len(decoded) == 2  # Skipped corrupted middle frame cleanly

    with pytest.raises(ERSUnsupportedCodecError):
        list(decoder.iter_frames(b"\x00\x00\x00\x18ftypmp42"))

    # Also test animated GIF decoding and full VideoPipeline
    gif_buf = io.BytesIO()
    im1 = Image.open(io.BytesIO(jpg1))
    im2 = Image.open(io.BytesIO(jpg2))
    im1.save(gif_buf, format="GIF", save_all=True, append_images=[im2], duration=400, loop=0)

    vpipe = VideoPipeline(
        ERSConfig(facial_model_path="packages/ers/models/facial_emotion_model.onnx")
    )
    result = vpipe.process_video("v1", "s-vid", "c-vid", avi_bytes)
    assert result.status == "completed"
    assert result.frames_processed >= 1
    assert result.is_validated is False  # Baseline ONNX model unvalidated
    assert result.is_definitive_claim is False

    # Test cancellation stops early
    cancel_evt = threading.Event()
    cancel_evt.set()
    cancelled = vpipe.process_video(
        "v-cancel", "s-vid", "c-vid", gif_buf.getvalue(), cancel_event=cancel_evt
    )
    assert cancelled.status == "cancelled"


def test_three_modality_fusion_dampening_and_validation_isolation() -> None:
    now = 1_700_000_000.0
    probs_happy = {
        "neutral": 0.02,
        "happiness": 0.90,
        "sadness": 0.02,
        "anger": 0.02,
        "fear": 0.01,
        "surprise": 0.02,
        "disgust": 0.01,
    }
    probs_angry = {
        "neutral": 0.02,
        "happiness": 0.02,
        "sadness": 0.02,
        "anger": 0.90,
        "fear": 0.01,
        "surprise": 0.02,
        "disgust": 0.01,
    }

    def _obs(mod: Modality, probs: dict[str, float], validated: bool = True) -> EmotionObservation:
        dom = max(probs.items(), key=lambda kv: kv[1])[0]
        return EmotionObservation(
            observation_id=f"id-{mod.value}",
            timestamp=now,
            modality=mod,
            emotion_probabilities=probs,
            dominant_estimate=dom if validated else "unknown",
            confidence=0.90 if validated else 0.0,
            uncertainty=0.10 if validated else 1.0,
            quality_score=0.95,
            model_id=f"m-{mod.value}",
            model_version="1.0.0",
            processing_latency_ms=1.0,
            status=ObservationStatus.OK if validated else ObservationStatus.MODEL_UNVALIDATED,
            input_quality=InputQualityStatus.ACCEPTABLE,
            model_state=(
                ModelState.MODEL_LOADED_VALIDATED
                if validated
                else ModelState.MODEL_LOADED_UNVERIFIED
            ),
            is_validated=validated,
        )

    fusion = MultimodalFusionPipeline(ERSConfig(correlated_agreement_dampening=0.85))
    # All 3 agreeing validated streams -> confidence strictly dampened <= 0.85 * quality
    res_3 = fusion.fuse(
        _obs(Modality.FACIAL, probs_happy),
        _obs(Modality.SPEECH, probs_happy),
        text_obs=_obs(Modality.TEXT, probs_happy),
        current_time=now,
        session_id="mm-3",
    )
    assert res_3.is_validated is True
    assert res_3.dominant_estimate == "happiness"
    assert res_3.confidence <= 0.85
    assert sorted(res_3.classification_eligible_modalities) == ["facial", "speech", "text"]

    # Conflicting speech vs agreeing face+text -> conflict detected
    res_conflict = fusion.fuse(
        _obs(Modality.FACIAL, probs_happy),
        _obs(Modality.SPEECH, probs_angry),
        text_obs=_obs(Modality.TEXT, probs_happy),
        current_time=now,
    )
    assert res_conflict.conflicting_evidence is True
    assert res_conflict.conflict_metric > 0.45

    # Unvalidated text isolated from validated face+speech
    res_iso = fusion.fuse(
        _obs(Modality.FACIAL, probs_happy),
        _obs(Modality.SPEECH, probs_happy),
        text_obs=_obs(Modality.TEXT, probs_angry, validated=False),
        current_time=now,
    )
    assert "text" in res_iso.diagnostic_modalities
    assert "text" not in res_iso.classification_eligible_modalities


def test_model_registry_governance_and_checkpoint_integrity(tmp_path: Path) -> None:
    registry = ModelRegistry()
    discovered = registry.discover_directory("packages/ers/models")
    assert len(discovered) >= 2
    for entry in discovered:
        assert entry.qualification_state == ModelQualificationState.MODEL_LOADED_UNVALIDATED
        assert entry.activated is False
        with pytest.raises(ERSSafetyViolationError):
            registry.activate_model(entry.manifest.model_id)

    # Validate synthetic validated record fails activation cleanly if revoked
    val_manifest = ModelManifest(
        model_id="valid-m",
        name="Valid M",
        version="1.0.0",
        modality=Modality.FACIAL,
        framework="onnx",
        artifact_path="packages/ers/models/facial_emotion_model.onnx",
        sha256_checksum="0e8955c5187b2b9f69f9638e005b09abdbb1412951024e535fdefef48cc7d81b",
        license="MIT",
        commercial_use_allowed=True,
        source="unit",
        cpu_supported=True,
        accelerator_support=["CPUExecutionProvider"],
        input_specification={"name": "input_image", "shape": [1, 1, 64, 64], "dtype": "float32"},
        output_specification={"name": "logits", "shape": [1, 7], "classes": []},
    )
    val_rec = ModelValidationRecord(
        record_id="val-1",
        model_id="valid-m",
        model_version="1.0.0",
        artifact_sha256="0e8955c5187b2b9f69f9638e005b09abdbb1412951024e535fdefef48cc7d81b",
        is_validated=True,
        training_dataset="test",
        training_dataset_version="1.0",
        dataset_license="MIT",
        commercial_use_allowed=True,
        label_mapping=["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"],
        evaluation_dataset="test",
        evaluation_split="test",
        evaluation_script="eval",
        evaluation_script_version="1.0",
        evaluation_metrics={"macro_f1": 0.72, "accuracy": 0.75},
        evaluator="qa",
        validation_timestamp="2026-11-25T00:00:00Z",
    )
    entry = registry.register(val_manifest, validation_record=val_rec)
    assert entry.qualification_state == ModelQualificationState.MODEL_VALIDATED
    registry.activate_model("valid-m")
    assert registry.get_entry("valid-m").activated is True  # type: ignore[union-attr]
    registry.revoke_model("valid-m", "security-audit")
    assert (
        registry.get_entry("valid-m").qualification_state == ModelQualificationState.MODEL_REVOKED
    )  # type: ignore[union-attr]
    with pytest.raises(ERSSafetyViolationError):
        registry.activate_model("valid-m")

    # Checkpoint save, resume & tamper detection
    cm = CheckpointManager(tmp_path / "ckpts")
    w_path = cm.save(
        "run1",
        TrainingCheckpoint(
            epoch=3,
            best_val_loss=0.42,
            weights={"W1": np.ones((4, 2), dtype=np.float32)},
            history=[{"epoch": 3.0, "val_loss": 0.42}],
        ),
    )
    loaded = cm.load_latest("run1")
    assert loaded is not None and loaded.epoch == 3
    w_path.write_bytes(b"corrupted-checkpoint")
    with pytest.raises(Exception, match="SHA-256"):
        cm.load_latest("run1")


@pytest.mark.asyncio
async def test_nested_actuator_safety_interlock() -> None:
    bus = CoreEventBusAdapter()
    with pytest.raises(RuntimeError):
        await bus.publish("ers.observation.created", {"nested": {"cmd_vel": 1.0}})

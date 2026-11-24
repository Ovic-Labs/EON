"""Unit tests for visual and acoustic quality evaluation."""

import io
import wave

import numpy as np
from eon_ers.quality.audio_quality import AudioQualityEvaluator
from eon_ers.quality.face_quality import FaceQualityEvaluator
from eon_ers.types import QualityGrade
from PIL import Image


def test_face_quality_empty_payload() -> None:
    evaluator = FaceQualityEvaluator()
    assessment, img = evaluator.evaluate(b"")
    assert assessment.grade == QualityGrade.UNUSABLE
    assert assessment.score == 0.0
    assert assessment.is_acceptable is False
    assert img is None


def test_face_quality_corrupted_payload() -> None:
    evaluator = FaceQualityEvaluator()
    assessment, img = evaluator.evaluate(b"corrupted-invalid-image-data-header")
    assert assessment.grade == QualityGrade.UNUSABLE
    assert assessment.is_acceptable is False
    assert img is None


def test_face_quality_resolution_checks() -> None:
    # 20x20 is below default 48x48
    small_img = Image.new("RGB", (20, 20), color=(128, 128, 128))
    buf = io.BytesIO()
    small_img.save(buf, format="PNG")
    evaluator = FaceQualityEvaluator(min_resolution=(48, 48))
    assessment, img = evaluator.evaluate(buf.getvalue())
    assert assessment.is_acceptable is False
    assert any("below minimum" in r for r in assessment.reasons)


def test_face_quality_good_image() -> None:
    # 100x100 with texture
    arr = np.random.randint(50, 200, size=(100, 100, 3), dtype=np.uint8)
    good_img = Image.fromarray(arr)
    buf = io.BytesIO()
    good_img.save(buf, format="PNG")
    evaluator = FaceQualityEvaluator(min_resolution=(48, 48), blur_threshold=10.0)
    assessment, img = evaluator.evaluate(buf.getvalue())
    assert assessment.is_acceptable is True
    assert assessment.grade in (QualityGrade.EXCELLENT, QualityGrade.ACCEPTABLE)
    assert assessment.score > 0.5
    assert img is not None


def test_audio_quality_empty_payload() -> None:
    evaluator = AudioQualityEvaluator()
    assessment, samples, sr = evaluator.evaluate(b"")
    assert assessment.grade == QualityGrade.UNUSABLE
    assert assessment.score == 0.0
    assert assessment.is_acceptable is False
    assert samples is None


def test_audio_quality_silence_detection() -> None:
    sr = 16000
    # 1 second of complete zero silence
    zeros = np.zeros(16000, dtype=np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(zeros.tobytes())

    evaluator = AudioQualityEvaluator(silence_threshold_db=-40.0)
    assessment, samples, dec_sr = evaluator.evaluate(buf.getvalue())
    assert any("silence" in r.lower() for r in assessment.reasons)
    assert samples is not None
    assert dec_sr == 16000


def test_audio_quality_valid_signal() -> None:
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # Sine wave with amplitude 0.4
    signal = (0.4 * np.sin(2 * np.pi * 220 * t) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(signal.tobytes())

    evaluator = AudioQualityEvaluator()
    assessment, samples, dec_sr = evaluator.evaluate(buf.getvalue())
    assert assessment.is_acceptable is True
    assert assessment.score > 0.5
    assert samples is not None
    assert dec_sr == 16000

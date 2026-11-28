import hashlib
from pathlib import Path

import pytest
from eon_ers.evaluation.dataset import DatasetMetadata, EvaluationSample


@pytest.mark.parametrize(
    ("name", "body"),
    [
        ("samples.json", "{}"),
        ("samples.json", '{"samples":[]}'),
        ("samples.json", '[{"sample_id":"a","subject_id":null,"label":"sadness"}]'),
        ("samples.csv", "sample_id,subject_id,label\n"),
        ("samples.csv", "sample_id,subject_id,label\na,b\n"),
        ("samples.txt", "sample_id,subject_id,label\na,b,neutral\n"),
    ],
)
def test_matching_digest_cannot_qualify_invalid_inventory(tmp_path: Path, name: str, body: str):
    path = tmp_path / name
    path.write_text(body)
    meta = DatasetMetadata(name="fixture", source="test", version="1", license="test")
    assert not meta.verify_manifest(path, hashlib.sha256(path.read_bytes()).hexdigest())[0]


def test_manifest_binds_training_inventory(tmp_path: Path):
    path = tmp_path / "manifest.csv"
    path.write_text("sample_id,subject_id,label\na,b,neutral\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = DatasetMetadata(name="fixture", source="test", version="1", license="test")
    sample = EvaluationSample(sample_id="a", subject_id="b", label="neutral")
    assert meta.verify_manifest(path, digest, samples=[sample])[0]
    assert not meta.verify_manifest(
        path, digest, samples=[sample.model_copy(update={"subject_id": "other"})]
    )[0]


def test_invalid_bootstrap_role_fails_closed(monkeypatch):
    from eon_ers.live.server import create_live_app

    monkeypatch.setenv("EON_ERS_BOOTSTRAP_API_KEYS", "fixture:typo:test-only")
    with pytest.raises(ValueError, match="Invalid role"):
        create_live_app()


def test_sensor_simulator_requires_reconnection_after_timeout_and_reset():
    from ovic_eon.hardware import LinkState, SensorFrame, SimulatedRobot

    now = [0.0]
    sim = SimulatedRobot(clock=lambda: now[0])
    assert sim.state == LinkState.OFFLINE
    sim.connect()
    frame = SensorFrame(pcm=bytes(32))
    sim.update(frame)
    assert sim.read() == frame
    now[0] = 1.0
    assert sim.state == LinkState.STALE
    with pytest.raises(RuntimeError):
        sim.read()
    sim.connect()
    assert sim.read() == SensorFrame()
    sim.emergency_stop()
    with pytest.raises(RuntimeError):
        sim.connect()
    sim.reset()
    assert sim.state == LinkState.OFFLINE


def test_abstention_counts_against_ground_truth_recall():
    from eon_ers.evaluation.metrics import compute_classification_metrics

    summary, classes, matrix = compute_classification_metrics(
        ["neutral"] * 4, ["neutral", "unknown", "unknown", "insufficient_evidence"], ["neutral"]
    )
    assert matrix == [[1]]
    assert classes["neutral"]["support"] == 4
    assert classes["neutral"]["recall"] == 0.25
    assert summary["macro_f1"] == 0.4


@pytest.mark.parametrize(
    "key,value",
    [("session_id", "session-1"), ("content_sha256", hashlib.sha256(b"sample").hexdigest())],
)
def test_cross_subject_recording_leakage(key, value):
    from eon_ers.evaluation.dataset import EvaluationPartition

    def sample(identifier):
        return EvaluationSample(
            sample_id=identifier, subject_id=identifier, label="neutral", metadata={key: value}
        )

    with pytest.raises(ValueError, match="leakage"):
        EvaluationPartition([sample("train")], [], [sample("test")])


def test_invalid_auth_toggle_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    from eon_ers.live.server import create_live_app

    monkeypatch.setenv("EON_ERS_API_AUTH", "invalid")
    with pytest.raises(ValueError, match="EON_ERS_API_AUTH"):
        create_live_app()


@pytest.mark.parametrize(
    "key,value",
    [("session_id", "recording-1"), ("content_sha256", hashlib.sha256(b"signal").hexdigest())],
)
def test_manifest_binds_recording_metadata(tmp_path, key, value):
    path = tmp_path / "manifest.csv"
    path.write_text(f"sample_id,subject_id,label,{key}\na,b,neutral,{value}\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = DatasetMetadata(name="fixture", source="test", version="1", license="test")
    sample = EvaluationSample(sample_id="a", subject_id="b", label="neutral", metadata={key: value})
    assert meta.verify_manifest(path, digest, samples=[sample])[0]
    assert not meta.verify_manifest(
        path, digest, samples=[sample.model_copy(update={"metadata": {}})]
    )[0]
    assert not meta.verify_manifest(
        path, digest, samples=[sample.model_copy(update={"metadata": {key: "changed"}})]
    )[0]

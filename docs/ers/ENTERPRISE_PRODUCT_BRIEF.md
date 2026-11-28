# OVIC Labs | EON ERS

**On-device affective observation SDK for human-facing robotics**

EON ERS gives robotics and AI teams a Python interface for processing facial,
vocal, text, and multimodal inputs locally. Customer applications receive
observations with signal quality, confidence, model status, and abstention
data. A social robot can use these signals to adapt how it communicates,
subject to the integrator's own interaction policy.

## Integration and evaluation

| Capability | Buyer-facing behavior |
| --- | --- |
| Local SDK | Embed `ovic_eon.ers.ERSClient` in a Python 3.11 or 3.12 application and process inputs in the same process. |
| EON ERS Studio | Use the desktop camera preview and local image viewer to inspect face boxes, latency, and observation status without a server or account. |
| Consent and data handling | Integrate the session consent lifecycle before sending participant data. The desktop demo keeps the current frame in memory. |
| Downstream integration | Consume quality and abstention signals for interaction design. Robot actuation stays under the integrator's separate control policy. |
| Delivery | The SDK wheel excludes synthetic baseline weights. Supply eligible model artifacts and their qualification evidence for the deployment. |

**Current offer scope.** SDK integration evaluation and desktop demonstrations
with abstention. Production emotion-classification performance and deployment
acceptance are pending. Facial expression labels describe observable evidence
within a defined test protocol. A person's internal emotional state requires
separate ground truth, such as a participant report.

## Production qualification

OVIC Labs' requested **99.89%** is a prospective release target. With 1,000
equally weighted cases, the smallest achievable rate that meets it is
**999/1,000 (99.90%)**. The denominator includes abstentions for top-line
accuracy. Report coverage and accuracy on classified cases separately.

An acceptance run should lock the SDK and model versions, the target device,
the emotion categories, and the pass criteria before evaluation. Use
independent held-out participants and appropriately authorized footage across
target devices, camera positions, illumination, occlusions, and demographics.
Record per-class recall and macro F1 alongside top-line accuracy. Measure false
positives on face-free frames, face-box localization, and worst-case latency
separately. Validate model and dataset usage rights for the intended deployment.

The 1,000-case engineering run below assesses the local image path, face-box
behavior, and abstention. Its inputs do not supply independent emotion labels.

## 1,000-case local SDK qualification run

**Run date:** 27 November 2026. **Runtime:** Python 3.12.14, x86-64 CPU.
**SDK baseline:** `bd96884`. **Model configuration:** No model weights or
ONNX Runtime installed in the test environment.

| Check | Observed result |
| --- | ---: |
| Distinct image inputs completed | 1,000 / 1,000 |
| Correct primary face box on portrait variants (IoU ≥ 0.50) | 0 / 500 |
| Misplaced primary face box on portrait variants | 500 / 500 |
| False face box on face-free variants | 500 / 500 |
| Emotion abstentions | 1,000 / 1,000 |
| Validated emotion classifications | 0 / 1,000 |
| SDK-reported processing latency, median / p95 | 8.49 ms / 10.27 ms |

The local SDK completed the image path and withheld every emotion estimate.
The current heuristic detector failed localization on the portrait family
and treated features in the flower photo as faces. This is a failed
face-detection result for these two input families. It provides no estimate
of production face-detection or emotion-classification accuracy.

The runner selected 500 different transforms from each of two photos.
Variants change scale, placement, brightness, and orientation. The portrait
reference box was manually annotated and transformed with the image. The
1,000 distinct inputs are correlated transformations of two fixtures.
This run did not exercise the physical webcam, audio inference, or robot hardware.

### Reproduce the run

Use the Matplotlib sample `grace_hopper.jpg` and scikit-learn sample
`flower.jpg` from a local installation or fixture directory.

```bash
python -m pip install .
python packages/ers/benchmarks/qualify_desktop_sdk.py \
  --portrait /path/to/grace_hopper.jpg \
  --face-box 0.295 0.220 0.735 0.555 \
  --background /path/to/flower.jpg
```

| Fixture | SHA-256 |
| --- | --- |
| `grace_hopper.jpg` | `a8ca6d734765703b09728ab47fe59f473d93ae3967fc24c7c0288c3c7adb7130` |
| `flower.jpg` | `a77f6ec41e353afdf8bdff2ea981b2955535d8d83294f8cfa49cf4e423dd5638` |

## OpenCV detector retest

Studio now uses the OpenCV 4 frontal-face cascade. SDK callers can select it
with `ERSConfig(face_detector="opencv")` after installing the `studio` extra.
The detector returns a face box only when the cascade finds a candidate.

| Check on the same 1,000 image variants | Legacy heuristic | OpenCV 4.14.0 |
| --- | ---: | ---: |
| Correct primary box on portrait variants (IoU ≥ 0.50) | 0 / 500 | 500 / 500 |
| False boxes on face-free variants | 500 / 500 | 42 / 500 |
| Emotion abstentions | 1,000 / 1,000 | 1,000 / 1,000 |
| SDK processing latency, median / p95 | 8.49 ms / 10.27 ms | 20.42 ms / 25.92 ms |

The observed false-positive rate for the flower variants was 8.4%. Before
customer deployment, validate detection on independent people, varied head
poses, and diverse face-free scenes. The run used the same two fixtures and
an environment without ONNX Runtime. It does not establish emotion accuracy
or physical webcam performance.

To reproduce the OpenCV run, install with `python -m pip install ".[studio]"`
and add `--detector opencv` to the command above.

## Independent holdout and target camera

Run these commands from the SDK checkout after installing `.[studio]`.

```bash
python packages/ers/benchmarks/qualify_heldout_ers.py /path/to/heldout.json
python packages/ers/benchmarks/qualify_studio_camera.py --camera 0 --frames 100 --consent-confirmed
```

The image runner reads a JSON manifest with a dataset ID, a usage-rights
reference, training and validation subject IDs, and test samples. Relative
image paths resolve from the manifest folder. Use pseudonymous subject IDs
and keep the manifest and photos local.

```json
{
  "dataset_id": "site-a-heldout-v1",
  "usage_reference": "OVIC Labs approval record ID",
  "training_subjects": ["train-01"],
  "validation_subjects": ["val-01"],
  "samples": [
    {"image": "portrait.jpg", "box": [0.25, 0.20, 0.70, 0.80], "subject": "test-01", "expression": "neutral"},
    {"image": "empty-scene.jpg", "box": null}
  ]
}
```

The sample illustrates the manifest format. A qualification dataset needs
independently sourced participants and scenes for the intended deployment.
Provide the complete training and validation subject IDs to check split
overlap. The runner also rejects duplicate image contents. A label is
optional for face localization. Use an independently annotated visible
expression label for accuracy testing.

With an approved local runtime and model, pass `--facial-model /path/to/model.onnx`.
The runner scores the SDK's actual output, counts abstentions and
localization failures against accuracy, and leaves accuracy unreported
when the SDK classifies no examples. It does not certify the source data,
activate a model, or create a signed validation record. The older
`evaluate_models.py` runs synthetic fixtures and rejects explicit empirical
mode before inference.

The camera command measures time from starting a camera read through return
of the SDK result, separately from SDK processing time. It excludes display
rendering time. Use the production camera and target host, record their
configuration with the output, and confirm consent for anyone in view.

### Profile fallback verification

A diagnostic smoke run used two additional scikit-image portraits and three
face-free photos, with hand-annotated face boxes. The frontal detector
localized one portrait. The stricter profile fallback localized both
(IoU ≥ 0.50) and returned no boxes on the three controls. These five
examples are development evidence. The profile settings have seen this
smoke set, so independent production qualification still requires unseen
participants, poses, and scenes.

The previous 1,000 image variants retained 500/500 portrait matches and
42/500 false face boxes. Median/p95 SDK processing rose to 28.66/65.94 ms
on the current x86-64 test host. All 1,000 emotion estimates were withheld.
Neither run used ONNX Runtime. The physical camera runner reported the
camera as unavailable in this environment, so target-device latency
remains unmeasured.

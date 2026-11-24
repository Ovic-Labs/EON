# ERS Accuracy Validation Plan & Scientific Qualification Protocol

## 1. Executive Summary

This document establishes the scientific evaluation framework, statistical methodology, and qualification criteria for the Emotion Recognition System (ERS) within OVIC EON. 

A central architectural mandate of EON is **epistemic modesty**: affective perception engines must never present probabilistic observations as ground-truth internal psychological states, and must never invent discrete emotional classifications when sensory evidence is ambiguous, unvalidated, or insufficient.

This plan details:
1. Target empirical benchmark datasets for computer vision and speech prosody.
2. Formal mathematical formulations for evaluation metrics and calibration.
3. Automated qualification thresholds required before a model can transition to `MODEL_LOADED_VALIDATED`.
4. Cryptographic validation record binding specifications.

---

## 2. Empirical Benchmark Datasets

To ensure rigorous qualification, synthetic fixtures or hand-engineered parameters are strictly prohibited from granting production validation status. Models must be qualified against standard, empirically validated affective datasets.

### 2.1 Facial Expression Benchmarks

| Dataset | Modality | Samples | Classes | Annotation Protocol | Licensing / Usage |
|---|---|---|---|---|---|
| **AffectNet** | In-the-wild facial images | 450,000+ | 8 discrete + Valence/Arousal | Continuous double-annotation | Research / Academic only |
| **RAF-DB** | Real-world affective faces | 29,672 | 7 basic emotions + compound | Crowdsourced multi-annotator | Academic research |
| **ExpW** | Expressions in-the-wild | 91,793 | 7 basic emotions | Face-focused web crawl | Research only |

### 2.2 Speech Prosody Benchmarks

| Dataset | Modality | Actors / Utterances | Classes | Audio Quality | Licensing / Usage |
|---|---|---|---|---|---|
| **RAVDESS** | Audio-visual speech & song | 24 professional actors (7,356 files) | 8 discrete categories | 48 kHz 16-bit uncompressed WAV | CC BY-NC-SA 4.0 |
| **CREMA-D** | Multi-ethnic speech | 91 actors (7,442 clips) | 6 basic emotions | 16 kHz studio recording | Open Database License |
| **IEMOCAP** | Dyadic conversational speech | 10 actors (12 hours) | Categorical & dimensional | Multi-modal motion capture + audio | Academic use only |

---

## 3. Scientific Evaluation Metrics

### 3.1 Macro Classification Metrics

Because affective datasets exhibit severe natural class imbalance (e.g., happiness and neutral dominate in wild collections, while disgust is rare), raw accuracy is mathematically insufficient. The ERS evaluation suite enforces **Macro-Averaged F1** and **Balanced Accuracy**:

$$\text{Balanced Accuracy} = \frac{1}{K} \sum_{k=1}^K \text{Recall}_k$$

$$\text{Macro-F1} = \frac{1}{K} \sum_{k=1}^K \frac{2 \cdot \text{Precision}_k \cdot \text{Recall}_k}{\text{Precision}_k + \text{Recall}_k}$$

Where $K$ is the number of emotion categories ($K = 7$ in standard ERS configuration: `neutral`, `happiness`, `sadness`, `anger`, `fear`, `surprise`, `disgust`).

### 3.2 Calibration Metrics: Expected Calibration Error (ECE)

A model is calibrated when its predicted probability reflects the true empirical likelihood of correctness. ECE bins predictions into $M = 10$ equally spaced confidence intervals $B_m$:

$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

Where:
- $N$ is total sample count.
- $\text{acc}(B_m)$ is empirical accuracy in bin $m$.
- $\text{conf}(B_m)$ is mean confidence score in bin $m$.

Target: **$\text{ECE} \le 0.10$** for qualified production weights.

### 3.3 Brier Score (Multi-Class Mean Squared Probability Error)

Measures overall probabilistic reliability:

$$\text{BS} = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (p_{ik} - y_{ik})^2$$

Where $y_{ik} \in \{0, 1\}$ is one-hot ground truth and $p_{ik}$ is model predicted probability for class $k$.

---

## 4. Qualification Gating Thresholds

Before any model artifact can receive `is_validated = True` in its `ModelValidationRecord`, it must satisfy all four gating criteria simultaneously:

```
+-------------------------------------------------------------+
|               MODEL QUALIFICATION GATES                     |
+-------------------------------------------------------------+
| Gate 1: Macro-F1 >= 0.40 on empirical test split            |
| Gate 2: Balanced Accuracy >= 0.40                           |
| Gate 3: Training Dataset Provenance VERIFIED                |
| Gate 4: Artifact SHA-256 Cryptographically Bound            |
+-------------------------------------------------------------+
```

If any gate fails:
- The model is tagged `MODEL_LOADED_UNVERIFIED`.
- `is_validated` is strictly set to `False`.
- The inference pipeline forces observation status to `MODEL_UNVALIDATED`.
- Discrete classifications are suppressed to `INSUFFICIENT_EVIDENCE` or `UNKNOWN` with confidence $0.0$, uncertainty $1.0$.

---

## 5. Epistemic Modesty Invariants

1. **Non-Definitive Claim Invariant:** Every `EmotionObservation` and `FusionResult` must strictly carry `is_definitive_claim = False`.
2. **Zero Inferred Psychology:** Predictions represent categorized physical expressions (facial landmark geometry, acoustic pitch contours), not ground-truth mental states.
3. **No Fallback Fabrication:** When confidence is below threshold or uncertainty exceeds threshold, systems must abstain (`status = ObservationStatus.INSUFFICIENT_EVIDENCE`).

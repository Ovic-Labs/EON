# ERS Real-World Evaluation Protocol — Phase 3.1.4

**Project:** OVIC EON — Emotional Intelligence Infrastructure for Robotics  
**Organization:** OVIC Labs  
**Component:** ERS (Emotion Recognition System)  
**Standard:** Scientific Evaluation & Zero-Leakage Holdout Verification  
**Date:** 2026-11-24  

---

## 1. Scope & Objective

This document defines the official, non-negotiable protocol for scientifically evaluating emotion recognition models within OVIC EON ERS. Prior iterations permitted synthetic validation fixtures for pipeline execution testing. Under Phase 3.1.4, synthetic fixtures are strictly restricted to execution integrity tests; **accuracy qualification requires empirical affective datasets and zero-leakage subject-independent holdout partitions**.

---

## 2. Target Affective Datasets

The ERS scientific evaluation framework establishes formal schemas and loaders for the following empirical affective benchmarks:

### 2.1 Facial Expression Benchmarks
1. **AffectNet (Mollahosseini et al., 2017)**:
   - *Scale:* ~450,000 real-world facial images annotated across discrete categorical emotions and continuous Valence/Arousal.
   - *Licensing:* Academic / Non-Commercial Research Use Only.
   - *Partitioning Rule:* Subject-independent holdout. No person present in training/fine-tuning partitions may appear in validation or testing partitions.
2. **RAF-DB (Li et al., 2017 - Real-world Affective Faces Database)**:
   - *Scale:* 29,672 highly diverse real-world facial images with crowd-sourced compound and basic emotion annotations.
   - *Licensing:* Academic / Research License.
   - *Partitioning Rule:* Predefined subject splits with rigorous cross-subject cross-validation.

### 2.2 Acoustic Speech Prosody Benchmarks
1. **RAVDESS (Livingstone & Russo, 2018)**:
   - *Scale:* 7,356 speech and song audio-visual recordings from 24 professional actors (12 male, 12 female).
   - *Licensing:* Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
   - *Partitioning Rule:* Actor-independent holdout. Example standard: Actors 1–18 for training/tuning, Actors 19–24 strictly held out for final test evaluation.
2. **CREMA-D (Cao et al., 2014)**:
   - *Scale:* 7,442 audio clips from 91 distinct multicultural actors expressing 6 basic emotions across varying intensity levels.
   - *Licensing:* Open Database License (ODbL) / Research.
   - *Partitioning Rule:* 91-actor independent splitting. Actors 1–70 training, 71–80 validation, 81–91 holdout test.

---

## 3. Zero-Leakage Partitioning Requirements

Data leakage between training and testing sets invalidates empirical claims of generalization. ERS enforces the following mathematical assertions at runtime via `EvaluationPartition._verify_zero_leakage()`:

$$\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{val}} = \emptyset$$
$$\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset$$
$$\mathcal{S}_{\text{val}} \cap \mathcal{S}_{\text{test}} = \emptyset$$

Where $\mathcal{S}$ denotes the set of unique human subject IDs (actors, speakers, individuals). If any non-empty intersection is detected:
- The partitioning tool immediately raises a `ValueError`.
- Model evaluation aborts.
- Validation record generation is blocked.

---

## 4. Evaluation Metrics & Qualification Thresholds

To pass scientific qualification (`is_validated = True`), a model evaluated on empirical holdout partitions must meet all of the following statistical criteria:

| Metric | Minimum Acceptable Threshold | Formula / Description | Justification |
|:---|:---|:---|:---|
| **Macro-F1 Score** | $\ge 0.400$ | $\frac{1}{K}\sum_{k=1}^K F1_k$ | Prevents class-imbalance exploitation; substantially exceeds random guessing ($\frac{1}{7} \approx 0.143$). |
| **Balanced Accuracy** | $\ge 0.400$ | $\frac{1}{K}\sum_{k=1}^K \frac{TP_k}{TP_k + FN_k}$ | Measures average recall across all 7 categorical states. |
| **Expected Calibration Error (ECE)** | $\le 0.150$ | $\sum_{m=1}^M \frac{\|B_m\|}{N} \|\text{acc}(B_m) - \text{conf}(B_m)\|$ | Ensures confidence scores reliably reflect actual probability of correctness. |
| **Brier Score** | $\le 0.350$ | $\frac{1}{N}\sum_{i=1}^N \sum_{k=1}^K (p_{ik} - y_{ik})^2$ | Strictly proper scoring rule penalizing overconfident incorrect predictions. |
| **Abstention Rate Under Low SNR** | Verified | Percentage of classifications abstaining as `INSUFFICIENT_EVIDENCE` when SNR < 3 dB or blur > threshold. | Guarantees safety under degraded environmental conditions. |

---

## 5. Execution Environment Diagnostic Policy

If empirical dataset directories (`data/affectnet`, `data/ravdess`) are missing in the local execution environment:
1. `evaluate_models.py` logs an explicit diagnostic:
   ```text
   Empirical dataset (AffectNet/RAF-DB/RAVDESS) not found in local environment.
   Marking real-world dataset evaluation as BLOCKED.
   Running synthetic fixture suite for execution and contract testing only.
   ```
2. The benchmark runner proceeds with execution verification using synthetic fixtures to ensure code contracts and ONNX runtime bindings function correctly.
3. The resulting `.validation.json` records explicitly set:
   ```json
   "is_validated": false,
   "validation_status": "UNVALIDATED (qualification thresholds not met; scientific accuracy qualification BLOCKED)"
   ```
4. Production emotion recognition remains **NOT QUALIFIED**.

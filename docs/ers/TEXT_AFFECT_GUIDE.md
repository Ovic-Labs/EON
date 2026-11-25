# Textual Affect Analysis Guide

## Scientific Separation Principle
`eon_ers.text` analyzes UTF-8 textual cues separately from facial and vocal observations. Spoken or written words do not always match external facial/vocal affect or internal subjective feeling.

## Pipeline (`TextNormalizer` -> `TextTokenizer` -> `TextPipeline`)
- Rejects empty/whitespace strings, null bytes, invalid UTF-8 sequences, and payloads exceeding `ERSConfig.max_text_length` (`8192` chars).
- Performs Unicode NFC normalization without retaining raw plaintext inside `EmotionObservation.expression_observations` (exposes structural metrics + distinct `text_sentiment` enum only).
- Scrubs `text_payload` immediately after inference.
- Experimental lexical adapter (`ExperimentalTextAffectAdapter`) remains `MODEL_UNVALIDATED`; `ONNXTextModelAdapter` enforces SHA-256 and `ModelValidationRecord` bindings.

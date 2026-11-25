# Dataset Acquisition & Provenance Guide

## Current Status: Unacquired (`BLOCKED`)
No restricted human emotion dataset binaries or images/audio are distributed in this repository.

## Registered Benchmarks (`eon_ers.evaluation.dataset.KNOWN_DATASET_PROVENANCE`)

| Dataset ID | Name | Modality | License | Commercial Use | Source |
|---|---|---|---|---|---|
| `affectnet` | AffectNet | Facial | Non-Commercial Research Only | No | http://mohammadmahoor.com/affectnet/ |
| `raf_db` | RAF-DB | Facial | Academic / Non-Commercial License | No | http://www.whdeng.cn/RAF/model1.html |
| `fer2013` | FER2013 | Facial | Challenge Research Only (verify terms) | No | Kaggle ICML 2013 Challenge |
| `ravdess` | RAVDESS | Speech | CC BY-NC-SA 4.0 | No | https://zenodo.org/record/1188976 |
| `crema_d` | CREMA-D | Speech | ODbL / Research | No | https://github.com/CheyneyComputerScience/CREMA-D |

## Safe Verification Workflow
1. Obtain official dataset access per the author's license.
2. Compute the downloaded archive SHA-256 digest and register it in `DatasetMetadata(checksum=...)`.
3. Extract archives strictly through `DatasetMetadata.safe_extract_archive()` (rejects path traversal, symlinks/hardlinks, unsupported containers, and decompression bombs).
4. Partition strictly via `create_subject_independent_partition()` so no actor or subject overlaps between train, validation, and test splits.

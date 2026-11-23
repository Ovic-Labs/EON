"""Unit tests for the Phase 0 documentation validation gates (scripts/validate_docs.py).

Covers both positive tests on the actual repository baseline and negative tests
using isolated temporary test fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_docs import (
    check_acceptance_id_uniqueness,
    check_clone_url,
    check_commercial_licensing_strategy,
    check_defect_register_integrity,
    check_document_metadata,
    check_evidence_integrity,
    check_file_structure,
    check_markdown_links,
    check_no_duplicate_requirement_definitions,
    check_performance_reconciliation,
    check_performance_target_classification,
    check_privacy_and_safety_boundaries,
    check_rtm_metrics,
    check_traceability_completeness,
    check_verification_methods,
    run_all_checks,
)

REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)


# ==============================================================================
# POSITIVE TESTS (Live Repository Baseline)
# ==============================================================================


def test_gate1_file_structure_passes() -> None:
    """Gate 1: Live repository contains all 16 Phase 0 specs and 19 governance files."""
    assert check_file_structure(REPO_ROOT) is True


def test_gate2_clone_url_passes() -> None:
    """Gate 2: Live README specifies correct repository clone URL."""
    assert check_clone_url(REPO_ROOT) is True


def test_gate3_markdown_links_pass() -> None:
    """Gate 3: Live documentation has zero broken internal markdown links."""
    assert check_markdown_links(REPO_ROOT) is True


def test_gate4_no_duplicate_requirements_pass() -> None:
    """Gate 4: Live specifications contain zero duplicate requirement definitions."""
    assert check_no_duplicate_requirement_definitions(REPO_ROOT) is True


def test_gate5_acceptance_id_uniqueness_passes() -> None:
    """Gate 5: Live Acceptance Criteria contains 179 unique AC definitions."""
    assert check_acceptance_id_uniqueness(REPO_ROOT) is True


def test_gate6_performance_reconciliation_passes() -> None:
    """Gate 6: All 21 performance targets reconcile across PRD, SRS, PERF, and AC."""
    assert check_performance_reconciliation(REPO_ROOT) is True


def test_gate7_performance_classification_passes() -> None:
    """Gate 7: Performance targets are classified as PROVISIONAL."""
    assert check_performance_target_classification(REPO_ROOT) is True


def test_gate8_evidence_integrity_passes() -> None:
    """Gate 8: Evidence register does not declare premature PASS for runtime phases."""
    assert check_evidence_integrity(REPO_ROOT) is True


def test_gate9_defect_register_integrity_passes() -> None:
    """Gate 9: Defect register contains zero unresolved critical/high defects."""
    assert check_defect_register_integrity(REPO_ROOT) is True


def test_gate10_rtm_metrics_pass() -> None:
    """Gate 10: RTM JSON metrics match Phase 0 baseline (290 source, 203 SRS, 0% impl)."""
    assert check_rtm_metrics(REPO_ROOT) is True


def test_gate11_traceability_completeness_passes() -> None:
    """Gate 11: Traceability graph is complete across all requirement classes."""
    assert check_traceability_completeness(REPO_ROOT) is True


def test_gate12_verification_methods_pass() -> None:
    """Gate 12: All 60 FRs and 78 NFRs declare objective verification methods."""
    assert check_verification_methods(REPO_ROOT) is True


def test_gate13_commercial_licensing_strategy_passes() -> None:
    """Gate 13: Commercial licensing strategy document is complete and contains disclaimers."""
    assert check_commercial_licensing_strategy(REPO_ROOT) is True


def test_gate14_privacy_and_safety_boundaries_pass() -> None:
    """Gate 14: Privacy and safety specifications contain required invariants."""
    assert check_privacy_and_safety_boundaries(REPO_ROOT) is True


def test_gate15_document_metadata_passes() -> None:
    """Gate 15: All 16 Phase 0 documents contain valid metadata headers."""
    assert check_document_metadata(REPO_ROOT) is True


def test_all_15_gates_pass() -> None:
    """Comprehensive test: run_all_checks succeeds across the entire repository."""
    assert run_all_checks(REPO_ROOT) is True


# ==============================================================================
# NEGATIVE TESTS (Isolated Mock Directory Fixtures)
# ==============================================================================


def test_gate1_file_structure_missing_file_fails(tmp_path: Path) -> None:
    """Gate 1 fails when a required specification file is missing."""
    docs_dir = tmp_path / "docs" / "product"
    docs_dir.mkdir(parents=True)
    (docs_dir / "PRD.md").write_text("dummy", encoding="utf-8")
    assert check_file_structure(str(tmp_path)) is False


def test_gate2_clone_url_incorrect_fails(tmp_path: Path) -> None:
    """Gate 2 fails when the clone URL is incorrect or points to another repo."""
    readme = tmp_path / "README.md"
    readme.write_text("git clone https://github.com/Wrong-Org/Wrong-Repo.git", encoding="utf-8")
    assert check_clone_url(str(tmp_path)) is False


def test_gate3_markdown_links_broken_link_fails(tmp_path: Path) -> None:
    """Gate 3 fails when a markdown file contains a broken relative link."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    doc = docs_dir / "test.md"
    doc.write_text("[Broken Link](non_existent_file.md)", encoding="utf-8")
    assert check_markdown_links(str(tmp_path)) is False


def test_gate4_duplicate_requirement_id_fails(tmp_path: Path) -> None:
    """Gate 4 fails when a duplicate requirement ID is defined across files."""
    prod_dir = tmp_path / "docs" / "product"
    prod_dir.mkdir(parents=True)
    fr_file = prod_dir / "FUNCTIONAL_REQUIREMENTS.md"
    fr_file.write_text(
        "### EON-FR-001 — First Definition\n\n### EON-FR-001 — Duplicate Definition\n",
        encoding="utf-8",
    )
    assert check_no_duplicate_requirement_definitions(str(tmp_path)) is False


def test_gate5_acceptance_id_duplicate_or_count_mismatch_fails(tmp_path: Path) -> None:
    """Gate 5 fails when acceptance criteria count is not exactly 179 or has duplicates."""
    acc_dir = tmp_path / "docs" / "acceptance"
    acc_dir.mkdir(parents=True)
    ac_file = acc_dir / "ACCEPTANCE_CRITERIA.md"
    ac_file.write_text("### AC-PROD-001\n### AC-PROD-001\n", encoding="utf-8")
    assert check_acceptance_id_uniqueness(str(tmp_path)) is False


def test_gate6_performance_reconciliation_missing_target_fails(tmp_path: Path) -> None:
    """Gate 6 fails when a required performance target is missing from a spec."""
    for sub in ["product", "requirements", "acceptance"]:
        (tmp_path / "docs" / sub).mkdir(parents=True)
    (tmp_path / "docs" / "product" / "PRD.md").write_text("No targets", encoding="utf-8")
    (tmp_path / "docs" / "requirements" / "SRS.md").write_text("No targets", encoding="utf-8")
    ac_file = tmp_path / "docs" / "acceptance" / "ACCEPTANCE_CRITERIA.md"
    ac_file.write_text("None", encoding="utf-8")
    perf_file = tmp_path / "docs" / "product" / "PERFORMANCE_REQUIREMENTS.md"
    perf_file.write_text("None", encoding="utf-8")
    assert check_performance_reconciliation(str(tmp_path)) is False


def test_gate7_performance_target_missing_provisional_classification_fails(
    tmp_path: Path,
) -> None:
    """Gate 7 fails when targets are claimed to be production-certified rather than provisional."""
    prod_dir = tmp_path / "docs" / "product"
    prod_dir.mkdir(parents=True)
    perf_file = prod_dir / "PERFORMANCE_REQUIREMENTS.md"
    perf_file.write_text("All targets are final and production certified.", encoding="utf-8")
    assert check_performance_target_classification(str(tmp_path)) is False


def test_gate8_evidence_integrity_premature_pass_fails(tmp_path: Path) -> None:
    """Gate 8 fails when a premature PASS is claimed on future runtime capabilities."""
    acc_dir = tmp_path / "docs" / "acceptance"
    acc_dir.mkdir(parents=True)
    ev_file = acc_dir / "EVIDENCE_REGISTER.md"
    ev_file.write_text(
        "| Sub-Phase 1.4 Runtime | PASS | Full execution |\n",
        encoding="utf-8",
    )
    assert check_evidence_integrity(str(tmp_path)) is False


def test_gate9_defect_register_open_critical_fails(tmp_path: Path) -> None:
    """Gate 9 fails when there are unresolved critical or high defects."""
    acc_dir = tmp_path / "docs" / "acceptance"
    acc_dir.mkdir(parents=True)
    def_file = acc_dir / "DEFECT_REGISTER.md"
    def_file.write_text(
        "| DEF-099 | Unhandled segfault | Critical | Open | None |\n",
        encoding="utf-8",
    )
    assert check_defect_register_integrity(str(tmp_path)) is False


def _make_valid_rtm_dict() -> dict:
    """Helper to produce a valid in-memory RTM dictionary structure."""
    return {
        "metrics": {
            "total_source_requirements": 290,
            "functional_requirements_count": 60,
            "non_functional_requirements_count": 78,
            "performance_requirements_count": 66,
            "privacy_safety_requirements_count": 86,
            "total_srs_requirements": 203,
            "total_acceptance_criteria": 179,
            "total_use_cases": 54,
            "coverage_percentage": 100.0,
            "specification_mapping_coverage_percentage": 100.0,
            "implementation_coverage_percentage": 0.0,
        },
        "requirements": {
            "functional": [
                {"id": f"EON-FR-{i:03d}", "title": f"FR {i}", "status": "APPROVED_BASELINE"}
                for i in range(1, 61)
            ],
            "non_functional": [
                {"id": f"EON-NFR-{i:03d}", "title": f"NFR {i}", "status": "APPROVED_BASELINE"}
                for i in range(1, 79)
            ],
            "performance": [
                {
                    "id": f"EON-PERF-{i:03d}",
                    "title": f"PERF {i}",
                    "status": "PROVISIONAL_NOT_BENCHMARKED",
                }
                for i in range(1, 67)
            ],
            "privacy_and_safety": [
                {"id": f"EON-PSR-{i:03d}", "title": f"PSR {i}", "status": "APPROVED_BASELINE"}
                for i in range(1, 87)
            ],
            "srs": [
                {"id": f"EON-SRS-{i:03d}", "title": f"SRS {i}", "status": "APPROVED_BASELINE"}
                for i in range(1, 204)
            ],
            "use_cases": [{"id": f"UC-CASE-{i:03d}", "title": f"UC {i}"} for i in range(1, 55)],
        },
    }


def test_gate10_rtm_metrics_premature_implementation_fails(tmp_path: Path) -> None:
    """Gate 10 fails if RTM JSON reports non-zero implementation for Phase 0."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = _make_valid_rtm_dict()
    data["metrics"]["implementation_coverage_percentage"] = 50.0
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_rtm_metrics(str(tmp_path)) is False


def test_gate10_rtm_metrics_incorrect_totals_fails(tmp_path: Path) -> None:
    """Gate 10 fails when metric counts do not match expected totals."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = _make_valid_rtm_dict()
    data["metrics"]["functional_requirements_count"] = 59
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_rtm_metrics(str(tmp_path)) is False


def test_gate11_traceability_completeness_count_mismatch_fails(tmp_path: Path) -> None:
    """Gate 11 fails when requirement counts do not match expected classes."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = {
        "requirements": {
            "functional": ["FR1"],
            "non_functional": [],
            "performance": [],
            "privacy_and_safety": [],
            "srs": [],
            "use_cases": [],
        }
    }
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_traceability_completeness(str(tmp_path)) is False


def test_gate11_missing_id_in_category_fails(tmp_path: Path) -> None:
    """Gate 11 fails when an expected requirement ID is missing or replaced."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = _make_valid_rtm_dict()
    data["requirements"]["functional"][-1]["id"] = "EON-FR-999"
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_traceability_completeness(str(tmp_path)) is False


def test_gate11_duplicate_id_in_json_fails(tmp_path: Path) -> None:
    """Gate 11 fails when duplicate requirement IDs exist within a category."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = _make_valid_rtm_dict()
    data["requirements"]["functional"][1]["id"] = "EON-FR-001"
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_traceability_completeness(str(tmp_path)) is False


def test_gate11_malformed_record_in_json_fails(tmp_path: Path) -> None:
    """Gate 11 fails when an item record is not a dictionary."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = _make_valid_rtm_dict()
    data["requirements"]["functional"][0] = "malformed-string"
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_traceability_completeness(str(tmp_path)) is False


def test_gate11_missing_title_in_json_fails(tmp_path: Path) -> None:
    """Gate 11 fails when a requirement record lacks a title."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = _make_valid_rtm_dict()
    del data["requirements"]["functional"][0]["title"]
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_traceability_completeness(str(tmp_path)) is False


def test_gate11_invalid_status_in_json_fails(tmp_path: Path) -> None:
    """Gate 11 fails when a requirement has an unauthorized lifecycle status."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    data = _make_valid_rtm_dict()
    data["requirements"]["functional"][0]["status"] = "UNAUTHORIZED_PRODUCTION"
    rtm_file.write_text(json.dumps(data), encoding="utf-8")
    assert check_traceability_completeness(str(tmp_path)) is False


def test_gate11_markdown_json_id_mismatch_fails(tmp_path: Path) -> None:
    """Gate 11 fails when markdown headers do not match JSON requirement IDs."""
    req_dir = tmp_path / "docs" / "requirements"
    prod_dir = tmp_path / "docs" / "product"
    req_dir.mkdir(parents=True)
    prod_dir.mkdir(parents=True)
    rtm_file = req_dir / "requirement_traceability_matrix.json"
    fr_file = prod_dir / "FUNCTIONAL_REQUIREMENTS.md"
    rtm_file.write_text(json.dumps(_make_valid_rtm_dict()), encoding="utf-8")
    fr_file.write_text("## EON-FR-999 — Mismatched\n", encoding="utf-8")
    assert check_traceability_completeness(str(tmp_path)) is False


def test_gate12_verification_methods_missing_declarations_fails(tmp_path: Path) -> None:
    """Gate 12 fails when verification methods are missing from requirements."""
    prod_dir = tmp_path / "docs" / "product"
    prod_dir.mkdir(parents=True)
    fr_file = prod_dir / "FUNCTIONAL_REQUIREMENTS.md"
    fr_file.write_text("No verification here", encoding="utf-8")
    nfr_file = prod_dir / "NON_FUNCTIONAL_REQUIREMENTS.md"
    nfr_file.write_text("No verification here", encoding="utf-8")
    assert check_verification_methods(str(tmp_path)) is False


def test_gate13_commercial_licensing_missing_sections_fails(tmp_path: Path) -> None:
    """Gate 13 fails when commercial licensing strategy lacks required legal governance."""
    prod_dir = tmp_path / "docs" / "product"
    prod_dir.mkdir(parents=True)
    lic_file = prod_dir / "COMMERCIAL_LICENSING_STRATEGY.md"
    lic_file.write_text("Just MIT license.", encoding="utf-8")
    assert check_commercial_licensing_strategy(str(tmp_path)) is False


def test_gate14_privacy_safety_missing_invariants_fails(tmp_path: Path) -> None:
    """Gate 14 fails when required safety invariants are omitted."""
    prod_dir = tmp_path / "docs" / "product"
    prod_dir.mkdir(parents=True)
    psr_file = prod_dir / "PRIVACY_AND_SAFETY_REQUIREMENTS.md"
    psr_file.write_text("Basic privacy doc without safety boundaries.", encoding="utf-8")
    assert check_privacy_and_safety_boundaries(str(tmp_path)) is False


def test_gate15_document_metadata_missing_headers_fails(tmp_path: Path) -> None:
    """Gate 15 fails when document header governance metadata is absent."""
    prod_dir = tmp_path / "docs" / "product"
    prod_dir.mkdir(parents=True)
    prd_file = prod_dir / "PRD.md"
    prd_file.write_text(
        "# Product Requirements Document\nNo metadata header here.\n",
        encoding="utf-8",
    )
    assert check_document_metadata(str(tmp_path)) is False

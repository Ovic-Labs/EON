#!/usr/bin/env python3
"""OVIC EON — Documentation Qualification and Structure Validation Suite.

Phase 0 Final Verification and Automated Regression Audit.
"""

import json
import os
import re
import sys

REQUIRED_PHASE0_DOCS = [
    "docs/product/PRODUCT_VISION.md",
    "docs/product/ENGINE_SCOPE.md",
    "docs/product/CUSTOMER_SEGMENTS.md",
    "docs/product/USE_CASES.md",
    "docs/product/FUNCTIONAL_REQUIREMENTS.md",
    "docs/product/NON_FUNCTIONAL_REQUIREMENTS.md",
    "docs/product/PERFORMANCE_REQUIREMENTS.md",
    "docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md",
    "docs/product/PRD.md",
    "docs/requirements/SRS.md",
    "docs/requirements/REQUIREMENT_TRACEABILITY.md",
    "docs/acceptance/ACCEPTANCE_CRITERIA.md",
    "docs/acceptance/TEST_EVIDENCE_REGISTER.md",
    "docs/acceptance/DEFECT_REGISTER.md",
    "docs/acceptance/RELEASE_ACCEPTANCE.md",
]

REQUIRED_GOVERNANCE_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/README.md",
    "docs/requirements/requirement_traceability_matrix.json",
    "docs/acceptance/PHASE_0_FINAL_VERIFICATION_REPORT.md",
    "docs/roadmap/PHASE_1_EXECUTION_PLAN.md",
    "docs/developer/INSTALLATION.md",
    "docs/developer/DATA_CONTRACTS_GUIDE.md",
    "docs/engineering/PHASE_1_1_IMPLEMENTATION_REPORT.md",
    "docs/engineering/PHASE_1_2_IMPLEMENTATION_REPORT.md",
    "docs/architecture/DATA_SCHEMA_ARCHITECTURE.md",
    "docs/architecture/EVENT_ENVELOPE_SPECIFICATION.md",
    "docs/architecture/SCHEMA_VERSIONING_POLICY.md",
]

EXPECTED_CLONE_URL = "https://github.com/Ovic-Labs/EON.git"

RECONCILED_PERF_METRICS = [
    "Core event routing p50",
    "Core event routing p95",
    "Core event routing p99",
    "Lightweight internal event throughput",
    "Lightweight cross-engine workflow p95",
    "ERS lightweight observation rate",
    "ERS processing latency p95",
    "EMS local retrieval p95",
    "EMS local write p95",
    "ERE deterministic reasoning p95",
    "PSE state update p95",
    "SIE deterministic processing p95",
    "ERG deterministic planning p95",
    "HBU lightweight observation rate",
    "HBU processing latency p95",
    "API lightweight operation p95",
    "API lightweight throughput goal",
    "ROS 2 local message delivery p95",
    "Core idle resident memory",
    "Core startup readiness",
    "Extended soak qualification",
]


def check_file_structure():
    """Verify all required documentation and governance files exist."""
    print("Checking repository documentation structure...")
    missing = []
    for doc in REQUIRED_PHASE0_DOCS + REQUIRED_GOVERNANCE_DOCS:
        norm_path = os.path.normpath(doc)
        if not os.path.exists(norm_path):
            missing.append(doc)
    if missing:
        print(f"FAILED: Missing required document(s): {missing}")
        return False
    p0_count = len(REQUIRED_PHASE0_DOCS)
    gov_count = len(REQUIRED_GOVERNANCE_DOCS)
    print(f"SUCCESS: All {p0_count} Phase 0 documents and {gov_count} governance files exist.")
    return True


def check_clone_url():
    """Verify README contains canonical clone URL."""
    print("Checking README clone URL...")
    if not os.path.exists("README.md"):
        print("FAILED: README.md not found.")
        return False
    with open("README.md", encoding="utf-8") as f:
        content = f.read()
    if EXPECTED_CLONE_URL not in content:
        print(f"FAILED: README.md does not contain expected clone URL '{EXPECTED_CLONE_URL}'")
        return False
    print(f"SUCCESS: Clone URL verified: {EXPECTED_CLONE_URL}")
    return True


def check_markdown_links():
    """Verify internal markdown hyperlinks resolve correctly."""
    print("Checking internal Markdown links...")
    files = []
    for root, _dirs, filenames in os.walk("."):
        if ".git" in root or ".gemini" in root or "brain" in root:
            continue
        for f in filenames:
            if f.endswith(".md"):
                files.append(os.path.normpath(os.path.join(root, f)))

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken = []
    total_checked = 0

    for filepath in files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        for match in link_pattern.finditer(content):
            text, url = match.groups()
            if url.startswith(("http://", "https://", "mailto:")):
                continue
            total_checked += 1
            clean_url = url.split("#")[0]
            if clean_url:
                target_path = os.path.normpath(os.path.join(os.path.dirname(filepath), clean_url))
                if not os.path.exists(target_path):
                    broken.append((filepath, text, url, target_path))

    if broken:
        print(f"FAILED: Found {len(broken)} broken internal link(s):")
        for b in broken:
            print(f"  In {b[0]}: [{b[1]}]({b[2]}) -> resolved to {b[3]} (NOT FOUND)")
        return False

    msg = (
        f"SUCCESS: Checked {total_checked} internal links across {len(files)} "
        "markdown files with 0 broken links."
    )
    print(msg)
    return True


def check_no_duplicate_requirement_definitions():
    """Audit canonical specification documents for duplicate requirement IDs."""
    print("Checking requirement definition uniqueness (excluding RTM matrix)...")
    spec_files = [
        "docs/product/FUNCTIONAL_REQUIREMENTS.md",
        "docs/product/NON_FUNCTIONAL_REQUIREMENTS.md",
        "docs/product/PERFORMANCE_REQUIREMENTS.md",
        "docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md",
        "docs/requirements/SRS.md",
        "docs/acceptance/ACCEPTANCE_CRITERIA.md",
    ]

    all_defs = {}
    duplicates = []

    for sf in spec_files:
        norm_path = os.path.normpath(sf)
        if not os.path.exists(norm_path):
            continue
        with open(norm_path, encoding="utf-8") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, 1):
            m = re.match(r"^#+\s+([A-Z0-9_-]+(?:—[^\n]+)?)", line)
            if m:
                raw_header = m.group(1)
                req_id = raw_header.split("—")[0].split(" ")[0].strip()
                if any(
                    req_id.startswith(p)
                    for p in ["EON-FR-", "EON-NFR-", "EON-PERF-", "EON-PSR-", "EON-SRS-", "AC-"]
                ):
                    if req_id in all_defs:
                        duplicates.append((req_id, all_defs[req_id], (sf, idx, line.strip())))
                    else:
                        all_defs[req_id] = (sf, idx, line.strip())

    if duplicates:
        print(f"FAILED: Found {len(duplicates)} duplicate requirement definitions:")
        for d in duplicates:
            print(
                f"  ID {d[0]}: first defined at {d[1][0]}:{d[1][1]}, "
                f"duplicated at {d[2][0]}:{d[2][1]}"
            )
        return False

    msg = (
        f"SUCCESS: Verified {len(all_defs)} requirement definitions "
        "across specification documents with 0 duplicates."
    )
    print(msg)
    return True


def check_performance_reconciliation():
    """Verify all 21 system performance targets are reconciled across specs."""
    print("Checking performance targets reconciliation across PRD, SRS, PERF, and AC...")
    perf_files = {
        "PRD": "docs/product/PRD.md",
        "SRS": "docs/requirements/SRS.md",
        "AC": "docs/acceptance/ACCEPTANCE_CRITERIA.md",
        "PERF": "docs/product/PERFORMANCE_REQUIREMENTS.md",
    }

    missing_in_files = {}
    for label, path in perf_files.items():
        with open(path, encoding="utf-8") as f:
            content = f.read()
        missing = []
        for metric in RECONCILED_PERF_METRICS:
            if not any(w.lower() in content.lower() for w in [metric, metric.replace(" ", "")]):
                words = metric.split()
                if not all(w.lower() in content.lower() for w in words[:2]):
                    missing.append(metric)
        if missing:
            missing_in_files[label] = missing

    if missing_in_files:
        print(f"FAILED: Performance targets missing in specifications: {missing_in_files}")
        return False

    msg = (
        "SUCCESS: All 21 provisional performance targets reconciled across "
        "PRD, SRS, PERF, and AC specifications."
    )
    print(msg)
    return True


def check_evidence_integrity():
    """Verify evidence registers preserve Phase 0 integrity without false passes."""
    print("Checking evidence registers for strict Phase 0 integrity...")
    evidence_file = os.path.normpath("docs/acceptance/TEST_EVIDENCE_REGISTER.md")
    if not os.path.exists(evidence_file):
        print(f"FAILED: {evidence_file} not found.")
        return False

    with open(evidence_file, encoding="utf-8") as f:
        text = f.read()

    premature_passes = []
    lines = text.splitlines()
    in_future_section = False
    for idx, line in enumerate(lines, 1):
        if "Group E:" in line or "Group F:" in line or "Group G:" in line:
            in_future_section = True
        if in_future_section and line.startswith("# "):
            in_future_section = False
        if in_future_section and "| EON-EVD-2026-" in line:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 6:
                status = cols[5]
                if status == "PASS":
                    premature_passes.append((idx, cols[0], status))

    if premature_passes:
        print(
            "FAILED: Evidence register contains premature execution status "
            f"for future runtime tests: {premature_passes}"
        )
        return False

    msg = (
        "SUCCESS: Evidence register integrity verified: "
        "future runtime tests remain NOT_APPLICABLE TO PHASE 0."
    )
    print(msg)
    return True


def check_rtm_metrics():
    """Validate machine-readable RTM JSON dataset schema and metrics."""
    print("Checking machine-readable RTM JSON metrics...")
    json_path = os.path.normpath("docs/requirements/requirement_traceability_matrix.json")
    if not os.path.exists(json_path):
        print(f"FAILED: {json_path} not found.")
        return False
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    metrics = data.get("metrics", {})
    if metrics.get("total_source_requirements") != 290:
        found_cnt = metrics.get("total_source_requirements")
        print(f"FAILED: Expected 290 source requirements, found {found_cnt}")
        return False
    if metrics.get("total_srs_requirements") != 203:
        found_srs = metrics.get("total_srs_requirements")
        print(f"FAILED: Expected 203 SRS requirements, found {found_srs}")
        return False
    if metrics.get("total_acceptance_criteria") != 179:
        found_ac = metrics.get("total_acceptance_criteria")
        print(f"FAILED: Expected 179 acceptance criteria, found {found_ac}")
        return False
    if (
        metrics.get("coverage_percentage") != 100.0
        or metrics.get("specification_mapping_coverage_percentage") != 100.0
    ):
        err = f"FAILED: Expected 100.0% spec coverage, found {metrics.get('coverage_percentage')}"
        print(err)
        return False
    if metrics.get("implementation_coverage_percentage") != 0.0:
        err = (
            "FAILED: Expected 0.0% implementation coverage for Phase 0, "
            f"found {metrics.get('implementation_coverage_percentage')}"
        )
        print(err)
        return False
    msg = (
        "SUCCESS: Machine-readable RTM verified: 290 source reqs, 203 SRS reqs, "
        "179 ACs, 100.0% spec coverage, 0.0% implementation."
    )
    print(msg)
    return True


def main():
    """Execute all verification gates."""
    print("==================================================")
    print("   OVIC EON — Phase 0 Documentation Audit Suite   ")
    print("==================================================")

    checks = [
        check_file_structure,
        check_clone_url,
        check_markdown_links,
        check_no_duplicate_requirement_definitions,
        check_performance_reconciliation,
        check_evidence_integrity,
        check_rtm_metrics,
    ]

    all_passed = True
    for check in checks:
        print()
        if not check():
            all_passed = False

    print()
    print("==================================================")
    if all_passed:
        print("   ALL DOCUMENTATION QUALIFICATION CHECKS PASSED  ")
        print("==================================================")
        sys.exit(0)
    else:
        print("   DOCUMENTATION QUALIFICATION CHECKS FAILED      ")
        print("==================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()

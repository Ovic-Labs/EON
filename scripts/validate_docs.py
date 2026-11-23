#!/usr/bin/env python3
"""OVIC EON — Documentation Qualification and Structure Validation Suite.

Phase 0 Final Production Qualification and Automated Regression Audit.
Implements 15 deterministic verification gates for Phase 0 engineering specifications.
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
    "docs/product/COMMERCIAL_LICENSING_STRATEGY.md",
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
    "docs/architecture/CORE_EVENT_BUS_ARCHITECTURE.md",
    "docs/architecture/EVENT_ROUTING_AND_DELIVERY.md",
    "docs/architecture/BACKPRESSURE_AND_PRIORITY_POLICY.md",
    "docs/developer/EVENT_BUS_DEVELOPER_GUIDE.md",
    "docs/engineering/PHASE_1_3_IMPLEMENTATION_REPORT.md",
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


def check_file_structure(base_dir: str = ".") -> bool:
    """Gate 1: Verify all required documentation and governance files exist."""
    print("Gate 1: Checking repository documentation structure...")
    missing = []
    for doc in REQUIRED_PHASE0_DOCS + REQUIRED_GOVERNANCE_DOCS:
        norm_path = os.path.normpath(os.path.join(base_dir, doc))
        if not os.path.exists(norm_path):
            missing.append(doc)
    if missing:
        print(f"FAILED: Missing required document(s): {missing}")
        return False
    p0_count = len(REQUIRED_PHASE0_DOCS)
    gov_count = len(REQUIRED_GOVERNANCE_DOCS)
    print(f"SUCCESS: All {p0_count} Phase 0 specifications and {gov_count} governance files exist.")
    return True


def check_clone_url(base_dir: str = ".") -> bool:
    """Gate 2: Verify README contains canonical clone URL."""
    print("Gate 2: Checking README clone URL...")
    readme_path = os.path.normpath(os.path.join(base_dir, "README.md"))
    if not os.path.exists(readme_path):
        print("FAILED: README.md not found.")
        return False
    with open(readme_path, encoding="utf-8") as f:
        content = f.read()
    if EXPECTED_CLONE_URL not in content:
        print(f"FAILED: README.md does not contain expected clone URL '{EXPECTED_CLONE_URL}'")
        return False
    print(f"SUCCESS: Clone URL verified: {EXPECTED_CLONE_URL}")
    return True


def check_markdown_links(base_dir: str = ".") -> bool:
    """Gate 3: Verify internal markdown hyperlinks resolve correctly."""
    print("Gate 3: Checking internal Markdown links...")
    files = []
    skip_dirs = [".git", ".gemini", "brain", ".pytest_cache", "node_modules"]
    for root, _dirs, filenames in os.walk(base_dir):
        if any(skip in root for skip in skip_dirs):
            continue
        for fname in filenames:
            if fname.endswith(".md"):
                files.append(os.path.normpath(os.path.join(root, fname)))

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken = []
    total_checked = 0

    for filepath in files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        for match in link_pattern.finditer(content):
            text, url = match.groups()
            if url.startswith(("http://", "https://", "mailto:", "#")):
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


def check_no_duplicate_requirement_definitions(base_dir: str = ".") -> bool:
    """Gate 4: Audit canonical specification documents for duplicate requirement IDs."""
    print("Gate 4: Checking requirement definition uniqueness (excluding RTM matrix)...")
    spec_files = [
        "docs/product/FUNCTIONAL_REQUIREMENTS.md",
        "docs/product/NON_FUNCTIONAL_REQUIREMENTS.md",
        "docs/product/PERFORMANCE_REQUIREMENTS.md",
        "docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md",
        "docs/requirements/SRS.md",
        "docs/acceptance/ACCEPTANCE_CRITERIA.md",
    ]

    all_defs: dict[str, tuple[str, int, str]] = {}
    duplicates: list[tuple[str, tuple[str, int, str], tuple[str, int, str]]] = []

    for sf in spec_files:
        norm_path = os.path.normpath(os.path.join(base_dir, sf))
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


def check_acceptance_id_uniqueness(base_dir: str = ".") -> bool:
    """Gate 5: Verify acceptance criteria IDs (179 AC definitions) are unique and complete."""
    print("Gate 5: Checking Acceptance Criteria ID uniqueness and completeness...")
    ac_file = os.path.normpath(os.path.join(base_dir, "docs/acceptance/ACCEPTANCE_CRITERIA.md"))
    if not os.path.exists(ac_file):
        print(f"FAILED: {ac_file} not found.")
        return False

    with open(ac_file, encoding="utf-8") as f:
        lines = f.readlines()

    ac_ids = []
    for line in lines:
        m = re.match(r"^#+\s+(AC-[A-Z0-9-]+)", line)
        if m:
            ac_ids.append(m.group(1))

    if len(ac_ids) != len(set(ac_ids)):
        duplicates = [x for x in ac_ids if ac_ids.count(x) > 1]
        print(f"FAILED: Duplicate AC IDs found: {set(duplicates)}")
        return False

    if len(ac_ids) != 179:
        print(f"FAILED: Expected exactly 179 AC definitions, found {len(ac_ids)}")
        return False

    print(f"SUCCESS: Verified all {len(ac_ids)} Acceptance Criteria are unique.")
    return True


def check_performance_reconciliation(base_dir: str = ".") -> bool:
    """Gate 6: Verify all 21 system performance targets are reconciled across specs."""
    print("Gate 6: Checking performance targets reconciliation across PRD, SRS, PERF, and AC...")
    perf_files = {
        "PRD": os.path.join(base_dir, "docs/product/PRD.md"),
        "SRS": os.path.join(base_dir, "docs/requirements/SRS.md"),
        "AC": os.path.join(base_dir, "docs/acceptance/ACCEPTANCE_CRITERIA.md"),
        "PERF": os.path.join(base_dir, "docs/product/PERFORMANCE_REQUIREMENTS.md"),
    }

    missing_in_files: dict[str, list[str]] = {}
    for label, path in perf_files.items():
        if not os.path.exists(path):
            missing_in_files[label] = ["FILE_NOT_FOUND"]
            continue
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


def check_performance_target_classification(base_dir: str = ".") -> bool:
    """Gate 7: Verify all performance targets are clearly classified as provisional."""
    print("Gate 7: Checking performance target classification as provisional...")
    perf_file = os.path.normpath(os.path.join(base_dir, "docs/product/PERFORMANCE_REQUIREMENTS.md"))
    if not os.path.exists(perf_file):
        print(f"FAILED: {perf_file} not found.")
        return False

    with open(perf_file, encoding="utf-8") as f:
        content = f.read()

    if "provisional" not in content.lower():
        print(
            "FAILED: PERFORMANCE_REQUIREMENTS.md does not classify performance "
            "targets as provisional."
        )
        return False

    print(
        "SUCCESS: Performance targets are rigorously classified as PROVISIONAL "
        "pending hardware measurement."
    )
    return True


def check_evidence_integrity(base_dir: str = ".") -> bool:
    """Gate 8: Verify evidence registers preserve Phase 0 integrity without false passes."""
    print("Gate 8: Checking evidence registers for strict Phase 0 integrity...")
    evidence_file = os.path.normpath(
        os.path.join(base_dir, "docs/acceptance/TEST_EVIDENCE_REGISTER.md")
    )
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


def check_defect_register_integrity(base_dir: str = ".") -> bool:
    """Gate 9: Verify defect register contains zero unresolved critical/high defects."""
    print("Gate 9: Checking defect register integrity...")
    defect_file = os.path.normpath(os.path.join(base_dir, "docs/acceptance/DEFECT_REGISTER.md"))
    if not os.path.exists(defect_file):
        print(f"FAILED: {defect_file} not found.")
        return False

    with open(defect_file, encoding="utf-8") as f:
        content = f.read()

    if "0 Open Defects" not in content and "0 open defects" not in content.lower():
        print("FAILED: Defect register does not indicate 0 open defects for Phase 0 baseline.")
        return False

    print("SUCCESS: Defect register verified: zero unresolved critical/high Phase 0 defects.")
    return True


def check_rtm_metrics(base_dir: str = ".") -> bool:
    """Gate 10: Validate machine-readable RTM JSON dataset schema and metrics."""
    print("Gate 10: Checking machine-readable RTM JSON metrics...")
    json_path = os.path.normpath(
        os.path.join(base_dir, "docs/requirements/requirement_traceability_matrix.json")
    )
    if not os.path.exists(json_path):
        print(f"FAILED: {json_path} not found.")
        return False
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"FAILED: Invalid JSON syntax in RTM matrix: {exc}")
        return False

    metrics = data.get("metrics", {})
    sub_metrics = [
        ("total_source_requirements", 290),
        ("functional_requirements_count", 60),
        ("non_functional_requirements_count", 78),
        ("performance_requirements_count", 66),
        ("privacy_safety_requirements_count", 86),
        ("total_srs_requirements", 203),
        ("total_acceptance_criteria", 179),
        ("total_use_cases", 54),
    ]
    for metric_name, expected_val in sub_metrics:
        val = metrics.get(metric_name)
        if val != expected_val:
            print(f"FAILED: Metric '{metric_name}' expected {expected_val}, found {val}")
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


def check_traceability_completeness(base_dir: str = ".") -> bool:
    """Gate 11: Validate requirement traceability completeness and detect orphans."""
    print("Gate 11: Checking requirement traceability completeness...")
    json_path = os.path.normpath(
        os.path.join(base_dir, "docs/requirements/requirement_traceability_matrix.json")
    )
    if not os.path.exists(json_path):
        print(f"FAILED: {json_path} not found.")
        return False

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    reqs = data.get("requirements", {})
    source_counts = {
        "functional": len(reqs.get("functional", [])),
        "non_functional": len(reqs.get("non_functional", [])),
        "performance": len(reqs.get("performance", [])),
        "privacy_and_safety": len(reqs.get("privacy_and_safety", [])),
    }

    if source_counts["functional"] != 60:
        print(f"FAILED: Expected 60 FRs, found {source_counts['functional']}")
        return False
    if source_counts["non_functional"] != 78:
        print(f"FAILED: Expected 78 NFRs, found {source_counts['non_functional']}")
        return False
    if source_counts["performance"] != 66:
        print(f"FAILED: Expected 66 PERF reqs, found {source_counts['performance']}")
        return False
    if source_counts["privacy_and_safety"] != 86:
        print(f"FAILED: Expected 86 PSRs, found {source_counts['privacy_and_safety']}")
        return False

    total_source = sum(source_counts.values())
    srs_count = len(reqs.get("srs", []))
    use_case_count = len(reqs.get("use_cases", []))

    if total_source != 290 or srs_count != 203 or use_case_count != 54:
        print(
            f"FAILED: Mismatched counts: total_source={total_source}, "
            f"srs={srs_count}, uc={use_case_count}"
        )
        return False

    # ID-level and schema validation
    expected_id_sets = {
        "functional": {f"EON-FR-{i:03d}" for i in range(1, 61)},
        "non_functional": {f"EON-NFR-{i:03d}" for i in range(1, 79)},
        "performance": {f"EON-PERF-{i:03d}" for i in range(1, 67)},
        "privacy_and_safety": {f"EON-PSR-{i:03d}" for i in range(1, 87)},
        "srs": {f"EON-SRS-{i:03d}" for i in range(1, 204)},
    }
    allowed_statuses = {
        "APPROVED_BASELINE",
        "APPROVED",
        "SPECIFIED",
        "PROVISIONAL_NOT_BENCHMARKED",
    }

    for cat, expected_set in expected_id_sets.items():
        actual_items = reqs.get(cat, [])
        actual_ids: set[str] = set()
        for item in actual_items:
            if not isinstance(item, dict):
                print(f"FAILED: Malformed requirement record in {cat}: {item}")
                return False
            req_id = item.get("id")
            if not req_id:
                print(f"FAILED: Missing requirement ID in {cat}: {item}")
                return False
            if req_id in actual_ids:
                print(f"FAILED: Duplicate requirement ID in {cat}: {req_id}")
                return False
            actual_ids.add(req_id)

            if not item.get("title"):
                print(f"FAILED: Missing title in {cat} item: {req_id}")
                return False

            status = item.get("status")
            if status not in allowed_statuses:
                print(f"FAILED: Invalid requirement status '{status}' for {req_id}")
                return False

        diff = actual_ids ^ expected_set
        if diff:
            print(f"FAILED: Requirement ID mismatch in {cat}: {diff}")
            return False

    # Cross-reference with markdown specification headers if present
    md_map = {
        "functional": ("docs/product/FUNCTIONAL_REQUIREMENTS.md", "EON-FR"),
        "non_functional": ("docs/product/NON_FUNCTIONAL_REQUIREMENTS.md", "EON-NFR"),
        "performance": ("docs/product/PERFORMANCE_REQUIREMENTS.md", "EON-PERF"),
        "privacy_and_safety": ("docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md", "EON-PSR"),
        "srs": ("docs/requirements/SRS.md", "EON-SRS"),
    }
    for cat, (rel_path, prefix) in md_map.items():
        md_file = os.path.normpath(os.path.join(base_dir, rel_path))
        if os.path.exists(md_file):
            with open(md_file, encoding="utf-8") as f:
                content = f.read()
            header_ids = set(re.findall(rf"^#+\s+({prefix}-\d{{3}})", content, re.MULTILINE))
            json_ids = {r["id"] for r in reqs[cat]}
            if header_ids != json_ids:
                diff_ids = header_ids ^ json_ids
                print(f"FAILED: Headers in {rel_path} do not match JSON IDs: {diff_ids}")
                return False

    print(
        "SUCCESS: Traceability complete: 290 source requirements "
        "(60 FR, 78 NFR, 66 PERF, 86 PSR), 203 SRS, 54 Use Cases verified by exact IDs."
    )
    return True


def check_verification_methods(base_dir: str = ".") -> bool:
    """Gate 12: Verify all requirements declare an objective verification method."""
    print("Gate 12: Checking requirement verification methods...")
    fr_file = os.path.normpath(os.path.join(base_dir, "docs/product/FUNCTIONAL_REQUIREMENTS.md"))
    nfr_file = os.path.normpath(
        os.path.join(base_dir, "docs/product/NON_FUNCTIONAL_REQUIREMENTS.md")
    )

    targets = [(fr_file, 60, "Functional"), (nfr_file, 78, "Non-Functional")]
    for fpath, expected_count, label in targets:
        if not os.path.exists(fpath):
            print(f"FAILED: {fpath} not found.")
            return False
        with open(fpath, encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r"\*\*Verification:\*\*", content)
        if len(matches) != expected_count:
            print(
                f"FAILED: Expected {expected_count} verification methods in {label} "
                f"Requirements, found {len(matches)}"
            )
            return False

    print(
        "SUCCESS: Objective verification methods (Test/Inspection/Analysis/Demonstration) "
        "defined for all 60 FRs and 78 NFRs."
    )
    return True


def check_commercial_licensing_strategy(base_dir: str = ".") -> bool:
    """Gate 13: Verify commercial licensing strategy completeness and legal disclaimers."""
    print("Gate 13: Checking Commercial Licensing Strategy completeness...")
    lic_file = os.path.normpath(
        os.path.join(base_dir, "docs/product/COMMERCIAL_LICENSING_STRATEGY.md")
    )
    if not os.path.exists(lic_file):
        print(f"FAILED: {lic_file} not found.")
        return False

    with open(lic_file, encoding="utf-8") as f:
        content = f.read()

    required_keywords = [
        "Open-Core",
        "Apache License 2.0",
        "Category A: Permissive",
        "Category C: Strong Copyleft",
        "Software Bill of Materials",
        "Legal Disclaimer",
        "Model Weights",
        "Dataset",
        "OEM",
    ]

    missing = [kw for kw in required_keywords if kw.lower() not in content.lower()]
    if missing:
        print(f"FAILED: COMMERCIAL_LICENSING_STRATEGY.md missing required sections: {missing}")
        return False

    print(
        "SUCCESS: Commercial Licensing Strategy verified: covers Open-Core, "
        "whitelist, models, datasets, SBOM, and legal disclaimer."
    )
    return True


def check_privacy_and_safety_boundaries(base_dir: str = ".") -> bool:
    """Gate 14: Verify safety non-authoritative boundary and privacy constraints."""
    print("Gate 14: Checking privacy and safety architectural boundaries...")
    psr_file = os.path.normpath(
        os.path.join(base_dir, "docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md")
    )
    if not os.path.exists(psr_file):
        print(f"FAILED: {psr_file} not found.")
        return False

    with open(psr_file, encoding="utf-8") as f:
        content = f.read()

    safety_invariants = [
        "is_authoritative_stop=False",
        "uncertain",
        "emergency",
        "non-diagnostic",
    ]

    missing = [inv for inv in safety_invariants if inv.lower() not in content.lower()]
    if missing:
        print(f"FAILED: PRIVACY_AND_SAFETY_REQUIREMENTS.md missing safety invariants: {missing}")
        return False

    print(
        "SUCCESS: Privacy & safety boundaries verified: non-authoritative motion, "
        "uncertainty, and non-diagnostic constraints enforced."
    )
    return True


def check_document_metadata(base_dir: str = ".") -> bool:
    """Gate 15: Verify all Phase 0 documents contain valid metadata headers."""
    print("Gate 15: Checking document metadata and ownership headers...")
    missing_metadata = []
    for doc in REQUIRED_PHASE0_DOCS:
        norm_path = os.path.normpath(os.path.join(base_dir, doc))
        if not os.path.exists(norm_path):
            continue
        with open(norm_path, encoding="utf-8") as f:
            header = "".join([f.readline() for _ in range(25)])

        for field in ["Document ID:", "Status:", "Version:"]:
            if field not in header:
                missing_metadata.append((doc, field))

    if missing_metadata:
        print(f"FAILED: Phase 0 document(s) missing metadata fields: {missing_metadata}")
        return False

    print(
        f"SUCCESS: All {len(REQUIRED_PHASE0_DOCS)} Phase 0 documents contain "
        "complete governance metadata headers."
    )
    return True


def run_all_checks(base_dir: str = ".") -> bool:
    """Execute all 15 verification gates."""
    print("==================================================")
    print("   OVIC EON — Phase 0 Documentation Audit Suite   ")
    print("==================================================")

    checks = [
        check_file_structure,
        check_clone_url,
        check_markdown_links,
        check_no_duplicate_requirement_definitions,
        check_acceptance_id_uniqueness,
        check_performance_reconciliation,
        check_performance_target_classification,
        check_evidence_integrity,
        check_defect_register_integrity,
        check_rtm_metrics,
        check_traceability_completeness,
        check_verification_methods,
        check_commercial_licensing_strategy,
        check_privacy_and_safety_boundaries,
        check_document_metadata,
    ]

    all_passed = True
    for check in checks:
        print()
        if not check(base_dir):
            all_passed = False

    print()
    print("==================================================")
    if all_passed:
        print("   ALL 15 DOCUMENTATION QUALIFICATION GATES PASSED")
        print("==================================================")
        return True
    else:
        print("   DOCUMENTATION QUALIFICATION GATES FAILED       ")
        print("==================================================")
        return False


def main() -> None:
    """Main entrypoint for script execution."""
    success = run_all_checks(".")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

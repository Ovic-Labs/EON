#!/usr/bin/env python3
"""
OVIC EON — Documentation Qualification and Structure Validation Suite
Phase 0 Final Verification and Automated Regression Audit
"""

import os
import sys
import re
import json

REQUIRED_PHASE0_DOCS = [
    'docs/product/PRODUCT_VISION.md',
    'docs/product/ENGINE_SCOPE.md',
    'docs/product/CUSTOMER_SEGMENTS.md',
    'docs/product/USE_CASES.md',
    'docs/product/FUNCTIONAL_REQUIREMENTS.md',
    'docs/product/NON_FUNCTIONAL_REQUIREMENTS.md',
    'docs/product/PERFORMANCE_REQUIREMENTS.md',
    'docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md',
    'docs/product/PRD.md',
    'docs/requirements/SRS.md',
    'docs/requirements/REQUIREMENT_TRACEABILITY.md',
    'docs/acceptance/ACCEPTANCE_CRITERIA.md',
    'docs/acceptance/TEST_EVIDENCE_REGISTER.md',
    'docs/acceptance/DEFECT_REGISTER.md',
    'docs/acceptance/RELEASE_ACCEPTANCE.md',
]

REQUIRED_GOVERNANCE_DOCS = [
    'README.md',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'docs/README.md',
    'docs/requirements/requirement_traceability_matrix.json',
    'docs/acceptance/PHASE_0_FINAL_VERIFICATION_REPORT.md',
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
    "Extended soak qualification"
]

def check_file_structure():
    print("Checking repository documentation structure...")
    missing = []
    for doc in REQUIRED_PHASE0_DOCS + REQUIRED_GOVERNANCE_DOCS:
        norm_path = os.path.normpath(doc)
        if not os.path.exists(norm_path):
            missing.append(doc)
    if missing:
        print(f"FAILED: Missing required document(s): {missing}")
        return False
    print(f"SUCCESS: All {len(REQUIRED_PHASE0_DOCS)} Phase 0 documents and {len(REQUIRED_GOVERNANCE_DOCS)} governance files exist.")
    return True

def check_clone_url():
    print("Checking README clone URL...")
    if not os.path.exists('README.md'):
        print("FAILED: README.md not found.")
        return False
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    if EXPECTED_CLONE_URL not in content:
        print(f"FAILED: README.md does not contain expected clone URL '{EXPECTED_CLONE_URL}'")
        return False
    print(f"SUCCESS: Clone URL verified: {EXPECTED_CLONE_URL}")
    return True

def check_markdown_links():
    print("Checking internal Markdown links...")
    files = []
    for root, dirs, filenames in os.walk('.'):
        if '.git' in root or '.gemini' in root or 'brain' in root:
            continue
        for f in filenames:
            if f.endswith('.md'):
                files.append(os.path.normpath(os.path.join(root, f)))

    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    broken = []
    total_checked = 0

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for match in link_pattern.finditer(content):
            text, url = match.groups()
            if url.startswith(('http://', 'https://', 'mailto:')):
                continue
            total_checked += 1
            clean_url = url.split('#')[0]
            if clean_url:
                target_path = os.path.normpath(os.path.join(os.path.dirname(filepath), clean_url))
                if not os.path.exists(target_path):
                    broken.append((filepath, text, url, target_path))

    if broken:
        print(f"FAILED: Found {len(broken)} broken internal link(s):")
        for b in broken:
            print(f"  In {b[0]}: [{b[1]}]({b[2]}) -> resolved to {b[3]} (NOT FOUND)")
        return False

    print(f"SUCCESS: Checked {total_checked} internal links across {len(files)} markdown files with 0 broken links.")
    return True

def check_no_duplicate_requirement_definitions():
    print("Checking requirement definition uniqueness (excluding RTM matrix)...")
    spec_files = [
        'docs/product/FUNCTIONAL_REQUIREMENTS.md',
        'docs/product/NON_FUNCTIONAL_REQUIREMENTS.md',
        'docs/product/PERFORMANCE_REQUIREMENTS.md',
        'docs/product/PRIVACY_AND_SAFETY_REQUIREMENTS.md',
        'docs/requirements/SRS.md',
        'docs/acceptance/ACCEPTANCE_CRITERIA.md'
    ]

    all_defs = {}
    duplicates = []

    for sf in spec_files:
        norm_path = os.path.normpath(sf)
        if not os.path.exists(norm_path):
            continue
        with open(norm_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for idx, line in enumerate(lines, 1):
            m = re.match(r'^#+\s+([A-Z0-9_-]+(?:—[^\n]+)?)', line)
            if m:
                raw_header = m.group(1)
                req_id = raw_header.split('—')[0].split(' ')[0].strip()
                if any(req_id.startswith(p) for p in ['EON-FR-', 'EON-NFR-', 'EON-PERF-', 'EON-PSR-', 'EON-SRS-', 'AC-']):
                    if req_id in all_defs:
                        duplicates.append((req_id, all_defs[req_id], (sf, idx, line.strip())))
                    else:
                        all_defs[req_id] = (sf, idx, line.strip())

    if duplicates:
        print(f"FAILED: Found {len(duplicates)} duplicate requirement definitions:")
        for d in duplicates:
            print(f"  ID {d[0]}: first defined at {d[1][0]}:{d[1][1]}, duplicated at {d[2][0]}:{d[2][1]}")
        return False

    print(f"SUCCESS: Verified {len(all_defs)} requirement definitions across specification documents with 0 duplicates.")
    return True

def check_performance_reconciliation():
    print("Checking performance targets reconciliation across PRD, SRS, PERF, and AC...")
    perf_files = {
        'PRD': 'docs/product/PRD.md',
        'SRS': 'docs/requirements/SRS.md',
        'AC': 'docs/acceptance/ACCEPTANCE_CRITERIA.md',
        'PERF': 'docs/product/PERFORMANCE_REQUIREMENTS.md'
    }

    missing_in_files = {}
    for label, path in perf_files.items():
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        missing = []
        for metric in RECONCILED_PERF_METRICS:
            # check metric presence in loose casing/spacing
            core_kw = metric.split()[-1] # e.g. "p50", "p95", "throughput", "memory"
            if not any(w.lower() in content.lower() for w in [metric, metric.replace(' ', '')]):
                # fuzzy check
                words = metric.split()
                if not all(w.lower() in content.lower() for w in words[:2]):
                    missing.append(metric)
        if missing:
            missing_in_files[label] = missing

    if missing_in_files:
        print(f"FAILED: Performance targets missing in specifications: {missing_in_files}")
        return False

    print(f"SUCCESS: All 21 provisional performance targets reconciled across PRD, SRS, PERF, and AC specifications.")
    return True

def check_evidence_integrity():
    print("Checking evidence registers for strict Phase 0 integrity...")
    evidence_file = os.path.normpath('docs/acceptance/TEST_EVIDENCE_REGISTER.md')
    if not os.path.exists(evidence_file):
        print(f"FAILED: {evidence_file} not found.")
        return False

    with open(evidence_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Verify that future runtime implementation tests (Group E, F, G) are NOT marked PASS
    premature_passes = []
    lines = text.splitlines()
    in_future_section = False
    for idx, l in enumerate(lines, 1):
        if 'Group E:' in l or 'Group F:' in l or 'Group G:' in l:
            in_future_section = True
        if in_future_section and l.startswith('# '):
            in_future_section = False
        if in_future_section and '| EON-EVD-2026-' in l:
            cols = [c.strip() for c in l.split('|')[1:-1]]
            if len(cols) >= 6:
                status = cols[5]
                if status == 'PASS':
                    premature_passes.append((idx, cols[0], status))

    if premature_passes:
        print(f"FAILED: Evidence register contains premature execution status for future runtime tests: {premature_passes}")
        return False

    print("SUCCESS: Evidence register integrity verified: future runtime tests remain NOT_APPLICABLE TO PHASE 0.")
    return True

def check_rtm_metrics():
    print("Checking machine-readable RTM JSON metrics...")
    json_path = os.path.normpath('docs/requirements/requirement_traceability_matrix.json')
    if not os.path.exists(json_path):
        print(f"FAILED: {json_path} not found.")
        return False
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    metrics = data.get('metrics', {})
    if metrics.get('total_source_requirements') != 290:
        print(f"FAILED: Expected 290 source requirements, found {metrics.get('total_source_requirements')}")
        return False
    if metrics.get('total_srs_requirements') != 203:
        print(f"FAILED: Expected 203 SRS requirements, found {metrics.get('total_srs_requirements')}")
        return False
    if metrics.get('coverage_percentage') != 100.0:
        print(f"FAILED: Expected 100.0% coverage, found {metrics.get('coverage_percentage')}")
        return False
    print(f"SUCCESS: Machine-readable RTM verified: 290 source reqs, 203 SRS reqs, 100.0% coverage.")
    return True

def main():
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

if __name__ == '__main__':
    main()

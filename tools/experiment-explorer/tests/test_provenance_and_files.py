"""Test suite for physical file existence, manifest parsing, and cryptographic SHA-256 integrity."""
from __future__ import annotations

import sys
from pathlib import Path

# Add explorer root
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pytest
from lib.loaders import get_enriched_trials, load_normalized_evidence_raw
from lib.provenance import (
    REPO_ROOT,
    compute_file_sha256,
    read_manifest_file,
    verify_file_integrity,
)


def test_admitted_files_physical_presence():
    """Verify that all 226 admitted raw evidence files physically exist on disk."""
    norm_data = load_normalized_evidence_raw()
    records = norm_data.get("records", [])

    missing_files = []

    for r in records:
        prov = r.get("provenance", {})

        mf = prov.get("manifest")
        if mf:
            p = REPO_ROOT / mf
            if not p.is_file():
                missing_files.append(f"Manifest missing: {mf}")

        res = prov.get("result")
        if res:
            p = REPO_ROOT / res
            if not p.is_file():
                missing_files.append(f"Result JSON missing: {res}")

        jfr = prov.get("jfr")
        if jfr:
            p = REPO_ROOT / jfr
            if not p.is_file():
                missing_files.append(f"JFR binary missing: {jfr}")

    assert len(missing_files) == 0, f"Found missing files: {missing_files}"


def test_admitted_files_sha256_cryptographic_matches():
    """Verify 100% cryptographic SHA-256 hash match rate for all normalized trial references."""
    norm_data = load_normalized_evidence_raw()
    records = norm_data.get("records", [])

    mismatches = []
    checked_count = 0

    for r in records:
        prov = r.get("provenance", {})

        # Check k6 result file
        res_path = prov.get("result")
        expected_res_sha = prov.get("result_sha256")
        if res_path and expected_res_sha:
            actual_sha = compute_file_sha256(res_path)
            checked_count += 1
            if actual_sha != expected_res_sha:
                mismatches.append(f"Result SHA mismatch: {res_path} (expected {expected_res_sha}, got {actual_sha})")

        # Check JFR file
        jfr_path = prov.get("jfr")
        expected_jfr_sha = prov.get("jfr_sha256")
        if jfr_path and expected_jfr_sha:
            actual_sha = compute_file_sha256(jfr_path)
            checked_count += 1
            if actual_sha != expected_jfr_sha:
                mismatches.append(f"JFR SHA mismatch: {jfr_path} (expected {expected_jfr_sha}, got {actual_sha})")

    assert checked_count == 151, f"Expected 151 hashed file references (76 results + 75 JFRs), checked {checked_count}"
    assert len(mismatches) == 0, f"Found cryptographic hash mismatches: {mismatches}"


def test_manifest_read_and_parse():
    """Verify that execution manifests are valid JSON and can be parsed."""
    trials = get_enriched_trials()
    manifest_trials = [t for t in trials if t.manifest_path]

    for t in manifest_trials:
        assert t.manifest_path is not None
        content = read_manifest_file(t.manifest_path)
        assert "error" not in content
        assert "run_id" in content
        assert content["run_id"] == t.run_id


def test_missing_and_tampered_artifact_detection():
    """Verify that missing files and corrupted hashes are strictly caught by provenance verification."""
    # Test non-existent file
    missing_ver = verify_file_integrity("results/non-existent-artifact-12345.json", "abc123expected")
    assert missing_ver["exists"] is False
    assert missing_ver["match"] is False
    assert missing_ver["status"] == "MISSING_FILE"

    # Test existing file with corrupted/wrong hash
    # Use real manifest file but pass invalid hash
    wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    tampered_ver = verify_file_integrity("results/run-manifest-20261015-142534.json", wrong_hash)
    assert tampered_ver["exists"] is True
    assert tampered_ver["match"] is False
    assert tampered_ver["status"] == "HASH_MISMATCH"


#!/usr/bin/env python3
"""Fail-closed integrity and cryptographic verification for the benchmark evidence dataset."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/main/resources/static/data/normalized-evidence.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not DATA.exists():
        print(f"FATAL: normalized evidence file missing at {DATA}", file=sys.stderr)
        return 1

    data = json.loads(DATA.read_text(encoding="utf-8"))
    records = data.get("records", [])
    assert data.get("schema_version") == 1, f"Unexpected schema_version: {data.get('schema_version')}"
    
    # Stratum consistency assertions
    assert len([r for r in records if r["run_set"] == "java21-synchronization-20261008-repeated"]) == 12
    assert len([r for r in records if r["run_set"] == "native-boundary-20261008-repeated"]) == 27
    
    for record in records:
        for key in ("run_id", "run_set", "condition_id", "metrics", "classification", "provenance"):
            assert key in record, f"missing {key} in {record.get('run_id')}"
        assert record["jfr"]["count"] is None or record["jfr"]["count"] >= 0

    historical_sync = [
        r for r in records
        if r["run_set"] == "java21-synchronization-20261008-repeated"
    ]
    assert all(
        r["jfr"]["count"] == 110
        for r in historical_sync
        if r["condition_id"] == "synchronized"
    )
    jni = [r for r in records if r["family"] == "jni-boundary"]
    assert len(jni) == 27 and all(r["jfr"]["count"] == 0 for r in jni)

    # Fail-closed physical existence and SHA-256 integrity verification
    verified_files = 0
    missing_files = []
    mismatched_files = []

    for r in records:
        prov = r.get("provenance", {})
        
        # Check manifest
        manifest_rel = prov.get("manifest")
        if manifest_rel:
            manifest_path = ROOT / manifest_rel
            if not manifest_path.exists():
                missing_files.append(str(manifest_path))
            else:
                verified_files += 1

        # Check result k6 file and SHA-256
        res_rel = prov.get("result")
        if res_rel:
            res_path = ROOT / res_rel
            if not res_path.exists():
                missing_files.append(str(res_path))
            else:
                expected_sha = prov.get("result_sha256")
                if expected_sha:
                    actual_sha = sha256_file(res_path)
                    if actual_sha != expected_sha:
                        mismatched_files.append((str(res_path), actual_sha, expected_sha))
                verified_files += 1

        # Check JFR recording and SHA-256
        jfr_rel = prov.get("jfr")
        if jfr_rel:
            jfr_path = ROOT / jfr_rel
            if not jfr_path.exists():
                missing_files.append(str(jfr_path))
            else:
                expected_sha = prov.get("jfr_sha256")
                if expected_sha:
                    actual_sha = sha256_file(jfr_path)
                    if actual_sha != expected_sha:
                        mismatched_files.append((str(jfr_path), actual_sha, expected_sha))
                verified_files += 1

    if missing_files:
        print(f"FAIL-CLOSED: {len(missing_files)} referenced evidence files are missing on disk:", file=sys.stderr)
        for m in missing_files[:10]:
            print(f"  MISSING: {m}", file=sys.stderr)
        return 1

    if mismatched_files:
        print(f"FAIL-CLOSED: {len(mismatched_files)} evidence files failed SHA-256 checksum verification:", file=sys.stderr)
        for path, actual, expected in mismatched_files[:10]:
            print(f"  MISMATCH: {path} (actual: {actual}, expected: {expected})", file=sys.stderr)
        return 1

    print(f"SUCCESS: Validated {len(records)} records and verified physical existence and SHA-256 integrity for {verified_files} raw files.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"validation assertion failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"validation failed with exception: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Small, dependency-free integrity check for the dashboard dataset."""
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "src/main/resources/static/data/normalized-evidence.json"


def main() -> int:
    data = json.loads(DATA.read_text())
    records = data["records"]
    assert data["schema_version"] == 1
    assert len([r for r in records if r["run_set"] == "java21-synchronization-20261008-repeated"]) == 12
    assert len([r for r in records if r["run_set"] == "native-boundary-20261008-repeated"]) == 27
    for record in records:
        for key in ("run_id", "run_set", "condition_id", "metrics", "classification", "provenance"):
            assert key in record, f"missing {key} in {record.get('run_id')}"
        assert record["jfr"]["count"] is None or record["jfr"]["count"] >= 0
    sync = [r for r in records if r["family"] == "synchronization"]
    assert all(r["jfr"]["count"] == 110 for r in sync if r["condition_id"] == "synchronized")
    jni = [r for r in records if r["family"] == "jni-boundary"]
    assert len(jni) == 27 and all(r["jfr"]["count"] == 0 for r in jni)
    print(f"validated {len(records)} records")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, json.JSONDecodeError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Normalize benchmark manifests, k6 JSONL and JFR evidence for the local dashboard.

This intentionally uses only the Python standard library.  It preserves one
record per manifest/trial and labels measured, derived and conceptual fields.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = ROOT / "src/main/resources/static/data/normalized-evidence.json"


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = max(0, min(len(values) - 1, math.ceil(p * len(values)) - 1))
    return round(values[index], 3)


def k6_metrics(path: Path) -> dict:
    durations: list[float] = []
    requests = failures = 0
    endpoints: set[str] = set()
    for line in path.read_text(errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("metric") == "http_req_duration" and item.get("type") == "Point":
            point = item.get("data", {})
            tags = point.get("tags", {})
            if tags.get("expected_response") != "false":
                durations.append(float(point.get("value", 0)))
            url = tags.get("url") or tags.get("name")
            if url:
                endpoints.add(url.rsplit("/", 1)[-1])
        if item.get("metric") == "http_reqs" and item.get("type") == "Point":
            requests += 1
            if item.get("data", {}).get("tags", {}).get("expected_response") == "false":
                failures += 1
    return {
        "requests": requests,
        "http_failures": failures,
        "failure_rate": round(failures / requests, 6) if requests else None,
        "median_ms": percentile(durations, 0.50),
        "p95_ms": percentile(durations, 0.95),
        "samples": len(durations),
        "endpoints": sorted(endpoints),
    }


def jfr_pinned(path: Path) -> dict:
    if not path.exists():
        return {"available": False, "count": None, "classification": "measured"}
    try:
        result = subprocess.run(
            ["jfr", "print", "--events", "jdk.VirtualThreadPinned", str(path)],
            text=True, capture_output=True, check=False,
        )
        count = result.stdout.count("jdk.VirtualThreadPinned {")
        return {"available": True, "count": count, "classification": "measured"}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "count": None, "error": str(exc),
                "classification": "measured"}


def load_manifest(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def label_condition(manifest: dict) -> tuple[str, str]:
    condition = manifest.get("condition_id") or manifest.get("lock_variant") or "unknown"
    if condition == "synchronized":
        return "synchronized", "Virtual Threads + synchronized"
    if condition == "platform-synchronized":
        return "platform-synchronized", "Platform Threads + synchronized"
    if condition == "reentrant-lock":
        return "reentrant-lock", "Virtual Threads + ReentrantLock"
    if condition == "no-lock-diagnostic":
        return "no-lock", "Virtual Threads + no-lock diagnostic"
    if condition == "blocking-jni":
        return "blocking-jni", "Blocking JNI"
    if condition == "native-short":
        return "native-short", "Short JNI control"
    if condition == "pure-java-sleep":
        return "pure-java-sleep", "Pure Java sleep control"
    return condition, condition.replace("-", " ").title()


def main() -> int:
    records = []
    manifests = sorted(RESULTS.glob("run-manifest-*.json"))
    for manifest_path in manifests:
        manifest = load_manifest(manifest_path)
        if not manifest or manifest.get("run_set") not in {
            "java21-synchronization-20261008-repeated",
            "native-boundary-20261008-repeated",
        }:
            continue
        condition_id, condition_label = label_condition(manifest)
        result_files = manifest.get("result_files") or []
        result_path = ROOT / result_files[0]["path"] if result_files else None
        jfr_path = ROOT / manifest["jfr_file"] if manifest.get("jfr_file") else None
        metrics = k6_metrics(result_path) if result_path and result_path.exists() else {}
        jfr = jfr_pinned(jfr_path) if jfr_path else {"available": False, "count": None}
        records.append({
            "trial_id": manifest.get("trial_id"),
            "run_id": manifest.get("run_id"),
            "run_set": manifest.get("run_set"),
            "family": "synchronization" if "synchronization" in manifest.get("run_set", "") else "jni-boundary",
            "condition_id": condition_id,
            "condition_label": condition_label,
            "jdk": manifest.get("java_vendor_and_version"),
            "jdk_major": (manifest.get("java_vendor_and_version") or "").split("version ")[-1].split(".")[0],
            "execution_mode": manifest.get("execution_mode"),
            "virtual_threads_enabled": manifest.get("virtual_threads_enabled", True),
            "target_vus": int(manifest.get("target_vus") or manifest.get("target_vus_or_arrival_rate") or 0),
            "timestamp_utc": manifest.get("timestamp_utc"),
            "metrics": metrics,
            "jfr": jfr,
            "classification": {
                "trial": "measured",
                "metrics": "measured from raw k6 JSONL",
                "jfr": "measured from JFR event stream; zero is explicit",
                "condition_label": "derived",
            },
            "provenance": {
                "manifest": str(manifest_path.relative_to(ROOT)),
                "result": result_files[0]["path"] if result_files else None,
                "result_sha256": sha256(result_path) if result_path else None,
                "jfr": manifest.get("jfr_file"),
                "jfr_sha256": sha256(jfr_path) if jfr_path else None,
                "git_commit": manifest.get("git_commit"),
                "native_enabled": manifest.get("native_enabled"),
            },
        })

    # CPU control is a standalone k6 artifact, not part of either repeated set.
    cpu_path = RESULTS / "cpu-control-20261008.json"
    if cpu_path.exists():
        records.append({
            "trial_id": "cpu-control-20261008",
            "run_id": "cpu-control-20261008",
            "run_set": "cpu-control-20261008",
            "family": "controls",
            "condition_id": "cpu-control",
            "condition_label": "CPU-only control",
            "jdk": "See CPU control artifact",
            "jdk_major": "unknown",
            "execution_mode": "unknown",
            "virtual_threads_enabled": None,
            "target_vus": None,
            "timestamp_utc": None,
            "metrics": k6_metrics(cpu_path),
            "jfr": {"available": False, "count": None},
            "classification": {
                "trial": "measured",
                "metrics": "measured from raw k6 JSONL",
                "jfr": "not available",
                "condition_label": "derived",
            },
            "provenance": {"result": str(cpu_path.relative_to(ROOT)),
                           "result_sha256": sha256(cpu_path)},
        })

    data = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": "Interactive Experimental Evidence Explorer",
        "records": records,
        "concepts": [
            {"id": "monitor-pinning", "label": "Java 21 monitor pinning",
             "classification": "conceptual",
             "text": "A Java 21 synchronized critical section can pin a virtual thread while blocking work executes."},
            {"id": "native-boundary", "label": "Native carrier occupation",
             "classification": "conceptual",
             "text": "Long JNI residency may occupy a carrier; the current JFR stream reports zero VirtualThreadPinned events, so this remains a behavioral interpretation."},
        ],
        "limitations": [
            "One-carrier scheduler settings are mechanism-isolation stress conditions, not production defaults.",
            "JFR event semantics differ across JDK releases; zero JNI events are explicit evidence, not proof of absence of carrier occupation.",
            "The no-lock condition is a diagnostic upper-bound control, not a valid payment design.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {OUT} ({len(records)} trial-level records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Unit tests for metric recalculation and workload clock anchoring."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import pytest

from scripts.recalculate_metrics import parse_k6_file, percentile


def test_percentile_calculation():
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert percentile(vals, 0.50) == 30.0
    assert percentile(vals, 0.95) == 50.0
    assert percentile([], 0.50) is None


def test_scenario_start_clock_anchoring():
    """Verify that slow initial request completion does not misanchor t0."""
    base_time = datetime(2026, 10, 8, 14, 0, 0, tzinfo=timezone.utc)
    
    # First request: starts at base_time, lasts 5000ms, finishes at base_time + 5s
    # Second request: starts at base_time + 16s, lasts 100ms, finishes at base_time + 16.1s (steady state)
    # Third request: starts at base_time + 50s, lasts 100ms, finishes at base_time + 50.1s (ramp down)
    points = [
        # Request 1 (first completion at +5s, but started at +0s)
        {
            "metric": "http_req_duration",
            "type": "Point",
            "data": {
                "time": (base_time + timedelta(seconds=5)).isoformat(),
                "value": 5000.0,
                "tags": {"expected_response": "true"},
            },
        },
        {
            "metric": "http_reqs",
            "type": "Point",
            "data": {
                "time": (base_time + timedelta(seconds=5)).isoformat(),
                "value": 1,
                "tags": {"expected_response": "true"},
            },
        },
        # Request 2 (steady state: +16s from t0, well within [15s, 45s])
        {
            "metric": "http_req_duration",
            "type": "Point",
            "data": {
                "time": (base_time + timedelta(seconds=16.1)).isoformat(),
                "value": 100.0,
                "tags": {"expected_response": "true"},
            },
        },
        {
            "metric": "http_reqs",
            "type": "Point",
            "data": {
                "time": (base_time + timedelta(seconds=16.1)).isoformat(),
                "value": 1,
                "tags": {"expected_response": "true"},
            },
        },
        # Request 3 (ramp-down: +50.1s from t0, outside [15s, 45s])
        {
            "metric": "http_req_duration",
            "type": "Point",
            "data": {
                "time": (base_time + timedelta(seconds=50.1)).isoformat(),
                "value": 100.0,
                "tags": {"expected_response": "true"},
            },
        },
        {
            "metric": "http_reqs",
            "type": "Point",
            "data": {
                "time": (base_time + timedelta(seconds=50.1)).isoformat(),
                "value": 1,
                "tags": {"expected_response": "true"},
            },
        },
    ]

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        for p in points:
            f.write(json.dumps(p) + "\n")
        temp_path = Path(f.name)

    try:
        metrics = parse_k6_file(temp_path)
        # t0 is base_time (14:00:00), t_max is 14:00:50.1 -> actual_span_s = 50.1s
        assert abs(metrics["actual_span_s"] - 50.1) < 0.01
        assert metrics["full_reqs"] == 3
        # In steady state [15s, 45s], only Request 2 falls in (elapsed 16.1s)
        assert metrics["steady_reqs"] == 1
        assert metrics["steady_p50"] == 100.0
        # Full duration throughput uses actual span
        assert abs(metrics["full_throughput"] - (3 / 50.1)) < 0.01
        # Steady throughput uses 30.0s window
        assert abs(metrics["steady_throughput"] - (1 / 30.0)) < 0.01
    finally:
        temp_path.unlink(missing_ok=True)


def test_reconciliation_k6_file_exists_and_parses():
    k6_file = Path("results/run-10vus-20261008-142445.json")
    if not k6_file.exists():
        pytest.skip("Reconciliation file results/run-10vus-20261008-142445.json not present in checkout")
    metrics = parse_k6_file(k6_file)
    assert metrics["full_reqs"] > 0
    assert metrics["steady_reqs"] > 0
    assert metrics["steady_throughput"] > 0
    assert metrics["actual_span_s"] > 30.0

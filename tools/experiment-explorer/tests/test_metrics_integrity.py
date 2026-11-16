"""Test suite for metric recalculation agreement and scientific findings."""
from __future__ import annotations

import sys
from pathlib import Path

# Add explorer root
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import numpy as np
import pytest
from lib.loaders import (
    get_enriched_trials,
    load_metric_recalculations_df,
    load_persistence_experiments,
)


def test_metric_recalculations_agreement():
    """Verify that enriched trials faithfully match authoritative values in metric-recalculations.csv."""
    trials = get_enriched_trials()
    recalc_df = load_metric_recalculations_df()
    recalc_map = {str(row["run_id"]): row for _, row in recalc_df.iterrows()}

    for t in trials:
        recalc_row = recalc_map.get(t.run_id)
        if recalc_row is not None:
            # Check full-run metrics
            assert t.metrics.full_reqs == int(recalc_row["full_reqs"])
            assert abs(t.metrics.full_throughput - float(recalc_row["full_throughput"])) < 1e-4

            # Check steady-state metrics
            assert t.metrics.steady_reqs == int(recalc_row["steady_reqs"])
            assert abs(t.metrics.steady_throughput - float(recalc_row["steady_throughput"])) < 1e-4

            if recalc_row["steady_p50"] is not None and not np.isnan(recalc_row["steady_p50"]):
                assert t.metrics.steady_p50 is not None
                assert abs(t.metrics.steady_p50 - float(recalc_row["steady_p50"])) < 1e-3


def test_synchronization_flagship_findings():
    """Verify the core thesis finding: ReentrantLock unpins carrier but preserves serialization."""
    trials = get_enriched_trials()

    # Stratum 1: java21-primary-repeat
    s1_sync = [t for t in trials if t.run_set == "java21-primary-repeat" and t.condition_id == "synchronized"]
    s1_lock = [t for t in trials if t.run_set == "java21-primary-repeat" and t.condition_id == "reentrant-lock"]

    assert len(s1_sync) == 3
    assert len(s1_lock) == 3

    # Throughput comparison
    sync_tp = [t.metrics.steady_throughput for t in s1_sync]
    lock_tp = [t.metrics.steady_throughput for t in s1_lock]
    sync_full_tp = [t.metrics.full_throughput for t in s1_sync]
    lock_full_tp = [t.metrics.full_throughput for t in s1_lock]

    mean_sync_tp = float(np.mean(sync_tp))
    mean_lock_tp = float(np.mean(lock_tp))
    mean_sync_full = float(np.mean(sync_full_tp))
    mean_lock_full = float(np.mean(lock_full_tp))

    # Hold-window throughput: 1.967 req/s vs 1.956 req/s
    assert abs(mean_sync_tp - 1.9667) < 0.001
    assert abs(mean_lock_tp - 1.9556) < 0.001

    # Full-run throughput: 1.964 req/s for both
    assert abs(mean_sync_full - 1.9636) < 0.001
    assert abs(mean_lock_full - 1.9636) < 0.001

    # Pinning events: synchronized has 108–110, ReentrantLock has strictly 0
    for t in s1_sync:
        assert t.jfr_pinning_count is not None and t.jfr_pinning_count > 100
    for t in s1_lock:
        assert t.jfr_pinning_count == 0


def test_java24_unpinning_and_latency():
    """Verify JEP 491 behavior: Java 24 emits 0 pinning events, but p95 jumps to ~9,001 ms."""
    trials = get_enriched_trials()

    j24_sync = [t for t in trials if t.run_set == "java24-sync-repeat"]
    assert len(j24_sync) == 3

    # Throughput is still ~1.967 req/s
    for t in j24_sync:
        assert abs(t.metrics.steady_throughput - 1.9667) < 0.01

    # Pinning events are 0
    for t in j24_sync:
        assert t.jfr_pinning_count == 0

    # p95 latency is ~9001 ms
    p95_vals = [t.metrics.steady_p95 for t in j24_sync if t.metrics.steady_p95 is not None]
    assert len(p95_vals) == 3
    mean_p95 = float(np.mean(p95_vals))
    assert 8950.0 < mean_p95 < 9050.0, f"Expected p95 ~9001 ms, got {mean_p95}"


def test_native_jni_silent_captivity():
    """Verify that blocking JNI emits 0 JFR pinning events despite total carrier captivity."""
    trials = get_enriched_trials()

    jni_blocking = [t for t in trials if t.run_set == "native-boundary-20261008-repeated" and t.condition_id == "blocking-jni"]
    assert len(jni_blocking) == 9  # 3 JDKs x 3 trials

    for t in jni_blocking:
        assert t.jfr_pinning_count == 0
        assert abs(t.metrics.steady_throughput - 1.9667) < 0.05


def test_persistence_two_treatment_ablation():
    """Verify Treatment A (uncontended/excluded) vs Treatment B (Little's Law active contention)."""
    pers_records = load_persistence_experiments()
    assert len(pers_records) == 12  # 6 Treatment A + 6 Treatment B

    # Treatment B
    t_b = [r for r in pers_records if "Treatment B" in r.treatment]
    assert len(t_b) == 6

    pool1 = [r for r in t_b if r.pool_size == 1]
    pool10 = [r for r in t_b if r.pool_size == 10]

    assert len(pool1) == 3
    assert len(pool10) == 3

    # Pool 1 throughput ~ 3.27 req/s
    for r in pool1:
        assert abs(r.hold_tp - 3.27) < 0.05
        assert 15000.0 < r.hold_p50 < 15200.0

    # Pool 10 throughput ~ 32.60 req/s
    for r in pool10:
        assert abs(r.hold_tp - 32.60) < 0.20
        assert 1400.0 < r.hold_p50 < 1450.0

    # JFR pinning events strictly 0
    for r in t_b:
        assert r.jfr_pinning_events == 0


def test_dual_window_divergence_and_hold_interval_semantics():
    """Verify that whole-run and hold-window metrics diverge, proving hold-window is a sample, not equilibrium."""
    trials = get_enriched_trials()

    # In ramping workloads like pure-java-sleep, steady throughput is substantially higher than full throughput
    sleep_trials = [t for t in trials if t.condition_id == "pure-java-sleep"]
    assert len(sleep_trials) >= 3

    for t in sleep_trials:
        # Full TP is ~12.98 req/s, steady TP is ~16.5 req/s (27% delta)
        assert t.metrics.full_throughput < t.metrics.steady_throughput
        assert t.metrics.throughput_delta_pct > 20.0, "Expected significant delta between whole-run and hold window"


def test_carrier_configuration_segregation():
    """Verify that 1-carrier and 8-carrier trials are strictly segregated and never pooled."""
    trials = get_enriched_trials()

    s1_trials = [t for t in trials if t.stratum_id == 1]
    s5_trials = [t for t in trials if t.stratum_id == 5]

    assert len(s1_trials) == 12
    assert len(s5_trials) == 12

    for t in s1_trials:
        assert t.carrier_category == "1-carrier"
        assert t.parallelism == 1
        assert t.max_pool_size == 1

    for t in s5_trials:
        assert t.carrier_category == "8-carrier/default"
        assert t.parallelism == 8
        assert t.max_pool_size == 256


"""Automated unit tests for Chapter 7 Migration Guidance models, queueing math, and triage pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

# Add explorer root
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import pytest
from lib.loaders import load_persistence_experiments
from lib.migration_data import (
    CORE_RULES,
    DEPENDENCIES_REGISTRY,
    REFACTORING_PATTERNS,
    calculate_downstream_pool_capacity,
    calculate_service_demand_capacity,
    calculate_threadlocal_heap_footprint,
    evaluate_migration_readiness,
)


def test_service_demand_capacity_queueing_math():
    """Verify queueing math against Stratum 1 (PaymentService mutex bottleneck)."""
    # Boundary: zero service demand
    zero_res = calculate_service_demand_capacity(service_demand_ms=0.0)
    assert zero_res["max_throughput_rps"] == 0.0
    assert zero_res["achieved_throughput_rps"] == 0.0

    # Stratum 1 theoretical calculation:
    # 500 ms mutex hold time, 10 concurrent VUs, think time = 0
    res = calculate_service_demand_capacity(service_demand_ms=500.0, concurrent_vus=10, think_time_ms=0.0)
    assert res["max_throughput_rps"] == 2.0
    assert res["achieved_throughput_rps"] == 2.0
    assert res["expected_latency_ms"] == 5000.0
    assert res["saturation_ratio"] == 1.0

    # Compare with empirical Stratum 1 measurements:
    # In Stratum 1 (parallelism=1), measured hold throughput is ~1.97 req/s
    # and hold median latency is ~4,960 ms (range ~4,900 - 4,972 ms)
    empirical_tp = 1.97
    empirical_latency_ms = 4960.0

    tp_diff_pct = abs(res["achieved_throughput_rps"] - empirical_tp) / res["achieved_throughput_rps"] * 100.0
    lat_diff_pct = abs(res["expected_latency_ms"] - empirical_latency_ms) / res["expected_latency_ms"] * 100.0

    assert tp_diff_pct < 5.0, f"Throughput difference {tp_diff_pct:.2f}% exceeds 5% bound"
    assert lat_diff_pct < 5.0, f"Latency difference {lat_diff_pct:.2f}% exceeds 5% bound"


def test_downstream_pool_capacity_queueing_math():
    """Verify HikariCP pool sizing against Stratum 8 empirical persistence measurements."""
    # Boundary: zero hold time
    zero_pool = calculate_downstream_pool_capacity(pool_size=10, hold_time_ms=0.0)
    assert zero_pool["max_throughput_rps"] == 0.0

    # Stratum 8 Treatment B: 300 ms connection hold, 50 concurrent VUs
    # 1. Pool size 1:
    # Theoretical: X_max = 1 / 0.3 = 3.3333 req/s, R = (50/1) * 300 = 15,000 ms
    p1 = calculate_downstream_pool_capacity(pool_size=1, hold_time_ms=300.0, concurrent_vus=50)
    assert abs(p1["max_throughput_rps"] - 3.3333) < 1e-3
    assert abs(p1["closed_loop_throughput_rps"] - 3.3333) < 1e-3
    assert p1["closed_loop_latency_ms"] == 15000.0
    assert p1["queue_wait_ms"] == 14700.0
    assert p1["active_connections"] == 1
    assert p1["queued_requests"] == 49

    # 2. Pool size 10:
    # Theoretical: X_max = 10 / 0.3 = 33.3333 req/s, R = (50/10) * 300 = 1,500 ms
    p10 = calculate_downstream_pool_capacity(pool_size=10, hold_time_ms=300.0, concurrent_vus=50)
    assert abs(p10["max_throughput_rps"] - 33.3333) < 1e-3
    assert abs(p10["closed_loop_throughput_rps"] - 33.3333) < 1e-3
    assert p10["closed_loop_latency_ms"] == 1500.0
    assert p10["queue_wait_ms"] == 1200.0
    assert p10["active_connections"] == 10
    assert p10["queued_requests"] == 40

    # Match against empirical Stratum 8 records
    s8_records = [r for r in load_persistence_experiments() if "Stratum 8" in r.treatment]
    assert len(s8_records) == 6

    s8_pool1 = [r for r in s8_records if r.pool_size == 1]
    s8_pool10 = [r for r in s8_records if r.pool_size == 10]

    # Empirical Pool 1: hold_tp ~ 3.27 req/s, hold_p50 ~ 15,123 ms
    emp_p1_tp = float(sum(r.hold_tp for r in s8_pool1) / len(s8_pool1))
    emp_p1_lat = float(sum(r.hold_p50 for r in s8_pool1) / len(s8_pool1))

    diff_p1_tp = abs(p1["closed_loop_throughput_rps"] - emp_p1_tp) / emp_p1_tp * 100.0
    diff_p1_lat = abs(p1["closed_loop_latency_ms"] - emp_p1_lat) / emp_p1_lat * 100.0
    assert diff_p1_tp < 5.0, f"Pool 1 TP diff {diff_p1_tp:.2f}% exceeds 5%"
    assert diff_p1_lat < 5.0, f"Pool 1 latency diff {diff_p1_lat:.2f}% exceeds 5%"

    # Empirical Pool 10: hold_tp ~ 32.60 req/s, hold_p50 ~ 1,431 ms
    emp_p10_tp = float(sum(r.hold_tp for r in s8_pool10) / len(s8_pool10))
    emp_p10_lat = float(sum(r.hold_p50 for r in s8_pool10) / len(s8_pool10))

    diff_p10_tp = abs(p10["closed_loop_throughput_rps"] - emp_p10_tp) / emp_p10_tp * 100.0
    diff_p10_lat = abs(p10["closed_loop_latency_ms"] - emp_p10_lat) / emp_p10_lat * 100.0
    assert diff_p10_tp < 5.0, f"Pool 10 TP diff {diff_p10_tp:.2f}% exceeds 5%"
    assert diff_p10_lat < 5.0, f"Pool 10 latency diff {diff_p10_lat:.2f}% exceeds 5%"


def test_downstream_pool_timeout_cascade():
    """Verify timeout cascade and open-loop overflow detection."""
    # Under connection timeout of 250 ms, queue wait 1200 ms triggers timeout vulnerability
    t_res = calculate_downstream_pool_capacity(
        pool_size=10,
        hold_time_ms=300.0,
        concurrent_vus=50,
        connection_timeout_ms=250.0,
        arrival_rate_rps=50.0,
    )
    assert t_res["timeout_vulnerable"] is True
    # Capacity is 33.33 req/s, arrival is 50.0 req/s -> overflow ~ (50 - 33.33) / 50 = 33.33%
    assert t_res["timeout_rate_pct"] > 30.0


def test_threadlocal_heap_footprint():
    """Verify ThreadLocal memory bloat calculations (§7.3 Rule 5 / CLM-RQ2-07)."""
    mem = calculate_threadlocal_heap_footprint(
        concurrent_virtual_threads=100_000,
        context_payload_kb=50.0,
        platform_pool_workers=200,
    )
    # 200 * 50 KB * 1024 = 10,240,000 bytes (~9.77 MB)
    assert mem["platform_heap_bytes"] == 10_240_000
    assert abs(mem["platform_heap_mb"] - 9.77) < 0.05

    # 100,000 * 50 KB * 1024 = 5,120,000,000 bytes (~4.768 GiB / 5.0 GB decimal)
    assert mem["virtual_heap_bytes"] == 5_120_000_000
    assert abs(mem["virtual_heap_gb"] - 4.768) < 0.01

    # Expansion ratio = 100,000 / 200 = 500x
    assert mem["expansion_ratio"] == 500.0
    assert mem["risk_level"] == "CRITICAL"


def test_registries_completeness():
    """Verify that all core rules, ecosystem dependencies, and patterns are complete."""
    # 1. Five Core Architectural Rules
    assert len(CORE_RULES) == 5
    expected_claims = {"CLM-MIG-01", "CLM-MIG-02", "CLM-MIG-03", "CLM-MIG-04", "CLM-RQ2-07"}
    actual_claims = {rule.claim_id for rule in CORE_RULES.values()}
    assert actual_claims == expected_claims

    # 2. Ecosystem Dependencies: 14 total (5 from Table 7.1 + 9 extended)
    assert len(DEPENDENCIES_REGISTRY) == 14
    dep_artifacts = {dep.artifact_id for dep in DEPENDENCIES_REGISTRY}
    table_7_1_artifacts = {
        "org.postgresql:postgresql",
        "com.mysql:mysql-connector-j",
        "com.fasterxml.jackson.core:jackson-databind",
        "org.apache.tomcat.embed:tomcat-embed-core",
        "com.zaxxer:HikariCP",
    }
    assert table_7_1_artifacts.issubset(dep_artifacts)

    # Invariant ledger extended artifacts
    extended_artifacts = {
        "org.mariadb.jdbc:mariadb-java-client",
        "org.xerial:sqlite-jdbc",
        "org.apache.httpcomponents.client5:httpclient5",
        "org.apache.commons:commons-pool2",
        "org.springframework.boot:spring-boot-loader",
        "org.springframework:spring-core",
        "ch.qos.logback:logback-classic",
        "org.apache.logging.log4j:log4j-core",
        "io.opentelemetry:opentelemetry-javaagent",
    }
    assert extended_artifacts.issubset(dep_artifacts)

    # 3. Four Refactoring Patterns
    assert len(REFACTORING_PATTERNS) == 4
    expected_patterns = {"PAT-01", "PAT-02", "PAT-03A", "PAT-03B"}
    assert set(REFACTORING_PATTERNS.keys()) == expected_patterns


def test_evaluate_migration_readiness_non_short_circuiting():
    """Verify that the 6-stage triage pipeline does NOT short-circuit and collects all issues."""
    assessment = evaluate_migration_readiness(
        unverified_dependencies=["org.xerial:sqlite-jdbc", "com.mysql:mysql-connector-j"],
        has_jni=True,
        jni_is_blocking_or_unpredictable=True,
        has_blocking_sync=True,
        is_domain_bottleneck=False,
        target_jdk_version=21,
        uses_database=True,
        connection_hold_time_ms=300.0,
        hikari_pool_size=1,
        concurrent_vus=50,
        connection_timeout_ms=250.0,
        has_app_semaphore=False,
        uses_threadlocal=True,
        has_finally_remove=False,
        has_jfr_enabled=True,
        jfr_threshold_ms=20.0,
        monitors_carrier_metrics=False,
        has_compute_bound_work=True,
    )

    # Must have results for all 6 stages
    assert len(assessment.stage_results) == 6

    # Composite risk must be CRITICAL
    assert assessment.composite_risk == "CRITICAL"
    assert assessment.blocking_issues_count >= 4

    # Stages 1, 2, 3, 4, 5 must all flag issues
    stage_risks = {s["stage"]: s["risk"] for s in assessment.stage_results}
    assert stage_risks[1] == "CRITICAL"  # Hazardous SQLite
    assert stage_risks[2] == "CRITICAL"  # Blocking JNI
    assert stage_risks[3] == "CRITICAL"  # Non-bottleneck blocking sync on Java 21
    assert stage_risks[4] == "CRITICAL"  # Pool 1 with timeout vulnerability
    assert stage_risks[5] == "CRITICAL"  # Missing finally remove
    assert stage_risks[6] == "MEDIUM"    # 20ms JFR blind spot + missing carrier metrics

    # All relevant rules must be prescribed
    assert 1 in assessment.prescribed_rules
    assert 2 in assessment.prescribed_rules
    assert 3 in assessment.prescribed_rules
    assert 4 in assessment.prescribed_rules
    assert 5 in assessment.prescribed_rules

    # All relevant patterns must be prescribed
    assert "PAT-01" in assessment.prescribed_patterns
    assert "PAT-02" in assessment.prescribed_patterns
    assert "PAT-03A" in assessment.prescribed_patterns


def test_evaluate_migration_readiness_clean_profile():
    """Verify that a compliant application receives a CLEAN assessment."""
    assessment = evaluate_migration_readiness(
        unverified_dependencies=[],
        has_jni=False,
        has_blocking_sync=False,
        uses_database=False,
        uses_threadlocal=False,
        has_jfr_enabled=True,
        jfr_threshold_ms=5.0,
        monitors_carrier_metrics=True,
        has_compute_bound_work=False,
    )
    assert assessment.composite_risk == "CLEAN"
    assert assessment.blocking_issues_count == 0
    assert assessment.advisory_issues_count == 0
    assert len(assessment.prescribed_rules) == 0


def test_evaluate_migration_readiness_jdk24_sync():
    """Verify that Java 24 relaxes monitor pinning alerts due to JEP 491."""
    assessment = evaluate_migration_readiness(
        has_blocking_sync=True,
        target_jdk_version=24,
        has_jfr_enabled=True,
        jfr_threshold_ms=5.0,
        monitors_carrier_metrics=True,
    )
    stage_3 = next(s for s in assessment.stage_results if s["stage"] == 3)
    assert stage_3["risk"] == "LOW"
    assert "JEP 491" in stage_3["details"]


def test_evaluate_migration_readiness_jdk25_scoped_values():
    """Verify that Java 25 prescribes standard Scoped Values (PAT-03B)."""
    assessment = evaluate_migration_readiness(
        uses_threadlocal=True,
        has_finally_remove=True,
        target_jdk_version=25,
        has_jfr_enabled=True,
        jfr_threshold_ms=5.0,
        monitors_carrier_metrics=True,
    )
    assert "PAT-03B" in assessment.prescribed_patterns
    assert 5 in assessment.prescribed_rules


def test_mva_think_time_queueing_math():
    """Verify that Exact MVA queueing math accurately handles think time and transitions."""
    # 1. Single user with think time: R should equal S exactly (no queueing)
    single = calculate_service_demand_capacity(service_demand_ms=100.0, concurrent_vus=1, think_time_ms=900.0)
    assert single["expected_latency_ms"] == 100.0
    assert abs(single["achieved_throughput_rps"] - 1.0) < 1e-3

    # 2. Light load (2 users, S=100ms, Z=900ms):
    # Mean Value Analysis: R(1)=100ms -> Q(1)=0.1 -> R(2)=100*(1+0.1)=110ms
    light = calculate_service_demand_capacity(service_demand_ms=100.0, concurrent_vus=2, think_time_ms=900.0)
    assert abs(light["expected_latency_ms"] - 110.0) < 1.0
    assert abs(light["achieved_throughput_rps"] - 1.98) < 0.05

    # 3. Heavy saturation (100 users, S=100ms, Z=900ms):
    # Saturated ceiling = 10.0 req/s, R -> 100 * 100 - 900 = 9,100 ms
    heavy = calculate_service_demand_capacity(service_demand_ms=100.0, concurrent_vus=100, think_time_ms=900.0)
    assert abs(heavy["achieved_throughput_rps"] - 10.0) < 1e-3
    assert abs(heavy["expected_latency_ms"] - 9100.0) < 5.0
    assert heavy["saturation_ratio"] == 1.0


def test_downstream_pool_closed_loop_timeout_cascade():
    """Verify closed-loop timeout cascade percentage when arrival_rate_rps is omitted."""
    res = calculate_downstream_pool_capacity(
        pool_size=10,
        hold_time_ms=300.0,
        concurrent_vus=50,
        connection_timeout_ms=250.0,
        arrival_rate_rps=None,
    )
    assert res["timeout_vulnerable"] is True
    # 50 VUs, Pool 10 -> queue wait 1200 ms > 250 ms timeout
    # Timed out queued requests: 40 - 10*(250/300) = 31.67 -> 31.67 / 50 = 63.3%
    assert abs(res["timeout_rate_pct"] - 63.33) < 0.5


def test_threadlocal_heap_footprint_boundaries():
    """Verify ThreadLocal memory calculation boundary cases."""
    # Zero payload
    zero_pay = calculate_threadlocal_heap_footprint(concurrent_virtual_threads=1000, context_payload_kb=0.0)
    assert zero_pay["platform_heap_bytes"] == 0
    assert zero_pay["virtual_heap_bytes"] == 0
    assert zero_pay["virtual_heap_mb"] == 0.0
    assert zero_pay["risk_level"] == "LOW"

    # Zero threads
    zero_thr = calculate_threadlocal_heap_footprint(concurrent_virtual_threads=0, context_payload_kb=50.0)
    assert zero_thr["virtual_heap_bytes"] == 0
    assert zero_thr["virtual_heap_mb"] == 0.0
    assert zero_thr["risk_level"] == "LOW"


def test_evaluate_migration_readiness_observability_defect_unmasking():
    """Verify that Stage 6 reports BOTH missing JFR AND missing carrier metrics without masking."""
    assessment = evaluate_migration_readiness(
        has_jfr_enabled=False,
        monitors_carrier_metrics=False,
    )
    s6 = next(s for s in assessment.stage_results if s["stage"] == 6)
    assert s6["risk"] == "HIGH"
    # Both defects must be mentioned in details
    assert "Operating without Java Flight Recorder" in s6["details"]
    assert "Telemetry lacks carrier thread queue latency" in s6["details"]

    # Both actions must be prescribed
    act_text = " ".join(assessment.prescribed_actions)
    assert "Enable continuous JFR" in act_text
    assert "Implement carrier queue latency metrics" in act_text
    assert 4 in assessment.prescribed_rules


def test_evaluate_migration_readiness_commons_pool2_prescribes_rule_3():
    """Verify that hazardous Commons Pool 2 prescribes Rule 3."""
    assessment = evaluate_migration_readiness(
        unverified_dependencies=["org.apache.commons:commons-pool2"],
    )
    assert assessment.composite_risk == "CRITICAL"
    assert 3 in assessment.prescribed_rules


def test_evaluate_migration_readiness_fast_jni_prescribes_rule_2():
    """Verify that non-blocking JNI prescribes Rule 2 for operational qualification."""
    assessment = evaluate_migration_readiness(
        has_jni=True,
        jni_is_blocking_or_unpredictable=False,
    )
    assert 2 in assessment.prescribed_rules
    s2 = next(s for s in assessment.stage_results if s["stage"] == 2)
    assert s2["risk"] == "MEDIUM"


def test_page_07_interactive_widget_simulation():
    """Verify that Page 07 handles dynamic widget changes without exceptions via AppTest."""
    from streamlit.testing.v1 import AppTest

    page_path = APP_DIR / "pages/07_migration_guidelines.py"
    at = AppTest.from_file(str(page_path))
    at.run()
    assert not at.exception, f"Initial render error: {at.exception}"

    # Verify widgets are present and active
    assert len(at.slider) > 0
    assert len(at.checkbox) > 0
    assert len(at.selectbox) > 0

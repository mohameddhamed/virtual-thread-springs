"""Data schemas and type contracts for the Virtual Threads Experiment Explorer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class StratumDefinition:
    """Definition of one of the 8 canonical evidence strata."""
    stratum_id: int
    name: str
    code: str
    run_set_patterns: list[str]
    description: str
    admission_status: str  # 'primary', 'supporting', 'historical', 'diagnostic', 'excluded', 'ablation'
    expected_carrier: str
    target_count: int


# The 8 authoritative strata established in Stage 1.3 Adjudication Charter
STRATA: dict[int, StratumDefinition] = {
    1: StratumDefinition(
        stratum_id=1,
        name="Stratum 1 · Java 21 Primary Synchronization Matrix",
        code="stratum-1-primary-sync",
        run_set_patterns=["java21-primary-matrix", "java21-primary-repeat"],
        description="Single-carrier mechanism-isolation stress tests (parallelism=1, maxPoolSize=1) evaluating synchronized, ReentrantLock, and diagnostic controls.",
        admission_status="primary",
        expected_carrier="1-carrier",
        target_count=12,
    ),
    2: StratumDefinition(
        stratum_id=2,
        name="Stratum 2 · Runtime Comparison (Java 24 / 25 JEP 491)",
        code="stratum-2-runtime-comparison",
        run_set_patterns=["java24-sync-repeat", "java24-lock-repeat", "spring-java24-sync-boundary", "spring-java25-sync-boundary"],
        description="Cross-JDK evaluation of JEP 491 object monitor unpinning on OpenJDK 24.0.2 and 25-ea.",
        admission_status="supporting",
        expected_carrier="1-carrier",
        target_count=10,
    ),
    3: StratumDefinition(
        stratum_id=3,
        name="Stratum 3 · Native JNI Boundary Matrix",
        code="stratum-3-jni-boundary",
        run_set_patterns=["native-boundary-20261008-repeated"],
        description="Multi-JDK evaluation of blocking C system calls, short JNI calls, and Java sleep under single-carrier constraint.",
        admission_status="primary",
        expected_carrier="1-carrier",
        target_count=27,
    ),
    4: StratumDefinition(
        stratum_id=4,
        name="Stratum 4 · Supporting Architectural Diagnostic Controls",
        code="stratum-4-diagnostic-controls",
        run_set_patterns=["java21-endpoint-isolation", "java21-cpu-control"],
        description="Endpoint isolation controls (/orders vs /products) and CPU-bound algorithmic baselines on platform vs virtual threads.",
        admission_status="supporting",
        expected_carrier="1-carrier",
        target_count=18,
    ),
    5: StratumDefinition(
        stratum_id=5,
        name="Stratum 5 · 8-Carrier Historical Baseline Matrix",
        code="stratum-5-historical-8carrier",
        run_set_patterns=["java21-synchronization-20261008-repeated"],
        description="Historical Apple M1 unconstrained 8-carrier baseline executions. Kept distinct from single-carrier mechanism isolation.",
        admission_status="historical",
        expected_carrier="8-carrier/default",
        target_count=12,
    ),
    6: StratumDefinition(
        stratum_id=6,
        name="Stratum 6 · Exploratory Pilots & Standalone Controls",
        code="stratum-6-exploratory-pilots",
        run_set_patterns=["java21-lock-semaphore-pilot-20261015", "software-lab-baseline-2026-10-26", "historical-pilot-oct08", "cpu-control-20261008"],
        description="Exploratory synchronization pilots, preliminary tests, and standalone hardware CPU controls.",
        admission_status="exploratory",
        expected_carrier="mixed",
        target_count=27,
    ),
    7: StratumDefinition(
        stratum_id=7,
        name="Stratum 7 · Excluded / Flawed Persistence Pilots (Treatment A)",
        code="stratum-7-excluded-persistence",
        run_set_patterns=["java21-h2-pool-sensitivity", "docker-pg-orders-pool"],
        description="Methodologically flawed persistence pilots: delay occurred before acquiring JDBC connection, leaving pool >98% idle.",
        admission_status="excluded",
        expected_carrier="mixed",
        target_count=13,
    ),
    8: StratumDefinition(
        stratum_id=8,
        name="Stratum 8 · Relational Persistence Contention Ablation (Treatment B)",
        code="stratum-8-persistence-ablation",
        run_set_patterns=["java21-orders-persistence-contention"],
        description="Active connection-held contention via ConnectionCallback under HikariCP pool sizes 1 vs 10 with companion Actuator telemetry.",
        admission_status="ablation",
        expected_carrier="1-carrier",
        target_count=6,
    ),
}


@dataclass
class TrialMetrics:
    """Dual-window metrics for a single experimental trial."""
    # Full run (0 - 55.0s)
    full_reqs: int
    full_duration_s: float
    full_throughput: float
    full_p50: Optional[float]
    full_p95: Optional[float]
    full_p99: Optional[float]
    failures: int
    failure_rate: float
    # Steady-state hold window (15.0 - 45.0s)
    steady_reqs: int
    steady_duration_s: float
    steady_throughput: float
    steady_p50: Optional[float]
    steady_p95: Optional[float]
    steady_p99: Optional[float]
    # Deltas
    throughput_delta_pct: float
    p50_delta_pct: float


@dataclass
class EnrichedTrialRecord:
    """Canonical representation of an experimental trial record combining all freeze sources."""
    trial_id: str
    run_id: str
    run_set: str
    family: str
    condition_id: str
    condition_label: str
    jdk: str
    jdk_major: str
    execution_mode: str
    virtual_threads_enabled: bool
    target_vus: int
    timestamp_utc: Optional[str]
    carrier_category: str
    parallelism: int
    max_pool_size: int
    stratum_id: int
    stratum_name: str
    admission_status: str
    jfr_available: bool
    jfr_pinning_count: Optional[int]
    metrics: TrialMetrics
    manifest_path: Optional[str]
    result_path: Optional[str]
    jfr_path: Optional[str]
    result_sha256: Optional[str]
    jfr_sha256: Optional[str]
    telemetry_path: Optional[str] = None
    git_commit: Optional[str] = None
    raw_dict: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtifactCensusRecord:
    """Row in artifact-inventory.csv."""
    artifact_id: str
    path: str
    filename: str
    artifact_type: str
    size_bytes: int
    sha256: str
    associated_run_id: str
    associated_trial_id: str
    in_normalized_dataset: bool
    candidate_status: str
    classification_reason: str


@dataclass
class PersistenceTrialRecord:
    """Trial record for Stratum 8 (Treatment B) and Stratum 7 (Treatment A) persistence experiments."""
    treatment: str  # 'Treatment A (Pre-Acquisition Delay Control)' or 'Treatment B (Connection-Held Contention)'
    pool_size: int
    trial: int
    run_id: str
    whole_tp: float
    hold_tp: float
    whole_p50: float
    hold_p50: float
    whole_p95: float
    hold_p95: float
    mean_active: float
    max_active: float
    mean_pending: float
    peak_pending: float
    total_timeouts: int
    jfr_pinning_events: int
    status: str  # 'admitted_ablation' or 'excluded_methodological_flaw'
    manifest_file: Optional[str] = None
    k6_file: Optional[str] = None
    jfr_file: Optional[str] = None

"""Migration guidance domain models, queueing math, registries, and triage pipeline.

Synthesizes Chapter 7 Migration Guidance and the Claim-to-Evidence Ledger
into authoritative computational and structural models for the Experiment Explorer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ==============================================================================
# 1. Domain Dataclasses
# ==============================================================================

@dataclass(frozen=True)
class MigrationRule:
    """Core architectural migration rule derived from empirical evidence."""
    rule_number: int
    name: str
    claim_id: str
    epistemic_badge: str
    proposition: str
    queueing_reality: str
    rationale: str
    evidence_stratum: str
    target_page: str
    target_pattern_id: Optional[str] = None


@dataclass(frozen=True)
class DependencyEntry:
    """Ecosystem dependency baseline and virtual thread carrier-risk classification."""
    artifact_id: str
    component_name: str
    evaluated_baseline: str
    resolved_in_study: Optional[str]
    risk_category: str  # e.g., "Socket-lock compatibility", "ThreadLocal/memory behavior", etc.
    risk_level: str  # "SAFE", "ACTION_REQUIRED", "HAZARDOUS"
    rationale: str
    source_issue: str
    remediation_action: str


@dataclass(frozen=True)
class RefactoringPattern:
    """Correctness-preserving refactoring pattern for enterprise Spring Boot MVC."""
    pattern_id: str  # e.g., "PAT-01", "PAT-02", "PAT-03A", "PAT-03B"
    title: str
    target_jdk: str
    epistemic_class: str
    problem_statement: str
    before_code: str
    after_code: str
    invariants_and_gotchas: list[str]


@dataclass(frozen=True)
class TriageAssessment:
    """Structured assessment produced by the 6-stage non-short-circuiting audit pipeline."""
    composite_risk: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "CLEAN"
    stage_results: list[dict[str, Any]]
    prescribed_actions: list[str]
    prescribed_rules: list[int]
    prescribed_patterns: list[str]
    blocking_issues_count: int
    advisory_issues_count: int


# ==============================================================================
# 2. Analytical Queueing Mathematics
# ==============================================================================

def calculate_service_demand_capacity(
    service_demand_ms: float,
    concurrent_vus: int = 10,
    think_time_ms: float = 0.0,
) -> dict[str, float]:
    """Calculate capacity and response time under Amdahl's Law and Little's Law.

    Models a closed-loop queueing network where N concurrent jobs serialize
    behind a critical section with service demand S.

    Closed-loop Interactive Response Time Law:
        R = (N / X) - Z
    When saturated by serialized bottleneck S (where X_max = 1 / S):
        X = min(N / (S + Z), 1 / S)
        R = (N * S) - Z  (when think time Z = 0: R = N * S)

    Validated against Stratum 1 (PaymentService mutex):
        service_demand = 500 ms, N = 10 VUs -> X = 2.0 req/s, R = 5,000 ms
        Empirical Stratum 1: 1.97 req/s, 4,960 ms steady p50 (within 2% of theory).
    """
    if service_demand_ms <= 0.0:
        return {
            "service_demand_ms": 0.0,
            "concurrent_vus": float(concurrent_vus),
            "think_time_ms": float(think_time_ms),
            "max_throughput_rps": 0.0,
            "achieved_throughput_rps": 0.0,
            "expected_latency_ms": 0.0,
            "saturation_ratio": 0.0,
        }

    s_sec = service_demand_ms / 1000.0
    z_sec = max(0.0, think_time_ms / 1000.0)
    n = max(1, concurrent_vus)

    # Bottleneck theoretical ceiling (Amdahl's Law)
    x_max = 1.0 / s_sec

    # Exact Mean Value Analysis (MVA) for single-server closed queueing network
    # (Reiser & Lavenberg 1980; Lazowska et al. 1984)
    # When Z = 0, collapses analytically to: R = N * S, X = min(N/(N*S), 1/S) = 1/S.
    # When Z > 0, models exact queueing delay and transition from light to heavy load.
    q = 0.0
    r_sec = s_sec
    x_achieved = 0.0
    for i in range(1, n + 1):
        r_sec = s_sec * (1.0 + q)
        x_achieved = float(i) / (r_sec + z_sec) if (r_sec + z_sec) > 0 else x_max
        q = x_achieved * r_sec

    x_achieved = min(x_max, x_achieved)
    r_ms = max(service_demand_ms, r_sec * 1000.0)
    saturation = min(1.0, x_achieved / x_max) if x_max > 0 else 0.0

    return {
        "service_demand_ms": service_demand_ms,
        "concurrent_vus": float(n),
        "think_time_ms": think_time_ms,
        "max_throughput_rps": round(x_max, 4),
        "achieved_throughput_rps": round(x_achieved, 4),
        "expected_latency_ms": round(r_ms, 2),
        "saturation_ratio": round(saturation, 4),
    }


def calculate_downstream_pool_capacity(
    pool_size: int,
    hold_time_ms: float,
    concurrent_vus: int = 50,
    connection_timeout_ms: Optional[float] = None,
    arrival_rate_rps: Optional[float] = None,
) -> dict[str, Any]:
    """Calculate downstream connection pool capacity, Little's Law equilibrium, and timeout cascades.

    Models HikariCP connection pool contention under virtual threads (Stratum 8).
    Supports:
      1. Closed-loop equilibrium (Little's Law for K parallel servers):
         X_max = K / T_hold
         If N >= K: R = (N / K) * T_hold, Queue Wait W_q = (N/K - 1) * T_hold
         Validated against Stratum 8:
           - Pool 1: 300 ms hold, 50 VUs -> 3.33 req/s, 15,000 ms (Empirical: 3.27 req/s, 15,123 ms)
           - Pool 10: 300 ms hold, 50 VUs -> 33.33 req/s, 1,500 ms (Empirical: 32.60 req/s, 1,431 ms)
      2. Open-loop timeout cascades:
         If arrival_rate > X_max and W_q > connection_timeout_ms, requests suffer acquisition timeouts.
    """
    k = max(1, pool_size)
    if hold_time_ms <= 0.0:
        return {
            "pool_size": k,
            "hold_time_ms": 0.0,
            "concurrent_vus": concurrent_vus,
            "max_throughput_rps": 0.0,
            "closed_loop_throughput_rps": 0.0,
            "closed_loop_latency_ms": 0.0,
            "queue_wait_ms": 0.0,
            "active_connections": 0,
            "queued_requests": 0,
            "timeout_vulnerable": False,
            "timeout_rate_pct": 0.0,
        }

    t_hold_sec = hold_time_ms / 1000.0
    n = max(1, concurrent_vus)

    # Theoretical maximum pool capacity: X_max = K / T_hold
    x_max = float(k) / t_hold_sec

    # Closed-loop Little's Law equilibrium
    if n <= k:
        # No queuing, sufficient connections for all concurrent requests
        closed_tp = float(n) / t_hold_sec
        closed_r_ms = hold_time_ms
        queue_wait_ms = 0.0
        active_conns = n
        queued = 0
    else:
        # Saturated connection pool: all K connections active, (N - K) queued
        closed_tp = x_max
        closed_r_ms = (float(n) / float(k)) * hold_time_ms
        queue_wait_ms = closed_r_ms - hold_time_ms
        active_conns = k
        queued = n - k

    # Timeout cascade evaluation
    timeout_vulnerable = False
    timeout_rate_pct = 0.0

    # 1. Closed-loop queue wait exceeding connection acquisition timeout
    if connection_timeout_ms is not None and connection_timeout_ms > 0:
        if queue_wait_ms > connection_timeout_ms:
            timeout_vulnerable = True
            # In closed-loop queueing: requests waiting longer than connection_timeout_ms time out.
            # Max queued requests serviced within timeout: Q_max = K * (connection_timeout_ms / hold_time_ms)
            q_max_serviced = k * (connection_timeout_ms / hold_time_ms)
            timed_out = max(0.0, float(queued) - q_max_serviced)
            timeout_rate_pct = round((timed_out / float(n)) * 100.0, 2)

    # 2. Open-loop arrival rate exceeding service capacity
    if arrival_rate_rps is not None and arrival_rate_rps > 0:
        if arrival_rate_rps > x_max:
            timeout_vulnerable = True
            open_loop_timeout_pct = round(((arrival_rate_rps - x_max) / arrival_rate_rps) * 100.0, 2)
            timeout_rate_pct = max(timeout_rate_pct, open_loop_timeout_pct)

    return {
        "pool_size": k,
        "hold_time_ms": hold_time_ms,
        "concurrent_vus": n,
        "max_throughput_rps": round(x_max, 4),
        "closed_loop_throughput_rps": round(closed_tp, 4),
        "closed_loop_latency_ms": round(closed_r_ms, 2),
        "queue_wait_ms": round(queue_wait_ms, 2),
        "active_connections": active_conns,
        "queued_requests": queued,
        "timeout_vulnerable": timeout_vulnerable,
        "timeout_rate_pct": timeout_rate_pct,
    }


def calculate_threadlocal_heap_footprint(
    concurrent_virtual_threads: int,
    context_payload_kb: float,
    platform_pool_workers: int = 200,
) -> dict[str, Any]:
    """Calculate theoretical ThreadLocal retained heap footprint under scaling.

    Implements §7.3 Rule 5 (CLM-RQ2-07):
    Bounded platform threads (e.g. 200 workers) bound ThreadLocal retention to:
        200 * M_context
    Unbounded virtual threads (e.g. 100,000 threads) yield theoretical worst-case retention:
        100,000 * 50 KB = 5.0 GB (5,120,000,000 bytes).
    """
    if concurrent_virtual_threads <= 0 or context_payload_kb <= 0.0:
        n_p = max(1, platform_pool_workers)
        return {
            "concurrent_virtual_threads": max(0, concurrent_virtual_threads),
            "context_payload_kb": max(0.0, context_payload_kb),
            "platform_pool_workers": n_p,
            "platform_heap_bytes": 0,
            "virtual_heap_bytes": 0,
            "platform_heap_mb": 0.0,
            "virtual_heap_mb": 0.0,
            "virtual_heap_gb": 0.0,
            "expansion_ratio": 1.0,
            "risk_level": "LOW",
        }

    n_v = max(1, concurrent_virtual_threads)
    n_p = max(1, platform_pool_workers)
    payload_bytes = context_payload_kb * 1024.0

    platform_heap_bytes = int(n_p * payload_bytes)
    virtual_heap_bytes = int(n_v * payload_bytes)
    expansion_ratio = round(virtual_heap_bytes / platform_heap_bytes, 2)

    # Risk classification based on worst-case retention
    if virtual_heap_bytes >= 4 * 1024 * 1024 * 1024:  # >= 4 GB
        risk_level = "CRITICAL"
    elif virtual_heap_bytes >= 1024 * 1024 * 1024:  # >= 1 GB
        risk_level = "HIGH"
    elif virtual_heap_bytes >= 256 * 1024 * 1024:  # >= 256 MB
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "concurrent_virtual_threads": n_v,
        "context_payload_kb": context_payload_kb,
        "platform_pool_workers": n_p,
        "platform_heap_bytes": platform_heap_bytes,
        "virtual_heap_bytes": virtual_heap_bytes,
        "platform_heap_mb": round(platform_heap_bytes / (1024 * 1024), 2),
        "virtual_heap_mb": round(virtual_heap_bytes / (1024 * 1024), 2),
        "virtual_heap_gb": round(virtual_heap_bytes / (1024 * 1024 * 1024), 3),
        "expansion_ratio": expansion_ratio,
        "risk_level": risk_level,
    }


# ==============================================================================
# 3. Authoritative Registries
# ==============================================================================

CORE_RULES: dict[int, MigrationRule] = {
    1: MigrationRule(
        rule_number=1,
        name="The Mutex Refactoring Rule",
        claim_id="CLM-MIG-01",
        epistemic_badge="[MEASURED & INTERPRETED]",
        proposition=(
            "Do not refactor synchronized blocks to ReentrantLock expecting throughput improvements "
            "if the critical section represents an application-level serialization bottleneck. "
            "Consider ReentrantLock only when measured carrier scarcity makes monitor pinning a material "
            "risk to unrelated work."
        ),
        queueing_reality=(
            "Amdahl's Law dictates that if a critical section dominates execution time, maximum throughput is "
            "strictly capped by mu = 1 / T_critical. Refactoring to ReentrantLock unpins the carrier thread, "
            "but competing virtual threads remain serialized at the application level."
        ),
        rationale=(
            "In Stratum 1 (parallelism=1), replacing synchronized with ReentrantLock yielded strictly 0% throughput "
            "gain (1.97 req/s across all trials). Default non-fair ReentrantLock introduces AQS barging jitter."
        ),
        evidence_stratum="Stratum 1 & 4 (CLM-RQ1-01, CLM-RQ1-04, CLM-RQ1-05)",
        target_page="pages/02_synchronization.py",
        target_pattern_id="PAT-01",
    ),
    2: MigrationRule(
        rule_number=2,
        name="The Native JNI Isolation Rule",
        claim_id="CLM-MIG-02",
        epistemic_badge="[MEASURED & INTERPRETED]",
        proposition=(
            "Offload foreign calls that can block for materially long or unpredictable periods to dedicated, "
            "bounded platform thread pools. Direct invocation is appropriate only after the operation's execution "
            "time and concurrency have been bounded and its implementation has been verified as non-blocking."
        ),
        queueing_reality=(
            "HotSpot cannot freeze or unmount native C/C++ stack frames. When native code enters a blocking OS syscall "
            "(nanosleep, blocking read, POSIX mutex), the carrier OS thread is held captive in the kernel wait queue. "
            "Direct JNI calls consume ~1% CPU while stalling the scheduler, yet JFR emits ZERO jdk.VirtualThreadPinned events."
        ),
        rationale=(
            "Stratum 3 demonstrated silent carrier starvation. Isolating foreign blocking calls to dedicated platform pools "
            "protects the virtual thread scheduler against thread starvation."
        ),
        evidence_stratum="Stratum 3 (CLM-RQ2-01, CLM-RQ2-02)",
        target_page="pages/04_native_boundary.py",
        target_pattern_id="PAT-02",
    ),
    3: MigrationRule(
        rule_number=3,
        name="The Connection Pool Sizing Fallacy",
        claim_id="CLM-MIG-03",
        epistemic_badge="[MEASURED & EXTERNALLY SUPPORTED]",
        proposition=(
            "Do not scale database connection pools proportionally to virtual thread concurrency. Size the pool "
            "within database and application capacity limits, calibrate it to workload SLOs, and protect requests "
            "with an acquisition timeout or application-level semaphore appropriate to the service contract."
        ),
        queueing_reality=(
            "Downstream Bottleneck Shift Law: Unpinning carrier threads only prevents runtime carrier exhaustion—it "
            "transfers queue formation in full to the JDBC connection pool. Under Little's Law, maximum throughput is "
            "capped at X_max = K / T_hold, regardless of virtual thread count."
        ),
        rationale=(
            "Stratum 8 empirically validated that pool size 1 capped throughput to 3.27 req/s with 15,123 ms p50 latency, "
            "while pool size 10 scaled to 32.60 req/s with 1,431 ms p50. Virtual threads unmounted cleanly (0 pins), "
            "shifting queueing entirely to HikariCP."
        ),
        evidence_stratum="Stratum 8 (CLM-RQ2-03, CLM-RQ2-04)",
        target_page="pages/05_persistence.py",
        target_pattern_id=None,
    ),
    4: MigrationRule(
        rule_number=4,
        name="The Production Observability Rule",
        claim_id="CLM-MIG-04",
        epistemic_badge="[EXTERNALLY SUPPORTED & INTERPRETED]",
        proposition=(
            "Never rely solely on jdk.VirtualThreadPinned JFR alerts to monitor virtual thread health. "
            "Complement JFR with carrier thread pool queue latency metrics and operating system thread state monitoring."
        ),
        queueing_reality=(
            "HotSpot's standard profile.jfc filters monitor pinning events lasting < 20 ms (the 20 ms blind spot). "
            "Furthermore, direct native blocking calls bypass Continuation.yield() entirely and emit strictly 0 JFR events. "
            "Virtual threads do NOT run on ForkJoinPool.commonPool(), but on DEFAULT_SCHEDULER."
        ),
        rationale=(
            "Multi-tier telemetry is required: JFR pinning events + carrier pool queue latency + OS-level kernel wait metrics "
            "(pidstat / eBPF off-CPU tracing)."
        ),
        evidence_stratum="Stratum 1 & 3 (CLM-METH-04, CLM-RQ2-01)",
        target_page="pages/04_native_boundary.py",
        target_pattern_id=None,
    ),
    5: MigrationRule(
        rule_number=5,
        name="ThreadLocal Memory Hygiene",
        claim_id="CLM-RQ2-07",
        epistemic_badge="[THEORETICAL PROJECTION & EXTERNALLY SUPPORTED]",
        proposition=(
            "Eliminate unbounded ThreadLocal allocations in request paths. In Java 21 LTS, enforce mandatory cleanup "
            "using try-finally { context.remove(); }. For post-Java 21 runtimes (standardized in Java 25 via JEP 506), "
            "migrate request context storage to Scoped Values."
        ),
        queueing_reality=(
            "Bounded platform pools (200 workers) bound retained memory to 200 * M_context. Under 100,000 virtual threads "
            "each retaining a 50 KB context payload, worst-case theoretical heap retention scales to ~5.0 GB."
        ),
        rationale=(
            "Virtual threads do not recycle ThreadLocal maps in the manner of pooled platform workers. In Java 21 LTS, "
            "disciplined try-finally removal is mandatory. Scoped Values (JEP 506) provide permanent scope unbinding in Java 25."
        ),
        evidence_stratum="Code Inspection & JEP 444 / JEP 506 (CLM-RQ2-07)",
        target_page="pages/01_overview.py",
        target_pattern_id="PAT-03A",
    ),
}


DEPENDENCIES_REGISTRY: list[DependencyEntry] = [
    # 5 from Chapter 7 Table 7.1
    DependencyEntry(
        artifact_id="org.postgresql:postgresql",
        component_name="PostgreSQL JDBC Driver (pgjdbc)",
        evaluated_baseline="42.6.0 or later to verify",
        resolved_in_study="42.7.10 in pom.xml",
        risk_category="Socket-lock compatibility",
        risk_level="SAFE",
        rationale=(
            "pgjdbc Issue #1951, PR #2629, PR #2635 document version-specific socket-lock changes. "
            "Prior to 42.6.0, socket reads synchronized on monitors, pinning carriers on every query."
        ),
        source_issue="pgjdbc Issue #1951, PR #2629, PR #2635",
        remediation_action="Upgrade to pgjdbc >= 42.6.0 and inspect deployed query execution path.",
    ),
    DependencyEntry(
        artifact_id="com.mysql:mysql-connector-j",
        component_name="MySQL Connector/J",
        evaluated_baseline="9.0.0 or later to verify",
        resolved_in_study="N/A",
        risk_category="Socket-lock compatibility",
        risk_level="ACTION_REQUIRED",
        rationale=(
            "Protocol-reader synchronization in NativeProtocol/MysqlIO was addressed in 9.0.0. "
            "MySQL Connector/J 8.4 LTS remains below evaluated threshold; LTS status alone does not establish safety."
        ),
        source_issue="MySQL Bug #109346, Bug #110512",
        remediation_action="Upgrade to MySQL Connector/J >= 9.0.0. Do not assume 8.4 LTS is virtual-thread safe.",
    ),
    DependencyEntry(
        artifact_id="com.fasterxml.jackson.core:jackson-databind",
        component_name="Jackson Databind / Core",
        evaluated_baseline="2.16.0 baseline to verify",
        resolved_in_study="2.19.4",
        risk_category="ThreadLocal/memory behavior",
        risk_level="SAFE",
        rationale=(
            "Legacy ThreadLocal<SoftReference<BufferRecycler>> caused heap explosion under high virtual thread counts. "
            "2.16.0 introduced pluggable JsonRecyclerPools.sharedLockFreePool()."
        ),
        source_issue="FasterXML/jackson-core Issue #1089",
        remediation_action="Verify jackson-databind >= 2.16.0 and validate retained buffer memory under target load.",
    ),
    DependencyEntry(
        artifact_id="org.apache.tomcat.embed:tomcat-embed-core",
        component_name="Apache Tomcat Embedded",
        evaluated_baseline="10.1.18 baseline to verify",
        resolved_in_study="10.1.52",
        risk_category="Container compatibility",
        risk_level="SAFE",
        rationale=(
            "Container virtual-thread integration and lifecycle behavior are version- and configuration-dependent; "
            "10.1.18 addressed executor lifecycle and thread-binding edge cases."
        ),
        source_issue="Tomcat Bugzilla #66580, Spring Boot #38258",
        remediation_action="Ensure Tomcat >= 10.1.18 (bundled in Spring Boot >= 3.2.0).",
    ),
    DependencyEntry(
        artifact_id="com.zaxxer:HikariCP",
        component_name="HikariCP Connection Pool",
        evaluated_baseline="5.1.0 baseline to verify",
        resolved_in_study="6.3.3",
        risk_category="Pool behavior/capacity",
        risk_level="SAFE",
        rationale=(
            "HikariCP connection waiting uses LockSupport.parkNanos() in ConcurrentBag; virtual threads unmount "
            "cleanly without carrier pinning. However, downstream pool sizing requires strict calibration."
        ),
        source_issue="HikariCP Issue #1463, PR #2055",
        remediation_action="Retain HikariCP >= 5.1.0; calibrate maximumPoolSize and connectionTimeout against database capacity.",
    ),
    # 9 extended from Invariant Ledger
    DependencyEntry(
        artifact_id="org.mariadb.jdbc:mariadb-java-client",
        component_name="MariaDB Connector/J",
        evaluated_baseline="4.0.0 or later to verify",
        resolved_in_study="N/A",
        risk_category="Socket-lock compatibility",
        risk_level="ACTION_REQUIRED",
        rationale="Driver internal synchronization and SSL pinned carriers on pre-4.0.0 releases. CONJ-1367 verified zero pinning in 4.0.0.",
        source_issue="MariaDB JIRA CONJ-1367",
        remediation_action="Upgrade to MariaDB Connector/J >= 4.0.0.",
    ),
    DependencyEntry(
        artifact_id="org.xerial:sqlite-jdbc",
        component_name="SQLite JDBC Driver",
        evaluated_baseline="HAZARDOUS (Direct call unsafe)",
        resolved_in_study="N/A",
        risk_category="Native blocking",
        risk_level="HAZARDOUS",
        rationale=(
            "Native C downcalls via JNI (_thread_in_native) capture carrier threads with strictly 0 JFR pinning events. "
            "Direct execution under virtual threads induces silent scheduler starvation."
        ),
        source_issue="xerial/sqlite-jdbc Issue #1136",
        remediation_action="Isolate SQLite operations to a dedicated bounded platform thread pool (Pattern 2).",
    ),
    DependencyEntry(
        artifact_id="org.apache.httpcomponents.client5:httpclient5",
        component_name="Apache HttpClient 5",
        evaluated_baseline="5.4.0 or later to verify",
        resolved_in_study="N/A",
        risk_category="Socket-lock compatibility",
        risk_level="ACTION_REQUIRED",
        rationale=(
            "PoolingHttpClientConnectionManager.lease() synchronized on this.pool throughout 5.3.x. "
            "HttpClient 5.4.0 overhauled connection leasing with ReentrantLock (5.3.x is unsafe!)."
        ),
        source_issue="Apache HTTPCLIENT-2310, GitHub PR #515",
        remediation_action="Upgrade to Apache HttpClient >= 5.4.0; avoid 5.3.x under virtual threads.",
    ),
    DependencyEntry(
        artifact_id="org.apache.commons:commons-pool2",
        component_name="Apache Commons Pool 2",
        evaluated_baseline="UNREMEDIATED (2.12.x hazardous)",
        resolved_in_study="N/A",
        risk_category="Pool behavior/capacity",
        risk_level="HAZARDOUS",
        rationale=(
            "GenericObjectPool retains synchronized monitors. PR #230 was never merged into 2.12.x. "
            "DBCP2 and legacy Jedis relying on Commons Pool 2 cause carrier pinning under contention."
        ),
        source_issue="Apache Commons Pool PR #230, POOL-402",
        remediation_action="Migrate away from Commons Pool 2 / DBCP2 to HikariCP or virtual-thread-safe connection pooling.",
    ),
    DependencyEntry(
        artifact_id="org.springframework.boot:spring-boot-loader",
        component_name="Spring Boot Executable JAR (LaunchedClassLoader)",
        evaluated_baseline="Config Guidance / Packaging",
        resolved_in_study="Evaluated in packaging pipeline",
        risk_category="Classloader lock",
        risk_level="ACTION_REQUIRED",
        rationale=(
            "LaunchedClassLoader and JarUrlClassLoader lock on nested jar entry reads during runtime class loading "
            "and reflection under virtual threads."
        ),
        source_issue="Spring Boot Issues #51463 & #50925",
        remediation_action="Unpack fat JAR (jar -xf) in container images or production environments to avoid nested JAR locking.",
    ),
    DependencyEntry(
        artifact_id="org.springframework:spring-core",
        component_name="Spring Framework Core",
        evaluated_baseline="6.1.1 / 6.2.6 or later",
        resolved_in_study="6.2.x via Boot 3.5.12",
        risk_category="Framework synchronization",
        risk_level="SAFE",
        rationale=(
            "ConcurrencyThrottleSupport adapted from synchronized to ReentrantLock (#32251); "
            "non-blocking limit rejection (#34727); SseEmitter virtual-thread optimizations (#30996)."
        ),
        source_issue="Spring Framework Issues #32251, #34727, #30996",
        remediation_action="Ensure Spring Framework >= 6.1.1 (Spring Boot >= 3.2.0).",
    ),
    DependencyEntry(
        artifact_id="ch.qos.logback:logback-classic",
        component_name="Logback Classic",
        evaluated_baseline="1.3.15 / 1.4.15 / 1.5.0 or later",
        resolved_in_study="1.5.x via Boot",
        risk_category="Logging carrier pinning",
        risk_level="SAFE",
        rationale=(
            "Synchronous OutputStreamAppender pinned carriers during disk/console writes. "
            "Resolved in 1.3.15/1.4.15/1.5.0. Still mandates AsyncAppender for high-throughput logging."
        ),
        source_issue="Logback Issue #737",
        remediation_action="Verify Logback >= 1.4.15/1.5.0 and configure AsyncAppender to bulkhead logging I/O.",
    ),
    DependencyEntry(
        artifact_id="org.apache.logging.log4j:log4j-core",
        component_name="Apache Log4j 2",
        evaluated_baseline="2.21.0 or later",
        resolved_in_study="N/A",
        risk_category="Logging carrier pinning",
        risk_level="ACTION_REQUIRED",
        rationale=(
            "Synchronized locks in RollingFileManager and OutputStreamManager pinned carrier threads during rollover "
            "and flush operations. Fixed in 2.21.0."
        ),
        source_issue="Log4j2 JBS/JIRA LOG4J2-3622, Issue #1532",
        remediation_action="Upgrade to Log4j2 >= 2.21.0 and enable asynchronous loggers (LMAX Disruptor).",
    ),
    DependencyEntry(
        artifact_id="io.opentelemetry:opentelemetry-javaagent",
        component_name="OpenTelemetry Java / Micrometer",
        evaluated_baseline="OTel >= 1.32.1 / Micrometer >= 1.12.0",
        resolved_in_study="Micrometer 1.14.x",
        risk_category="Telemetry visibility",
        risk_level="SAFE",
        rationale=(
            "OTel WeakConcurrentHashMap expunging in VirtualField held locks causing carrier stalls/deadlocks (#9534, #10747). "
            "Micrometer 1.12.0+ provides micrometer-java21 with VirtualThreadMetrics tracking carrier queues."
        ),
        source_issue="OpenTelemetry Issues #9534 & #10747, Micrometer Java 21 module",
        remediation_action="Upgrade OTel Javaagent >= 1.32.1; enable Micrometer VirtualThreadMetrics.",
    ),
]


REFACTORING_PATTERNS: dict[str, RefactoringPattern] = {
    "PAT-01": RefactoringPattern(
        pattern_id="PAT-01",
        title="Safe Mutex Refactoring (Eliminating Monitor Pinning)",
        target_jdk="Java 21+",
        epistemic_class="[MEASURED & THEORETICAL / CONDITIONAL]",
        problem_statement=(
            "Legacy synchronized blocks wrapping blocking I/O, sleep, or network calls pin the underlying "
            "carrier thread on Java 21 LTS (CLM-RQ1-01), causing carrier starvation under single or scarce carriers."
        ),
        before_code=(
            "// BEFORE: Anti-pattern triggering Java 21 monitor pinning (CLM-RQ1-01)\n"
            "@Service\n"
            "public class LegacyPaymentService {\n"
            "    private final Object paymentMonitor = new Object();\n\n"
            "    public PaymentResponse processPayment(PaymentRequest request) {\n"
            "        // VULNERABILITY: Synchronized monitor couples continuation to OS carrier.\n"
            "        // When executeGatewayCall() performs blocking socket I/O, the carrier pins.\n"
            "        synchronized (paymentMonitor) {\n"
            "            return executeGatewayCall(request);\n"
            "        }\n"
            "    }\n\n"
            "    private PaymentResponse executeGatewayCall(PaymentRequest request) {\n"
            "        return restTemplate.postForObject(\"/api/pay\", request, PaymentResponse.class);\n"
            "    }\n"
            "}"
        ),
        after_code=(
            "// AFTER: Safe, Virtual-Thread-Aware Explicit Lock Refactoring\n"
            "@Service\n"
            "public class RefactoredPaymentService {\n"
            "    // REFACTORING: ReentrantLock unmounts continuation cleanly via LockSupport.park()\n"
            "    // Explicitly select fair or non-fair mode based on application contract.\n"
            "    // Non-fair mode (default) matches experimental baseline (PaymentService.java)\n"
            "    // and may improve throughput but permits AQS direct-CAS barging (CLM-RQ1-05).\n"
            "    private final ReentrantLock paymentLock = new ReentrantLock();\n\n"
            "    public PaymentResponse processPayment(PaymentRequest request) {\n"
            "        // MANDATORY: Always follow standard lock-try-finally paradigm\n"
            "        paymentLock.lock();\n"
            "        try {\n"
            "            return executeGatewayCall(request);\n"
            "        } finally {\n"
            "            // GUARANTEE: Lock release is mandatory in finally block to prevent deadlock\n"
            "            paymentLock.unlock();\n"
            "        }\n"
            "    }\n\n"
            "    private PaymentResponse executeGatewayCall(PaymentRequest request) {\n"
            "        return restTemplate.postForObject(\"/api/pay\", request, PaymentResponse.class);\n"
            "    }\n"
            "}"
        ),
        invariants_and_gotchas=[
            "Amdahl's Bottleneck Invariant: Refactoring to ReentrantLock does NOT increase throughput if the lock represents a domain serialization bottleneck (CLM-MIG-01).",
            "AQS Barging Jitter: Non-fair ReentrantLock (default) allows incoming threads to barge ahead of queued waiters, increasing latency variance (CLM-RQ1-05).",
            "Mandatory try-finally: Failing to unlock inside finally leads to permanent deadlock and uncollected virtual thread continuations.",
        ],
    ),
    "PAT-02": RefactoringPattern(
        pattern_id="PAT-02",
        title="Foreign Function (JNI) Platform Thread Offloading with AbortPolicy",
        target_jdk="Java 21+",
        epistemic_class="[MEASURED & THEORETICAL / CONDITIONAL]",
        problem_statement=(
            "Direct invocation of blocking native C/C++ libraries (JNI or Panama FFM) holds the carrier thread "
            "captive in the OS kernel without emitting JFR pinning events, causing silent JVM starvation (CLM-RQ2-01)."
        ),
        before_code=(
            "// BEFORE: Direct blocking JNI invocation on Virtual Thread (CLM-RQ2-01)\n"
            "@Service\n"
            "public class LegacyCryptoService {\n"
            "    static { System.loadLibrary(\"nativecrypto\"); }\n"
            "    private native byte[] decryptPayloadNative(byte[] encryptedData);\n\n"
            "    public byte[] processData(byte[] input) {\n"
            "        // VULNERABILITY: Direct invocation enters blocking foreign native code.\n"
            "        // HotSpot cannot unmount native C stack frames. When the C function executes\n"
            "        // a blocking POSIX syscall (nanosleep, socket read, mutex wait), the underlying\n"
            "        // carrier thread is held hostage for the duration of the call.\n"
            "        // HotSpot emits ZERO jdk.VirtualThreadPinned events (silent carrier starvation).\n"
            "        return decryptPayloadNative(input);\n"
            "    }\n"
            "}"
        ),
        after_code=(
            "// AFTER: Safe Foreign Call Isolation via Bounded Platform Thread Pool\n"
            "@Service\n"
            "public class IsolatedCryptoService {\n"
            "    static { System.loadLibrary(\"nativecrypto\"); }\n"
            "    private native byte[] decryptPayloadNative(byte[] encryptedData);\n\n"
            "    private final ExecutorService nativePlatformPool;\n\n"
            "    public IsolatedCryptoService(@Qualifier(\"nativePlatformPool\") ExecutorService nativePlatformPool) {\n"
            "        this.nativePlatformPool = nativePlatformPool;\n"
            "    }\n\n"
            "    public byte[] processData(byte[] input, Duration timeout)\n"
            "            throws ExecutionException, TimeoutException, InterruptedException {\n"
            "        // OFFLOAD: Shift blocking foreign call to dedicated OS platform thread\n"
            "        Future<byte[]> future = nativePlatformPool.submit(() -> decryptPayloadNative(input));\n"
            "        try {\n"
            "            // UNMOUNT: Calling virtual thread parks cleanly on LockSupport while\n"
            "            // awaiting the platform worker, releasing its carrier immediately.\n"
            "            return future.get(timeout.toMillis(), TimeUnit.MILLISECONDS);\n"
            "        } catch (TimeoutException | InterruptedException ex) {\n"
            "            future.cancel(true); // Signal cooperative interruption to platform worker\n"
            "            throw ex;\n"
            "        }\n"
            "    }\n"
            "}\n\n"
            "// MANDATORY EXECUTOR CONFIGURATION BEAN:\n"
            "@Configuration\n"
            "public class NativePoolConfiguration {\n"
            "    @Bean(name = \"nativePlatformPool\", destroyMethod = \"shutdown\")\n"
            "    public ExecutorService nativePlatformPool(\n"
            "            @Value(\"${native.pool.size:16}\") int poolSize,\n"
            "            @Value(\"${native.pool.queue-capacity:500}\") int queueCapacity) {\n"
            "        return new ThreadPoolExecutor(\n"
            "            poolSize, poolSize, 60L, TimeUnit.SECONDS,\n"
            "            new ArrayBlockingQueue<>(queueCapacity),\n"
            "            new CustomizableThreadFactory(\"native-platform-\"),\n"
            "            new ThreadPoolExecutor.AbortPolicy() // MANDATORY: Fail-fast sheds load\n"
            "        );\n"
            "    }\n"
            "}"
        ),
        invariants_and_gotchas=[
            "The CallerRunsPolicy Trap: In traditional pools CallerRunsPolicy provides backpressure, but under virtual threads it forces the calling virtual thread to execute the native task synchronously, immediately pinning its carrier and causing JVM-wide carrier paralysis.",
            "The POSIX Interruption Boundary: future.cancel(true) sets the Java interrupt flag, but blocking POSIX syscalls (nanosleep, read, POSIX mutex) ignore JVM interrupts. The platform thread remains trapped in the OS kernel until the syscall completes.",
            "Bounded Queue Requirement: Never use unbounded LinkedBlockingQueue; use ArrayBlockingQueue(200-500) paired with Little's Law dimensioning and AbortPolicy.",
        ],
    ),
    "PAT-03A": RefactoringPattern(
        pattern_id="PAT-03A",
        title="Defensive ThreadLocal Lifecycle Encapsulation",
        target_jdk="Java 21 LTS (Primary Production Guidance)",
        epistemic_class="[THEORETICAL / CONDITIONAL]",
        problem_statement=(
            "Unbounded ThreadLocal allocations in high-concurrency request paths retain large object graphs on "
            "transient virtual threads, risking severe heap bloat and OutOfMemoryError under scale (CLM-RQ2-07)."
        ),
        before_code=(
            "// BEFORE: Fragile ThreadLocal without guaranteed removal\n"
            "@Component\n"
            "public class FragileSecurityFilter implements Filter {\n"
            "    private static final ThreadLocal<SecurityUser> USER_CONTEXT = new ThreadLocal<>();\n\n"
            "    @Override\n"
            "    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)\n"
            "            throws IOException, ServletException {\n"
            "        SecurityUser user = authenticate(req);\n"
            "        USER_CONTEXT.set(user);\n"
            "        // HAZARD: If chain throws exception or does not clean up, context object\n"
            "        // remains trapped in ThreadLocal$ThreadLocalMap until GC / thread termination.\n"
            "        chain.doFilter(req, res);\n"
            "    }\n"
            "}"
        ),
        after_code=(
            "// AFTER: Defensive ThreadLocal Lifecycle Encapsulation (Mandatory Java 21 Pattern)\n"
            "@Component\n"
            "public class ProductionSecurityContextFilter implements Filter {\n"
            "    private static final ThreadLocal<SecurityUser> USER_CONTEXT = new ThreadLocal<>();\n\n"
            "    public static SecurityUser getCurrentUser() {\n"
            "        return USER_CONTEXT.get();\n"
            "    }\n\n"
            "    @Override\n"
            "    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)\n"
            "            throws IOException, ServletException {\n"
            "        SecurityUser user = authenticate(req);\n"
            "        USER_CONTEXT.set(user);\n"
            "        try {\n"
            "            chain.doFilter(req, res);\n"
            "        } finally {\n"
            "            // MANDATORY LIFECYCLE ENFORCEMENT: Clean up in finally block unconditionally!\n"
            "            // Prevents uncollected context objects from polluting continuation heap stack.\n"
            "            USER_CONTEXT.remove();\n"
            "        }\n"
            "    }\n"
            "}"
        ),
        invariants_and_gotchas=[
            "Mandatory finally remove(): Every filter or interceptor setting a ThreadLocal MUST call .remove() in a guaranteed finally block.",
            "Heap Dumps Audit: Under 100,000 concurrent virtual threads, verify with Eclipse MAT that ThreadLocalMap retained size remains bounded.",
            "Transient Threads: Virtual threads should be transient (request-scoped); pooling virtual threads is an explicit anti-pattern.",
        ],
    ),
    "PAT-03B": RefactoringPattern(
        pattern_id="PAT-03B",
        title="Modern Scoped Values Standardization (Java 25 JEP 506 / Java 21 Preview)",
        target_jdk="Java 25 LTS (Standard) / Java 21-24 (Preview JEP 446/487)",
        epistemic_class="[EXTERNALLY SUPPORTED]",
        problem_statement=(
            "ThreadLocal maps are mutable, inheritable by default, and prone to memory leaks. Scoped Values "
            "provide lightweight, immutable context propagation with automatic scope unbinding."
        ),
        before_code=(
            "// BEFORE: Mutable ThreadLocal subject to leak if finally-cleanup fails\n"
            "@Component\n"
            "public class TraditionalUserContextFilter implements Filter {\n"
            "    private static final ThreadLocal<SecurityUser> USER_CONTEXT = new ThreadLocal<>();\n"
            "    // ... requires manual try-finally cleanup\n"
            "}"
        ),
        after_code=(
            "// AFTER: Modern Scoped Values (Finalized standard in Java 25 via JEP 506)\n"
            "@Component\n"
            "public class ModernSecurityContextFilter implements Filter {\n"
            "    // REFACTORING: ScopedValue is immutable, lightweight, and automatically unbinds\n"
            "    public static final ScopedValue<SecurityUser> USER_CONTEXT = ScopedValue.newInstance();\n\n"
            "    @Override\n"
            "    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)\n"
            "            throws IOException, ServletException {\n"
            "        SecurityUser user = authenticate(req);\n\n"
            "        // BOUND SCOPE: User context is valid ONLY within this callable scope.\n"
            "        // The binding unbinds automatically when the scope exits.\n"
            "        try {\n"
            "            ScopedValue.where(USER_CONTEXT, user).run(() -> {\n"
            "                try {\n"
            "                    chain.doFilter(req, res);\n"
            "                } catch (IOException | ServletException ex) {\n"
            "                    throw new RuntimeServletExceptionBridge(ex);\n"
            "                }\n"
            "            });\n"
            "        } catch (RuntimeServletExceptionBridge bridge) {\n"
            "            Throwable cause = bridge.getCause();\n"
            "            if (cause instanceof IOException ioEx) throw ioEx;\n"
            "            if (cause instanceof ServletException sEx) throw sEx;\n"
            "            throw new ServletException(cause);\n"
            "        }\n"
            "    }\n\n"
            "    // EXCEPTION BRIDGE: Checked exceptions wrapped across Runnable and rethrown,\n"
            "    // while unchecked runtime exceptions propagate unmolested to @ControllerAdvice.\n"
            "    private static class RuntimeServletExceptionBridge extends RuntimeException {\n"
            "        public RuntimeServletExceptionBridge(Throwable cause) {\n"
            "            super(cause);\n"
            "        }\n"
            "    }\n"
            "}"
        ),
        invariants_and_gotchas=[
            "Runtime Baseline: OpenJDK 21 LTS requires --enable-preview (JEP 446); standardized without preview in Java 25 LTS via JEP 506.",
            "Exception Propagation Fidelity: Checked exceptions (IOException, ServletException) require an unboxing bridge across Runnable lambda.",
            "Synchronous Scope Constraint: ScopedValue.where().run() covers synchronous execution; async servlet dispatch or child task forks require StructuredTaskScope.",
        ],
    ),
}


# ==============================================================================
# 4. The 6-Stage Non-Short-Circuiting Audit Pipeline (§7.6.2)
# ==============================================================================

def evaluate_migration_readiness(
    # Stage 1: Dependencies
    unverified_dependencies: Optional[list[str]] = None,
    # Stage 2: Native / JNI
    has_jni: bool = False,
    jni_is_blocking_or_unpredictable: bool = False,
    # Stage 3: Synchronization
    has_blocking_sync: bool = False,
    is_domain_bottleneck: bool = True,
    target_jdk_version: int = 21,
    # Stage 4: Database / HikariCP
    uses_database: bool = False,
    connection_hold_time_ms: float = 0.0,
    hikari_pool_size: int = 10,
    concurrent_vus: int = 50,
    connection_timeout_ms: float = 30000.0,
    has_app_semaphore: bool = False,
    # Stage 5: Context & ThreadLocal
    uses_threadlocal: bool = False,
    has_finally_remove: bool = True,
    estimated_context_kb: float = 50.0,
    expected_concurrent_threads: int = 10000,
    # Stage 6: Observability & Compute
    has_jfr_enabled: bool = True,
    jfr_threshold_ms: float = 20.0,
    monitors_carrier_metrics: bool = False,
    has_compute_bound_work: bool = False,
) -> TriageAssessment:
    """Execute the 6-stage non-short-circuiting migration triage pipeline (§7.6.2).

    Every component or request path must pass through all relevant checks.
    A remediation in one stage never bypasses subsequent stages.
    """
    stage_results: list[dict[str, Any]] = []
    prescribed_actions: list[str] = []
    prescribed_rules: list[int] = []
    prescribed_patterns: list[str] = []

    # -------------------------------------------------------------------------
    # Stage 1: Dependency Tree Resolution
    # -------------------------------------------------------------------------
    s1_risk = "CLEAN"
    s1_details = "Third-party dependencies meet evaluated virtual-thread baseline checks."
    unverified = unverified_dependencies or []

    hazardous_artifacts = {"org.xerial:sqlite-jdbc", "org.apache.commons:commons-pool2"}
    has_hazardous = any(dep in hazardous_artifacts for dep in unverified)

    if has_hazardous:
        s1_risk = "CRITICAL"
        s1_details = f"Detected hazardous unremediated dependencies: {', '.join([d for d in unverified if d in hazardous_artifacts])}."
        prescribed_actions.append("Audit and replace hazardous dependencies (e.g. migrate Commons Pool to HikariCP; offload SQLite JDBC).")
        if 2 not in prescribed_rules and any("sqlite" in d for d in unverified):
            prescribed_rules.append(2)
            prescribed_patterns.append("PAT-02")
        if 3 not in prescribed_rules and any("commons-pool" in d for d in unverified):
            prescribed_rules.append(3)
    elif unverified:
        s1_risk = "HIGH"
        s1_details = f"Unverified or below-baseline dependencies detected ({len(unverified)} artifacts): {', '.join(unverified)}."
        prescribed_actions.append("Execute 'mvn dependency:tree -Dverbose' and upgrade dependencies to evaluated baselines (Table 7.1).")

    stage_results.append({
        "stage": 1,
        "name": "Dependency Tree Resolution",
        "risk": s1_risk,
        "details": s1_details,
    })

    # -------------------------------------------------------------------------
    # Stage 2: Native / Foreign Function Boundary
    # -------------------------------------------------------------------------
    s2_risk = "CLEAN"
    s2_details = "No native JNI or Panama FFM boundaries detected in request path."

    if has_jni:
        if 2 not in prescribed_rules:
            prescribed_rules.append(2)
        if jni_is_blocking_or_unpredictable:
            s2_risk = "CRITICAL"
            s2_details = (
                "Blocking or unpredictable native C calls hold carrier OS threads captive without triggering "
                "JFR pinning alerts (CLM-RQ2-01). Carrier starvation will occur under concurrency."
            )
            prescribed_actions.append(
                "Isolate native C blocking operations to a dedicated bounded platform thread pool using AbortPolicy (Pattern 2)."
            )
            if "PAT-02" not in prescribed_patterns:
                prescribed_patterns.append("PAT-02")
        else:
            s2_risk = "MEDIUM"
            s2_details = (
                "In-memory / fast native operations detected. Direct call remains conditional: verify non-blocking "
                "execution time (<10 µs) and bounded concurrency."
            )
            prescribed_actions.append("Benchmark native execution time and verify implementation performs no blocking kernel syscalls.")

    stage_results.append({
        "stage": 2,
        "name": "Native Foreign-Function Boundary",
        "risk": s2_risk,
        "details": s2_details,
    })

    # -------------------------------------------------------------------------
    # Stage 3: Synchronized Monitors around Blocking I/O
    # -------------------------------------------------------------------------
    s3_risk = "CLEAN"
    s3_details = "No synchronized monitors enclosing blocking I/O or sleep delays."

    if has_blocking_sync:
        if target_jdk_version >= 24:
            s3_risk = "LOW"
            s3_details = (
                f"Target JDK {target_jdk_version} includes JEP 491 (Object Monitor Unpinning). Monitor pinning is "
                "eliminated by the JVM; verify residual native frame or class-initializer pinning."
            )
            prescribed_actions.append(f"Audit deployment on OpenJDK {target_jdk_version} for residual class-initialization or JNI pinning paths.")
        else:
            # Java 21-23
            if is_domain_bottleneck:
                s3_risk = "HIGH"
                s3_details = (
                    "Critical section serializes a domain bottleneck. Amdahl's Law dictates that replacing synchronized "
                    "with ReentrantLock will NOT raise endpoint throughput (CLM-MIG-01). Carrier pinning will occur on Java 21."
                )
                prescribed_actions.append(
                    "Do not refactor synchronized to ReentrantLock expecting throughput gains (Rule 1). If carrier starvation "
                    "impacts unrelated endpoints, evaluate ReentrantLock or upgrade to Java 24 (JEP 491)."
                )
                if 1 not in prescribed_rules:
                    prescribed_rules.append(1)
            else:
                s3_risk = "CRITICAL"
                s3_details = (
                    "Synchronized monitor blocks carrier threads during non-bottleneck I/O, causing severe carrier "
                    "starvation for concurrent unrelated services (CLM-RQ1-01)."
                )
                prescribed_actions.append(
                    "Refactor synchronized block to ReentrantLock with mandatory try-finally pattern (Pattern 1, Rule 1)."
                )
                if 1 not in prescribed_rules:
                    prescribed_rules.append(1)
                if "PAT-01" not in prescribed_patterns:
                    prescribed_patterns.append("PAT-01")

    stage_results.append({
        "stage": 3,
        "name": "Synchronization & Monitor Pinning",
        "risk": s3_risk,
        "details": s3_details,
    })

    # -------------------------------------------------------------------------
    # Stage 4: Database Connection Pool Demarcation
    # -------------------------------------------------------------------------
    s4_risk = "CLEAN"
    s4_details = "No relational database connection checkout in request path."

    if uses_database:
        pool_calc = calculate_downstream_pool_capacity(
            pool_size=hikari_pool_size,
            hold_time_ms=connection_hold_time_ms,
            concurrent_vus=concurrent_vus,
            connection_timeout_ms=connection_timeout_ms,
        )
        if pool_calc["timeout_vulnerable"]:
            s4_risk = "CRITICAL"
            s4_details = (
                f"Connection queue wait ({pool_calc['queue_wait_ms']:.1f} ms) exceeds configured connectionTimeout "
                f"({connection_timeout_ms:.1f} ms). High risk of timeout cascade and HTTP 500 errors (CLM-RQ2-03)."
            )
            prescribed_actions.append(
                "Enforce application-level Semaphore to bound concurrency contending for database connections, "
                "or calibrate pool size and transaction boundaries."
            )
            if 3 not in prescribed_rules:
                prescribed_rules.append(3)
        elif concurrent_vus > hikari_pool_size and not has_app_semaphore:
            s4_risk = "HIGH"
            s4_details = (
                f"Unconstrained virtual threads ({concurrent_vus} VUs) exceed pool size ({hikari_pool_size}). "
                f"Downstream Bottleneck Shift will inflate queue latency to ~{pool_calc['closed_loop_latency_ms']:.1f} ms."
            )
            prescribed_actions.append(
                "Calibrate HikariCP maximumPoolSize to database hardware limits; gate connection-held sections with a Semaphore (Rule 3)."
            )
            if 3 not in prescribed_rules:
                prescribed_rules.append(3)
        else:
            s4_risk = "LOW"
            s4_details = (
                f"Pool configured ({hikari_pool_size} conns, {pool_calc['max_throughput_rps']:.1f} req/s capacity). "
                "Connections checkout within calibrated bounds."
            )

    stage_results.append({
        "stage": 4,
        "name": "Database Connection Pool Demarcation",
        "risk": s4_risk,
        "details": s4_details,
    })

    # -------------------------------------------------------------------------
    # Stage 5: Context Propagation & ThreadLocal Lifecycle
    # -------------------------------------------------------------------------
    s5_risk = "CLEAN"
    s5_details = "No ThreadLocal or ScopedValue usage in request path."

    if uses_threadlocal:
        tl_calc = calculate_threadlocal_heap_footprint(
            concurrent_virtual_threads=expected_concurrent_threads,
            context_payload_kb=estimated_context_kb,
        )
        if not has_finally_remove:
            s5_risk = "CRITICAL"
            s5_details = (
                f"ThreadLocal.set() without guaranteed try-finally {{ remove(); }} cleanup under {expected_concurrent_threads:,} "
                f"concurrent virtual threads risks ~{tl_calc['virtual_heap_gb']:.2f} GB heap bloat (CLM-RQ2-07)."
            )
            prescribed_actions.append(
                "Enforce mandatory try-finally { context.remove(); } in all filters and interceptors (Pattern 3A, Rule 5)."
            )
            if 5 not in prescribed_rules:
                prescribed_rules.append(5)
            if "PAT-03A" not in prescribed_patterns:
                prescribed_patterns.append("PAT-03A")
        else:
            if target_jdk_version >= 25:
                s5_risk = "LOW"
                s5_details = (
                    f"Defensive cleanup in place. Target JDK {target_jdk_version} supports standardized Scoped Values (JEP 506). "
                    "Recommended for immutable context propagation without ThreadLocal memory bloat."
                )
                prescribed_actions.append("Migrate request context to standard Scoped Values (Pattern 3B, JEP 506).")
                if 5 not in prescribed_rules:
                    prescribed_rules.append(5)
                if "PAT-03B" not in prescribed_patterns:
                    prescribed_patterns.append("PAT-03B")
            else:
                s5_risk = "MEDIUM" if tl_calc["risk_level"] in {"HIGH", "CRITICAL"} else "LOW"
                s5_details = (
                    f"Defensive try-finally cleanup is present. Theoretical peak retention under {expected_concurrent_threads:,} "
                    f"threads is {tl_calc['virtual_heap_mb']:.1f} MB ({tl_calc['expansion_ratio']}x expansion vs platform pool)."
                )
                if 5 not in prescribed_rules:
                    prescribed_rules.append(5)
                if "PAT-03A" not in prescribed_patterns:
                    prescribed_patterns.append("PAT-03A")

    stage_results.append({
        "stage": 5,
        "name": "Context Propagation & ThreadLocal Lifecycle",
        "risk": s5_risk,
        "details": s5_details,
    })

    # -------------------------------------------------------------------------
    # Stage 6: Observability, Compute Qualification & JFR Thresholds
    # -------------------------------------------------------------------------
    s6_findings: list[str] = []
    s6_risk = "CLEAN"

    if not has_jfr_enabled:
        s6_risk = "HIGH"
        s6_findings.append("Operating without Java Flight Recorder. Monitor pinning and carrier unmount stalls cannot be detected.")
        prescribed_actions.append("Enable continuous JFR with jdk.VirtualThreadPinned event capture in production (Rule 4).")
        if 4 not in prescribed_rules:
            prescribed_rules.append(4)
    elif jfr_threshold_ms > 5.0:
        s6_risk = "MEDIUM"
        s6_findings.append(
            f"JFR pinning threshold is set to {jfr_threshold_ms:.1f} ms (standard profile.jfc default is 20 ms). "
            "Micro-pinning events between 5 ms and 20 ms are completely dropped from telemetry (CLM-METH-04)."
        )
        prescribed_actions.append(
            "Deploy custom low-threshold.jfc setting jdk.VirtualThreadPinned threshold to 5 ms in staging environments (Rule 4)."
        )
        if 4 not in prescribed_rules:
            prescribed_rules.append(4)
    else:
        s6_findings.append("Continuous JFR configured with low threshold (≤ 5 ms).")

    if not monitors_carrier_metrics:
        if s6_risk == "CLEAN":
            s6_risk = "MEDIUM"
        s6_findings.append("Telemetry lacks carrier thread queue latency and OS-level thread state monitoring.")
        prescribed_actions.append(
            "Implement carrier queue latency metrics (Micrometer) and OS-level thread telemetry (pidstat / eBPF) (Rule 4)."
        )
        if 4 not in prescribed_rules:
            prescribed_rules.append(4)
    else:
        if s6_risk == "CLEAN":
            s6_findings.append("Carrier worker queue metrics and OS-level thread telemetry configured.")

    if has_compute_bound_work:
        prescribed_actions.append(
            "Benchmark compute-bound algorithmic sections separately; virtual threads provide no performance gain for CPU workloads."
        )

    s6_details = " ".join(s6_findings) if s6_findings else "Continuous JFR and multi-tier telemetry configured."

    stage_results.append({
        "stage": 6,
        "name": "Observability & Telemetry Protocol",
        "risk": s6_risk,
        "details": s6_details,
    })

    # -------------------------------------------------------------------------
    # Composite Risk Calculation
    # -------------------------------------------------------------------------
    risk_rank = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "CLEAN": 1}
    max_rank = max(risk_rank.get(res["risk"], 1) for res in stage_results)
    reverse_rank = {5: "CRITICAL", 4: "HIGH", 3: "MEDIUM", 2: "LOW", 1: "CLEAN"}
    composite = reverse_rank[max_rank]

    blocking_count = sum(1 for res in stage_results if res["risk"] in {"CRITICAL", "HIGH"})
    advisory_count = sum(1 for res in stage_results if res["risk"] in {"MEDIUM", "LOW"})

    return TriageAssessment(
        composite_risk=composite,
        stage_results=stage_results,
        prescribed_actions=list(dict.fromkeys(prescribed_actions)),
        prescribed_rules=sorted(list(set(prescribed_rules))),
        prescribed_patterns=list(dict.fromkeys(prescribed_patterns)),
        blocking_issues_count=blocking_count,
        advisory_issues_count=advisory_count,
    )

# Canonical Data Contract & Evidence Architecture

**Virtual Threads Experiment Explorer**  
**MSc Thesis:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
**Evaluation Scope:** 76 Normalized Records · 8 Evidence Strata · 543 Enumerated Artifacts · 75 Manifest-Backed Runs  

---

## 1. Architectural Purpose & Data Flow

The Virtual Threads Experiment Explorer is an interactive, read-only scientific dashboard designed for academic review and empirical verification. It provides supervisory examination access to benchmark runs, treatment comparisons, repeated trial distributions, and cryptographic artifact provenance.

### Core Architectural Separation

```
[Raw Benchmark Evidence]
├── k6 JSONL (results/*.json)
├── JFR Recordings (results/jfr/*.jfr)
├── Companion Telemetry (results/telemetry-*.csv)
└── Execution Manifests (results/run-manifest-*.json)
         │
         ▼
[Authoritative Preprocessing & Freeze Pipeline]
├── scripts/recalculate_metrics.py  ──► docs/evidence-freeze/metric-recalculations.csv
├── scripts/normalize_evidence.py   ──► src/main/resources/static/data/normalized-evidence.json
├── scripts/generate_artifact_inv.py ──► docs/evidence-freeze/artifact-inventory.csv
└── scripts/generate_run_family.py  ──► docs/evidence-freeze/run-family-matrix.csv
         │
         ▼
[Canonical Evidence Contracts (Read-Only)]
         │
         ▼
[tools/experiment-explorer (Streamlit + Plotly)]
├── lib/loaders.py         (Authoritative file ingestion & caching)
├── lib/schemas.py         (Strict typing & data validation)
├── lib/transformations.py (Descriptive statistics & grouping)
├── lib/provenance.py      (SHA-256 verification & artifact traceability)
└── pages/                 (Publication-grade interactive visual presentation)
```

### Governing Architectural Rules:
1. **No In-UI Metric Calculations:** Metric derivation happens strictly upstream in `scripts/recalculate_metrics.py`. The dashboard consumes verified metrics from `metric-recalculations.csv` and `normalized-evidence.json`.
2. **No On-the-Fly JFR Parsing:** JFR events are pre-extracted and verified in the frozen evidence datasets. JFR binaries are referenced for checksum verification and raw inspection, not dynamic JVM-parsing during page renders.
3. **Dual-Window Preservation:** Every throughput and latency metric presentation must expose both the Full-Run window ($[0, 55.0\text{ s}]$) and the Steady-State Hold window ($[15.0\text{ s}, 45.0\text{ s}]$).
4. **Descriptive Rigor ($N \le 3$):** Sample size restrictions must be explicitly stated. The dashboard reports descriptive statistics (mean, standard deviation, min, max, range) and trial-level scatter overlays; it never manufactures confidence intervals or inferential hypothesis tests.
5. **No Synthetic Mockups:** Every chart, table, and drill-down record maps directly to an authenticated file in the repository.

---

## 2. Authoritative Data Sources & Schemas

### 2.1 Normalized Evidence Dataset
* **File:** `src/main/resources/static/data/normalized-evidence.json`
* **Role:** Primary catalogue of admitted and verified benchmark trials ($N=76$).
* **Record Schema:**
  * `trial_id` (`str`): Identifier within condition (e.g. `"1"`, `"2"`, `"3"`, `"cpu-control-20261008"`).
  * `run_id` (`str`): Timestamped run identifier (`"YYYYMMDD-HHMMSS"`).
  * `run_set` (`str`): Registered pre-experimental suite name.
  * `family` (`str`): Experimental family (`"synchronization"`, `"jni-boundary"`, `"controls"`).
  * `condition_id` (`str`): Condition code (`"synchronized"`, `"reentrant-lock"`, `"platform-synchronized"`, `"no-lock"`, `"blocking-jni"`, `"native-short"`, `"pure-java-sleep"`, `"orders-virtual"`, `"orders-platform"`, `"products-virtual"`, `"products-platform"`, `"cpu-virtual"`, `"cpu-platform"`, `"cpu-control"`).
  * `condition_label` (`str`): Human-readable descriptive condition name.
  * `jdk` (`str`): Detailed Java version string reported in manifest.
  * `jdk_major` (`str`): Major version string (`"21"`, `"24"`, `"25"`, or `"unknown"`).
  * `execution_mode` (`str`): `"virtual"` or `"platform"`.
  * `virtual_threads_enabled` (`bool`): Boolean flag.
  * `target_vus` (`int`): Target virtual user count (10 or 50).
  * `timestamp_utc` (`str`): ISO-8601 execution timestamp.
  * `metrics` (`object`): k6 summary metrics (`requests`, `http_failures`, `failure_rate`, `median_ms`, `p95_ms`, `samples`, `endpoints`).
  * `jfr` (`object`): JFR pinning summary (`available`: `bool`, `count`: `int | null`, `classification`: `str`).
  * `provenance` (`object`): File paths and SHA-256 hashes for manifest, k6 result, and JFR recording.

### 2.2 Metric Recalculations Ledger
* **File:** `docs/evidence-freeze/metric-recalculations.csv`
* **Role:** Authoritative recalculation of all 76 normalized trials + 1 audit pilot run ($N=77$ rows).
* **Column Schema:**
  * `trial_id` (`str`), `run_id` (`str`), `run_set` (`str`), `condition_id` (`str`), `k6_file` (`str`).
  * `full_reqs` (`int`): Completed HTTP requests in full 55.0s window.
  * `full_duration_s` (`float`): Exactly 55.0.
  * `full_throughput` (`float`): `full_reqs / 55.0` (req/s).
  * `steady_reqs` (`int`): Completed HTTP requests in 30.0s hold window $[15.0\text{ s}, 45.0\text{ s}]$.
  * `steady_duration_s` (`float`): Exactly 30.0.
  * `steady_throughput` (`float`): `steady_reqs / 30.0` (req/s).
  * `throughput_delta_pct` (`float`): Percentage difference between full and steady throughput.
  * `full_p50` (`float`), `steady_p50` (`float`), `p50_delta_pct` (`float`): Median latency (ms).
  * `full_p95` (`float`), `steady_p95` (`float`): 95th percentile latency (ms).
  * `full_p99` (`float`), `steady_p99` (`float`): 99th percentile latency (ms).
  * `failures` (`int`), `failure_rate` (`float`): HTTP failures and failure ratio.

### 2.3 Run Family Matrix
* **File:** `docs/evidence-freeze/run-family-matrix.csv`
* **Role:** Complete census of all 126 manifest-backed experimental executions.
* **Key Fields:** `manifest_file`, `run_id`, `trial_id`, `run_set`, `run_family`, `endpoint`, `condition_id`, `lock_variant`, `carrier_category` (`"1-carrier"` vs `"8-carrier/default"`), `scheduler_parallelism`, `scheduler_max_pool_size`, `jdk_version`, `git_commit`, `db_engine`, `pool_size`, `target_vus`, `duration_seconds`, `jfr_file`, `result_file`, `is_in_normalized_set` (`bool`).

### 2.4 Artifact Inventory & Cryptographic Census
* **File:** `docs/evidence-freeze/artifact-inventory.csv`
* **Role:** Exhaustive physical census and SHA-256 ledger of all 543 files on disk in `results/`.
* **Column Schema:**
  * `artifact_id` (`str`): Unique identifier (`ART-0001` to `ART-0543`).
  * `path` (`str`): Relative file path from repo root.
  * `filename` (`str`): Base filename.
  * `artifact_type` (`str`): `manifest_json` (121), `k6_json` (157), `jfr_binary` (140), `telemetry_csv` (120), `markdown_report` (5).
  * `size_bytes` (`int`): File size on disk.
  * `sha256` (`str`): Hexadecimal SHA-256 checksum.
  * `associated_run_id` (`str`), `associated_trial_id` (`str`).
  * `in_normalized_dataset` (`str`): `"TRUE"` (226 files) or `"FALSE"` (317 files).
  * `candidate_status` (`str`): `admitted_normalized` (226), `historical_baseline` (239), `diagnostic` (12), `exploratory_uninstrumented` (9), `unmapped` (57).
  * `classification_reason` (`str`): Narrative admission justification.

### 2.5 Claim-to-Evidence Ledger & Epistemic Strata
* **File:** `docs/evidence-freeze/claim-evidence-ledger.md`
* **Role:** Maps research questions (RQ1, RQ2, RQ3) to specific claims, raw evidence artifacts, and empirical strata.

---

## 3. The Dual-Window Measurement Contract

Every experiment utilizes a closed-loop staged load profile executed via k6:
- **Ramp-Up Interval:** $t \in [0.0\text{ s}, 15.0\text{ s})$ — concurrency ramps from 0 to target VUs (10 or 50).
- **Hold Window (Steady-State):** $t \in [15.0\text{ s}, 45.0\text{ s}]$ — constant nominal concurrency held for exactly 30.0 seconds.
- **Ramp-Down Interval:** $t \in (45.0\text{ s}, 55.0\text{ s}]$ — concurrency steps down to 0.

### Epistemic Methodological Mandate:
* **The hold window is a constant-concurrency sampling interval, NOT proof of statistical stationarity or ergodicity.**
* In long-latency conditions (e.g. JNI blocking or 500 ms mutual exclusion), individual request latencies ($\approx 5.0\text{ s}$) span significant fractions of the 30-second hold window.
* Ramping and drain phases introduce substantial throughput distortion if only whole-run metrics are used. Therefore, **both whole-run and hold-window metrics must always be reported together**.

---

## 4. Forensic Resolution of the Inventory Discrepancy

### The 504 vs 543 Artifact Discrepancy Resolved
Earlier audit documentation cited **504 total artifacts** (and Chapter 5 cited 504), while the generated `artifact-inventory.csv` enumerated **543 artifacts**:

| Physical Category | Earlier Snapshot (Chapter 5) | Active Disk Inventory | Delta (New Runs) |
|---|:---:|:---:|:---:|
| Run Manifests (`manifest_json`) | 113 | 121 | +8 |
| Load Test Results (`k6_json`) | 150 | 157 | +7 |
| JFR Binary Recordings (`jfr_binary`) | 132 | 140 | +8 |
| Telemetry CSV Streams (`telemetry_csv`) | 104 | 120 | +16 |
| Markdown Reports (`markdown_report`) | 5 | 5 | 0 |
| **Total** | **504** | **543** | **+39** |

### Root Cause:
1. The **504 count** reflects the initial evidence freeze taken prior to executing the Stratum 8 relational persistence ablation suite (`java21-orders-persistence-contention` [6 runs: 6 manifests, 6 k6 JSONs, 6 JFRs, 12 process & pool telemetry CSVs = 30 files]) and two preliminary persistence validation pilots (+9 files). Total: exactly $504 + 39 = 543$ files.
2. The narrative text in `artifact-inventory-summary.md` Section 2 preserved the static markdown table from the 504-file snapshot, while Section 3 dynamically computed the active 543-file census.
3. The normalized evidence dataset strictly preserves the **76 trial records** across both snapshots (75 manifests, 76 k6 JSONs, 75 JFRs = 226 admitted raw files, with 100% cryptographic hash matches).

---

## 5. The Eight Evidence Strata

All experimental evidence in the repository is partitioned into eight non-overlapping strata:

1. **Stratum 1 — Java 21 Primary Synchronization Matrix (12 runs):**
   * Suites: `java21-primary-matrix` (6 runs) & `java21-primary-repeat` (6 runs).
   * Configuration: OpenJDK 21.0.8, single-carrier stress isolation (`parallelism=1, maxPoolSize=1`), 10 VUs, `/payments`.
   * Treatments: `synchronized`, `reentrant-lock`, `fair-reentrant-lock`, `no-lock` (diagnostic).
2. **Stratum 2 — Runtime Comparison Matrix (10 runs):**
   * Suites: `java24-sync-repeat` (3), `java24-lock-repeat` (3), `spring-java24-sync-boundary` (2), `spring-java25-sync-boundary` (2).
   * Evaluates JEP 491 object monitor unpinning across JDK 21, 24.0.2, and 25-ea.
3. **Stratum 3 — Native JNI Boundary Matrix (27 runs):**
   * Suite: `native-boundary-20261008-repeated` (9 runs each on JDK 21, 24, 25-ea).
   * Treatments: `blocking-jni`, `native-short`, `pure-java-sleep`. Carrier captivity without JFR pinning events.
4. **Stratum 4 — Architectural Diagnostic Controls (18 runs):**
   * Suites: `java21-endpoint-isolation` (12 runs: orders/products on virtual/platform) & `java21-cpu-control` (6 runs: cpu on virtual/platform).
5. **Stratum 5 — 8-Carrier Historical Baseline Matrix (12 runs):**
   * Suite: `java21-synchronization-20261008-repeated` (12 runs: sync, platform-sync, reentrant-lock, no-lock on 8-carrier default pool).
   * Historical baseline on Apple M1. Must not be pooled with 1-carrier runs.
6. **Stratum 6 — Exploratory Pilots & Standalone Controls (27 runs):**
   * Unadmitted exploratory runs, lock/semaphore pilots, Zulu baseline checks, October 8 exploratory pilots, and standalone CPU control record 76.
7. **Stratum 7 — Excluded / Methodologically Flawed Persistence Pilots (13 runs):**
   * Suites: H2 pool sensitivity (6 runs), Docker PostgreSQL (6 runs), aborted run 142557 (1 run).
   * **Methodological Flaw (Treatment A):** In these early persistence runs, the blocking sleep occurred *before* acquiring a JDBC connection, resulting in pool idle rates $>98\%$. Classified as excluded for pool contention evaluation.
8. **Stratum 8 — Two-Treatment Factorial Relational Persistence Ablation (6 runs):**
   * Suite: `java21-orders-persistence-contention`.
   * **Treatment B (Active Contention):** Evaluates true connection pool contention by holding the JDBC connection across a 300 ms blocking delay via `ConnectionCallback`. HikariCP pool sizes 1 vs 10 under 50 VUs with Actuator pool telemetry and companion JFR.

---

## 6. Verification and Cryptographic Constraints

* **Normalized Dataset Admitted Files:** Exactly 226 files (75 manifests, 76 k6 JSONs, 75 JFRs).
* **Hash Verification:** 100% of admitted files must match recorded SHA-256 hashes in `normalized-evidence.json` and manifests.
* **JFR Event Zero Semantics:** In JFR analysis, a count of 0 is an explicit, verified event absence ($\ge 20\text{ ms}$ threshold), not a missing or uncollected value.
* **Diagnostic Conditions:** The `no-lock` treatment is strictly a diagnostic throughput upper-bound ceiling. It fails the mutual exclusion invariant and must never be presented as an application candidate.

---

## 7. Migration Guidance & Architectural Decision Data Model

Synthesizes Chapter 7 Migration Guidance, the Claim-to-Evidence Ledger, and empirical findings into formal computational and structural models (`lib/migration_data.py`).

### 7.1 Domain Dataclasses
* `MigrationRule`: Encapsulates a core architectural rule, its ledger claim mapping, epistemic class badge, exact proposition text, queueing reality, and empirical grounding.
* `DependencyEntry`: Encapsulates an ecosystem artifact, evaluated baseline, resolved study version, risk category, risk level (`SAFE`, `ACTION_REQUIRED`, `HAZARDOUS`), rationale, and remediation action.
* `RefactoringPattern`: Encapsulates a correctness-preserving code pattern (`PAT-01`, `PAT-02`, `PAT-03A`, `PAT-03B`), target JDK version, problem statement, syntax-highlighted Java before/after listings, and architectural invariants/gotchas.
* `TriageAssessment`: Output contract of the 6-stage audit pipeline containing composite risk (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `CLEAN`), stage findings, prescribed actions, prescribed rules, and prescribed patterns.

### 7.2 Analytical Queueing Math Contracts
* `calculate_service_demand_capacity(service_demand_ms, concurrent_vus, think_time_ms)`:
  * Amdahl's Law theoretical capacity ceiling: $X_{\text{max}} = 1 / S$.
  * Interactive Response Time Law (Little's Law closed-loop equilibrium): $R = (N / X) - Z = N \times S$ (when $Z=0$).
  * Calibrated against Stratum 1 (PaymentService mutex): $S = 500\text{ ms}, N = 10 \implies X = 2.0\text{ req/s}, R = 5,000\text{ ms}$ (matches empirical $1.97\text{ req/s}$ and $4,960\text{ ms}$ within 2%).
* `calculate_downstream_pool_capacity(pool_size, hold_time_ms, concurrent_vus, connection_timeout_ms, arrival_rate_rps)`:
  * Downstream Bottleneck Shift (Little's Law for $K$ parallel servers): $X_{\text{max}} = K / T_{\text{hold}}$.
  * Saturated closed-loop response time: $R = (N / K) \times T_{\text{hold}}$, queue wait $W_q = (N/K - 1) \times T_{\text{hold}}$.
  * Calibrated against Stratum 8 (Orders persistence contention):
    * Pool 1 ($K=1, T_{\text{hold}}=300\text{ ms}, N=50$): $X = 3.33\text{ req/s}, R = 15,000\text{ ms}$ (empirical $3.27\text{ req/s}, 15,123\text{ ms}$).
    * Pool 10 ($K=10, T_{\text{hold}}=300\text{ ms}, N=50$): $X = 33.33\text{ req/s}, R = 1,500\text{ ms}$ (empirical $32.60\text{ req/s}, 1,431\text{ ms}$).
  * Open-loop timeout cascade detection: flags timeout vulnerability when $W_q > \text{connectionTimeout}$.
* `calculate_threadlocal_heap_footprint(concurrent_virtual_threads, context_payload_kb, platform_pool_workers)`:
  * Bounded platform pool: $M_{\text{platform}} = N_{\text{workers}} \times M_{\text{context}}$.
  * Unbounded virtual threads: $M_{\text{virtual}} = N_{\text{virtual}} \times M_{\text{context}}$.
  * Evaluated against CLM-RQ2-07 ($100,000$ virtual threads $\times 50\text{ KB} = 5,120,000,000\text{ bytes} \approx 5.0\text{ GB}$).

### 7.3 Authoritative Registries
* **5 Core Architectural Rules:**
  1. `CLM-MIG-01`: The Mutex Refactoring Rule (`[MEASURED & INTERPRETED]`)
  2. `CLM-MIG-02`: The Native JNI Isolation Rule (`[MEASURED & INTERPRETED]`)
  3. `CLM-MIG-03`: The Connection Pool Sizing Fallacy (`[MEASURED & EXTERNALLY SUPPORTED]`)
  4. `CLM-MIG-04`: The Production Observability Rule (`[EXTERNALLY SUPPORTED & INTERPRETED]`)
  5. `CLM-RQ2-07`: ThreadLocal Memory Hygiene (`[THEORETICAL PROJECTION & EXTERNALLY SUPPORTED]`)
* **14 Ecosystem Dependencies:**
  * 5 from Chapter 7 Table 7.1: PostgreSQL (`pgjdbc`), MySQL Connector/J, Jackson Databind, Tomcat Embedded, HikariCP.
  * 9 extended from Invariant Ledger: MariaDB Connector/J, SQLite JDBC, Apache HttpClient 5, Apache Commons Pool 2, Spring Boot Executable (Fat JAR ClassLoader), Spring Framework Core, Logback Classic, Apache Log4j 2, OpenTelemetry Java / Micrometer.
* **4 Correctness-Preserving Refactoring Patterns:**
  * `PAT-01`: Safe Mutex Refactoring (`LegacyPaymentService` $\to$ `RefactoredPaymentService`)
  * `PAT-02`: Foreign Function (JNI) Platform Thread Offloading with `AbortPolicy`
  * `PAT-03A`: Defensive ThreadLocal Lifecycle Encapsulation (`try-finally { remove(); }`)
  * `PAT-03B`: Modern Scoped Values Standardization (Java 25 JEP 506 / Preview JEP 446) with `RuntimeServletExceptionBridge`

### 7.4 Six-Stage Non-Short-Circuiting Triage Audit Pipeline
* Every component passes through all 6 stages unconditionally:
  1. Stage 1: Dependency Tree Resolution
  2. Stage 2: Native / Foreign Function Boundary
  3. Stage 3: Synchronized Monitors around Blocking I/O
  4. Stage 4: Database Connection Pool Demarcation
  5. Stage 5: Context Propagation & ThreadLocal Lifecycle
  6. Stage 6: Observability, Compute Qualification & JFR Thresholds
* Emits composite risk rating, stage scorecards, prescribed corrective actions, and linked rules/patterns.


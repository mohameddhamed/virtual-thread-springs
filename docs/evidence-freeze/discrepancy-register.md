# Stage 1.3 Discrepancy Register

**Document Identity:** Authoritative Discrepancy Register & Defect Resolution Ledger  
**Title:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
**Auditor:** Virtual Threads Research & Evidence Auditor  
**Date:** 5 November 2026  
**Status:** Frozen & Reconciled against Stage 1.1, Stage 1.2, and Adjudication Charter  

---

## 1. Executive Summary & Purpose

This register formally records every historical contradiction, calculation error, measurement blind spot, configuration defect, and construct flaw identified during the research lifecycle (from initial Scout Report through Fact-Checks, Checkpoint Audits, and Stage 1.1/1.2 investigations).

Rather than sanitizing the project's history, this register documents the **exact origin, physical evidence, missing data, materiality to RQ1/RQ2, and the concrete editorial resolution** for every discrepancy. No issue is left unassigned or silently resolved.

---

## 2. Master Discrepancy Matrix

| Discrepancy ID | Summary / Focus | Originating Context | Materiality | Resolution Category | Status |
|---|---|---|:---:|---|:---:|
| **`DISC-01`** | Throughput Normalization Variance Conflation | Reconciliation Report | Medium | Corrected by Calculation | **RESOLVED** |
| **`DISC-02`** | JNI 100% CPU Telemetry Conflation | Reconciliation Report | Critical | Corrected by Physical Telemetry | **RESOLVED** |
| **`DISC-03`** | JFR Pinning Blind Spot on Native Syscalls | Checkpoint 4 & Triage | Critical | Resolved by HotSpot C++ Mechanics | **RESOLVED** |
| **`DISC-04`** | "256 k6 JSONs" Glob Double-Counting Defect | Reproducibility Audit | High | Corrected by Master Census (504 files) | **RESOLVED** |
| **`DISC-05`** | Ramp-Up Latency Inflection in Platform Runs | Metric Recalculation | High | Dual-Window Reporting Mandate | **RESOLVED** |
| **`DISC-06`** | `application.yml` Indentation & H2 Fallback | Reproducibility Audit | High | Code Audit & Autoconfig Qualification | **RESOLVED** |
| **`DISC-07`** | `OrderService.java` Pre-Checkout Sleep Defect | Reconciliation Report | Critical | Code Audit & Little's Law Proof | **RESOLVED** |
| **`DISC-08`** | PostgreSQL Runs Lacking JFR & Cgroup Telemetry | Checkpoint 4 & Triage | Medium | Stratum 7 Boundary Qualification | **RESOLVED** |
| **`DISC-09`** | JFR 20 ms Threshold Masking Sub-20ms Events | Fact-Check JDK Runtime | High | Observability Boundary Qualification | **RESOLVED** |
| **`DISC-10`** | Scheduler Parallelism vs. Container CPU Quotas | Fact-Check Methodology | High | Bare-Metal Host Characterization | **RESOLVED** |
| **`DISC-11`** | Inferential Overreach from Small Sample Size ($N=3$) | Fact-Check Methodology | High | Descriptive Engineering Framing | **RESOLVED** |
| **`DISC-12`** | Theoretical Misattribution: CALM vs. Amdahl | Scout Report Finding 6.2 | Medium | Purged from Thesis; Amdahl Adopted | **RESOLVED** |

---

## 3. Detailed Forensic Discrepancy Records

---

### `DISC-01`: Throughput Normalization Variance Conflation
* **Description & Origin:** In `docs/experiment-audit-triage-reconciliation.md` (lines 38, 186, 213), the author evaluated benchmark run `run-10vus-20261008-142445.json` and reported:
  - Full run: $109 / 55\text{s} = 1.98\text{ req/s}$
  - Steady state: $59 / 30\text{s} = 1.97\text{ req/s}$
  The author repeatedly stated that including the 15s ramp-up and 10s ramp-down introduced *"less than 0.2% variance"*.
* **Relevant Claim IDs:** `CLM-METH-02`
* **Available Evidence on Disk:**
  - Raw k6 JSON: `results/run-10vus-20261008-142445.json`
  - Recalculation Tool: `scripts/recalculate_metrics.py`
  - Audit Report: `docs/evidence-freeze/metric-recalculation-audit.md`
* **Missing Evidence / Gap:** The original author omitted unrounded intermediate calculations and failed to verify that relative throughput error matched stated percentage.
* **Materiality to RQ1/RQ2:** **Medium.** Does not alter the finding that 500 ms serialization caps throughput at ~1.97 req/s, but represents an unforced mathematical error vulnerable to examiner challenge.
* **Forensic Resolution & Action:**
  - Unrounded throughput: $109 / 55.0 = 1.981818\text{ req/s}$; $59 / 30.0 = 1.966667\text{ req/s}$.
  - True throughput delta: $|1.981818 - 1.966667| / 1.981818 \times 100\% = \mathbf{0.765\%}$.
  - Median latency (p50) delta: $|4945.431 - 4954.529| / 4945.431 \times 100\% = \mathbf{0.184\%}$.
  - **Thesis Action:** Correct all summary tables and prose. Explicitly cite **0.765%** for throughput variance and **0.184%** for p50 latency variance.
* **Owner / Chapter Impact:** Chapter 3 (Section 3.8), Chapter 5 (Section 5.1).

---

### `DISC-02`: JNI 100% CPU Telemetry Conflation
* **Description & Origin:** `docs/experiment-audit-triage-reconciliation.md` (line 149) stated: *"Process telemetry CSVs (`results/telemetry-*.csv`) recorded 100% CPU utilization on the carrier thread during `/native` execution."* This contradicted the claim that `/native` executed a 500 ms POSIX `nanosleep`.
* **Relevant Claim IDs:** `CLM-RQ2-01`, `CLM-RQ2-02`
* **Available Evidence on Disk:**
  - C Source: `native/native_blocking.c#L15-L17` (confirms true `nanosleep()` syscall).
  - Telemetry Script: `run-benchmark.sh#L145-L156` (samples `ps -p $APP_PID -o %cpu=`).
  - Telemetry Streams: 9 companion CSVs (`results/telemetry-20261008-143952.csv` through `150118.csv`).
  - Forensic Audit: `docs/evidence-freeze/forensic-investigations.md#L45-L95`.
* **Missing Evidence / Gap:** Process-level `ps` cannot isolate per-carrier thread CPU counters on Darwin without DTrace/Instruments.
* **Materiality to RQ1/RQ2:** **Critical.** Conflating carrier thread blocking (sleeping in kernel) with active CPU exhaustion invalidates the architectural explanation of JNI behavior.
* **Forensic Resolution & Action:**
  - Stage 1.2 parsing across all 9 `blocking-jni` executions proved steady-state JVM CPU utilization is **$1.04\% \pm 0.12\%$** (peak steady-state $\le 8.5\%$).
  - The author conflated **carrier occupancy** (carrier 100% captive/unavailable) with **carrier CPU utilization** (active cycles), likely influenced by literature discussions of SQLite busy-wait spinloops (`sqlite3_busy_timeout`).
  - **Thesis Action:** State that during `nanosleep`, carrier utilization is near-zero CPU (~1%), demonstrating that carrier starvation occurs silently without CPU load spikes.
* **Owner / Chapter Impact:** Chapter 5 (Section 5.5), Chapter 6 (Section 6.2.1).

---

### `DISC-03`: JFR Pinning Diagnostic Blind Spot on Native Syscalls
* **Description & Origin:** Checkpoint 4 audit and research triage questioned why 27 executions of `/native` across JDK 21, 24, and 25-ea produced exactly zero `jdk.VirtualThreadPinned` events in JFR despite carrier throughput being throttled to $1.97\text{ req/s}$.
* **Relevant Claim IDs:** `CLM-RQ2-01`, `CLM-METH-04`
* **Available Evidence on Disk:**
  - JFR Files: 27 binary files in `results/jfr/` (`Stratum 3`).
  - HotSpot C++ Source: `continuation.cpp`, `continuationFreeze.cpp`.
  - Forensic Audit: `docs/evidence-freeze/forensic-investigations.md#L98-L122`.
* **Missing Evidence / Gap:** JFR does not provide an event for "carrier thread blocked in OS kernel."
* **Materiality to RQ1/RQ2:** **Critical.** Determines whether zero JFR pinning events can be trusted as proof of carrier health.
* **Forensic Resolution & Action:**
  - HotSpot architecture confirms `jdk.VirtualThreadPinned` is emitted **only when a thread attempts to unmount (`Continuation.yield()`) and fails**.
  - A thread executing a native system call (`nanosleep`) transitions to `_thread_in_native`. It never executes bytecode and never calls `Continuation.yield()`.
  - HotSpot never evaluates continuation freeze, so `post_pinned_event` is never reached.
  - **Thesis Action:** Define this phenomenon as an intrinsic architectural blind spot of JFR: JFR detects unmount failures, not native blocking or carrier starvation.
* **Owner / Chapter Impact:** Chapter 5 (Section 5.5), Chapter 6 (Section 6.2.1), Chapter 7 (Section 7.4).

---

### `DISC-04`: The "256 k6 JSONs" Glob Double-Counting Defect
* **Description & Origin:** Checkpoint 4 audit and earlier reproducibility reports claimed the disk contained *"256 k6 JSON result files, 113 manifests, and 132 JFR recordings"*, conflicting with the 76 records in `normalized-evidence.json`.
* **Relevant Claim IDs:** `CLM-METH-01`
* **Available Evidence on Disk:**
  - File Inventory: `docs/evidence-freeze/artifact-inventory.csv` (504 rows).
  - Inventory Summary: `docs/evidence-freeze/artifact-inventory-summary.md`.
  - Script: `scripts/generate_artifact_inventory.py`.
* **Missing Evidence / Gap:** Clarification of shell glob expansion behavior in earlier audit logs.
* **Materiality to RQ1/RQ2:** **High (Provenance).** Resolves examiner concerns regarding data integrity and potential fabrication.
* **Forensic Resolution & Action:**
  - Stage 1.1 proved that the earlier auditor ran `ls results/run-*.json | wc -l`, which matched both 113 manifests (`run-manifest-*.json`) and 143 benchmark results (`run-<vus>-*.json`), totaling 256.
  - The earlier auditor counted 256 JSONs and then separately added 113 manifests, double-counting the 113 manifests.
  - True disk population: **150 k6 JSONs, 113 manifests, 132 JFRs, 104 telemetry CSVs, 5 MD reports (504 files total)**.
  - **Thesis Action:** Present the 504-file census table in the methodology chapter and appendix, permanently documenting the glob double-counting root cause.
* **Owner / Chapter Impact:** Chapter 3 (Section 3.7), Chapter 4 (Section 4.4), Appendix A.

---

### `DISC-05`: Ramp-Up Latency Inflection in Platform Synchronized Executions
* **Description & Origin:** Agent 3's independent recalculation revealed that for October 8 `platform-synchronized` executions, whole-run median latency was reported as **~3920 ms**, whereas steady-state median latency was **~4930–4950 ms** (+25.8% shift).
* **Relevant Claim IDs:** `CLM-METH-02`, `CLM-RQ1-04`
* **Available Evidence on Disk:**
  - Recalculations: `docs/evidence-freeze/metric-recalculations.csv` (rows 9, 13).
  - Recalculation Audit: `docs/evidence-freeze/metric-recalculation-audit.md#L110-L165`.
* **Missing Evidence / Gap:** Lack of stage transition markers in k6 JSONL data stream.
* **Materiality to RQ1/RQ2:** **High.** Under-reporting latency by 1000 ms skews the comparison between platform threads and virtual threads.
* **Forensic Resolution & Action:**
  - In a 10-VU closed-loop ramp-up ($t \in [0, 15\text{s}]$), VUs scale linearly from 1 to 10. Early requests encounter minimal queueing (latencies 510 ms to 3400 ms).
  - Sorting all requests across the full 55s pulled the median into the ramp-up slope (~3920 ms), whereas the saturated queue equilibrium at 10 VUs is ~4930 ms.
  - **Thesis Action:** Implement the mandatory dual-window reporting policy approved in Gate 2: report both whole-run and derived hold-window (15–45s) metrics side-by-side.
* **Owner / Chapter Impact:** Chapter 3 (Section 3.8), Chapter 5 (Section 5.2).

---

### `DISC-06`: `application.yml` Indentation Defect & H2 Autoconfiguration Fallback
* **Description & Origin:** Code inspection in Stage 1.1/1.2 revealed that `datasource:` was indented under `demo:` in `src/main/resources/application.yml#L13-L17`.
* **Relevant Claim IDs:** `CLM-RQ2-04`
* **Available Evidence on Disk:**
  - YAML File: `src/main/resources/application.yml#L13-L31`.
  - Docker Compose: `docker-compose.yml#L9-L15`.
  - Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L125-L140`.
* **Missing Evidence / Gap:** Runtime HikariCP pool configuration dump from local H2 execution logs.
* **Materiality to RQ1/RQ2:** **High.** Affects claims regarding whether local H2 pool sizing was explicitly configured or default.
* **Forensic Resolution & Action:**
  - Spring Boot ignored `demo.datasource.*` and fell back to default auto-configured in-memory H2 with `maximumPoolSize = 10`.
  - Docker Compose PostgreSQL runs injected standard `SPRING_DATASOURCE_*` environment variables, correctly applying custom pool sizes.
  - **Thesis Action:** Disclose the indentation defect in Chapter 4; clarify that local H2 runs operated on auto-configured defaults.
* **Owner / Chapter Impact:** Chapter 4 (Section 4.2), Chapter 6 (Section 6.2.2).

---

### `DISC-07`: `OrderService.java` Pre-Acquisition Sleep Defect
* **Description & Origin:** Triage and reconciliation assumed `/orders` tested connection pool saturation under 50 VUs with pool size 1 vs. 10. Code inspection revealed `simulateSlowQuery()` executed before connection checkout.
* **Relevant Claim IDs:** `CLM-RQ2-03`, `CLM-MIG-03`
* **Available Evidence on Disk:**
  - Source Code: `src/main/java/.../OrderService.java#L40-L48`.
  - Benchmark Results: `results/run-10vus-20261015-143319.json`, `results/docker-pg-orders-pool1-trial1.json`.
  - Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L145-L185`.
* **Missing Evidence / Gap:** Direct HikariCP JMX pool occupancy telemetry.
* **Materiality to RQ1/RQ2:** **Critical.** Invalidates claims that the project empirically measured database connection pool exhaustion or saturation.
* **Forensic Resolution & Action:**
  - In `OrderService.java`, `simulateSlowQuery()` (`Thread.sleep(300)`) executed before `jdbcTemplate.queryForList(...)`. The connection was never checked out during sleep.
  - Little's Law derivation ($L_{\text{pool}} \approx 0.0166\text{ connections}$) proves the pool was over 98% idle even at pool size 1.
  - **Thesis Action:** Reclassify the `/orders` experiment: it evaluates virtual thread sleep unmounting during simulated processing delay, not connection pool contention. All pool sizing guidance must be supported by theoretical derivations and external literature.
* **Owner / Chapter Impact:** Chapter 4 (Section 4.3), Chapter 5 (Section 5.6), Chapter 6 (Section 6.2.2), Chapter 7 (Section 7.3).

---

### `DISC-08`: PostgreSQL Runs Lacking JFR and Cgroup Telemetry
* **Description & Origin:** The six Docker Compose PostgreSQL runs (`docker-pg-orders-pool{1,10}-trial{1,2,3}.json`) lacked companion JFR binary recordings and cgroup utilization telemetry.
* **Relevant Claim IDs:** `CLM-RQ2-05`
* **Available Evidence on Disk:**
  - Load Results: 6 k6 JSONs in `results/docker-pg-orders-pool*.json`.
  - Docker Config: `Dockerfile#L14-L18`, `docker-compose.yml#L1-L30`.
  - Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L190-L215`.
* **Missing Evidence / Gap:** Containerized JFR binary streams and `/sys/fs/cgroup/cpu.stat` logs.
* **Materiality to RQ1/RQ2:** **Medium.** Prevents making JFR pinning claims on PostgreSQL.
* **Forensic Resolution & Action:**
  - `Dockerfile` omitted `-XX:StartFlightRecording` and `docker-compose.yml` lacked host volume mounts for JFR.
  - Relegated to **Stratum 7** (Construct-Flawed / Incomplete Executions).
  - **Thesis Action:** Admit k6 performance numbers as exploratory container evidence; explicitly state that carrier unmounting was not measured via JFR on PostgreSQL.
* **Owner / Chapter Impact:** Chapter 5 (Section 5.6), Chapter 6 (Section 6.2.2).

---

### `DISC-09`: JFR 20 ms Detection Threshold Masking Sub-20ms Pinning
* **Description & Origin:** HotSpot's `profile.jfc` specifies `threshold=20ms` for `jdk.VirtualThreadPinned`. Earlier drafts interpreted zero recorded events as proof that no pinning occurred.
* **Relevant Claim IDs:** `CLM-RQ1-03`, `CLM-METH-04`
* **Available Evidence on Disk:**
  - Shell Script: `run-benchmark.sh#L164` (`settings=profile`).
  - OpenJDK Definition: HotSpot `profile.jfc`.
  - Fact-Check: `docs/fact-check-jdk-runtime.md#L115-L135`.
* **Missing Evidence / Gap:** Custom `.jfc` execution with `threshold=0ms` or `-XX:+FlightRecorderOptions:stackdepth=64`.
* **Materiality to RQ1/RQ2:** **High.** Precision boundary on the claim that `ReentrantLock` "eliminates" pinning.
* **Forensic Resolution & Action:**
  - Zero recorded events in `profile.jfc` proves absence of pinning events $\ge 20\text{ ms}$. Shorter pinning events could have occurred without logging.
  - **Thesis Action:** Explicitly qualify all "zero pinning" claims as *"zero pinning events $\ge 20\text{ ms}$ under HotSpot profile.jfc configuration"*.
* **Owner / Chapter Impact:** Chapter 3 (Section 3.5), Chapter 5 (Section 5.2), Chapter 6 (Section 6.1.1).

---

### `DISC-10`: Conflation of Scheduler Parallelism with Container CPU Quota
* **Description & Origin:** Earlier drafts described `-Djdk.virtualThreadScheduler.parallelism=1` as "1-CPU container equivalence" or "container quota modeling".
* **Relevant Claim IDs:** `CLM-METH-01`
* **Available Evidence on Disk:**
  - Manifests: All manifests in Strata 1, 3, 4 record Darwin arm64 host with 8 logical processors.
  - Adjudication: `docs/evidence-freeze/referee-review-adjudication.md#L75-L88`.
* **Missing Evidence / Gap:** Bare-metal Linux cgroup quota comparisons.
* **Materiality to RQ1/RQ2:** **High (Methodological Rigor).** Conflates thread pool worker sizing with operating system CPU scheduling bandwidth.
* **Forensic Resolution & Action:**
  - `parallelism=1` is a JVM scheduler concurrency constraint that limits `ForkJoinPool` workers to 1. Host OS background tasks, GC, Tomcat acceptor threads, and k6 client executed across 8 Apple M1 cores.
  - **Thesis Action:** Purge all claims of "container equivalence". Designate `parallelism=1` strictly as a bare-metal mechanism-isolation benchmark.
* **Owner / Chapter Impact:** Chapter 3 (Section 3.4), Chapter 4 (Section 4.4).

---

### `DISC-11`: Inferential Overreach from Small Sample Size ($N=3$)
* **Description & Origin:** Previous audit text used language suggesting universal stability and definitive performance characteristics from three repeated process trials.
* **Relevant Claim IDs:** `CLM-METH-03`
* **Available Evidence on Disk:**
  - Metric CSV: `docs/evidence-freeze/metric-recalculations.csv`.
  - Audit Report: `docs/evidence-freeze/metric-recalculation-audit.md` Section 5.
* **Missing Evidence / Gap:** Large-sample statistical population ($N \ge 30$) or cross-platform execution matrices.
* **Materiality to RQ1/RQ2:** **High (Academic Defense).** Prevents rejection by thesis examiners for overclaiming on small samples.
* **Forensic Resolution & Action:**
  - $N=3$ process repetitions are reliable descriptive mechanism-isolation units (showing tight clustering with $<0.7\%$ spread), but cannot support inferential hypothesis testing.
  - **Thesis Action:** Report raw trial ranges (min, max, median, stdev) descriptively. Frame conclusions around mechanism demonstration rather than statistical generalization.
* **Owner / Chapter Impact:** Chapter 3 (Section 3.6), Chapter 5 (Section 5.1).

---

### `DISC-12`: Theoretical Misattribution: CALM Theorem vs. Amdahl's Law
* **Description & Origin:** Scout Report Finding 6.2 cited Hellerstein's CALM Theorem (Consistency as Logical Monotonicity) as the theoretical framework explaining mutex lock degradation.
* **Relevant Claim IDs:** `CLM-RQ1-04`
* **Available Evidence on Disk:**
  - Scout Report: `docs/virtual-threads-research-scout-report.md#L620-L645`.
  - Methodology Fact-Check: `docs/fact-check-methodology-performance.md#L80-L105`.
  - Audit Reconciliation: `docs/experiment-audit-triage-reconciliation.md#L216`.
* **Missing Evidence / Gap:** Distributed coordination logs (CALM applies to distributed monotonicity, not in-memory Java locks).
* **Materiality to RQ1/RQ2:** **Medium.** Citing CALM Theorem for a single-JVM mutex reveals severe theoretical misunderstanding.
* **Forensic Resolution & Action:**
  - CALM Theorem governs distributed monotonic logic. Single-JVM mutual exclusion is governed by Amdahl's Law (1967) and Bernstein's Conditions (1966).
  - **Thesis Action:** Permanently purge all CALM Theorem citations from the thesis draft. Frame critical-section serialization strictly using Amdahl's Law.
* **Owner / Chapter Impact:** Chapter 2 (Background), Chapter 6 (Section 6.1.2).

---

## 4. Unresolved Gaps & Mandatory Editorial Actions

The following table summarizes the status, evidence gap, and mandatory editorial action for all twelve discrepancies:

| ID | Title | Available Evidence | Mandatory Thesis Editorial Action | Primary Chapter |
|---|---|---|---|:---:|
| `DISC-01` | Throughput Math Conflation | `metric-recalculations.csv` | Cite unrounded 0.765% throughput delta and 0.184% p50 delta | Ch 3 & 5 |
| `DISC-02` | JNI 100% CPU Conflation | 9 telemetry CSVs (~1.0% CPU) | State native blocking monopolizes carrier with near-zero CPU | Ch 5 & 6 |
| `DISC-03` | JFR Pinning Blind Spot | 27 JFR files (0 events) | Define JFR pinning as unmount failure, not OS stall detector | Ch 5, 6, 7 |
| `DISC-04` | 256 k6 Glob Double-Counting | 504 files in inventory | Present true 504-file census; explain manifest double-counting | Ch 3 & App A |
| `DISC-05` | Ramp-Up Latency Shift | Recalculated metrics | Mandatory dual-window reporting (whole-run vs. hold-window) | Ch 3 & 5 |
| `DISC-06` | H2 Indentation Defect | `application.yml` inspection | Document Spring Boot auto-configuration fallback to default H2 | Ch 4 & 6 |
| `DISC-07` | Pre-Checkout Sleep Defect | `OrderService.java` & Little's Law | Reclassify `/orders` as sleep unmounting, not pool contention | Ch 4, 5, 6, 7 |
| `DISC-08` | PostgreSQL JFR Omission | 6 raw k6 JSONs in Stratum 7 | Exclude PostgreSQL from carrier unmounting claims; report k6 only | Ch 5 & 6 |
| `DISC-09` | JFR 20 ms Threshold | `run-benchmark.sh` inspection | Bound zero-pinning claims to events $\ge 20\text{ ms}$ | Ch 3, 5, 6 |
| `DISC-10` | Parallelism vs. CPU Quota | Manifest host OS telemetry | Characterize `parallelism=1` as scheduler limit on 8-core Darwin | Ch 3 & 4 |
| `DISC-11` | $N=3$ Descriptive Limits | Trial dispersion calculations | Frame $N=3$ data descriptively; exclude inferential statistics | Ch 3 & 5 |
| `DISC-12` | CALM Theorem Misapplication | Literature fact-checks | Purge CALM; frame mutex bottlenecks strictly via Amdahl's Law | Ch 2 & 6 |

---

*(End of Stage 1.3 Discrepancy Register)*

# Stage 1.3 Claim-to-Evidence Ledger

**Document Identity:** Authoritative Claim-to-Evidence Ledger for MSc Thesis  
**Title:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
**Auditor:** Virtual Threads Research & Evidence Auditor  
**Date:** 5 November 2026  
**Status:** Frozen & Reconciled against Stage 1.1, Stage 1.2, and Adjudication Charter  

---

## 1. Epistemic Framework & Evidence Strata Architecture

To prevent narrative inflation and ensure defensibility during thesis examination, every statement destined for the thesis is governed by a two-dimensional qualification framework:
1. **The Epistemic Classification (5 Categories):** Defines the epistemological nature of the claim (how the claim is established).
2. **The Repository Evidence Stratum (7 Strata):** Identifies the exact experimental population from which empirical data originates, adhering strictly to the ratified Adjudication Charter.

### 1.1 The Five Epistemic Categories
* **`[MEASURED]`**: Directly observed and quantified via instrumented benchmark telemetry, raw k6 JSON lines, or JFR event streams from valid repository executions.
* **`[DERIVED]`**: Mathematically or statistically computed from measured data using documented, reproducible formulas (e.g., steady-state filtering, Little's Law estimations, dispersion metrics).
* **`[INTERPRETED]`**: Causal or architectural explanations of *why* observed phenomena occurred, derived by linking measured outcomes to HotSpot C++ mechanics, OS kernel behavior, or framework specifications.
* **`[EXTERNALLY SUPPORTED]`**: Established by official OpenJDK JEPs, HotSpot source code, vendor specifications, RFCs, or peer-reviewed literature, rather than local project measurements.
* **`[NOT ESTABLISHED]`**: Hypotheses, common beliefs, or pilot questions that local experimental evidence cannot substantiate or which local evidence actively refutes.

### 1.2 The Seven Evidence Strata (Adjudication Charter Section 6)
All 119 physical executions (+1 schema template) in the repository are strictly partitioned into seven non-overlapping strata:
* **Stratum 1 (12 executions)**: Java 21 Primary Experimental Synchronization Matrix (`java21-primary-matrix` [6] + `java21-primary-repeat` [6]). Mechanism isolation under `parallelism=1`.
* **Stratum 2 (10 executions)**: Java 24 & Java 25 Runtime Comparison Experiments (`java24-sync-repeat` [3] + `java24-lock-repeat` [3] + `spring-java24-sync-boundary` [2] + `spring-java25-sync-boundary` [2]).
* **Stratum 3 (27 executions)**: Multi-JDK Native JNI Boundary Matrix (`native-boundary-20261008-repeated`, 9 runs each on JDK 21, 24, 25-ea).
* **Stratum 4 (18 executions)**: Supporting Architectural Diagnostic Controls (`java21-endpoint-isolation` [12] + `java21-cpu-control` [6]).
* **Stratum 5 (12 executions)**: Stratified 8-Carrier Historical Baseline Matrix (`java21-synchronization-20261008-repeated`). Apple M1 unconstrained 8-carrier baseline.
* **Stratum 6 (27 executions)**: Exploratory, Pilot, and Standalone Diagnostic Executions (8 lock/semaphore pilots, 1 Zulu baseline check, 17 historical Oct 8 pilots, and 1 standalone CPU control).
* **Stratum 7 (13 executions)**: Excluded, Defective, or Construct-Flawed Executions (6 H2 pool sensitivity, 6 Docker PostgreSQL, and 1 aborted run 142557).

---

## 2. Research Question 1 (RQ1): Synchronization, Pinning, and Lock Serialization

> **RQ1 Focus:** How does synchronization (monitor pinning) interact with carrier-thread availability, application-level serialization, and runtime throughput in Java 21 Spring Boot MVC systems?

---

### `CLM-RQ1-01`: Java 21 Monitor Pinning Occurrence
* **Exact Proposition:** In Java 21, executing a blocking operation (`Thread.sleep`) within a Java `synchronized` block pins the virtual thread to its underlying carrier thread, generating `jdk.VirtualThreadPinned` events when the pin duration exceeds the configured JFR threshold.
* **Epistemic Class:** `[MEASURED]`
* **Evidence Stratum:** **Stratum 1** (`java21-primary-matrix`, `java21-primary-repeat`) & **Stratum 5** (`java21-synchronization-20261008-repeated`).
* **Experimental Conditions:** JDK 21.0.8, Darwin arm64 (Apple M1), endpoint `/payments`, lock treatment `synchronized`, 10 closed-loop VUs, 55s test window.
* **Raw Evidence Artifacts:**
  * Manifests: `results/run-manifest-20261015-141857.json`, `run-manifest-20261015-142646.json`
  * JFR Files: `results/jfr/recording-20261015-141857.jfr`, `recording-20261015-142646.jfr`
* **Analysis & Verification:** JFR binary parser recorded non-zero pinning events (e.g. exactly 110 events per trial in Stratum 5). Stack trace classifies pin origin directly at `PaymentService.processPayment()` synchronized monitor.
* **Boundaries & Limitations:** Measured with HotSpot `profile.jfc` threshold of 20 ms. Establishes pinning for monitor holds $\ge 20\text{ ms}$; cannot establish the frequency of sub-20ms pinning events.
* **Thesis Destination:** Chapter 5 (Section 5.2), Chapter 6 (Section 6.1).
* **Admission Decision:** **Admit as Primary Quantitative Finding.**

---

### `CLM-RQ1-02`: Carrier Pool Starvation Under Single-Carrier Stress
* **Exact Proposition:** Under a single-carrier scheduler configuration (`parallelism=1`, `maxPoolSize=1`), pinning the carrier thread during a 500 ms serialized synchronized block stalls all other virtual threads assigned to the scheduler, bounding system throughput to $\le 2.0\text{ req/s}$ regardless of concurrent virtual thread count (10 VUs).
* **Epistemic Class:** `[MEASURED]` + `[DERIVED]`
* **Evidence Stratum:** **Stratum 1** (`java21-primary-repeat`, trials 1–3).
* **Experimental Conditions:** JDK 21.0.8, `parallelism=1`, `maxPoolSize=1`, endpoint `/payments`, 10 VUs, closed-loop.
* **Raw Evidence Artifacts:**
  * Results: `results/run-10vus-20261015-142646.json`, `run-10vus-20261015-142750.json`, `run-10vus-20261015-142854.json`
  * Script: `scripts/recalculate_metrics.py`
* **Analysis & Verification:** Measured steady-state throughput is $1.967\text{ req/s}$ ($X_{\text{steady}} = 59 / 30.0\text{s}$), with steady-state median latency of $4966.78\text{ ms}$. Derived upper bound from 500 ms mutual exclusion is $1 / 0.500\text{s} = 2.000\text{ req/s}$.
* **Boundaries & Limitations:** Specific to single-carrier scheduler constraint. Does not represent unconstrained multi-core throughput where additional carriers remain unpinned.
* **Thesis Destination:** Chapter 5 (Section 5.2), Chapter 6 (Section 6.1).
* **Admission Decision:** **Admit as Primary Quantitative Finding.**

---

### `CLM-RQ1-03`: `ReentrantLock` Unpinning Independence
* **Exact Proposition:** Replacing `synchronized` with `java.util.concurrent.locks.ReentrantLock` around the 500 ms critical section completely eliminates recorded `jdk.VirtualThreadPinned` events in Java 21, allowing virtual threads to unmount from their carrier during cooperative blocking.
* **Epistemic Class:** `[MEASURED]`
* **Evidence Stratum:** **Stratum 1** (`java21-primary-matrix`, `java21-primary-repeat`).
* **Experimental Conditions:** JDK 21.0.8, `parallelism=1`, endpoint `/payments`, lock treatment `reentrant-lock`, 10 VUs.
* **Raw Evidence Artifacts:**
  * JFR Files: `results/jfr/recording-20261015-142959.jfr`, `recording-20261015-143105.jfr`, `recording-20261015-143210.jfr`
* **Analysis & Verification:** JFR event parser extracts exactly **0** `jdk.VirtualThreadPinned` events across all 6 primary ReentrantLock trials.
* **Boundaries & Limitations:** Establishes absence of pinning events $\ge 20\text{ ms}$. Carrier unmounting is enabled by JUC `AbstractQueuedSynchronizer` calling `LockSupport.park()`.
* **Thesis Destination:** Chapter 5 (Section 5.2), Chapter 6 (Section 6.1).
* **Admission Decision:** **Admit as Primary Quantitative Finding.**

---

### `CLM-RQ1-04`: Decoupling of Carrier Unpinning from Application Serialization (Core Thesis Thesis)
* **Exact Proposition:** Eliminating monitor pinning by refactoring to `ReentrantLock` does not eliminate application-level serialization: under an identical 500 ms in-memory critical section, throughput remains constrained to $\approx 1.96\text{ req/s}$ and median latency remains $\approx 4976\text{ ms}$, identical within $0.5\%$ to the synchronized treatment.
* **Epistemic Class:** `[MEASURED]` + `[INTERPRETED]`
* **Evidence Stratum:** **Stratum 1** (`java21-primary-repeat`).
* **Experimental Conditions:** JDK 21.0.8, `parallelism=1`, 10 VUs, comparing `payments-synchronized` vs. `payments-reentrant-lock`.
* **Raw Evidence Artifacts:**
  * Metrics CSV: `docs/evidence-freeze/metric-recalculations.csv` (rows 10 and 11).
  * Report: `docs/evidence-freeze/metric-recalculation-audit.md#L182-L215`.
* **Analysis & Verification:** Steady-state throughput: `synchronized` = $1.967\text{ req/s}$ vs. `reentrant-lock` = $1.963\text{ req/s}$ ($\Delta = 0.20\%$). Steady-state p50: `synchronized` = $4966.78\text{ ms}$ vs. `reentrant-lock` = $4981.95\text{ ms}$ ($\Delta = 0.31\%$).
* **Boundaries & Limitations:** Governed by Amdahl's Law (1967) and queueing theory. When the critical section duration ($500\text{ ms}$) dominates the request lifecycle, the bottleneck is mutual exclusion, not carrier thread availability.
* **Thesis Destination:** Chapter 5 (Section 5.3), Chapter 6 (Section 6.1.2), Chapter 8 (Discussion).
* **Admission Decision:** **Admit as Primary Central Contribution.**

---

### `CLM-RQ1-05`: Non-Fair Barging Signature in ReentrantLock Dispersion
* **Exact Proposition:** While median latency is identical between `synchronized` and `ReentrantLock`, `ReentrantLock` exhibits a wider within-treatment latency dispersion (spread $\approx 16\text{--}30\text{ ms}$, stdev $\approx 13\text{--}18\text{ ms}$) than `synchronized` (spread $\le 7.4\text{ ms}$, stdev $\le 3.6\text{ ms}$), reflecting non-fair queue barging in Java's `AbstractQueuedSynchronizer` (AQS).
* **Epistemic Class:** `[DERIVED]` + `[INTERPRETED]`
* **Evidence Stratum:** **Stratum 1** (`java21-primary-repeat`).
* **Experimental Conditions:** JDK 21.0.8, `parallelism=1`, 10 VUs, $N=3$ process repetitions.
* **Raw Evidence Artifacts:** `docs/evidence-freeze/metric-recalculations.csv`, `scripts/recalculate_metrics.py`.
* **Analysis & Verification:** Calculated standard deviations across steady-state trials. Confirmed via OpenJDK source inspection of `ReentrantLock` default non-fair sync constructor (`NonfairSync`).
* **Boundaries & Limitations:** Derived from $N=3$ process runs per condition. Represents qualitative behavioral signature of AQS barging, not an asymptotic distribution proof.
* **Thesis Destination:** Chapter 5 (Section 5.3), Chapter 6 (Section 6.1.3).
* **Admission Decision:** **Admit with Explicit Methodological Qualification ($N=3$).**

---

### `CLM-RQ1-06`: Java 24 Runtime Monitor Unpinning (JEP 491)
* **Exact Proposition:** On Java 24 (build 24.0.2), object monitor contention (`synchronized`) no longer pins virtual threads to carrier threads during cooperative blocking, recording exactly 0 `jdk.VirtualThreadPinned` events under the identical workload that produced 110 pinning events on Java 21.
* **Epistemic Class:** `[MEASURED]` + `[EXTERNALLY SUPPORTED]`
* **Evidence Stratum:** **Stratum 2** (`java24-sync-repeat`, trials 1–3).
* **Experimental Conditions:** OpenJDK 24.0.2, Darwin arm64, endpoint `/payments`, lock treatment `synchronized`, 10 VUs.
* **Raw Evidence Artifacts:**
  * Manifests: `results/run-manifest-20261015-144513.json`, `run-manifest-20261015-144617.json`, `run-manifest-20261015-144722.json`
  * JFR Files: `results/jfr/recording-20261015-144513.jfr`, `recording-20261015-144617.jfr`
* **Analysis & Verification:** JFR binary parser confirms exactly 0 pinning events. Reconciles with JEP 491 specification (HotSpot object monitor redesign to support continuation parking).
* **Boundaries & Limitations:** Validated on Java 24.0.2. Confirms unpinning, but throughput remains bound to $\approx 1.97\text{ req/s}$ due to Amdahl's serialization.
* **Thesis Destination:** Chapter 5 (Section 5.7), Chapter 6 (Section 6.1.4).
* **Admission Decision:** **Admit as Supporting Comparative Finding.**

---

### `CLM-RQ1-07`: Discarded HotSpot Carrier Dynamic Compensation Myth
* **Exact Proposition:** HotSpot's `ForkJoinPool` virtual thread scheduler never dynamically spawned additional carrier threads to compensate for monitor pinning; the setting `-Djdk.virtualThreadScheduler.maxPoolSize=1` only constrained `ForkJoinPool.ManagedBlocker` expansions (file I/O), not monitor pinning.
* **Epistemic Class:** `[EXTERNALLY SUPPORTED]` + `[INTERPRETED]`
* **Evidence Stratum:** External Technical Literature (JEP 444, HotSpot `forkJoinPool.c` / `VirtualThread.java`).
* **Experimental Conditions:** N/A (Specification / Code Audit).
* **Raw Evidence Artifacts:** `docs/fact-check-jdk-runtime.md#L45-L68`, `docs/experiment-audit.md#L112-L124`.
* **Analysis & Verification:** Inspection of OpenJDK HotSpot source code confirms that carrier threads executing `monitorenter` do not implement `ManagedBlocker`. HotSpot treats monitor pinning as a passive stall.
* **Boundaries & Limitations:** Directly refutes earlier Scout Report Finding 9.1.
* **Thesis Destination:** Chapter 2 (Background), Chapter 6 (Analysis).
* **Admission Decision:** **Admit as Corrective Theoretical Finding.**

---

## 3. Research Question 2 (RQ2): Architectural Migration Risks

> **RQ2 Focus:** What architectural risks—including native boundaries, connection pool management, context propagation, and observability limits—must engineering teams evaluate before enabling Virtual Threads in Spring Boot MVC?

---

### `CLM-RQ2-01`: Silent Carrier Starvation via JNI Blocking
* **Exact Proposition:** Invocations of native C functions via JNI that execute blocking system calls (`nanosleep`) hold the underlying OS carrier thread captive for the entire blocking duration, starving the carrier pool without emitting `jdk.VirtualThreadPinned` events.
* **Epistemic Class:** `[MEASURED]` + `[INTERPRETED]`
* **Evidence Stratum:** **Stratum 3** (`native-boundary-20261008-repeated`, 9 trials on JDK 21).
* **Experimental Conditions:** JDK 21.0.8, `parallelism=1`, endpoint `/native`, C library `libnativeblocking.dylib`, 10 VUs.
* **Raw Evidence Artifacts:**
  * JFR Files: `results/jfr/recording-20261008-143952.jfr` through `recording-20261008-144201.jfr` (all report 0 pinning events).
  * Load Results: `results/run-10vus-20261008-143952.json` (throughput pegged at $1.97\text{ req/s}$, p50 = $4963.36\text{ ms}$).
  * Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L40-L120`.
* **Analysis & Verification:** The carrier thread enters `_thread_in_native`. Because native code never calls `Continuation.yield()`, HotSpot's continuation freeze subsystem is bypassed entirely, suppressing JFR pinning event generation.
* **Boundaries & Limitations:** Demonstrates that JFR's `jdk.VirtualThreadPinned` is an unmount-failure event, not an OS carrier thread stall detector.
* **Thesis Destination:** Chapter 5 (Section 5.5), Chapter 6 (Section 6.2.1), Chapter 7 (Migration Guidance).
* **Admission Decision:** **Admit as Primary Architectural Risk Finding.**

---

### `CLM-RQ2-02`: JNI Carrier Captivity CPU State
* **Exact Proposition:** Carrier thread monopolization during a blocking POSIX `nanosleep()` system call consumes negligible active processor cycles (steady-state JVM process CPU $\approx 1.0\%$), disproving claims that native carrier blocking manifests as 100% CPU utilization.
* **Epistemic Class:** `[MEASURED]`
* **Evidence Stratum:** **Stratum 3** (`native-boundary-20261008-repeated`, 9 telemetry streams).
* **Experimental Conditions:** Apple M1 Darwin 25.2.0, bare-metal host, companion process telemetry sampled at 1-second intervals via `ps -p $APP_PID -o %cpu=`.
* **Raw Evidence Artifacts:**
  * Telemetry Streams: `results/telemetry-20261008-143952.csv`, `telemetry-20261008-144056.csv`, `telemetry-20261008-144201.csv`
  * Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L55-L95`
* **Analysis & Verification:** Average steady-state CPU across all 9 trials is $1.04\% \pm 0.12\%$, with peak steady-state sample $\le 8.5\%$. High initial CPU ($32\%\text{--}89\%$) is restricted to JVM startup and k6 ramp-up.
* **Boundaries & Limitations:** Measures JVM process CPU on Darwin; carrier is asleep in kernel wait-queue (`TASK_INTERRUPTIBLE` equivalent in Darwin XNU). Does not represent busy-wait native spin-loops (e.g. SQLite busy-timeout).
* **Thesis Destination:** Chapter 5 (Section 5.5), Chapter 6 (Section 6.2.1).
* **Admission Decision:** **Admit as Corrective Empirical Finding.**

---

### `CLM-RQ2-03`: Pre-Acquisition Delay Flaw in Database Connection Testing
* **Exact Proposition:** In the `/orders` benchmark, `simulateSlowQuery()` (`Thread.sleep(300)`) executed prior to `jdbcTemplate.queryForList(...)`, resulting in connection checkout durations of $< 0.1\text{ ms}$; consequently, the experiment tested virtual thread sleep unmounting rather than database connection pool contention or exhaustion.
* **Epistemic Class:** `[MEASURED]` + `[DERIVED]` + `[INTERPRETED]`
* **Evidence Stratum:** **Stratum 4** (`java21-endpoint-isolation`) & **Stratum 7** (`h2-pool-sensitivity`, `docker-pg-orders`).
* **Experimental Conditions:** Local H2 & Docker PostgreSQL, 50 VUs, HikariCP max pool sizes 1 vs. 10.
* **Raw Evidence Artifacts:**
  * Source Code: `src/main/java/.../OrderService.java#L40-L48`
  * Load Results: `results/run-10vus-20261015-143319.json`, `results/docker-pg-orders-pool1-trial1.json`
  * Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L145-L185`
* **Analysis & Verification:** Code audit confirms lack of `@Transactional`. Little's Law derivation ($L_{\text{pool}} = X \times T_{\text{hold}} = 166.4 \times 0.0001\text{s} \approx 0.0166\text{ connections}$) proves the connection pool was over 98% idle even at pool size 1.
* **Boundaries & Limitations:** Derived estimate from request throughput and query execution time under stated assumptions, not direct HikariCP internal pool JMX telemetry.
* **Thesis Destination:** Chapter 4 (Section 4.3), Chapter 5 (Section 5.6), Chapter 6 (Section 6.2.2).
* **Admission Decision:** **Admit with Mandatory Construct Flaw Qualification.**

---

### `CLM-RQ2-04`: HikariCP Property Ingestion Defect in Local H2 Environment
* **Exact Proposition:** In `application.yml`, lines 13–17 indented `datasource:` under `demo:`, causing Spring Boot 3 to ignore custom datasource properties and fall back to auto-configured in-memory H2 with default HikariCP parameters (`maximumPoolSize = 10`).
* **Epistemic Class:** `[MEASURED]` (via Source Inspection) + `[EXTERNALLY SUPPORTED]`
* **Evidence Stratum:** Configuration Audit (`src/main/resources/application.yml`).
* **Experimental Conditions:** Spring Boot 3.5.12, local execution.
* **Raw Evidence Artifacts:**
  * Configuration: `src/main/resources/application.yml#L13-L17`
  * Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L125-L140`
* **Analysis & Verification:** Spring Boot `DataSourceProperties` binds strictly to prefix `spring.datasource`. Grep across `src/` confirmed no `@ConfigurationProperties(prefix = "demo")` bean exists.
* **Boundaries & Limitations:** Affects local H2 runs. Does not affect Docker Compose PostgreSQL runs, which injected valid environment variables (`SPRING_DATASOURCE_*`).
* **Thesis Destination:** Chapter 4 (Section 4.2), Chapter 6 (Section 6.2.2).
* **Admission Decision:** **Admit as Configuration Defect Qualification.**

---

### `CLM-RQ2-05`: PostgreSQL Performance Isolation vs. JFR Omission
* **Exact Proposition:** Dockerized PostgreSQL benchmark executions demonstrated stable sub-millisecond query execution under 50 VUs, but cannot substantiate claims regarding carrier unmounting or carrier starvation during database network I/O because JFR instrumentation was omitted from the container runtime.
* **Epistemic Class:** `[MEASURED]` (k6) + `[NOT ESTABLISHED]` (JFR Pinning)
* **Evidence Stratum:** **Stratum 7** (`docker-pg-orders`, 6 unmanifested k6 runs).
* **Experimental Conditions:** Docker Compose, PostgreSQL 15-alpine, 50 VUs, `cpus: '0.5'`.
* **Raw Evidence Artifacts:**
  * Results: `results/docker-pg-orders-pool1-trial{1,2,3}.json`, `docker-pg-orders-pool10-trial{1,2,3}.json`
  * Dockerfile: `Dockerfile#L14-L18`
  * Forensic Report: `docs/evidence-freeze/forensic-investigations.md#L190-L215`
* **Analysis & Verification:** k6 output verifies zero failed HTTP requests and stable latency ($p50 \approx 303.5\text{ ms}$). Inspection of `Dockerfile` confirms no `-XX:StartFlightRecording` option was supplied.
* **Boundaries & Limitations:** Performance data is admitted as secondary exploratory evidence; all claims of measured carrier unmounting on PostgreSQL are declared **Not Established**.
* **Thesis Destination:** Chapter 5 (Section 5.6), Chapter 6 (Section 6.2.2).
* **Admission Decision:** **Admit Performance Data Only; Disqualify JFR Claims.**

---

### `CLM-RQ2-06`: Driver Pinning Immunity in Modern PostgreSQL JDBC
* **Exact Proposition:** The project resolved `org.postgresql:postgresql:42.7.10`, which safely exceeds the `pgjdbc >= 42.6.0` threshold wherein internal monitor synchronization was refactored to eliminate carrier pinning during network socket operations.
* **Epistemic Class:** `[EXTERNALLY SUPPORTED]` + `[MEASURED]` (Dependency Resolution)
* **Evidence Stratum:** Resolved Maven Dependency Tree (`pom.xml#L48-L51`).
* **Experimental Conditions:** Maven 3.9 build audit.
* **Raw Evidence Artifacts:** `pom.xml`, `docs/experiment-audit.md#L45-L60`.
* **Analysis & Verification:** `mvn dependency:tree` confirms exact version `42.7.10`. Fact-check report verified pgjdbc PR #2670 and Issue #1951.
* **Boundaries & Limitations:** Establishes driver-level code safety from external specifications; does not constitute local JFR measurement of socket unmounting.
* **Thesis Destination:** Chapter 4 (Section 4.2), Chapter 7 (Migration Guidance).
* **Admission Decision:** **Admit as Literature & Dependency Audit Finding.**

---

### `CLM-RQ2-07`: Memory Bloat Risk of Unbounded ThreadLocal Allocations
* **Exact Proposition:** While virtual threads unmount safely during blocking, retaining large ThreadLocal object graphs across millions of concurrent virtual threads risks severe heap exhaustion and memory bloat, as virtual threads do not recycle ThreadLocal maps in the manner of bounded platform thread pools.
* **Epistemic Class:** `[EXTERNALLY SUPPORTED]` + `[INTERPRETED]`
* **Evidence Stratum:** Anti-Pattern Inspection (`OrderService.java#L26-L28`) & Literature (JEP 444).
* **Experimental Conditions:** Static code inspection.
* **Raw Evidence Artifacts:** `src/main/java/.../OrderService.java#L10-L15`, `docs/fact-check-jdk-runtime.md#L80-L105`.
* **Analysis & Verification:** In `OrderService`, `REQUEST_CONTEXT` simulates Spring RequestContextHolder. JEP 444 establishes that unbounded virtual thread allocation turns per-thread memory overhead into an $O(N)$ heap scaling liability.
* **Boundaries & Limitations:** Demonstrated conceptually; the 10-VU and 50-VU closed-loop load tests did not generate enough concurrent threads to trigger an OutOfMemoryError.
* **Thesis Destination:** Chapter 6 (Section 6.2.3), Chapter 7 (Migration Guidance).
* **Admission Decision:** **Admit as Theoretical & Architectural Guidance Finding.**

---

## 4. Methodology, Infrastructure, and Measurement Claims

---

### `CLM-METH-01`: Physical Nature of Single-Carrier Concurrency
* **Exact Proposition:** The configuration `-Djdk.virtualThreadScheduler.parallelism=1` represents a JVM scheduler-level concurrency constraint executed on bare-metal Darwin (8 logical core Apple M1), designed strictly for mechanism isolation, and must not be described as a 1-vCPU container quota.
* **Epistemic Class:** `[MEASURED]` (Host Environment) + `[INTERPRETED]`
* **Evidence Stratum:** All Manifests in Strata 1, 3, 4, 6.
* **Experimental Conditions:** Host OS: Darwin 25.2.0 (macOS 15), Apple M1 (8 logical processors), 8 GB RAM.
* **Raw Evidence Artifacts:**
  * Manifests: `results/run-manifest-20261015-142646.json#L9-L12`
  * Adjudication: `docs/evidence-freeze/referee-review-adjudication.md#L75-L88`
* **Analysis & Verification:** Host inspection confirms 8 physical/logical cores. The JVM scheduler flag limits the `ForkJoinPool` carrier worker count to 1, while OS background threads, GC, JFR, and the benchmark client execute across all 8 host cores.
* **Boundaries & Limitations:** Valid for isolating contention mechanics; invalid as a model of Linux cgroup CPU bandwidth throttling (`cpu.max`).
* **Thesis Destination:** Chapter 3 (Section 3.4), Chapter 4 (Section 4.4).
* **Admission Decision:** **Admit as Methodological Baseline Specification.**

---

### `CLM-METH-02`: Dual-Window Metric Sensitivity & Ramp-Up Inflection
* **Exact Proposition:** For mutual exclusion bottlenecks (`/payments`), whole-run (55s) vs. hold-window (15–45s) throughput differs by $< 0.8\%$; however, for ramp-sensitive or unsaturated workloads (`platform-synchronized`), whole-run median latency (~3920 ms) under-reports steady-state equilibrium latency (~4930 ms) by $25.8\%$ due to requests completed during the 15s ramp-up slope.
* **Epistemic Class:** `[MEASURED]` + `[DERIVED]`
* **Evidence Stratum:** **Stratum 1** & **Stratum 5** (`metric-recalculations.csv`).
* **Experimental Conditions:** 10 VUs, 15s ramp-up, 30s hold, 10s ramp-down.
* **Raw Evidence Artifacts:**
  * Recalculations: `docs/evidence-freeze/metric-recalculations.csv#L10-L16`
  * Recalculation Audit: `docs/evidence-freeze/metric-recalculation-audit.md#L110-L165`
* **Analysis & Verification:** Calculated unrounded metrics. Resolved previous reporting error: throughput delta on run `142445` is **0.765%** (not $<0.2\%$), while p50 latency delta is **0.184%**.
* **Boundaries & Limitations:** Requires mandatory side-by-side reporting in Chapter 5. Hold window is qualified as a derived metric, not an unconditional steady-state proof.
* **Thesis Destination:** Chapter 3 (Section 3.8), Chapter 5 (Section 5.1).
* **Admission Decision:** **Admit as Methodological Mandate.**

---

### `CLM-METH-03`: Descriptive Bounding of $N=3$ Process Repetitions
* **Exact Proposition:** Observed latency ranges across $N=3$ process repetitions exhibit tight clustering (within-treatment relative spread $< 0.7\%$ of mean latency), confirming high process reproducibility for mechanism isolation, but sample sizes ($N=3$) are descriptive only and do not support inferential hypothesis testing or asymptotic variance claims.
* **Epistemic Class:** `[DERIVED]` + `[INTERPRETED]`
* **Evidence Stratum:** Strata 1, 3, 4, 5.
* **Experimental Conditions:** Independent process-level restarts with JVM warm-up.
* **Raw Evidence Artifacts:** `docs/evidence-freeze/metric-recalculations.csv`, `scripts/recalculate_metrics.py`.
* **Analysis & Verification:** Standard deviations and min/max spreads computed for all primary conditions in `metric-recalculation-audit.md` Section 5.
* **Boundaries & Limitations:** Excludes claims of statistical significance (p-values, Student's t-tests, ANOVA). Results are presented as empirical engineering benchmarks.
* **Thesis Destination:** Chapter 3 (Section 3.6), Chapter 5 (Section 5.1).
* **Admission Decision:** **Admit with Explicit Descriptive Framing.**

---

### `CLM-METH-04`: JFR 20 ms Threshold Diagnostic Limitation
* **Exact Proposition:** HotSpot's built-in `profile.jfc` configuration specifies a 20 ms threshold for `jdk.VirtualThreadPinned`; consequently, recording zero pinning events establishes only that no pinning events $\ge 20\text{ ms}$ occurred, and cannot prove the complete absence of micro-pinning events below 20 ms.
* **Epistemic Class:** `[EXTERNALLY SUPPORTED]` + `[INTERPRETED]`
* **Evidence Stratum:** JVM Configuration Audit (`run-benchmark.sh#L164`).
* **Experimental Conditions:** `-XX:StartFlightRecording=settings=profile`.
* **Raw Evidence Artifacts:** `run-benchmark.sh#L160-L165`, OpenJDK `profile.jfc` definition.
* **Analysis & Verification:** Inspection of `run-benchmark.sh` revealed script comment `# threshold=10ms` was non-operative. HotSpot loaded standard `profile.jfc` with default `threshold=20ms`.
* **Boundaries & Limitations:** All "zero pinning" claims in the thesis must be bounded to the 20 ms measurement window.
* **Thesis Destination:** Chapter 3 (Section 3.5), Chapter 6 (Section 6.2.4).
* **Admission Decision:** **Admit as Observability Qualification.**

---

### `CLM-METH-05`: Closed-Loop Workload Capacity Saturation
* **Exact Proposition:** Under a closed-loop k6 workload with 10 fixed virtual users, system throughput is fundamentally governed by Little's Law ($X = N / R$); when a 500 ms mutual exclusion bottleneck causes response time $R$ to scale to $\approx 5000\text{ ms}$, maximum possible throughput is mathematically capped at $10 / 5.0\text{s} = 2.0\text{ req/s}$, regardless of thread implementation efficiency.
* **Epistemic Class:** `[DERIVED]` + `[EXTERNALLY SUPPORTED]`
* **Evidence Stratum:** Workload Specification (`k6/isolated-load-test.js`).
* **Experimental Conditions:** 10 VUs, closed-loop (VU waits for response before sending next request).
* **Raw Evidence Artifacts:** `k6/isolated-load-test.js#L12-L21`, `docs/fact-check-methodology-performance.md#L30-L55`.
* **Analysis & Verification:** Little's Law (1961) applied to closed queueing network. Matches measured throughput ($1.96\text{--}1.98\text{ req/s}$) across all serialized conditions.
* **Boundaries & Limitations:** Explains why virtual threads cannot bypass queueing bottlenecks under closed-loop concurrency. Open-loop arrival rate testing remains future work.
* **Thesis Destination:** Chapter 3 (Section 3.3), Chapter 6 (Section 6.1.2).
* **Admission Decision:** **Admit as Theoretical & Derived Baseline.**

---

## 5. Engineering Migration Guidance Claims (Chapter 7)

---

### `CLM-MIG-01`: The Mutex Refactoring Rule
* **Exact Proposition:** Engineering teams must not refactor `synchronized` blocks to `ReentrantLock` expecting throughput improvements if the critical section represents an application-level serialization bottleneck; refactoring to `ReentrantLock` only recovers carrier availability for concurrent, independent tasks when carrier threads are scarce.
* **Epistemic Class:** `[INTERPRETED]` (from `CLM-RQ1-04` & `CLM-RQ1-02`)
* **Evidence Stratum:** Derived from Strata 1 & 4.
* **Thesis Destination:** Chapter 7 (Section 7.1).
* **Admission Decision:** **Admit as Core Migration Guideline.**

---

### `CLM-MIG-02`: The Native JNI Isolation Rule
* **Exact Proposition:** Legacy native libraries (JNI) or native database drivers (e.g. SQLite C drivers) must never be executed directly on virtual threads without dedicated off-carrier thread pools (e.g. bounded platform thread executors), as native blocking silently captures carrier threads without triggering JFR pinning alerts.
* **Epistemic Class:** `[INTERPRETED]` (from `CLM-RQ2-01` & `CLM-RQ2-02`)
* **Evidence Stratum:** Derived from Stratum 3.
* **Thesis Destination:** Chapter 7 (Section 7.2).
* **Admission Decision:** **Admit as Core Migration Guideline.**

---

### `CLM-MIG-03`: The Connection Pool Sizing Fallacy
* **Exact Proposition:** Migrating to virtual threads does not permit unbounded database connection pool expansion; physical database connection limits are governed by database server hardware (CPU, disk I/O, lock contention), and virtual threads awaiting connection checkout must be bounded via HikariCP queue timeouts to prevent server-side connection collapse.
* **Epistemic Class:** `[EXTERNALLY SUPPORTED]` + `[INTERPRETED]` (from `CLM-RQ2-03`)
* **Evidence Stratum:** External Best Practice & HikariCP Architecture.
* **Thesis Destination:** Chapter 7 (Section 7.3).
* **Admission Decision:** **Admit as Core Migration Guideline.**

---

### `CLM-MIG-04`: The JFR Production Monitoring Rule
* **Exact Proposition:** When monitoring virtual thread health in production, operations teams must recognize that `jdk.VirtualThreadPinned` only detects monitor-hold unmount failures above the configured JFR threshold (default 20 ms), and must complement JFR with carrier thread pool queue latency metrics and OS thread utilization monitoring to detect native or sub-threshold stalls.
* **Epistemic Class:** `[INTERPRETED]` (from `CLM-METH-04` & `CLM-RQ2-01`)
* **Evidence Stratum:** Derived from Strata 1 & 3.
* **Thesis Destination:** Chapter 7 (Section 7.4).
* **Admission Decision:** **Admit as Core Migration Guideline.**

---

## 6. Master Claim Admission Ledger Summary

| Claim ID | Category | Evidence Stratum | Core Subject | Admission Status |
|---|:---:|:---:|---|:---:|
| `CLM-RQ1-01` | `[MEASURED]` | Stratum 1 & 5 | Java 21 `synchronized` produces pinning events | **Admitted (Primary)** |
| `CLM-RQ1-02` | `[MEASURED]`+`[DERIVED]` | Stratum 1 | 1-carrier pool starves under 500ms lock; TP $\le 2.0$ | **Admitted (Primary)** |
| `CLM-RQ1-03` | `[MEASURED]` | Stratum 1 | `ReentrantLock` eliminates JFR pinning events | **Admitted (Primary)** |
| `CLM-RQ1-04` | `[MEASURED]`+`[INTERPRETED]` | Stratum 1 | Unpinning $\neq$ unserializing; TP identical (~1.96 req/s) | **Admitted (Core Thesis)** |
| `CLM-RQ1-05` | `[DERIVED]`+`[INTERPRETED]` | Stratum 1 | AQS non-fair barging increases ReentrantLock dispersion | **Admitted (Qualified N=3)** |
| `CLM-RQ1-06` | `[MEASURED]`+`[EXT_SUPP]` | Stratum 2 | Java 24 JEP 491 eliminates monitor pinning | **Admitted (Supporting)** |
| `CLM-RQ1-07` | `[EXT_SUPP]`+`[INTERP]` | External / Spec | HotSpot never compensated pinning with extra carriers | **Admitted (Corrective)** |
| `CLM-RQ2-01` | `[MEASURED]`+`[INTERPRETED]` | Stratum 3 | JNI `nanosleep` starves carrier; 0 JFR pinning events | **Admitted (Primary)** |
| `CLM-RQ2-02` | `[MEASURED]` | Stratum 3 | Steady-state JNI CPU is ~1.0%, not 100% | **Admitted (Corrective)** |
| `CLM-RQ2-03` | `[MEASURED]`+`[DERIVED]` | Stratum 4 & 7 | `/orders` sleep occurs pre-checkout; pool was unexercised | **Admitted (Construct Flaw)** |
| `CLM-RQ2-04` | `[MEASURED]`+`[EXT_SUPP]` | Config Audit | `demo.datasource` indentation defect; H2 defaulted | **Admitted (Defect Qual.)** |
| `CLM-RQ2-05` | `[MEASURED]`+`[NOT_EST]` | Stratum 7 | Docker PG k6 runs admitted; PG JFR pinning unestablished | **Admitted (Bounded k6)** |
| `CLM-RQ2-06` | `[EXT_SUPP]`+`[MEASURED]` | Maven Audit | PostgreSQL driver 42.7.10 exceeds safe 42.6.0 threshold | **Admitted (Spec/Audit)** |
| `CLM-RQ2-07` | `[EXT_SUPP]`+`[INTERP]` | Code / JEP 444 | ThreadLocal unbounded allocation memory bloat risk | **Admitted (Guidance)** |
| `CLM-METH-01` | `[MEASURED]`+`[INTERPRETED]` | Strata 1, 3, 4 | `parallelism=1` is scheduler constraint on 8-core Darwin | **Admitted (Baseline)** |
| `CLM-METH-02` | `[MEASURED]`+`[DERIVED]` | Stratum 1 & 5 | Dual-window reporting; ramp-up shifts p50 by 25.8% | **Admitted (Mandate)** |
| `CLM-METH-03` | `[DERIVED]`+`[INTERPRETED]` | Strata 1, 3, 4, 5 | $N=3$ runs are descriptive mechanism units, not inferential | **Admitted (Limitation)** |
| `CLM-METH-04` | `[EXT_SUPP]`+`[INTERP]` | Config / JFR | 20 ms JFR threshold drops sub-20ms pinning events | **Admitted (Limitation)** |
| `CLM-METH-05` | `[DERIVED]`+`[EXT_SUPP]` | k6 Workload | Closed-loop Little's Law caps 10-VU throughput at 2 req/s | **Admitted (Baseline)** |
| `CLM-MIG-01` | `[INTERPRETED]` | Guidance | Mutex refactoring rule: unpinning $\neq$ throughput gain | **Admitted (Guideline)** |
| `CLM-MIG-02` | `[INTERPRETED]` | Guidance | JNI isolation rule: isolate native blocking from carriers | **Admitted (Guideline)** |
| `CLM-MIG-03` | `[EXT_SUPP]`+`[INTERP]` | Guidance | Connection pool fallacy: VT does not allow unbounded DB pool | **Admitted (Guideline)** |
| `CLM-MIG-04` | `[INTERPRETED]` | Guidance | JFR production monitoring rule: complement with carrier metrics | **Admitted (Guideline)** |

---

*(End of Stage 1.3 Claim-to-Evidence Ledger)*

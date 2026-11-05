# Chapter 3: Research Design and Methodology

## 3.1 Research Paradigm

This dissertation adopts an **empirical systems engineering** paradigm to evaluate the architectural, performance, and runtime consequences of migrating a Spring Boot Model-View-Controller (MVC) application to Java 21 Virtual Threads (Project Loom). Rather than treating runtime migration as a purely syntactic or configuration-level change, this research models the transition as an architectural intervention within a multi-tier concurrency and queueing network.

The empirical investigation is structured around a controlled, instrumented Spring Boot MVC benchmark application. In empirical software engineering, synthetic micro-benchmarks (such as isolated Java Microbenchmark Harness [JMH] loops) often isolate instruction-level cache and branch behavior at the expense of framework realism. Conversely, large-scale production deployments introduce confounding environmental variables—such as dynamic network hops, non-deterministic database query optimizers, and variable multi-tenant resource contention—that obscure the low-level scheduling and synchronization mechanics of the Java Virtual Machine (JVM). A dedicated, representative framework artifact strikes an optimal methodological compromise: it retains the realistic request lifecycle of Spring MVC, Apache Tomcat, and HikariCP while establishing strict experimental controls over carrier concurrency, workload generation, lock boundaries, and flight recorder telemetry.

The research design is deductive and hypothesis-testing in character. It isolates the specific operational mechanisms—monitor pinning, carrier thread exhaustion, application-level serialization, native system call blocking, and connection pool checkout timing—that govern throughput and latency under virtualized thread scheduling.

---

## 3.2 Research Questions and Operational Constructs

The study addresses two foundational Research Questions:

*   **Research Question 1 (RQ1):** *How does synchronization (specifically monitor pinning) interact with carrier-thread availability, application-level serialization, and runtime throughput in Java 21 Spring Boot MVC systems?*
*   **Research Question 2 (RQ2):** *What architectural risks—including native boundaries, connection pool management, context propagation, and observability limits—must engineering teams evaluate before enabling Virtual Threads in existing Spring Boot MVC systems?*

To operationalize these questions into empirically testable hypotheses, each research question is mapped to specific independent variables, dependent performance metrics, low-level mechanism indicators, and explicit decision boundaries, as summarized in Table 3.1.

### Table 3.1: Operational Construct and Evidentiary Mapping Matrix

| Research Question | Experimental Treatment | Controlled Baseline | Dependent Metrics | Direct Evidence Artifact | Operational Interpretation Rule | Methodological Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RQ1: Monitor Pinning & Serialization** | Virtual Threads + `synchronized` (`payments-synchronized`) | Platform Threads + `synchronized` (`platform-synchronized`) | Throughput ($req/s$), $p50$, $p95$, $p99$ Latency ($ms$) | k6 JSONL streams, JFR `jdk.VirtualThreadPinned` events | Pinning confirmed if JFR records events $\ge 20\text{ ms}$; carrier starvation confirmed if throughput collapses under `parallelism=1` | Bounded to single-carrier mechanism isolation; JFR threshold drops events $<20\text{ ms}$ (`CLM-RQ1-01`, `CLM-RQ1-02`) |
| **RQ1: Mutex Refactoring** | Virtual Threads + `ReentrantLock` (`payments-reentrant-lock`) | Virtual Threads + `synchronized` (`payments-synchronized`) | Throughput ($req/s$), $p50$, $p95$, $p99$ Latency ($ms$), trial dispersion | k6 JSONL streams, JFR event streams, Telemetry CSV | Unpinning confirmed if JFR events $= 0$; Amdahl serialization confirmed if throughput remains identical to `synchronized` | Refactoring eliminates pinning but preserves serialization; AQS non-fair barging increases variance (`CLM-RQ1-03`, `CLM-RQ1-04`) |
| **RQ1: Runtime Evolution** | Java 24 Virtual Threads + `synchronized` (JEP 491) | Java 21 Virtual Threads + `synchronized` | JFR Pinning Count, Throughput ($req/s$) | JFR binary recordings on JDK 24.0.2 | JEP 491 monitor unpinning confirmed if JFR pinning events drop from 110 to 0 | Unpinning does not bypass Amdahl's Law; serialization persists at $\approx 1.97\text{ req/s}$ (`CLM-RQ1-06`) |
| **RQ2: Native JNI Boundary** | JNI 500 ms `nanosleep()` (`/native`) | Pure Java 500 ms `Thread.sleep()` (`/payments/no-lock`) | Throughput ($req/s$), JFR Pinning Count, Process %CPU | k6 JSONL streams, JFR recordings, Telemetry CSVs | Carrier capture confirmed if throughput drops to $1.97\text{ req/s}$; observability gap confirmed if JFR pinning $= 0$ | POSIX `nanosleep` is kernel sleep, not busy CPU; JFR detects unmount failures, not OS stalls (`CLM-RQ2-01`, `CLM-RQ2-02`) |
| **RQ2: Database Pool Contention** | HikariCP pool size 1 (`maximumPoolSize=1`) | HikariCP pool size 10 (`maximumPoolSize=10`) | Latency distribution ($ms$), pool acquisition errors | k6 JSONL streams (`docker-pg-orders`, `h2-pool`) | Pool saturation confirmed if pool size 1 induces queue acquisition delays or timeouts | Pre-acquisition sleep defect in `OrderService` executed delay before connection checkout (`CLM-RQ2-03`) |
| **RQ2: Observability & Diagnostics** | Diagnostic No-Lock (`payments-no-lock`) | Virtual Threads + `synchronized` | Throughput ($req/s$), Latency ($ms$) | k6 JSONL streams, JFR event streams | Theoretical ceiling established if throughput reaches concurrency limit without serialization | Unsynchronized concurrent modification represents unsafe state; upper bound only (`CLM-RQ1-04`) |

---

## 3.3 Experimental Artifact

The core experimental artifact is a custom Spring Boot 3.5.12 application (`virtual-threads-demo`) implemented in Java 21 and compiled using Maven 3.9. The artifact models an enterprise e-commerce backend containing realistic operational concerns, including transactional payment processing, catalog querying, background native hashing/computation, and relational persistence.

The application deliberately incorporates architectural patterns and anti-patterns representative of legacy Spring MVC systems:
1.  **Shared-State Mutual Exclusion:** Services protecting shared in-memory transactional ledgers via both Java language-level monitors (`synchronized`) and explicit concurrency utilities (`ReentrantLock`).
2.  **Native Interface (JNI) Operations:** Services bridging into compiled C shared libraries (`libnativeblocking.dylib`) executing operating system system calls.
3.  **Relational Database Persistence:** Services executing relational queries through Spring's `JdbcTemplate` backed by HikariCP connection pools across embedded (H2) and containerized (PostgreSQL) databases.
4.  **Per-Request Context Storage:** Services capturing request-scoped state within `ThreadLocal` storage, modeling patterns common in Spring Security and `RequestContextHolder`.

---

## 3.4 System Architecture

The physical request architecture follows the standard synchronous servlet model of Spring MVC, deployed on an embedded Apache Tomcat 10.1.52 container. In traditional deployment, each incoming HTTP connection is dispatched to an operating system platform thread allocated from a bounded worker pool (Tomcat's default pool of 200 threads). When Virtual Threads are enabled via the Spring Boot 3 configuration property:

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

Tomcat's request handling delegates to a virtual thread per-task executor (`Executors.newVirtualThreadPerTaskExecutor()`). In this execution mode, Tomcat dispatches every incoming HTTP request to an ephemeral virtual thread.

```
+-----------------------------------------------------------------------------------+
|                                Client Load (k6)                                   |
|                10 to 50 Concurrent Virtual Users (Closed-Loop)                     |
+-----------------------------------------+-----------------------------------------+
                                          | HTTP / REST
                                          v
+-----------------------------------------------------------------------------------+
|                        Embedded Apache Tomcat 10.1.52                             |
|           Thread-Per-Task Executor: newVirtualThreadPerTaskExecutor()             |
+-----------------------------------------+-----------------------------------------+
                                          | Dispatches Virtual Thread
                                          v
+-----------------------------------------------------------------------------------+
|                       Spring Boot MVC Application Layer                           |
|                                                                                   |
|  +---------------------+   +---------------------+   +-------------------------+  |
|  |  PaymentController  |   |   OrderController   |   |    NativeController     |  |
|  +----------+----------+   +----------+----------+   +------------+------------+  |
|             |                         |                           |               |
|             v                         v                           v               |
|  +---------------------+   +---------------------+   +-------------------------+  |
|  |   PaymentService    |   |    OrderService     |   |  NativeBlockingService  |  |
|  | - synchronized      |   | - ThreadLocal       |   | - JNI C shared library  |  |
|  | - ReentrantLock     |   | - JdbcTemplate      |   | - POSIX nanosleep()     |  |
|  | - No-Lock (Control) |   | - simulateSlowQuery |   | - POSIX sched_yield()   |  |
|  +---------------------+   +----------+----------+   +------------+------------+  |
+---------------------------------------|---------------------------|---------------+
                                        |                           |
                                        v                           v
                       +--------------------------------+  +-----------------+
                       |     HikariCP Connection Pool   |  | libnative-      |
                       | - Local H2 (Embedded)          |  | blocking.dylib  |
                       | - Docker PostgreSQL 15-alpine  |  +-----------------+
                       +--------------------------------+
```

---

## 3.5 Endpoint and Treatment Design

The benchmark artifact exposes six dedicated endpoints designed to isolate specific concurrency, scheduling, and boundary mechanisms. Table 3.2 details the operational specification of each endpoint.

### Table 3.2: Experimental Endpoint and Treatment Specifications

| Endpoint Route | Primary Treatment | Underlying Workload / Mechanism | Architectural Role | Strict Evidentiary Limitation |
| :--- | :--- | :--- | :--- | :--- |
| `/payments` | `synchronized` vs. `reentrant-lock` vs. `no-lock` | 500 ms critical section holding an in-memory lock during simulated processing delay | Isolates Java 21 monitor pinning against non-pinning explicit locks under identical mutual exclusion | Does not evaluate database contention; delay is synthetic in-memory duration (`CLM-RQ1-04`) |
| `/native` | `blocking-jni` | 500 ms C-level POSIX `nanosleep()` system call via JNI | Evaluates carrier thread behavior during non-yielding foreign function execution | Does not execute busy-wait arithmetic; steady-state CPU is ~1%, not 100% (`CLM-RQ2-02`) |
| `/native-short` | `native-short` | Fast JNI C invocation executing a non-blocking no-op return | Measures pure JNI transition overhead across the JVM boundary | Cannot be used to assess thread scheduling or carrier starvation |
| `/orders` | `orders-virtual` vs. `orders-platform` | 300 ms simulated slow query delay followed by relational SQL query (`SELECT *`) | Evaluates JDBC driver coordination and HikariCP connection checkout | Sleep delay executed *before* connection checkout; does not stress pool capacity (`CLM-RQ2-03`) |
| `/products` | `products-virtual` vs. `products-platform` | Non-blocking in-memory catalog lookup returning static JSON payloads | Establishes framework baseline throughput without I/O or lock contention | Fast-path execution; highly sensitive to client-side VU ramp-up dynamics (`CLM-METH-02`) |
| `/cpu` | `cpu-virtual` vs. `cpu-platform` | 10,000 rounds of cryptographic SHA-256 computation over an in-memory byte buffer | Evaluates virtual thread scheduling overhead under CPU-saturated compute workloads | Virtual threads offer no throughput benefit over compute-bound tasks; establishes compute parity |

---

## 3.6 Primary Synchronization Matrix

The primary experimental treatment evaluates the `/payments` endpoint under four distinct synchronization configurations:
1.  **Platform Synchronized Baseline (`platform-synchronized`):** Platform threads (standard OS threads) executing within a Java `synchronized` block protecting a 500 ms critical section.
2.  **Virtual Thread Synchronized Treatment (`synchronized`):** Virtual threads executing within an identical Java `synchronized` block protecting the 500 ms critical section. Under Java 21, monitor contention triggers carrier thread pinning.
3.  **Virtual Thread ReentrantLock Treatment (`reentrant-lock`):** Virtual threads executing within a `java.util.concurrent.locks.ReentrantLock` block protecting the 500 ms critical section. Virtual threads unmount from carrier threads during lock acquisition contention via `LockSupport.park()`.
4.  **No-Lock Diagnostic Control (`no-lock`):** Virtual threads executing the 500 ms delay with mutual exclusion completely removed. This condition represents an intentionally unsafe state that violates correctness invariants, serving solely as an empirical upper bound on unconstrained concurrent scheduling.

### 3.6.1 Synchronization Design Comparison

To frame the thesis within broader software architecture theory, the synchronization mechanisms evaluated here are contrasted against alternative paradigms in concurrent systems design:

*   **Java Monitors (`synchronized`):** Intrinsic locks coupled to the object header. In Java 21, HotSpot's monitor subsystem associates the lock with the underlying execution thread. Because virtual threads are user-mode continuations multiplexed onto kernel threads, entering a monitor couples the user-mode stack to the physical OS carrier thread, preventing the continuation from unmounting during blocking operations.
*   **Explicit Locks (`ReentrantLock`):** Implemented in user-space Java via `AbstractQueuedSynchronizer` (AQS). Waiting threads park via `LockSupport.park()`, which delegates to `VirtualThread.park()`, cleanly unmounting the virtual thread continuation and yielding the carrier thread back to the scheduler.
*   **Actor and Message-Passing Architectures (e.g., Erlang, Akka):** Rather than sharing mutable state behind mutual exclusion locks, actor models enforce single-threaded isolation per actor and communicate via asynchronous mailboxes. Java's design choice with Project Loom intentionally rejected the colored-function and mailbox overhead of actor frameworks, choosing instead to preserve the traditional synchronous blocking imperative style.
*   **Database-Mediated and Optimistic Locking:** Techniques such as multiversion concurrency control (MVCC) or optimistic offline locks (`@Version`) push contention resolution into the storage engine. While highly scalable for distributed architectures, in-memory transactional systems frequently require process-level mutual exclusion to serialize hardware access, cash registers, or local ledger writes.

---

## 3.7 Experimental Run Families and Evidence Strata

To ensure that historical, pilot, and flawed runs are not conflated with verified experimental conditions, the repository's 119 physical executions (+1 schema template) are partitioned into the seven non-overlapping strata established in the Adjudication Charter:

### Table 3.3: Repository Evidence Strata Census

| Stratum Identifier | Target Focus | Execution Count | Runtime JDK | Scheduler Sizing | HikariCP Pool | Admitted Corpus Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Stratum 1** | Java 21 Primary Synchronization Matrix | 12 | 21.0.8 | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Primary)** |
| **Stratum 2** | Java 24/25 Runtime Comparison Matrix | 10 | 24.0.2, 25-ea | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Supporting)** |
| **Stratum 3** | Multi-JDK Native JNI Boundary Matrix | 27 | 21.0.8, 24, 25 | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Primary)** |
| **Stratum 4** | Supporting Architectural Controls | 18 | 21.0.8 | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Supporting)** |
| **Stratum 5** | 8-Carrier Historical Baseline Matrix | 12 | 21.0.8 | `parallelism=8`, `maxPoolSize=256` | 10 (default) | **Admitted (Historical Baseline)** |
| **Stratum 6** | Exploratory Pilots & Diagnostic Runs | 27 | 21, 24, Zulu | Variable (1, 8, default) | Variable | **Excluded from Primary Metrics** |
| **Stratum 7** | Construct-Flawed / Incomplete Runs | 13 | 21.0.8 | `parallelism=1`, `4` | 1, 10 | **Excluded (Methodological Flaw)** |
| **Template** | Schema Reference (`run-manifest-template.json`) | 1 | N/A | None | None | **Non-Execution Metadata** |
| **Total** | **Master Repository Population** | **120** | — | — | — | **119 Executions + 1 Template** |

---

## 3.8 Workload Protocol and Closed-Loop Queueing Mechanics

Load generation is driven by [k6](https://k6.io/) (v1.7.1) executing a parameterized test script (`k6/isolated-load-test.js`). The workload follows a staged closed-loop concurrency profile:
1.  **Stage 1 (Ramp-Up):** 15 seconds, scaling linearly from 0 to target Virtual Users (10 or 50 VUs).
2.  **Stage 2 (Steady-State Hold):** 30 seconds, maintaining fixed concurrent VUs.
3.  **Stage 3 (Ramp-Down):** 10 seconds, scaling linearly from target VUs back to 0.

Total execution duration is exactly 55 seconds per trial.

### 3.8.1 Closed-Loop and Open-Loop Workload Formalization

In a **closed-loop** workload model, a fixed population of Virtual Users ($N$) submits an HTTP request, waits synchronously for the response, and immediately upon receipt generates the subsequent request (zero think-time, $Z = 0$).

System throughput ($X$) and response time ($R$) are governed strictly by Little's Law for closed queueing networks (`CLM-METH-05`):

$$N = X \times R \implies X = \frac{N}{R}$$

When a mutual exclusion lock serializes a critical section of duration $T_{\text{serial}} = 500\text{ ms}$, the maximum theoretical system throughput ($X_{\text{max}}$) is strictly bounded by Amdahl's Law:

$$X_{\text{max}} = \frac{1}{T_{\text{serial}}} = \frac{1}{0.500\text{ s}} = 2.000\text{ req/s}$$

As concurrency ($N = 10\text{ VUs}$) saturates the single serialized server, an internal request queue forms. Equilibrium mean response time expands according to:

$$R = \frac{N}{X_{\text{max}}} = \frac{10}{2.000\text{ req/s}} = 5.000\text{ s} = 5000\text{ ms}$$

Under closed-loop generation, if response time degrades to 5000 ms, the client self-throttles: each VU can dispatch at most one request every 5 seconds. Consequently, closed-loop workloads cannot generate arbitrary offered arrival rates; they establish equilibrium capacity limits.

An **open-loop** arrival-rate workload (e.g., dispatching Poisson arrivals at a fixed rate $\lambda$ independent of server completion) would reveal queue divergence and catastrophic latency explosion under saturation. However, for the specific research goal of **mechanism isolation**—verifying whether carrier unmounting occurs during lock wait without risking client-side memory collapse—the closed-loop saturation model is methodologically superior, reproducible, and mathematically tractable.

---

## 3.9 Runtime and Environment Control

To eliminate cross-host virtualization noise, all primary benchmark trials were executed on dedicated bare-metal hardware.

### 3.9.1 Hardware and Operating System Specifications
*   **Host Platform:** Apple Silicon M1 (bare metal, no hypervisor virtualization).
*   **Compute Architecture:** 8 physical/logical cores (4 Performance cores + 4 Efficiency cores).
*   **Memory:** 8 GB unified memory.
*   **Operating System:** Darwin 25.2.0 (macOS 15 Sequoia, arm64).

### 3.9.2 Scheduler Configuration: Mechanism Isolation vs. Container Quotas (`CLM-METH-01`)
In Strata 1, 2, 3, and 4, the JVM virtual thread scheduler was explicitly constrained via runtime flags:

```bash
-Djdk.virtualThreadScheduler.parallelism=1
-Djdk.virtualThreadScheduler.maxPoolSize=1
```

*   **Operational Role:** `parallelism=1` limits the underlying `ForkJoinPool` carrier worker thread count to exactly one. This forces all virtual threads to compete for a single carrier core. If a virtual thread pins the carrier (via `synchronized`) or blocks the carrier (via JNI `nanosleep`), all other virtual threads stall. This mechanism isolation turns latent carrier starvation into an immediate, measurable throughput collapse.
*   **Strict Methodological Boundary:** This setting is an in-process JVM scheduler constraint, **not a Linux cgroup CPU bandwidth quota** (`cpu.cfs_quota_us`). The JVM process, garbage collector, JFR threads, Tomcat acceptor threads, and the k6 load generator continue to execute concurrently across all 8 host cores of the Apple M1 processor. The thesis explicitly rejects describing `parallelism=1` as "1-CPU container equivalence."

---

## 3.10 Observability Protocol and Instrumentation

The experimental testbed incorporates three independent, non-interfering observability layers:

### 3.10.1 Java Flight Recorder (JFR) Configuration (`CLM-METH-04`)
Every admitted trial executes with continuous JFR recording enabled at JVM startup:

```bash
-XX:StartFlightRecording=filename=recording.jfr,settings=profile,dumponexit=true
-Djdk.tracePinnedThreads=full
```

*   **The 20 ms Detection Threshold:** The JVM loads HotSpot's standard `profile.jfc` template, which enforces a minimum duration threshold of 20 ms for event emission:
    ```xml
    <event name="jdk.VirtualThreadPinned">
      <setting name="enabled">true</setting>
      <setting name="threshold">20 ms</setting>
      <setting name="stackTrace">true</setting>
    </event>
    ```
*   **Diagnostic Limit:** JFR records `jdk.VirtualThreadPinned` events **only when the pin duration equals or exceeds 20 ms**. Consequently, zero recorded events establishes only that no pinning events $\ge 20\text{ ms}$ occurred; it cannot rule out transient sub-20ms micro-pinning events.

### 3.10.2 Host Process Telemetry
A companion background sampling daemon captures process-level resource metrics at 1-second intervals:

```bash
ps -p "$APP_PID" -o %cpu=
```

*   **Attribution Boundary:** On Darwin/BSD, `%cpu` measures the decaying CPU percentage of the entire JVM process (`$APP_PID`), not an isolated thread. It captures background GC and framework activity in addition to application execution.

### 3.10.3 Cryptographic Artifact Hashing and Manifest Provenance
At the completion of each benchmark trial, the execution harness (`run-benchmark.sh`) captures a structured execution manifest (`run-manifest-<timestamp>.json`). The manifest records runtime parameters, Git commit hashes, environment variables, exit codes, and cryptographic SHA-256 digests of the raw k6 JSON result and JFR binary recording.

---

## 3.11 Correctness Gates and Semantic Invariants

Before any benchmark execution is admitted for performance analysis, it must satisfy seven strict correctness gates:
1.  **HTTP Correctness:** 100% of HTTP responses must return status code `200 OK`. Any trial exhibiting client timeouts or non-200 responses is disqualified.
2.  **Mutual Exclusion Invariant:** In the `/payments` endpoint, state transactions must maintain strict sequential consistency. In the no-lock diagnostic control (`no-lock`), concurrent modification is intentionally violated to quantify unconstrained overhead.
3.  **Carrier Independence Invariant:** In `ReentrantLock` treatments, thread safety must be achieved without emitting monitor pinning events.
4.  **Driver Safety Invariant:** Relational database queries must execute through drivers free of internal carrier-pinning synchronization.
5.  **Clean Process Teardown:** The JVM process must terminate cleanly via SIGTERM/SIGINT with an exit code of 0.
6.  **Cryptographic Integrity Gate:** Raw artifact SHA-256 hashes must match the manifest records with zero byte corruption.
7.  **Execution Stratum Gate:** Only runs belonging to pre-registered, controlled strata (Strata 1–5) are admitted into quantitative thesis comparisons.

---

## 3.12 Replication and Analysis Unit

### 3.12.1 The Independent Process Execution as the Analysis Unit
The primary experimental unit is the **independent process execution**. Micro-benchmarks that execute repeated iterations within a single long-lived JVM session suffer from JIT profile pollution, biased class loading, and unrepresentative memory fragmentation. In this study, every trial represents an independent JVM invocation with dedicated warm-up, clean thread pool initialization, and isolated JFR recording.

### 3.12.2 Descriptive Bounding of Sample Size ($N=3$) (`CLM-METH-03`)
Each primary condition was executed across $N=3$ independent process-level repetitions. Across all conditions, steady-state within-treatment latency dispersion was exceptionally tight:
*   Fast-path / diagnostic controls (`no-lock`, `products`): latency spread $\Delta \le 0.20\text{ ms}$, standard deviation $\sigma \le 0.10\text{ ms}$.
*   Synchronized monitor conditions (`synchronized`): latency spread $\Delta \le 7.41\text{ ms}$, standard deviation $\sigma \le 3.63\text{ ms}$ (at $\sim 4930\text{ ms}$).
*   Native JNI blocking (`blocking-jni`): latency spread $\Delta \le 33.79\text{ ms}$, standard deviation $\sigma \le 12.73\text{ ms}$ (at $\sim 4960\text{ ms}$).

Because within-treatment relative spread is less than $0.7\%$ of mean latency, $N=3$ process repetitions provide a highly reliable descriptive basis for mechanism isolation. However, in accordance with methodological rigor, **these $N=3$ trials are presented as descriptive engineering repetitions only; they are not used to make inferential statistical claims (such as p-values or confidence intervals)**.

### 3.12.3 Dual-Window Reporting Mandate (`CLM-METH-02`)
To address the effect of the 15-second ramp-up stage, the thesis mandates **dual-window reporting** for all latency and throughput metrics:
1.  **Whole-Run Window ($t \in [0\text{s}, 55\text{s}]$):** Aggregates all completed requests from benchmark initiation to termination ($55.0\text{ s}$ denominator).
2.  **Steady-State Hold Window ($t \in [15\text{s}, 45\text{s}]$):** Filters requests whose completion timestamps fall strictly within the 30-second constant-load hold stage ($30.0\text{ s}$ denominator).

For saturated mutual exclusion bottlenecks (`/payments`), whole-run vs. hold-window throughput varies by $< 0.8\%$ ($1.98\text{ req/s}$ vs. $1.97\text{ req/s}$, exact unrounded throughput delta = **0.765%**, p50 latency delta = **0.184%**). However, for ramp-sensitive workloads (`platform-synchronized`), whole-run median latency (~3920 ms) under-reports steady-state queueing latency (~4930 ms) by **25.8%**. Reporting both metrics side-by-side guarantees transparency.

---

## 3.13 Claim-Admission Framework

To ensure that thesis conclusions strictly respect experimental boundaries, claims are categorized into five distinct epistemic classes:

```
+---------------------------------------------------------------------------------+
|                         EPISTEMIC TAXONOMY OF CLAIMS                            |
+---------------------------------------------------------------------------------+
|  [MEASURED]             Directly captured in k6, JFR, or telemetry files       |
|  [DERIVED]              Calculated via Little's Law, filtering, or dispersion   |
|  [INTERPRETED]          Causal explanation via HotSpot C++ / OS architecture     |
|  [EXTERNALLY SUPPORTED] Established by OpenJDK JEPs, RFCs, or vendor specs      |
|  [NOT ESTABLISHED]      Unmeasured mechanisms, construct flaws, or null findings|
+---------------------------------------------------------------------------------+
```

### Table 3.4: Representative Claim Admission and Categorization Rules

| Candidate Proposition | Epistemic Class | Supporting Evidence Stratum | Evidentiary Basis | Final Admission Rule |
| :--- | :---: | :---: | :--- | :--- |
| Java 21 `synchronized` produces carrier pinning | `[MEASURED]` | Stratum 1 & 5 | Non-zero JFR `jdk.VirtualThreadPinned` events | Admitted without qualification (`CLM-RQ1-01`) |
| `ReentrantLock` eliminates carrier pinning | `[MEASURED]` | Stratum 1 | Exactly 0 JFR events under `profile.jfc` | Admitted, qualified by 20 ms threshold (`CLM-RQ1-03`) |
| Unpinning does not improve serialized throughput | `[MEASURED]` + `[INTERPRETED]` | Stratum 1 | Throughput identical at $1.96\text{ req/s}$ ($<0.3\%$ delta) | Admitted as primary thesis contribution (`CLM-RQ1-04`) |
| JNI `nanosleep` consumes 100% carrier CPU | `[NOT ESTABLISHED]` | Stratum 3 | Telemetry proves steady-state CPU is ~1.0% | **Refuted and purged** (`CLM-RQ2-02`, `DISC-02`) |
| `/orders` proved HikariCP pool saturation | `[NOT ESTABLISHED]` | Stratum 4 & 7 | Sleep delay executed before connection checkout | **Disqualified as construct flaw** (`CLM-RQ2-03`) |
| PostgreSQL unmounts cleanly during socket I/O | `[EXTERNALLY SUPPORTED]` | External Spec | Resolved driver 42.7.10 refactored internal locks | Admitted via external literature only (`CLM-RQ2-06`) |

---

## 3.14 Threats to Validity and Mitigations

### Table 3.5: Methodological Threats to Validity Matrix

| Threat Category | Specific Methodological Risk | Potential Evidentiary Impact | Applied Mitigation / Research Boundary |
| :--- | :--- | :--- | :--- |
| **Construct Validity** | Pre-acquisition sleep delay in `/orders` (`CLM-RQ2-03`) | Connection was never held during 300 ms sleep; pool was never saturated | Reclassified experiment as sleep unmounting rather than connection pool contention. Pool behavior derived via Little's Law. |
| **Construct Validity** | `application.yml` indentation nesting defect (`CLM-RQ2-04`) | Custom pool settings under `demo:` ignored; H2 defaulted to pool size 10 | Explicitly disclosed in Chapter 4; local H2 runs characterized as default autoconfiguration baselines. |
| **Measurement Validity** | JFR 20 ms event threshold in `profile.jfc` (`CLM-METH-04`) | Sub-20ms monitor pinning events are filtered from flight recordings | All "zero pinning" claims bounded to $\ge 20\text{ ms}$; theoretical unmounting validated via AQS code inspection. |
| **Measurement Validity** | Process-level telemetry averaging (`CLM-RQ2-02`) | `ps -p %cpu=` measures total JVM process rather than single OS carrier thread | Established that steady-state JVM CPU is ~1%, proving carrier was sleeping in kernel, not spinning. |
| **Internal Validity** | Closed-loop client self-throttling (`CLM-METH-05`) | Response time inflation automatically depresses client arrival rate | Formalized via Little's Law ($X = N/R$). Closed-loop saturation bounded to capacity analysis. |
| **Internal Validity** | Single-carrier scheduler constraint (`CLM-METH-01`) | `parallelism=1` exacerbates contention beyond typical multi-core hardware | Dedicated to mechanism isolation; multi-carrier baseline captured separately in Stratum 5 (8 carriers). |
| **External Validity** | Bare-metal Apple Silicon host environment | Host architecture (arm64, Darwin) differs from enterprise Linux x86_64 servers | Hardware characteristics documented in detail; conclusions bounded to JVM-internal concurrency mechanics. |
| **Statistical Validity** | Small sample size ($N=3$ process trials) (`CLM-METH-03`) | Small sample cannot support inferential significance testing or ANOVA | Documented descriptive dispersion metrics; purged all inferential claims from results. |
| **Reproducibility** | Historical glob expansion discrepancy (`DISC-04`) | Previous audit conflated 113 manifests with 143 load tests (claimed 256 JSONs) | Master inventory established 504 physical disk files with 100% SHA-256 cryptographic match. |

---

*(End of Chapter 3 Draft Text)*

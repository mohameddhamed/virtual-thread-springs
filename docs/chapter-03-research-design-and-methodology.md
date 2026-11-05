# Chapter 3: Research Design and Methodology

## 3.1 Research Paradigm and Empirical Systems Strategy

This dissertation adopts an **empirical systems engineering** paradigm (Wohlin et al., 2012; Runeson & Höst, 2009) to evaluate the architectural, performance, and runtime consequences of migrating a Spring Boot Model-View-Controller (MVC) application to Java 21 Virtual Threads (Project Loom). Rather than treating runtime migration as a purely syntactic or configuration-level change, this research models the transition as an architectural intervention within a multi-tier concurrency and queueing network.

The empirical investigation is structured around a controlled, instrumented Spring Boot MVC benchmark application. In empirical software engineering, research designs must balance internal validity (the degree to which observed outcomes are directly attributable to experimental treatments) against external validity (the generalizability of conclusions to industrial software systems). Synthetic micro-benchmarks—such as isolated loops implemented via the Java Microbenchmark Harness (JMH)—excel at isolating instruction-level CPU cache and branch behavior, but completely omit framework-level interactions: HTTP network socket multiplexing, servlet container request dispatching via `newVirtualThreadPerTaskExecutor()`, connection pool checkout arbitration, and request-scoped [`ThreadLocal`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L28) lifecycles.

Conversely, large-scale production deployments introduce severe confounding environmental variables—dynamic wide-area network latency jitter, non-deterministic relational database query optimizers, multi-tenant CPU bandwidth throttling, and background operating system daemons—that obscure the low-level scheduling and synchronization mechanics of the Java Virtual Machine (JVM). A dedicated, representative framework artifact strikes an optimal methodological compromise: it retains the realistic request lifecycle of Spring MVC, Apache Tomcat, and HikariCP while establishing strict experimental controls over carrier concurrency, workload generation, lock boundaries, and flight recorder telemetry.

```
+---------------------------------------------------------------------------------------------------+
|                        EMPIRICAL SYSTEMS RESEARCH PIPELINE & ADJUDICATION                         |
+---------------------------------------------------------------------------------------------------+
  STAGE 1: HYPOTHESIS & TREATMENT FORMULATION
  ├── Research Questions: RQ1 (Synchronization & Pinning), RQ2 (Architectural Risks & Boundaries)
  ├── Independent Variables: Thread Model (Platform vs Virtual), Mutex Type, JDK (21, 24, 25), JNI
  └── Dependent Metrics: Throughput (X), Latency Percentiles (p50, p95, p99), Pinning Events, Process CPU
                                           │
                                           ▼
  STAGE 2: CONTROLLED TESTBED & RUNTIME CONTROLS
  ├── Host Hardware: Bare-metal Apple M1 (8 logical cores, arm64 Darwin 25.2.0, 8 GB RAM)
  ├── JVM Runtime Controls: OpenJDK 21.0.8 as recorded in the manifests; `-Xms2g -Xmx2g -XX:+UseG1GC` where present in the primary run configuration
  └── Mechanism Isolation: -Djdk.virtualThreadScheduler.parallelism=1 (CLM-METH-01 / DISC-10)
                                           │
                                           ▼
  STAGE 3: CLOSED-LOOP WORKLOAD GENERATION (k6 v1.7.1)
  ├── Staged Profile: 15s Ramp-Up (0 -> N VUs), 30s Steady Hold (N VUs), 10s Ramp-Down (N -> 0 VUs)
  └── Closed-Loop Dynamic: N = X * (R + Z), with `Z = 0.100 s` from the k6 script; the client self-throttles under queueing
                                           │
                                           ▼
  STAGE 4: MULTI-TIER INSTRUMENTATION & TELEMETRY
  ├── Layer 1 (Client Telemetry): Raw k6 JSONL request stream (timestamp, duration, status)
  ├── Layer 2 (JVM Flight Recorder): Continuous JFR profile.jfc (jdk.VirtualThreadPinned >= 20ms)
  └── Layer 3 (Host OS Telemetry): 1-second sampling daemon (ps -p $APP_PID -o %cpu=)
                                           │
                                           ▼
  STAGE 5: REPRODUCIBILITY & CRYPTOGRAPHIC VERIFICATION
  ├── Run Manifest Capture: Git commit, JVM flags, environment variables, exit codes
  └── Cryptographic Hashing: 368 result/JFR SHA-256 checks + 92 telemetry CSV checks (DISC-04)
                                           │
                                           ▼
  STAGE 6: DUAL-WINDOW METRIC RECALCULATION ENGINE
  ├── Whole-Run Window: t in [0s, 55s] (Total duration denominator: 55.0s)
  └── Steady-State Hold Window: t in [15s, 45s] (Eliminates 25.8% ramp-up latency distortion)
                                           │
                                           ▼
  STAGE 7: EPISTEMIC ADJUDICATION & CORPUS STRATIFICATION
  ├── Stratum Partitioning: Strata 1-5 Admitted (Primary/Baseline); Strata 6-7 Quarantined/Excluded
  └── Epistemic Classification: [MEASURED], [DERIVED], [INTERPRETED], [EXTERNALLY SUPPORTED]
+---------------------------------------------------------------------------------------------------+
```

The research design is deductive and experimental in character, with descriptive process repetitions and explicit construct-validity limits. It isolates the specific operational mechanisms—intrinsic monitor pinning, carrier thread exhaustion, application-level serialization, foreign function (JNI) carrier capture, and database connection pool checkout arbitration—that govern throughput and latency under virtualized thread scheduling.

---

## 3.2 Research Questions and Operational Constructs

The study addresses two foundational Research Questions:

*   **Research Question 1 (RQ1):** *How does synchronization (specifically monitor pinning) interact with carrier-thread availability, application-level serialization, and runtime throughput in Java 21 Spring Boot MVC systems?*
*   **Research Question 2 (RQ2):** *What architectural risks—including native boundaries, connection pool management, context propagation, and observability limits—must engineering teams evaluate before enabling Virtual Threads in existing Spring Boot MVC systems?*

### 3.2.1 Operational Hypotheses

To operationalize these research questions into testable empirical statements, each question is decomposed into explicit operational hypotheses:

*   **Hypothesis $H_{1.1}$ (Monitor Pinning Occurrence):** In Java 21, invoking a blocking call (`Thread.sleep`) within a Java `synchronized` block prevents HotSpot continuation stack freezing, pinning the virtual thread to its underlying OS carrier thread and generating `jdk.VirtualThreadPinned` events in Java Flight Recorder when hold durations equal or exceed 20 ms ([`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L54)).
*   **Hypothesis $H_{1.2}$ (Carrier Starvation under Schedulers):** Under a single-carrier scheduler configuration (`parallelism=1`), pinning the carrier thread during a 500 ms serialized critical section stalls all other virtual threads assigned to the scheduler, restricting system throughput to $\le 2.0\text{ req/s}$ regardless of concurrent virtual user population ([`CLM-RQ1-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L57-L69)).
*   **Hypothesis $H_{1.3}$ (Mutex Refactoring Independence):** Replacing `synchronized` with `java.util.concurrent.locks.ReentrantLock` around the 500 ms critical section eliminates recorded JFR pinning events by parking via `AbstractQueuedSynchronizer` (AQS), but does not improve throughput ($X \approx 1.96\text{ req/s}$) because system capacity remains bounded by Amdahl's Law ([`CLM-RQ1-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L72-L84), [`CLM-RQ1-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L86-L98)).
*   **Hypothesis $H_{1.4}$ (AQS Dispersion Signature):** The direct-CAS non-fair barging mechanism in `ReentrantLock`'s default `NonfairSync` increases within-treatment latency dispersion and tail variance relative to intrinsic monitors under high contention ([`CLM-RQ1-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L101-L111)).
*   **Hypothesis $H_{1.5}$ (Runtime Evolution):** On Java 24 (with JEP 491), object monitor contention no longer pins virtual threads to carrier threads during cooperative blocking, emitting zero JFR pinning events under workloads that pinned on Java 21 ([`CLM-RQ1-06`](../docs/evidence-freeze/claim-evidence-ledger.md#L114-L126)).
*   **Hypothesis $H_{2.1}$ (Silent Carrier Starvation via JNI):** Native C function invocations via JNI executing blocking system calls (`nanosleep`) hold the OS carrier thread captive in `_thread_in_native`, completely bypassing HotSpot continuation freeze logic and starving the scheduler without emitting JFR pinning events ([`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L160), [`DISC-03`](../docs/evidence-freeze/discrepancy-register.md#L81-L97)).
*   **Hypothesis $H_{2.2}$ (Carrier CPU State during Native Sleep):** In the tested macOS direct-JNI `nanosleep()` path, carrier occupation occurs in a Darwin/Mach wait state and consumes little active processor time (JVM process CPU approximately 1%), rather than busy-spinning ([`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176), [`DISC-02`](../docs/evidence-freeze/discrepancy-register.md#L63-L79)).
*   **Hypothesis $H_{2.3}$ (Connection Pool Checkout Contention):** Relational persistence under high concurrency shifts bottlenecks from web server threads to HikariCP connection checkout queues; however, if simulated latency executes before connection checkout, the pool remains unexercised regardless of pool sizing ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192), [`DISC-07`](../docs/evidence-freeze/discrepancy-register.md#L150-L165)).

### Table 3.1: Operational Construct and Evidentiary Mapping Matrix

| Research Question | Experimental Treatment | Controlled Baseline | Dependent Metrics | Direct Evidence Artifact | Operational Interpretation Rule | Methodological Limitation & Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RQ1: Monitor Pinning & Serialization** | Virtual Threads + `synchronized` (`payments-synchronized`) | Platform Threads + `synchronized` (`platform-synchronized`) | Throughput ($req/s$), $p50$, $p95$, $p99$ Latency ($ms$) | k6 JSONL streams, JFR `jdk.VirtualThreadPinned` events | Pinning confirmed if JFR records events $\ge 20\text{ ms}$; carrier starvation confirmed if throughput collapses under `parallelism=1` | Bounded to single-carrier scheduler isolation; JFR threshold drops events $<20\text{ ms}$ ([`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L54), [`CLM-RQ1-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L57-L69)) |
| **RQ1: Mutex Refactoring** | Virtual Threads + `ReentrantLock` (`payments-reentrant-lock`) | Virtual Threads + `synchronized` (`payments-synchronized`) | Throughput ($req/s$), $p50$, $p95$, $p99$ Latency ($ms$), trial dispersion | k6 JSONL streams, JFR event streams, Telemetry CSV | Unpinning confirmed if JFR events $= 0$; Amdahl serialization confirmed if throughput remains identical to `synchronized` | Refactoring eliminates pinning but preserves serialization; AQS non-fair barging increases dispersion ([`CLM-RQ1-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L72-L84), [`CLM-RQ1-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L86-L98)) |
| **RQ1: AQS Lock Dispersion** | Virtual Threads + `ReentrantLock` (`payments-reentrant-lock`) | Virtual Threads + `synchronized` (`payments-synchronized`) | Standard deviation ($\sigma$) and range ($\Delta$) of latency ($ms$) across trials | Recalculated metrics CSV, k6 point metrics | AQS direct-CAS barging confirmed if `ReentrantLock` dispersion exceeds `synchronized` by $> 5\times$ | Derived from $N=3$ process repetitions; qualitative signature of barging, not asymptotic proof ([`CLM-RQ1-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L101-L111)) |
| **RQ1: Runtime Evolution** | Java 24 Virtual Threads + `synchronized` (JEP 491) | Java 21 Virtual Threads + `synchronized` | JFR Pinning Count, Throughput ($req/s$) | JFR binary recordings on JDK 24.0.2 | JEP 491 monitor unpinning confirmed if JFR pinning events drop from 110 to 0 | Unpinning does not bypass Amdahl's Law; serialization persists at $\approx 1.97\text{ req/s}$ ([`CLM-RQ1-06`](../docs/evidence-freeze/claim-evidence-ledger.md#L114-L126)) |
| **RQ2: Native JNI Boundary** | JNI 500 ms `nanosleep()` (`/native`) | Pure Java 500 ms `Thread.sleep()` (`/payments/no-lock`) | Throughput ($req/s$), JFR Pinning Count, Process %CPU | k6 JSONL streams, JFR recordings, Telemetry CSVs | Carrier capture confirmed if throughput drops to $1.97\text{ req/s}$; observability gap confirmed if JFR pinning $= 0$ | POSIX `nanosleep` is kernel sleep, not busy CPU; JFR detects unmount failures, not OS stalls ([`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L160), [`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176)) |
| **RQ2: Database Pool Contention** | HikariCP pool size 1 (`maximumPoolSize=1`) | HikariCP pool size 10 (`maximumPoolSize=10`) | Latency distribution ($ms$), pool acquisition errors | k6 JSONL streams (`docker-pg-orders`, `h2-pool`) | Pool saturation confirmed if pool size 1 induces queue acquisition delays or timeouts | Pre-acquisition sleep defect in `OrderService` executed delay before connection checkout ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192)) |
| **RQ2: Observability & Diagnostics** | Diagnostic No-Lock (`payments-no-lock`) | Virtual Threads + `synchronized` | Throughput ($req/s$), Latency ($ms$) | k6 JSONL streams, JFR event streams | Theoretical ceiling established if throughput reaches concurrency limit without serialization | Unsynchronized concurrent modification represents unsafe state; upper bound only ([`CLM-RQ1-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L86-L98)) |

---

## 3.3 Experimental Artifact and Target Workload Modeling

The core experimental artifact is a custom Spring Boot 3.5.12 application (`virtual-threads-demo`) implemented in Java 21 LTS and built using Apache Maven 3.9 ([`pom.xml`](../pom.xml)). The artifact models an enterprise e-commerce backend containing realistic operational concerns, including transactional payment processing, catalog querying, background native hashing/computation, and relational persistence.

The application source code is structured under four primary modular packages:
1.  **Routing Layer (`controller`):** REST API endpoints mapping client HTTP requests to underlying transactional logic:
    *   [`PaymentController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/PaymentController.java): Routes `/payments` requests to test mutual exclusion treatments.
    *   [`OrderController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/OrderController.java): Routes `/orders` requests to test JDBC persistence and context propagation.
    *   [`ProductController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/ProductController.java): Routes `/products` requests for fast-path non-blocking catalog retrieval.
    *   [`NativeController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/NativeController.java): Routes `/native` requests executing foreign C system calls.
    *   [`NativeShortController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/NativeShortController.java): Routes `/native-short` requests measuring pure JNI boundary overhead.
    *   [`CpuController.java`](../src/main/java/com/thesis/virtualthreadsdemo/controller/CpuController.java): Routes `/cpu` requests executing deterministic FMA/square-root workloads.
2.  **Service Layer (`service`):** Business logic implementing concurrency control, state manipulation, and native library bindings:
    *   [`PaymentService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java): Encapsulates mutual exclusion lock strategies (`synchronized`, `reentrant-lock`, `fair-reentrant-lock`, `semaphore`, `fair-semaphore`, `none`).
    *   [`OrderService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java): Coordinates relational queries and captures request metadata within [`ThreadLocal`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L28) variables.
    *   [`NativeBlockingService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/NativeBlockingService.java): Loads and binds the native C dynamic shared library.
    *   [`CpuService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/CpuService.java): Executes CPU-intensive cryptographic hashing loops.
3.  **Persistence Layer (`repository`):** Relational database interactions executed via Spring's `JdbcTemplate` backed by HikariCP (version 6.3.3) across embedded H2 and containerized PostgreSQL 15-alpine databases.
4.  **Native Interface Layer (`native`):** A compiled C dynamic library ([`native_blocking.c`](../native/native_blocking.c) compiled to `libnativeblocking.dylib`) executing operating system system calls.

---

## 3.4 System Architecture and Concurrency Dispatch

The physical request architecture follows the synchronous servlet model of Spring MVC, deployed on an embedded Apache Tomcat 10.1.52 container. In traditional deployment, each incoming HTTP TCP connection is accepted and assigned to an operating system platform thread allocated from a bounded worker pool (Tomcat's default pool of 200 threads).

When Virtual Threads are enabled via Spring Boot 3 configuration ([`application.yml`](../src/main/resources/application.yml)):

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

Spring Boot auto-configures Tomcat's protocol handler by registering a customizer bean that delegates request handling to a virtual thread per-task executor (`Executors.newVirtualThreadPerTaskExecutor()`). In this execution mode, Tomcat dispatches every incoming HTTP request to an ephemeral virtual thread whose continuation is scheduled onto an underlying HotSpot carrier thread pool.

```
+-----------------------------------------------------------------------------------+
|                                Client Load (k6)                                   |
|               10 to 50 Concurrent Virtual Users (Closed-Loop Network)              |
+-----------------------------------------+-----------------------------------------+
                                          | HTTP / 1.1 Requests
                                          v
+-----------------------------------------------------------------------------------+
|                        Embedded Apache Tomcat 10.1.52                             |
|          Dispatch Executor: Executors.newVirtualThreadPerTaskExecutor()           |
+-----------------------------------------+-----------------------------------------+
                                          | Dispatches Ephemeral Virtual Thread
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
|  | - synchronized      |   | - ThreadLocal       |   | - JNI C dynamic bridge  |  |
|  | - ReentrantLock     |   | - JdbcTemplate      |   | - POSIX nanosleep()     |  |
|  | - No-Lock (Control) |   | - simulateSlowQuery |   | - POSIX sched_yield()   |  |
|  +---------------------+   +----------+----------+   +------------+------------+  |
+---------------------------------------|---------------------------|---------------+
                                        |                           |
                                        v                           v
                       +--------------------------------+  +-----------------+
                       |     HikariCP Connection Pool   |  | libnative-      |
                       | - Local H2 In-Memory DB        |  | blocking.dylib  |
                       | - Docker PostgreSQL 15-alpine  |  +-----------------+
                       +--------------------------------+           |
                                        │                           |
                                        ▼                           ▼
+-----------------------------------------------------------------------------------+
|                    Java Virtual Machine (HotSpot Runtime)                         |
|   Virtual Thread Continuations (Java Heap) <──> ForkJoinPool Scheduler            |
|   Carrier Worker Threads: ForkJoinPool-1-worker-1 (-D...parallelism=1)            |
+-----------------------------------------+-----------------------------------------+
                                          | Binds to Physical Cores
                                          v
+-----------------------------------------------------------------------------------+
|                        Host Operating System & Hardware                           |
|   Apple M1 Bare-Metal Host (8 Cores: 4 Firestorm Performance + 4 Icestorm Efficiency)|
|   Darwin 25.2.0 (macOS 15 Sequoia, arm64) -- 8 GB Unified Memory                  |
+-----------------------------------------------------------------------------------+
```

---

## 3.5 Endpoint and Treatment Design

The benchmark artifact exposes six dedicated endpoints designed to isolate specific concurrency, scheduling, and boundary mechanisms. Table 3.2 details the operational specification of each endpoint.

### Table 3.2: Experimental Endpoint and Treatment Specifications

| Endpoint Route | Primary Treatment | Underlying Workload / Mechanism | Architectural Role | Strict Evidentiary Limitation |
| :--- | :--- | :--- | :--- | :--- |
| `/payments` | `synchronized` vs. `reentrant-lock` vs. `no-lock` | 500 ms critical section holding an in-memory lock during simulated processing delay | Isolates Java 21 monitor pinning against non-pinning explicit locks under identical mutual exclusion | Does not evaluate database contention; delay is synthetic in-memory duration ([`CLM-RQ1-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L86-L98)) |
| `/native` | `blocking-jni` | 500 ms C-level POSIX `nanosleep()` system call via JNI | Evaluates carrier thread behavior during non-yielding foreign function execution | Does not execute busy-wait arithmetic; steady-state CPU is ~1%, not 100% ([`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176)) |
| `/native-short` | `native-short` | Fast JNI C invocation executing a non-blocking no-op return | Measures pure JNI transition overhead across the JVM boundary | Cannot be used to assess thread scheduling or carrier starvation |
| `/orders` | `orders-virtual` vs. `orders-platform` | 300 ms simulated slow query delay followed by relational SQL query (`SELECT *`) | Evaluates JDBC driver coordination and HikariCP connection checkout | Sleep delay executed *before* connection checkout; does not stress pool capacity ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192)) |
| `/products` | `products-virtual` vs. `products-platform` | Fast JDBC catalog lookup returning database rows | Establishes framework baseline throughput without I/O or lock contention | Fast-path execution; highly sensitive to client-side VU ramp-up dynamics ([`CLM-METH-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L271-L283)) |
| `/cpu` | `cpu-virtual` vs. `cpu-platform` | 5,000,000 iterations of `Math.fma` and `Math.sqrt` | Evaluates virtual thread scheduling overhead under CPU-saturated compute workloads | Virtual threads offer no throughput benefit over compute-bound tasks; establishes compute parity |

---

## 3.6 Primary Synchronization Matrix

The primary experimental treatment evaluates the `/payments` endpoint under four distinct synchronization configurations:
1.  **Platform Synchronized Baseline (`platform-synchronized`):** Platform threads (standard OS threads) executing within a Java `synchronized` block protecting a 500 ms critical section.
2.  **Virtual Thread Synchronized Treatment (`synchronized`):** Virtual threads executing within an identical Java `synchronized` block protecting the 500 ms critical section. Under Java 21, monitor contention triggers carrier thread pinning.
3.  **Virtual Thread ReentrantLock Treatment (`reentrant-lock`):** Virtual threads executing within a `java.util.concurrent.locks.ReentrantLock` block protecting the 500 ms critical section. Virtual threads unmount from carrier threads during lock acquisition contention via `LockSupport.park()`.
4.  **No-Lock Diagnostic Control (`no-lock`):** Virtual threads executing the 500 ms delay with mutual exclusion completely removed. This condition represents an intentionally unsafe state that violates correctness invariants, serving solely as an empirical upper bound on unconstrained concurrent scheduling.

### 3.6.1 Synchronization Design Comparison

To frame the thesis within broader software architecture theory, the synchronization mechanisms evaluated here are contrasted against alternative paradigms in concurrent systems design:

*   **Java Monitors (`synchronized`):** Intrinsic locks coupled to the object header mark-word. In Java 21, HotSpot's `ObjectMonitor` subsystem couples the lock to the executing OS thread. HotSpot's continuation subsystem evaluates `can_freeze()`, which returns `false` whenever `held_monitor_count() > 0`. Because virtual threads are user-mode continuations multiplexed onto kernel threads, entering a monitor prevents the continuation from unmounting during blocking operations, pinning the carrier thread.
*   **Explicit Locks (`ReentrantLock`):** Implemented in user-space Java via `AbstractQueuedSynchronizer` (AQS). Waiting threads park via `LockSupport.park()`, which delegates to `VirtualThread.park()`, cleanly unmounting the virtual thread continuation and yielding the carrier thread back to the scheduler. However, `ReentrantLock` defaults to a `NonfairSync` implementation wherein newly arriving threads attempt a direct Compare-And-Swap (CAS) to acquire the lock before queuing. Under intense contention, this barging behavior causes queue overtaking, dramatically expanding latency standard deviation ($\approx 16\text{--}30\text{ ms}$ for `ReentrantLock` vs. $\le 7.4\text{ ms}$ for `synchronized`, [`CLM-RQ1-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L101-L111)).
*   **Actor and Message-Passing Architectures (e.g., Erlang, Akka):** Rather than sharing mutable state behind mutual exclusion locks, actor models enforce single-threaded isolation per actor and communicate via asynchronous mailboxes. Java's design choice with Project Loom intentionally rejected the colored-function and mailbox overhead of actor frameworks, choosing instead to preserve the traditional synchronous blocking imperative style.
*   **Database-Mediated and Optimistic Locking:** Techniques such as multiversion concurrency control (MVCC) or optimistic offline locks (`@Version`) push contention resolution into the storage engine. While highly scalable for distributed architectures, in-memory transactional systems frequently require process-level mutual exclusion to serialize hardware access, cash registers, or local ledger writes.

---

## 3.7 Experimental Run Families and Evidence Strata

To ensure that historical, pilot, and flawed runs are not conflated with verified experimental conditions, the repository's 119 physical executions (+1 schema template) are partitioned into the seven non-overlapping strata established in the Adjudication Charter ([`referee-review-adjudication.md`](../docs/evidence-freeze/referee-review-adjudication.md#L298-L466)):

```
+---------------------------------------------------------------------------------------------------+
|                        MASTER REPOSITORY POPULATION CENSUS (120 RECORDS)                          |
+---------------------------------------------------------------------------------------------------+
  STRATUM 1: Java 21 Primary Synchronization Matrix (12 runs) ──────> [ADMITTED: PRIMARY FINDINGS]
  STRATUM 2: Java 24/25 Runtime Comparison Matrix (10 runs)   ──────> [ADMITTED: SUPPORTING FINDINGS]
  STRATUM 3: Multi-JDK Native JNI Boundary Matrix (27 runs)   ──────> [ADMITTED: PRIMARY RISK FINDINGS]
  STRATUM 4: Supporting Architectural Controls (18 runs)      ──────> [ADMITTED: SUPPORTING CONTROLS]
  STRATUM 5: 8-Carrier Historical Baseline Matrix (12 runs)   ──────> [ADMITTED: HISTORICAL BASELINE]
  STRATUM 6: Exploratory Pilots & Diagnostic Runs (27 runs)   ──────> [QUARANTINED: EXCLUDED FROM METRICS]
  STRATUM 7: Construct-Flawed / Defective Runs (13 runs)      ──────> [QUARANTINED: METHODOLOGICAL FLAW]
  ROW 120:   Manifest Schema Template (1 template)            ──────> [NON-EXECUTION METADATA]
+---------------------------------------------------------------------------------------------------+
```

### Table 3.3: Repository Evidence Strata Census

| Stratum Identifier | Target Focus | Execution Count | Runtime JDK | Scheduler Sizing | HikariCP Pool | Admitted Corpus Status | Epistemic Role |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Stratum 1** | Java 21 Primary Synchronization Matrix | 12 | 21.0.8 | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Primary)** | Core `/payments` synchronization comparisons (`CLM-RQ1-01` to `CLM-RQ1-05`) |
| **Stratum 2** | Java 24/25 Runtime Comparison Matrix | 10 | 24.0.2, 25-ea | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Supporting)** | Verification of JEP 491 object monitor unpinning across JDK releases (`CLM-RQ1-06`) |
| **Stratum 3** | Multi-JDK Native JNI Boundary Matrix | 27 | 21.0.8, 24, 25 | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Primary)** | $3 \times 3 \times 3$ factorial matrix evaluating native POSIX `nanosleep()` (`CLM-RQ2-01`, `CLM-RQ2-02`) |
| **Stratum 4** | Supporting Architectural Controls | 18 | 21.0.8 | `parallelism=1`, `maxPoolSize=1` | 10 (default) | **Admitted (Supporting)** | Endpoints `/orders`, `/products`, and `/cpu` controls (`CLM-RQ2-03`) |
| **Stratum 5** | 8-Carrier Historical Baseline Matrix | 12 | 21.0.8 | `parallelism=8`, `maxPoolSize=256` | 10 (default) | **Admitted (Baseline)** | Unconstrained Apple M1 8-carrier historical baseline (`CLM-METH-02`) |
| **Stratum 6** | Exploratory Pilots & Diagnostic Runs | 27 | 21, 24, Zulu | Variable (1, 8, default) | Variable | **Excluded from Primary** | Lock/semaphore pilots, Zulu check, and standalone unmanifested CPU control |
| **Stratum 7** | Construct-Flawed / Incomplete Runs | 13 | 21.0.8 | `parallelism=1`, `4` | 1, 10 | **Excluded (Method Flaw)** | Pre-query sleep runs (H2, Docker PG) and aborted execution 142557 |
| **Template** | Schema Reference ([`run-manifest-template.json`](../results/run-manifest-template.json)) | 1 | N/A | None | None | **Non-Execution Metadata** | Reference schema template defining run manifest format |
| **Total** | **Master Repository Population** | **120** | — | — | — | **119 Executions + 1 Template** | Master evidence population across 504 physical disk files ([`DISC-04`](../docs/evidence-freeze/discrepancy-register.md#L99-L115)) |

---

## 3.8 Workload Protocol and Closed-Loop Queueing Mechanics

Load generation is driven by [k6](https://k6.io/) (v1.7.1) executing a parameterized test script ([`k6/isolated-load-test.js`](../k6/isolated-load-test.js)). The workload follows a staged closed-loop concurrency profile:
1.  **Stage 1 (Ramp-Up):** 15 seconds, scaling linearly from 0 to target Virtual Users ($N = 10$ or $50$ VUs).
2.  **Stage 2 (Steady-State Hold):** 30 seconds, maintaining fixed concurrent VUs ($N$).
3.  **Stage 3 (Ramp-Down):** 10 seconds, scaling linearly from target VUs back to 0.

Total execution duration is exactly 55 seconds per trial.

### 3.8.1 Closed-Loop and Open-Loop Workload Formalization

In a **closed-loop** workload model, a fixed population of Virtual Users ($N$) submits an HTTP request, waits synchronously for the response, and immediately upon receipt generates the subsequent request (100 ms think-time, $Z = 0.100 s$).

```
+-----------------------------------------------------------------------------------+
|               CLOSED-LOOP QUEUEING DYNAMICS VS. OPEN-LOOP MODELS                  |
+-----------------------------------------------------------------------------------+
  CLOSED-LOOP MODEL (Used in this Research):
  +------------------+       HTTP Request        +--------------------------------+
  | Fixed Population | ────────────────────────> | Server / Saturated Critical    |
  | (N = 10 VUs)     | <──────────────────────── | Section (T_service = 500 ms)   |
  +------------------+       HTTP Response       +--------------------------------+
     ▲                                                          │
     └──────── Client waits synchronously before next call ─────┘
     *Self-Throttling Dynamic*: The cycle time approaches 5,000 ms -> throughput approaches 2 req/s

  OPEN-LOOP MODEL (Contrasting Industrial Traffic):
  [Poisson Arrival Stream (lambda = 50 req/s)] ───────> [Server Capacity (mu = 2 req/s)]
                                                              │
                                                              ▼
                                                   Queue explodes to infinity!
                                                   (Catastrophic client timeout)
+-----------------------------------------------------------------------------------+
```

System throughput ($X$) and response time ($R$) are governed strictly by Little's Law for closed queueing networks (Little, 1961; [`CLM-METH-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L312-L322)):

$$N = X \times (R + Z) \implies R = \frac{N}{X} - Z$$

When an endpoint executes a critical section protected by mutual exclusion, service rate is governed by the duration of the exclusive critical section. Let $T_{\text{serial}} = 500\text{ ms} = 0.500\text{ s}$. By Amdahl's Law (Amdahl, 1967) and operational single-server queueing bounds (Denning & Buzen, 1978), maximum theoretical saturation throughput ($X_{\text{max}}$) is strictly bounded by the reciprocal of service demand:

$$X_{\text{max}} = \frac{1}{T_{\text{serial}}} = \frac{1}{0.500\text{ s}} = 2.000\text{ req/s}$$

As client concurrency ($N = 10\text{ VUs}$) saturates the single serialized server, an internal request queue forms ($L_q \approx N - 1 = 9\text{ requests}$). Equilibrium mean response time expands according to:

$$R + Z = \frac{N}{X_{\text{max}}} = \frac{10}{2.000\text{ req/s}} = 5.000\text{ s}$$

With the script's $Z=0.100\text{ s}$ think time, the corresponding response-time estimate is $R\approx4.900\text{ s}$. The 5.000 s value is the closed-loop cycle time.

Under closed-loop generation, the client self-throttles because each VU waits for the response and then the script sleeps for 100 ms. Closed-loop workloads therefore cannot generate arbitrary offered arrival rates; they establish a bounded cycle-time relationship.

An **open-loop** arrival-rate workload (e.g., dispatching Poisson arrivals at a fixed rate $\lambda$ independent of server completion) would reveal queue divergence and catastrophic latency explosion when $\lambda > X_{\text{max}}$. However, for the specific research goal of **mechanism isolation**—verifying whether carrier unmounting occurs during lock wait without risking client-side memory collapse—the closed-loop saturation model is methodologically superior, reproducible, and mathematically tractable.

### 3.8.2 Mathematical Derivation of Database Pool Contention (`/orders`)

In the `/orders` endpoint, `OrderService.simulateSlowQuery()` executed `Thread.sleep(300)` *prior* to calling `jdbcTemplate.queryForList(...)` ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192), [`DISC-07`](../docs/evidence-freeze/discrepancy-register.md#L150-L165)).

The query execution time was measured at $T_{\text{query}} < 0.1\text{ ms} = 0.0001\text{ s}$. Under 50 VUs, the benchmark did not instrument HikariCP acquisition, active, or pending metrics. Because the 300 ms delay occurred before checkout, the experiment cannot establish pool occupancy or exhaustion:



The source ordering establishes only that the experiment did not hold a connection during the artificial delay. Pool saturation and occupancy remain unmeasured, so the result should be treated as a construct-validity limitation rather than a measured pool utilization result.

---

## 3.9 Runtime and Environment Control

To eliminate cross-host virtualization noise and hypervisor scheduling jitter, all primary benchmark trials were executed on dedicated bare-metal hardware.

### 3.9.1 Hardware and Operating System Specifications
*   **Host Platform:** Apple Silicon M1 (bare metal, no hypervisor virtualization).
*   **Compute Architecture:** 8 physical/logical processing cores: 4 high-performance Firestorm cores (3.2 GHz) + 4 energy-efficient Icestorm cores (2.06 GHz).
*   **Memory:** 8 GB unified system memory.
*   **Operating System:** Darwin 25.2.0 (macOS 15.2 Sequoia, arm64).
*   **Java Runtime:** OpenJDK runtime identity as recorded in the manifests; the manifests do not provide a reliable vendor label:
    *   Java 21 LTS: build `21.0.8+12-LTS`
    *   Java 24 GA: build `24.0.2+12`
    *   Java 25 Early Access: build `25-ea+18`
*   **JVM Memory Controls:** Heap sizing was fixed to prevent dynamic resizing pauses: `-Xms2g -Xmx2g -XX:+UseG1GC`.

### 3.9.2 Scheduler Configuration: Mechanism Isolation vs. Container Quotas (`CLM-METH-01` / `DISC-10`)
In Strata 1, 2, 3, and 4, the JVM virtual thread scheduler was explicitly constrained via runtime flags:

```bash
-Djdk.virtualThreadScheduler.parallelism=1
-Djdk.virtualThreadScheduler.maxPoolSize=1
```

*   **Operational Role:** `parallelism=1` limits the dedicated virtual-thread scheduler carrier-worker count to one. This forces all virtual threads to compete for a single carrier. If a virtual thread pins the carrier (via `synchronized`) or occupies it in the tested direct JNI path, other virtual threads stall. This mechanism isolation turns latent carrier starvation into an immediate, measurable throughput collapse.
*   **Strict Methodological Boundary:** This setting is an in-process JVM scheduler constraint, **not a Linux cgroup CPU bandwidth quota** (`cpu.cfs_quota_us` / `cpu.max`). The JVM process, garbage collector, JFR threads, Tomcat acceptor threads, and the k6 load generator continue to execute concurrently across all 8 host cores of the Apple M1 processor. The thesis explicitly rejects describing `parallelism=1` as "1-CPU container equivalence" ([`CLM-METH-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L256-L268), [`DISC-10`](../docs/evidence-freeze/discrepancy-register.md#L200-L213)).

---

## 3.10 Observability Protocol and Instrumentation

The experimental testbed incorporates three independent, non-interfering observability layers:

### 3.10.1 Java Flight Recorder (JFR) Configuration (`CLM-METH-04` / `DISC-09`)
Every admitted trial executes with continuous JFR recording enabled at JVM startup ([`run-benchmark.sh`](../run-benchmark.sh#L161-L167)):

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

```
+-----------------------------------------------------------------------------------+
|               JFR EVENT DURATION THRESHOLD FILTERING MECHANISM                    |
+-----------------------------------------------------------------------------------+
  Virtual Thread Pinning Duration
  0 ms ─────────────── 10 ms ─────────────── 20 ms ──────────────────────> 500 ms
  │                      │                     │                              │
  ├─ Pinning Duration < 20 ms ────────────────┤├─ Pinning Duration >= 20 ms ──┤
  │                                            │                              │
  ▼                                            ▼                              ▼
  FILTERED BY HOTSPOT RUNTIME                  RECORDED IN JFR FLIGHT RECORDING
  (Zero events written to recording.jfr)       (Emitted as jdk.VirtualThreadPinned)
  *Methodological Limitation*: Zero events proves absence of pins >= 20ms only!
+-----------------------------------------------------------------------------------+
```

*   **Diagnostic Limit:** JFR records `jdk.VirtualThreadPinned` events **only when the pin duration equals or exceeds 20 ms**. Although the script comments noted `# threshold=10ms`, HotSpot loaded `profile.jfc` with its default 20 ms threshold. Consequently, zero recorded events establishes only that no pinning events $\ge 20\text{ ms}$ occurred; it cannot rule out transient sub-20ms micro-pinning events ([`CLM-METH-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L299-L310), [`DISC-09`](../docs/evidence-freeze/discrepancy-register.md#L184-L198)).

### 3.10.2 Host Process Telemetry & Thread Attribution (`CLM-RQ2-02` / `DISC-02`)
A companion background sampling daemon captures process-level resource metrics at 1-second intervals ([`run-benchmark.sh`](../run-benchmark.sh#L145-L156)):

```bash
ps -p "$APP_PID" -o %cpu=
```

*   **Attribution Boundary:** On Darwin/BSD, `%cpu` measures the decaying CPU percentage of the entire JVM process (`$APP_PID`), not an isolated thread. It captures background GC and framework activity in addition to application execution.
*   **Kernel Sleep Verification:** Host telemetry captured an average steady-state process CPU of $1.04\% \pm 0.12\%$ during native JNI blocking. This empirically disproves the common myth that native carrier monopolization manifests as a 100% busy-wait CPU spin loop; the carrier thread was suspended in OS kernel sleep ([`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176), [`DISC-02`](../docs/evidence-freeze/discrepancy-register.md#L63-L79)).

### 3.10.3 Cryptographic Artifact Hashing and Manifest Provenance (`DISC-04`)
At the completion of each benchmark trial, the execution harness captures a structured execution manifest ([`run-manifest-template.json`](../results/run-manifest-template.json)). The manifest records runtime parameters, Git commit hashes (`1ccb617`, `5f9936c`), environment variables, exit codes, and cryptographic SHA-256 digests of the raw k6 JSON result and JFR binary recording.

An automated audit script ([`generate_artifact_inventory.py`](../scripts/generate_artifact_inventory.py)) executed 368 SHA-256 checks across k6 JSON result and JFR binary files, and 92 checks across companion telemetry CSV files, confirming **100% checksum agreement for those recorded comparisons** ([`DISC-04`](../docs/evidence-freeze/discrepancy-register.md#L99-L115)).

---

## 3.11 Correctness Gates and Semantic Invariants

Before any benchmark execution is admitted for quantitative analysis, it must satisfy seven strict correctness gates:
1.  **HTTP Correctness Gate:** 100% of HTTP responses must return status code `200 OK`. Any trial exhibiting client timeouts or non-200 responses is disqualified.
2.  **Mutual Exclusion Semantic Invariant:** In the `/payments` endpoint, state transactions must maintain strict sequential consistency. In the no-lock diagnostic control (`no-lock`), concurrent modification is intentionally permitted to quantify unconstrained scheduling overhead.
3.  **Carrier Independence Invariant:** In `ReentrantLock` treatments, thread safety must be achieved without emitting monitor pinning events.
4.  **Driver Safety Invariant:** Relational database queries must execute through drivers free of internal carrier-pinning synchronization. The Maven audit confirmed resolution of `org.postgresql:postgresql:42.7.10`, safely exceeding the `pgjdbc >= 42.6.0` unpinning patch threshold ([`CLM-RQ2-06`](../docs/evidence-freeze/claim-evidence-ledger.md#L226-L236)).
5.  **Process Teardown & Signal Handling Gate:** The JVM process must terminate cleanly via SIGTERM/SIGINT with an exit code of 0.
6.  **Cryptographic Integrity Gate:** Raw artifact SHA-256 hashes must match the corresponding manifest records for admitted files.
7.  **Execution Stratum Gate:** Only runs belonging to pre-registered, controlled strata (Strata 1–5) are admitted into quantitative thesis comparisons.

---

## 3.12 Replication, Analysis Unit, and Metric Recalculation

### 3.12.1 The Independent Process Execution as the Analysis Unit
The primary experimental unit is the **independent process execution**. Micro-benchmarks that execute repeated iterations within a single long-lived JVM session suffer from JIT profile pollution, biased class loading, and unrepresentative memory fragmentation. In this study, every trial represents an independent JVM invocation with dedicated warm-up, clean thread pool initialization, and isolated JFR recording.

### 3.12.2 Descriptive Bounding of Sample Size ($N=3$) (`CLM-METH-03` / `DISC-11`)
Each primary condition was executed across $N=3$ independent process-level repetitions. Across all conditions, steady-state within-treatment latency dispersion was exceptionally tight:
*   Fast-path / diagnostic controls (`no-lock`, `products`): latency spread $\Delta \le 0.20\text{ ms}$, standard deviation $\sigma \le 0.10\text{ ms}$.
*   Synchronized monitor conditions (`synchronized`): latency spread $\Delta \le 7.41\text{ ms}$, standard deviation $\sigma \le 3.63\text{ ms}$ (at $\sim 4930\text{ ms}$).
*   Native JNI blocking (`blocking-jni`): latency spread $\Delta \le 33.79\text{ ms}$, standard deviation $\sigma \le 12.73\text{ ms}$ (at $\sim 4960\text{ ms}$).

Because within-treatment relative spread is less than $0.7\%$ of mean latency, $N=3$ process repetitions provide a repeatable descriptive basis within the observed runs for mechanism isolation. However, in accordance with methodological rigor, **these $N=3$ trials are presented as descriptive engineering repetitions only; they are not used to make inferential statistical claims (such as p-values, Student's t-tests, or ANOVA)** ([`CLM-METH-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L286-L297), [`DISC-11`](../docs/evidence-freeze/discrepancy-register.md#L215-L228)).

### 3.12.3 Dual-Window Reporting Mandate (`CLM-METH-02` / `DISC-01` / `DISC-05`)
To address the effect of the 15-second ramp-up stage, the thesis mandates **dual-window reporting** for all latency and throughput metrics ([`metric-recalculations.csv`](../docs/evidence-freeze/metric-recalculations.csv)):
1.  **Whole-Run Window ($t \in [0\text{s}, 55\text{s}]$):** Aggregates all completed requests from benchmark initiation to termination ($55.0\text{ s}$ denominator).
2.  **Steady-State Hold Window ($t \in [15\text{s}, 45\text{s}]$):** Filters requests whose completion timestamps fall strictly within the 30-second constant-load hold stage ($30.0\text{ s}$ denominator).

```
+-----------------------------------------------------------------------------------+
|               DUAL-WINDOW LATENCY DISTORTION MECHANISM TIMELINE                   |
+-----------------------------------------------------------------------------------+
  Test Execution Window (55 Seconds Total)
  0s ───────────────────── 15s ─────────────────────────────── 45s ────────────── 55s
  │    Stage 1: Ramp-Up    │       Stage 2: Steady Hold        │ Stage 3: Ramp-Down │
  │    (0 -> 10 VUs)       │       (Fixed 10 VUs)              │ (10 -> 0 VUs)      │
  ├────────────────────────┼───────────────────────────────────┼────────────────────┤
  │ Uncrowded queue:       │ Fully saturated server queue:     │ Draining queue     │
  │ Latency: ~500ms-3900ms │ Latency: ~4930ms - 5000ms         │                    │
  │                        │                                   │                    │
  ├─ WHOLE-RUN WINDOW (0s to 55s): Median Latency ~ 3920 ms ───┴────────────────────┤
  │  (Ramp-up requests pull down median by 25.8%!)                                  │
  │                                                                                 │
  │                        ├─ STEADY-STATE HOLD WINDOW (15s to 45s) ─┤              │
  │                        │  True Equilibrium Median Latency: ~ 4930 ms            │
+-----------------------------------------------------------------------------------+
```

For saturated mutual exclusion bottlenecks (`/payments`), whole-run vs. hold-window throughput varies by $< 0.8\%$ ($1.98\text{ req/s}$ vs. $1.97\text{ req/s}$, exact unrounded throughput delta = **0.765%**, p50 latency delta = **0.184%** on run `142445`, resolving [`DISC-01`](../docs/evidence-freeze/discrepancy-register.md#L42-L61)).

However, for ramp-sensitive workloads (`platform-synchronized`), whole-run median latency (~3920 ms) under-reports steady-state queueing latency (~4930 ms) by **25.8%** ([`DISC-05`](../docs/evidence-freeze/discrepancy-register.md#L117-L131)). Reporting both metrics side-by-side guarantees transparency.

*Methodological Convention:* The recalculation engine ([`recalculate_metrics.py`](../scripts/recalculate_metrics.py)) defines $t_0$ as the timestamp of the first completed request ($\min \tau_k$) and filters by completion timestamp. Requests initiated during ramp-up that completed after $t = 15\text{s}$ are included in the hold window, reflecting the natural queue transition dynamics of the system.

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
| Java 21 `synchronized` produces carrier pinning | `[MEASURED]` | Stratum 1 & 5 | Non-zero JFR `jdk.VirtualThreadPinned` events | Admitted without qualification ([`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L54)) |
| `ReentrantLock` eliminates carrier pinning | `[MEASURED]` | Stratum 1 | Exactly 0 JFR events under `profile.jfc` | Admitted, qualified by 20 ms threshold ([`CLM-RQ1-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L72-L84)) |
| Unpinning does not improve serialized throughput | `[MEASURED]` + `[INTERPRETED]` | Stratum 1 | Throughput identical at $1.96\text{ req/s}$ ($<0.3\%$ delta) | Admitted as primary thesis contribution ([`CLM-RQ1-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L86-L98)) |
| JNI `nanosleep` consumes 100% carrier CPU | `[NOT ESTABLISHED]` | Stratum 3 | Telemetry proves steady-state CPU is ~1.0% | **Refuted and purged** ([`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176), [`DISC-02`](../docs/evidence-freeze/discrepancy-register.md#L63-L79)) |
| `/orders` proved HikariCP pool saturation | `[NOT ESTABLISHED]` | Stratum 4 & 7 | Sleep delay executed before connection checkout | **Disqualified as construct flaw** ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192), [`DISC-07`](../docs/evidence-freeze/discrepancy-register.md#L150-L165)) |
| PostgreSQL unmounts cleanly during socket I/O | `[EXTERNALLY SUPPORTED]` | External Spec | Resolved driver 42.7.10 refactored internal locks | Admitted via external literature only ([`CLM-RQ2-06`](../docs/evidence-freeze/claim-evidence-ledger.md#L226-L236)) |

---

## 3.14 Threats to Validity and Mitigations

The experimental design is evaluated against the validity framework established for empirical software engineering (Wohlin et al., 2012):

### Table 3.5: Methodological Threats to Validity Matrix

| Threat Category | Specific Methodological Risk | Potential Evidentiary Impact | Applied Mitigation / Research Boundary |
| :--- | :--- | :--- | :--- |
| **Construct Validity** | Pre-acquisition sleep delay in `/orders` ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192), [`DISC-07`](../docs/evidence-freeze/discrepancy-register.md#L150-L165)) | Connection was never held during 300 ms sleep; pool was never saturated | Reclassified experiment as sleep unmounting rather than connection pool contention. Pool utilization ($1.66\%$) derived via Little's Law. |
| **Construct Validity** | `application.yml` indentation nesting defect ([`CLM-RQ2-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L195-L207), [`DISC-06`](../docs/evidence-freeze/discrepancy-register.md#L133-L148)) | Custom pool settings under `demo:` ignored; H2 defaulted to pool size 10 | Explicitly disclosed in Chapter 4; local H2 runs characterized as default autoconfiguration baselines. |
| **Measurement Validity** | JFR 20 ms event threshold in `profile.jfc` ([`CLM-METH-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L299-L310), [`DISC-09`](../docs/evidence-freeze/discrepancy-register.md#L184-L198)) | Sub-20ms monitor pinning events are filtered from flight recordings | All "zero pinning" claims bounded to $\ge 20\text{ ms}$; theoretical unmounting validated via AQS code inspection. |
| **Measurement Validity** | Process-level telemetry averaging ([`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176), [`DISC-02`](../docs/evidence-freeze/discrepancy-register.md#L63-L79)) | `ps -p %cpu=` measures total JVM process rather than single OS carrier thread | Established that steady-state JVM CPU is ~1%, proving carrier was sleeping in kernel, not spinning. |
| **Internal Validity** | Closed-loop client self-throttling ([`CLM-METH-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L312-L322), [`DISC-12`](../docs/evidence-freeze/discrepancy-register.md#L230-L248)) | Response time inflation automatically depresses client arrival rate | Formalized via Little's Law ($X = N/R$). Closed-loop saturation bounded to capacity analysis. |
| **Internal Validity** | Single-carrier scheduler constraint ([`CLM-METH-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L256-L268), [`DISC-10`](../docs/evidence-freeze/discrepancy-register.md#L200-L213)) | `parallelism=1` exacerbates contention beyond typical multi-core hardware | Dedicated to mechanism isolation; multi-carrier baseline captured separately in Stratum 5 (8 carriers). |
| **External Validity** | Bare-metal Apple Silicon host environment | Host architecture (arm64, Darwin) differs from enterprise Linux x86_64 servers | Hardware characteristics documented in detail; conclusions bounded to JVM-internal concurrency mechanics. |
| **Statistical Validity** | Small sample size ($N=3$ process trials) ([`CLM-METH-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L286-L297), [`DISC-11`](../docs/evidence-freeze/discrepancy-register.md#L215-L228)) | Small sample cannot support inferential significance testing or ANOVA | Documented descriptive dispersion metrics; purged all inferential claims from results. |
| **Reproducibility** | Historical glob expansion discrepancy ([`DISC-04`](../docs/evidence-freeze/discrepancy-register.md#L99-L115)) | Previous audit conflated 113 manifests with 143 load tests (claimed 256 JSONs) | Master inventory established 504 physical disk files and checksum agreement for the recorded comparisons. |

---

*(End of Chapter 3)*

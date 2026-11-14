# Chapter 7: Migration Guidance

## 7.1 Intended Audience, Operational Scope, and Prerequisites

This chapter synthesizes the industrial motivation and problem statement of [Chapter 1: Introduction](../docs/chapter-01-introduction.md), the HotSpot runtime mechanics and literature foundations of [Chapter 2: Background and Related Work](../docs/chapter-02-background-and-related-work.md), the empirical systems methodology of [Chapter 3: Research Design and Methodology](../docs/chapter-03-research-design-and-methodology.md), the testbed and telemetry harness of [Chapter 4: Implementation and Research Infrastructure](../docs/chapter-04-implementation-and-research-infrastructure.md), the 125 benchmark executions (119 baseline runs across Strata 1–7 and 6 persistence runs in Stratum 8) of [Chapter 5: Experimental Results](../docs/chapter-05-experimental-results.md), and the queueing-theoretic derivations of [Chapter 6: Analysis and Answers to the Research Questions](../docs/chapter-06-analysis-and-answers-to-research-questions.md) into an evidence-bounded engineering migration framework. It provides software architects, principal engineers, and backend teams with actionable, correctness-preserving procedures for adopting Java 21 Virtual Threads within enterprise Spring Boot Model-View-Controller (MVC) systems.

To maintain strict epistemic integrity, every guideline, refactoring pattern, and diagnostic rule in this chapter is calibrated against the evidentiary framework established in [Chapter 3 (Section 3.13)](../docs/chapter-03-research-design-and-methodology.md#313-claim-admission-framework) and traceable to the [Claim-to-Evidence Ledger](../docs/evidence-freeze/claim-evidence-ledger.md) (`[MEASURED]`, `[EXTERNALLY SUPPORTED]`, `[HEURISTIC / LITERATURE]`, and `[THEORETICAL / CONDITIONAL]`).

### 7.1.1 Target System Characteristics
This guidance is specifically designed for enterprise systems possessing the following architectural characteristics:
1.  **Synchronous Servlet Architecture:** Applications built on Spring Boot 3.x and Apache Tomcat (or Eclipse Jetty / Undertow) utilizing synchronous HTTP request-response paradigms rather than reactive event loops (e.g., Spring WebFlux).
2.  **Relational Database Persistence:** Applications interacting with relational databases via standard JDBC interfaces, Spring's `JdbcTemplate`, or Spring Data JPA / Hibernate, managed by connection pools such as HikariCP (configured in [`application.yml`](../src/main/resources/application.yml)).
3.  **Heterogeneous Runtime Dependencies:** Codebases integrating third-party Java libraries, foreign function interfaces (JNI / Project Panama) such as [`native_blocking.c`](../native/native_blocking.c), or native cryptographic/driver packages.
4.  **High-Concurrency Workloads:** Services subject to concurrent traffic where thread pool exhaustion under platform threads historically limited system scalability.

### 7.1.2 Technical Prerequisites
Before initiating a virtual thread migration, engineering teams must establish three mandatory baseline prerequisites:
*   **JDK Runtime Baseline:** Deployment on OpenJDK 21 LTS or later. If monitor pinning elimination is desired without code refactoring, OpenJDK 24 (with JEP 491) is required `[EXTERNALLY SUPPORTED]`. If permanent standard Scoped Values (without preview flags) are required, OpenJDK 25 LTS (with JEP 506) is required `[EXTERNALLY SUPPORTED]`.
*   **Framework Baseline:** Spring Boot 3.2.0 or later (this study evaluated 3.5.12 in [`pom.xml`](../pom.xml)), ensuring native framework support for virtual thread dispatching via `spring.threads.virtual.enabled: true` in [`application.yml`](../src/main/resources/application.yml).
*   **Observability Baseline:** Production or staging infrastructure equipped to capture Java Flight Recorder (JFR) event streams, JVM Flight Recorder streaming APIs, and operating system thread/process metrics.

> [!NOTE]
> **Point-of-Use AI Disclosure (Dean's Directive 1/2026):** Generative AI assistance (Claude 3.5 Sonnet) was utilized in drafting and formatting the checklist outlines and decision tree prose in this migration guide. All architectural rules, refactoring patterns, and diagnostic procedures were formulated, tested, and validated by the author based on empirical findings. Full compliance details are formalized in §3.15.

---

## 7.2 Pre-Migration Inventory and Triage Checklist

Enabling Virtual Threads in production without prior architectural auditing introduces severe operational failure modes, including silent carrier thread starvation, connection pool exhaustion, and memory bloat. Engineering teams must conduct a systematic four-phase inventory before modifying production runtime configurations.

```
+-----------------------------------------------------------------------------------+
|                         PRE-MIGRATION INVENTORY PIPELINE                          |
+-----------------------------------------------------------------------------------+
  Phase 1: Static Codebase Audit
  ├── Scan for 'synchronized' blocks wrapping I/O, network calls, or long delays
  ├── Inventory 'ThreadLocal' usage across services, filters, and interceptors
  └── Identify foreign function invocations (JNI 'System.loadLibrary', Panama FFM)
           │
           ▼
  Phase 2: Dependency Tree Resolution
  ├── Execute: mvn dependency:tree -Dverbose
  ├── Verify database drivers: pgjdbc >= 42.6.0, MySQL Connector/J >= 9.0.0
  └── Verify JSON / serialization libraries: jackson-databind >= 2.16.0
           │
           ▼
  Phase 3: Database & Connection Pool Audit
  ├── Audit connection checkout lifecycles relative to transaction boundaries
  ├── Calibrate pool sizing against database hardware and workload SLOs
  └── Establish workload-aligned connection acquisition timeouts
           │
           ▼
  Phase 4: Observability Infrastructure Setup
  ├── Configure continuous JFR recording with custom thresholds
  └── Implement Carrier Worker & Queue Latency Metrics (JMX/OS-level Telemetry)
```

### 7.2.1 Phase 1: Static Codebase Audit
1.  **Monitor Synchronization Scan:** Identify all occurrences of the `synchronized` keyword (both method-level and block-level). Triage each occurrence into:
    *   *Type A (Pure In-Memory Mutex):* Fast updates to shared in-memory collections ($< 10\text{ }\mu\text{s}$ as an ideal micro-hold; $10\text{--}50\text{ }\mu\text{s}$ is a transitional heuristic range). Safe on Java 21 when no blocking work is enclosed; unpinning usually offers little benefit `[HEURISTIC / LITERATURE]`.
    *   *Type B (Blocking Mutex):* Synchronization enclosing blocking socket I/O, database access, external HTTP calls, or sleep delays (demonstrated by [`PaymentService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java)). **High Risk in the tested Java 21 construct:** it can trigger carrier pinning ([`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L54)) `[MEASURED]`.
2.  **ThreadLocal Inventory:** Locate all static and instance references to `ThreadLocal` (such as in [`OrderService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L28)). Determine whether cleanup is guaranteed via `finally` blocks, and evaluate the memory footprint of retained context payloads ([`CLM-RQ2-07`](../docs/evidence-freeze/claim-evidence-ledger.md#L239-L253)) `[THEORETICAL / CONDITIONAL]`.
3.  **Foreign Function Audit:** Locate all native method declarations (`native`) and JNI bindings (`System.loadLibrary`) such as [`NativeBlockingService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/NativeBlockingService.java). Determine whether the underlying C/C++ implementations (e.g., [`native_blocking.c`](../native/native_blocking.c)) execute blocking system calls (`read`, `connect`, `nanosleep`, or POSIX mutex locks) that hold carrier threads captive ([`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L161)) `[MEASURED]`.

### 7.2.2 Phase 2: Dependency Tree Resolution
Enterprise systems often inherit carrier-pinning vulnerabilities through transitive dependencies. Teams must execute:

```bash
mvn dependency:tree -Dverbose
```

Verify that all resolved libraries satisfy the minimum evaluated version thresholds established in Table 7.1.

### Table 7.1: Third-Party Dependency Baselines and Carrier-Risk Triage

| Dependency Artifact | Version or baseline to verify | Resolved in This Study | Risk or compatibility rationale | Risk category |
| :--- | :---: | :---: | :--- | :---: |
| `org.postgresql:postgresql` | **`42.6.0` or later to verify** | `42.7.10` in [`pom.xml`](../pom.xml) | pgjdbc Issue #1951, PR #2629, PR #2635 document version-specific socket-lock changes. Confirm the resolved version and inspect the deployed access path. | Socket-lock compatibility |
| `com.mysql:mysql-connector-j` | **`9.0.0` or later to verify** | N/A | Protocol-reader synchronization was addressed in 9.0.0. MySQL Connector/J 8.4 LTS remains below this evaluated threshold; LTS status alone does not establish virtual-thread safety. | Socket-lock compatibility |
| `com.fasterxml.jackson.core:jackson-databind` | **`2.16.0` baseline to verify** | `2.19.4` | Version-specific cache/recycler changes concern ThreadLocal-related memory behavior, not a universal carrier-pinning fix. Validate retained memory under the target workload. | ThreadLocal/memory behavior |
| `org.apache.tomcat.embed:tomcat-embed-core` | **`10.1.18` baseline to verify** | `10.1.52` | Container virtual-thread integration and lifecycle behavior are version- and configuration-dependent; this is not a blanket pinning-remediation threshold. | Container compatibility |
| `com.zaxxer:HikariCP` | **`5.1.0` baseline to verify** | `6.3.3` | HikariCP connection waiting uses parking mechanisms in the evaluated architecture; pool sizing and downstream capacity still require measurement. | Pool behavior/capacity |

> [!IMPORTANT]
> **Dependency Qualification:** These are version-specific baselines and risk checks, not universal safety guarantees. A driver change may address one internal synchronization path while leaving user-level locks, other libraries, native bindings, database saturation, or configuration errors unchanged. Verify the actual resolved artifact, source path, runtime, and workload.

---

## 7.3 The Five Core Architectural Migration Rules

Based on the empirical findings of this research, five foundational architectural rules govern virtual thread migrations.

---

### Rule 1: The Mutex Refactoring Rule ([`CLM-MIG-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L329-L335), [`CLM-RQ1-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L86-L98)) `[MEASURED & INTERPRETED]`
> **Rule 1:** *Do not refactor `synchronized` blocks to `ReentrantLock` expecting throughput improvements if the critical section represents an application-level serialization bottleneck. Consider `ReentrantLock` only when measured carrier scarcity makes monitor pinning a material risk to unrelated work.*

*   **Queueing Reality:** Amdahl's Law dictates that if a critical section dominates execution time, maximum throughput is strictly capped by $\mu = 1 / T_{\text{critical}}$ ([Section 6.1.1](../docs/chapter-06-analysis-and-answers-to-research-questions.md#611-the-mathematical-saturation-invariant-amdahls-law-and-queueing-theory)). Refactoring to `ReentrantLock` unpins the carrier thread, but competing virtual threads remain serialized at the application level.
*   **When to Refactor:**
    *   *Apply Refactoring:* When a measured deployment shows carrier scarcity and carrier pinning by Service X starves completely unrelated Services Y and Z.
    *   *Do Not Refactor:* When a microservice serves a single dedicated endpoint dominated by a shared mutex. Throughput will not change, and the default non-fair `ReentrantLock` may introduce queue-barging variation ([`CLM-RQ1-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L101-L111)) `[DERIVED & INTERPRETED]`.

---

### Rule 2: The Native JNI Isolation Rule ([`CLM-MIG-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L338-L344), [`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L161), [`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176)) `[MEASURED & INTERPRETED]`
> **Rule 2:** *Offload foreign calls that can block for materially long or unpredictable periods to dedicated, bounded platform thread pools. Direct invocation is appropriate only after the operation's execution time and concurrency have been bounded and its implementation has been verified as non-blocking.*

*   **Scope Clarification (Native Code vs. Standard Java):** Rule 2 applies **strictly to foreign native code (JNI and Panama FFM)**. It does *not* apply to standard Java blocking I/O (such as HTTP clients, Spring Data JDBC, Kafka, or `Thread.sleep()`), where direct invocation on virtual threads is the fundamental architectural paradigm. In pure Java, HotSpot unmounts virtual threads automatically during I/O blocks.
*   **The Physical Barrier of Native Code:** HotSpot cannot freeze or unmount native C/C++ stack frames. When native code enters a blocking operating system call (e.g., POSIX `nanosleep`, blocking C socket I/O, or POSIX mutex wait), the underlying carrier OS thread is held captive in the OS kernel wait queue. In the measured direct JNI path without Java callbacks (analyzed in [Section 6.2.1](../docs/chapter-06-analysis-and-answers-to-research-questions.md#621-risk-1-the-foreign-function-jni-silent-failure-mode-clm-rq2-01-clm-rq2-02)), carrier threads consumed $\sim 1\%$ CPU while completely stalling the scheduler, yet JFR emitted **zero `jdk.VirtualThreadPinned` events** ([`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L161), [`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176)) `[MEASURED]`.
*   **Triage Matrix: Where Direct Invocation Works vs. Where Offloading is Required:**

| Execution Category | Mechanism & Example | Invocation Strategy | Architectural Rationale |
| :--- | :--- | :---: | :--- |
| **Standard Java Blocking I/O** | `RestTemplate`, JDBC query, Kafka consumer, `ReentrantLock.lock()` | **Direct Invocation** | HotSpot unmounts virtual threads natively; carrier threads are immediately released to other tasks. |
| **Fast In-Memory Native CPU Work** | SIMD vector math, in-memory cryptographic hashing, zstd compression, [`/native-short`](../src/main/java/com/thesis/virtualthreadsdemo/controller/NativeShortController.java) | **Direct Invocation** | Finishes in microseconds; no OS kernel blocking calls. Offloading to a pool would add unnecessary context-switching overhead. |
| **Blocking Foreign / Native Operations** | POSIX `nanosleep()` ([`/native-sleep`](../src/main/java/com/thesis/virtualthreadsdemo/service/NativeBlockingService.java)), C database drivers (SQLite C), POSIX mutexes, hardware HSMs | **Platform Thread Offloading** (`Pattern 2`) | Cannot unmount; traps carrier thread. Offloading to a dedicated platform pool bulkheads the virtual thread carrier pool against starvation. |

---

### Rule 3: The Connection Pool Sizing Fallacy ([`CLM-MIG-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L347-L353), [`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192)) `[MEASURED & EXTERNALLY SUPPORTED]`
> **Rule 3:** *Do not scale database connection pools proportionally to virtual thread concurrency. Size the pool within database and application capacity limits, calibrate it to workload SLOs, and protect requests with an acquisition timeout or application-level semaphore appropriate to the service contract.*

*   **Capacity Reality and Downstream Bottleneck Shift:** Virtual threads eliminate the application-tier thread scaling limit, but cannot increase relational database concurrency or connection pool capacity ([Section 6.2.2](../docs/chapter-06-analysis-and-answers-to-research-questions.md#622-risk-2-finite-resource-capacities-and-database-pool-sizing-clm-rq2-03-clm-rq2-04)). As formalized by the Downstream Bottleneck Shift Law, when transactions hold physical connections across blocking work, unpinning carrier threads only prevents runtime carrier exhaustion—it transfers queue formation in full to the JDBC connection pool.
*   **Empirical Validation (Stratum 8):** In the Two-Treatment Factorial Persistence experiment ([Section 5.8](../docs/chapter-05-experimental-results.md#58-persistence-contention-and-downstream-pool-exhaustion-stratum-8)), 50 concurrent virtual threads were evaluated under connection-held delay ($T_{\text{hold}} = 300\text{ ms}$):
    *   *Single Connection ($\text{maximumPoolSize} = 1$):* Throughput was strictly capped at $3.27\text{ req/s}$ across all three trials ($\sigma = 0.00\text{ req/s}$, conforming precisely to Little's Law theoretical capacity $X_{\text{max}} = 1 / 0.300 = 3.33\text{ req/s}$), and hold-window median latency escalated to $15,123.0\text{ ms} \pm 40.1\text{ ms}$ ($p95 = 15,228.7\text{ ms}$). All 49 remaining virtual threads queued in HikariCP's pending handoff queue.
    *   *Ten Connections ($\text{maximumPoolSize} = 10$):* Expanding the pool to 10 connections yielded a near-perfect $9.97\times$ throughput scale to $32.60\text{ req/s} \pm 0.06\text{ req/s}$ and compressed median latency by $10.5\times$ to $1,431.3\text{ ms} \pm 6.8\text{ ms}$ ($p95 = 1,445.7\text{ ms}$), with an average of 9.2 active connections and 40 queued virtual threads.
    *   *Carrier Decoupling:* Crucially, across all trials, **strictly zero `jdk.VirtualThreadPinned` events occurred**, and carrier CPU utilization remained low ($2\%\text{--}4\%$ for pool size 1, $4\%\text{--}8\%$ for pool size 10) because virtual threads waiting for connections in HikariCP 6.x's `ConcurrentBag` unmount cleanly via `LockSupport.parkNanos()`.
*   **Heuristic Pool Sizing Calibration:** Brett Wooldridge's empirical formula `[EXTERNALLY SUPPORTED]`:
    $$\text{maximumPoolSize} = (\text{DB Physical Cores} \times 2) + \text{Effective Spindle Count}$$
    remains an appropriate hardware-aligned ceiling, not an immutable invariant. Scaling HikariCP past this bound risks database server thrashing, lock contention on the database engine, and connection overhead.
*   **Application-Level Bulkheading and SLO Timeouts:** Because virtual threads allow high request ingress without carrier starvation, unconstrained traffic easily creates multi-second connection acquisition queues. Production architectures must:
    1.  *Enforce Concurrency Bounds:* Gate connection-acquiring operations with an application-level `Semaphore` or rate limiter to bound the number of virtual threads contending for the pool concurrently.
    2.  *Workload-Aligned Acquisition Timeouts:* Calibrate `connectionTimeout` (e.g., 250–2000 ms) against client SLOs to fail fast under sustained saturation rather than queueing indefinitely under HikariCP's default 30-second timeout.
    3.  *Minimize Hold Time:* Restrict connection checkout strictly to the active SQL transaction boundary, avoiding pre-acquisition holds or post-transaction processing while retaining the connection.

---

### Rule 4: The Production Observability Rule ([`CLM-MIG-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L356-L362), [`CLM-METH-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L299-L309)) `[EXTERNALLY SUPPORTED & INTERPRETED]`
> **Rule 4:** *Never rely solely on `jdk.VirtualThreadPinned` JFR alerts to monitor virtual thread health. Complement JFR with carrier thread pool queue latency metrics and operating system thread state monitoring.*

*   **The 20 ms Blind Spot:** HotSpot's standard `profile.jfc` filters monitor pinning events lasting $< 20\text{ ms}$ ([Section 6.2.4](../docs/chapter-06-analysis-and-answers-to-research-questions.md#624-risk-4-observability-boundaries-and-diagnostic-blind-spots-clm-meth-04), [`CLM-METH-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L299-L309)) `[EXTERNALLY SUPPORTED]`. The operational effect of shorter pins remains workload-dependent and requires measurement.
*   **Scheduler Architecture Clarification:** Virtual threads do **NOT** execute on `ForkJoinPool.commonPool()`. They run on a dedicated, private `ForkJoinPool` instance encapsulated within `java.lang.VirtualThread.DEFAULT_SCHEDULER`, which is inaccessible via standard common pool APIs `[EXTERNALLY SUPPORTED]`.
*   **Multi-Tier Telemetry Architecture:**
    1.  *Carrier Thread Diagnostics:* JMX `java.lang:type=Threading` can expose platform-thread states, and implementation-specific carrier names can be inspected on a best-effort basis. Names such as `ForkJoinPool-1-worker-*` are not a supported scheduler metric API; production telemetry should not depend on them as a stable identity or pool-size signal.
    2.  *JFR Continuous Streaming:* Capture `jdk.VirtualThreadPinned` events and correlate them with application latency and OS telemetry. Do not treat the absence of a pinning event as proof that carriers are available, especially across native boundaries.
    3.  *Application Queue Dwell Metrics:* Track request time-to-first-byte and queue latency in servlet filters to detect carrier starvation.
    4.  *OS-Level Kernel Telemetry:* Monitor carrier threads at the operating system level using `pidstat -t -p <pid>`, `top -H`, or eBPF off-CPU tracing to detect threads suspended in kernel wait-queues while consuming zero CPU.

---

### Rule 5: ThreadLocal Memory Hygiene ([`CLM-RQ2-07`](../docs/evidence-freeze/claim-evidence-ledger.md#L239-L253)) `[THEORETICAL PROJECTION & EXTERNALLY SUPPORTED]`
> **Rule 5:** *Eliminate unbounded ThreadLocal allocations in request paths. In Java 21 LTS, enforce mandatory cleanup using `try-finally { context.remove(); }`. For post-Java 21 runtimes (standardized in Java 25 via JEP 506), migrate request context storage to Scoped Values.*

*   **Theoretical Memory Projection:** In traditional bounded platform thread pools (e.g., 200 workers), total retained memory from ThreadLocal instances is bounded to $200 \times M_{\text{context}}$. If an application scales to $100,000$ concurrent virtual threads and each retains a $50\text{ KB}$ context payload, the theoretical worst-case heap retention scales to:
    $$100,000 \times 50\text{ KB} \approx 5.0\text{ GB}$$
    *Epistemic Qualification:* This figure represents an arithmetic worst-case theoretical projection ([Section 6.2.3](../docs/chapter-06-analysis-and-answers-to-research-questions.md#623-risk-3-context-propagation-and-threadlocal-memory-scaling-clm-rq2-07)), not a measured empirical constant. In practice, heap retention depends on garbage collection cadence, context payload shallow/deep footprint, and whether virtual threads terminate promptly.
*   **Java 21 LTS Production Reality:** In Java 21 LTS, `ScopedValue` is a **Preview API (JEP 446)** requiring the `--enable-preview` JVM flag. Because enterprise production environments rarely permit preview flags, the primary production guidance for Java 21 LTS is strict, disciplined `ThreadLocal` lifecycle management using `try-finally { context.remove(); }`.
*   **Evolutionary Migration Path & Java 25 Finalization (JEP 506):** Scoped Values progressed through incubation and preview across Java 20 (JEP 429), Java 21 (JEP 446), Java 22 (JEP 464), Java 23 (JEP 481), and Java 24 (JEP 487), culminating in **final standardization in Java 25 via JEP 506**. For systems deployed on Java 25 LTS, Scoped Values are a standard alternative to `ThreadLocal`; framework context propagation and async-dispatch compatibility still require application-specific validation.
*   **Heap Profiling Audit Checklist:**
    1.  [ ] Capture heap dumps under representative load ($10^4\text{--}10^5$ concurrent virtual threads).
    2.  [ ] Inspect `java.lang.ThreadLocal$ThreadLocalMap` instances using Eclipse Memory Analyzer (MAT) or JProfiler.
    3.  [ ] Calculate retained shallow and deep heap size of domain context objects (e.g., `SecurityContextImpl`, `RequestContextHolder`).
    4.  [ ] Verify that virtual threads are transient (request-scoped) rather than long-lived pooled instances (an anti-pattern).
    5.  [ ] Confirm that every servlet filter and interceptor executing `ThreadLocal.set()` contains a corresponding `.remove()` within a guaranteed `finally` block.

---

## 7.4 Correctness-Preserving Refactoring Patterns

This section provides concrete, publication-grade "Before & After" code patterns demonstrating safe refactoring for enterprise Spring Boot applications.

### 7.4.1 Pattern 1: Safe Mutex Refactoring (Eliminating Monitor Pinning) `[MEASURED & THEORETICAL / CONDITIONAL]`

```java
// ==============================================================================
// BEFORE: Anti-pattern triggering Java 21 monitor pinning (CLM-RQ1-01)
// ==============================================================================
@Service
public class LegacyPaymentService {
    private final Object paymentMonitor = new Object();

    public PaymentResponse processPayment(PaymentRequest request) {
        // VULNERABILITY: Synchronized monitor couples continuation to OS carrier.
        // When executeGatewayCall() performs blocking socket I/O, the carrier pins.
        synchronized (paymentMonitor) {
            return executeGatewayCall(request);
        }
    }

    private PaymentResponse executeGatewayCall(PaymentRequest request) {
        // Blocking HTTP call or simulated slow operation
        return restTemplate.postForObject("/api/pay", request, PaymentResponse.class);
    }
}
```

```java
// ==============================================================================
// AFTER: Safe, Virtual-Thread-Aware Explicit Lock Refactoring
// ==============================================================================
@Service
public class RefactoredPaymentService {
    // REFACTORING: ReentrantLock unmounts continuation cleanly via LockSupport.park()
    // Explicitly select fair or non-fair mode based on the application contract.
    // Non-fair mode (default) matches the experimental baseline (PaymentService.java)
    // and may improve throughput but permits AQS direct-CAS barging (CLM-RQ1-05).
    // Fair mode changes acquisition ordering and may affect throughput and tail latency;
    // measure it before treating fairness as a latency guarantee.
    private final ReentrantLock paymentLock = new ReentrantLock(); 

    public PaymentResponse processPayment(PaymentRequest request) {
        // MANDATORY: Always follow the standard lock-try-finally paradigm
        paymentLock.lock();
        try {
            return executeGatewayCall(request);
        } finally {
            // GUARANTEE: Lock release is mandatory in finally block to prevent deadlock
            paymentLock.unlock();
        }
    }

    private PaymentResponse executeGatewayCall(PaymentRequest request) {
        return restTemplate.postForObject("/api/pay", request, PaymentResponse.class);
    }
}
```

---

### 7.4.2 Pattern 2: Foreign Function (JNI) Platform Thread Offloading `[MEASURED & THEORETICAL / CONDITIONAL]`

```java
// ==============================================================================
// BEFORE: Direct blocking JNI invocation on Virtual Thread (CLM-RQ2-01)
// ==============================================================================
@Service
public class LegacyCryptoService {
    static { System.loadLibrary("nativecrypto"); }
    private native byte[] decryptPayloadNative(byte[] encryptedData);

    public byte[] processData(byte[] input) {
        // VULNERABILITY: Direct invocation enters blocking foreign native code.
        // HotSpot cannot unmount native C stack frames. When the C function executes
        // a blocking POSIX syscall (nanosleep, socket read, mutex wait), the underlying
        // carrier thread is held hostage for the duration of the call.
        // HotSpot emits ZERO jdk.VirtualThreadPinned events (silent carrier starvation).
        return decryptPayloadNative(input);
    }
}
```

```java
// ==============================================================================
// AFTER: Safe Foreign Call Isolation via Bounded Platform Thread Pool
// ==============================================================================
@Service
public class IsolatedCryptoService {
    static { System.loadLibrary("nativecrypto"); }
    private native byte[] decryptPayloadNative(byte[] encryptedData);

    // Dedicated, bounded platform thread pool isolated from carrier threads
    private final ExecutorService nativePlatformPool;

    public IsolatedCryptoService(@Qualifier("nativePlatformPool") ExecutorService nativePlatformPool) {
        this.nativePlatformPool = nativePlatformPool;
    }

    public byte[] processData(byte[] input, Duration timeout)
            throws ExecutionException, TimeoutException, InterruptedException {
        // OFFLOAD: Shift blocking foreign call to dedicated OS platform thread
        Future<byte[]> future = nativePlatformPool.submit(() -> decryptPayloadNative(input));
        try {
            // UNMOUNT: Calling virtual thread parks cleanly on LockSupport while
            // awaiting the platform worker, releasing its carrier immediately.
            return future.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
        } catch (TimeoutException | InterruptedException ex) {
            future.cancel(true); // Signal cooperative interruption to platform worker
            throw ex;
        }
    }
}
```

#### Architectural Invariants and Implementation Gotchas

1. **The `CallerRunsPolicy` Trap (Immediate Carrier Starvation):**
   * *Mechanism & Hazard:* In traditional platform-thread architectures, `ThreadPoolExecutor.CallerRunsPolicy` is standard practice for graceful backpressure, forcing the submitting thread to execute rejected tasks when the queue is saturated. However, when callers are **virtual threads** (e.g., standard Spring Boot 3.x request threads), `CallerRunsPolicy` forces the calling virtual thread to execute the rejected native task synchronously.
   * *The Failure Mode:* Because foreign native C frames cannot unmount, executing the native method on the virtual thread immediately captures its underlying `ForkJoinPool` carrier thread. Under sustained ingress, rejected requests rapidly pin every available carrier thread (`Runtime.getRuntime().availableProcessors()`), triggering JVM-wide carrier starvation and paralyzing unrelated virtual threads.
   * *Prescribed Invariant:* Always configure `ThreadPoolExecutor.AbortPolicy` (or a custom load-shedder). The pool must fail fast with `RejectedExecutionException` (mapped to HTTP 503 / Circuit Breaker trips) to guarantee that carrier threads are never commandeered by rejected native work.

2. **The POSIX Cancellation/Interruption Boundary:**
   * *Semantic Disconnect:* When `future.get(timeout, ...)` times out, calling `future.cancel(true)` issues `Thread.interrupt()` to the executing platform worker. While standard Java blocking I/O responds to interrupts by throwing `InterruptedException` or closing channels, foreign C/C++ code executing through JNI or Panama FFM does not participate in JVM cooperative cancellation.
   * *The Kernel Reality:* Standard POSIX blocking system calls (`nanosleep()`, blocking `read()`, `recv()`, `poll()`, POSIX mutex locks) ignore the Java thread interrupt flag entirely. Unless the native C library explicitly handles POSIX signals (`SIGUSR1`) or periodically queries JVM interruption via JNI callbacks (`(*env)->ExceptionCheck(env)`), the platform thread remains trapped in the OS kernel until the syscall completes naturally.
   * *Prescribed Invariant:* `future.cancel(true)` releases the virtual thread continuation, but does *not* abort in-flight native C execution. The platform thread pool must be dimensioned to absorb un-abortable foreign tasks during timeout cascades without resource exhaustion.

3. **Pool Dimensioning and Backpressure (`ArrayBlockingQueue`):**
   * *Unbounded Queue Anti-Pattern:* Using an unbounded queue (such as `LinkedBlockingQueue` without capacity, as created by `Executors.newFixedThreadPool`) is fatal. Because virtual threads scale to tens of thousands with minimal memory, an unconstrained influx of native calls will accumulate without backpressure, leading to runaway heap consumption, multi-second queue latency, and catastrophic `OutOfMemoryError`.
   * *Bounded Queue Sizing:* The platform pool must employ a strictly bounded `ArrayBlockingQueue` (e.g., 200–500 slots) paired with Little's Law dimensioning ($N = \lambda \times T_{\text{hold}}$), bounded by OS thread stack memory and downstream native hardware/driver constraints.

```java
@Configuration
public class NativePoolConfiguration {
    @Bean(name = "nativePlatformPool", destroyMethod = "shutdown")
    public ExecutorService nativePlatformPool(
            @Value("${native.pool.size:16}") int poolSize,
            @Value("${native.pool.queue-capacity:500}") int queueCapacity) {
        return new ThreadPoolExecutor(
            poolSize, poolSize, 60L, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(queueCapacity),
            new CustomizableThreadFactory("native-platform-"),
            new ThreadPoolExecutor.AbortPolicy() // MANDATORY: Fail-fast sheds load
        );
    }
}
```

---

### 7.4.3 Pattern 3: ThreadLocal Memory Hygiene and Migration Pathways

#### Pattern 3A: Primary Java 21 LTS Production Guidance (`ThreadLocal` Defensive Hygiene) `[THEORETICAL / CONDITIONAL]`

```java
// ==============================================================================
// PRIMARY JAVA 21 LTS PATTERN: Defensive ThreadLocal Lifecycle Encapsulation
// ==============================================================================
@Component
public class ProductionSecurityContextFilter implements Filter {
    private static final ThreadLocal<SecurityUser> USER_CONTEXT = new ThreadLocal<>();

    public static SecurityUser getCurrentUser() {
        return USER_CONTEXT.get();
    }

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) 
            throws IOException, ServletException {
        SecurityUser user = authenticate(req);
        
        // MANDATORY: Set context immediately prior to downstream execution
        USER_CONTEXT.set(user);
        try {
            chain.doFilter(req, res);
        } finally {
            // MANDATORY LIFECYCLE ENFORCEMENT: Clean up in finally block unconditionally!
            // Prevents uncollected context objects from polluting the continuation heap stack.
            USER_CONTEXT.remove();
        }
    }
}
```

#### Pattern 3B: Forward-Looking Guidance: Scoped Values (Java 21 Preview / Java 25 JEP 506 Standard) `[EXTERNALLY SUPPORTED]`

> [!NOTE]
> **Runtime Versioning & Standardization:** In OpenJDK 21 LTS, `ScopedValue` is a Preview API under JEP 446 (requiring the `--enable-preview` JVM flag). In Java 25 LTS, Scoped Values is finalized as a permanent standard feature via **JEP 506** (no preview flag required). Teams targeting Java 25 LTS should adopt Pattern 3B as their standard context propagation mechanism.

> **Illustrative scope:** This filter example is pseudocode for synchronous
> downstream execution. Servlet async dispatch, framework-managed context,
> task submission, and child-thread propagation require separate validation.

```java
// ==============================================================================
// REFERENCE IMPLEMENTATION (Post-Java 21 / Java 25 JEP 506 Standard): Scoped Values
// ==============================================================================
@Component
public class ModernSecurityContextFilter implements Filter {
    // REFACTORING: ScopedValue is immutable, lightweight, and automatically unbinds
    public static final ScopedValue<SecurityUser> USER_CONTEXT = ScopedValue.newInstance();

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) 
            throws IOException, ServletException {
        SecurityUser user = authenticate(req);

        // BOUND SCOPE: The user context is legally valid ONLY within this callable scope.
        // The binding is automatically unbound when the scope exits—no finally
        // cleanup is needed for the binding itself. Object reclamation remains
        // subject to reachability and garbage collection.
        // Robust exception bridge preserves checked IOException and ServletException fidelity
        // while allowing unchecked exceptions to propagate unmolested to Spring @ControllerAdvice.
        try {
            ScopedValue.where(USER_CONTEXT, user).run(() -> {
                try {
                    chain.doFilter(req, res);
                } catch (IOException | ServletException ex) {
                    throw new RuntimeServletExceptionBridge(ex);
                }
            });
        } catch (RuntimeServletExceptionBridge bridge) {
            Throwable cause = bridge.getCause();
            if (cause instanceof IOException ioEx) throw ioEx;
            if (cause instanceof ServletException sEx) throw sEx;
            throw new ServletException(cause);
        }
    }

    // EXCEPTION PROPAGATION FIDELITY:
    // 1. Checked exceptions (IOException, ServletException) required by Filter.doFilter
    //    are wrapped into RuntimeServletExceptionBridge across the Runnable lambda boundary
    //    and unboxed at the outer boundary.
    // 2. Unchecked exceptions (e.g., ResponseStatusException, AccessDeniedException, custom business
    //    RuntimeExceptions) bypass the inner catch block completely and propagate unmolested out of
    //    ScopedValue.run(), ensuring standard Spring @ControllerAdvice and error handlers intercept
    //    them without wrapping or signature corruption.
    private static class RuntimeServletExceptionBridge extends RuntimeException {
        public RuntimeServletExceptionBridge(Throwable cause) {
            super(cause);
        }
    }
}
```

---

## 7.5 Post-Migration Observability and Verification Protocol

Following code refactoring and virtual thread enablement, engineering teams must execute a formal post-migration verification protocol.

### 7.5.1 Production JFR Observability Configuration `[THEORETICAL / CONDITIONAL & EXTERNALLY SUPPORTED]`
Deploy applications with continuous Java Flight Recorder settings configured to
capture monitor pinning events. The recording overhead, disk usage, and retention
policy must be measured and validated in staging for the target workload; the
configuration below is not universally low-overhead:

```bash
JAVA_OPTS="-XX:StartFlightRecording=dumponexit=true,disk=true,maxage=12h,maxsize=5g \
           -XX:FlightRecorderOptions=stackdepth=128"
```

> [!IMPORTANT]
> **Diagnostic Flag Distinction:** The JVM flag `-Djdk.tracePinnedThreads=short` (or `=full`) is a **diagnostic console tracing mechanism** designed for pre-production debugging and local defect reproduction. It prints call stacks directly to standard error or standard output. It must **NOT** be enabled in high-throughput production APM environments, as synchronous console I/O induces severe thread serialization and carrier contention.

To reduce the default 20 ms blind spot in pre-production staging environments, deploy a custom `low-threshold.jfc` file setting the pinning threshold to 5 ms:

```xml
<event name="jdk.VirtualThreadPinned">
  <setting name="enabled">true</setting>
  <setting name="threshold">5 ms</setting>
  <setting name="stackTrace">true</setting>
</event>
```

*Observability Caveat:* Configuring a 5 ms threshold significantly reduces the 20 ms blind spot, but does not capture micro-pinning events lasting $< 5\text{ ms}$. In the measured direct JNI path without a callback into Java, the native call bypassed the continuation-yield mechanism and emitted no pinning events. JFR is therefore not a general carrier-blocked detector; native code that calls back into Java or reaches other runtime pinning paths may behave differently, especially on JDK 24+ ([`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L161), [`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176)) `[MEASURED & EXTERNALLY SUPPORTED]`.

### 7.5.2 Dual-Window Verification Checklist `[MEASURED]`
During automated load testing, enforce the **Dual-Window Verification Protocol** ([`CLM-METH-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L271-L283)):
*   [ ] **Window Isolation:** Isolate the client ramp-up stage (0–15s) from steady-state evaluations (15–45s) to avoid the 25.8% median latency shift observed in [Chapter 5: Experimental Results](../docs/chapter-05-experimental-results.md#59-historical-baseline-and-flawed-strata-strata-5-and-7).
*   [ ] **Zero HTTP Defect Rate:** Verify that HTTP request error rates remain strictly at $0.000\%$.
*   [ ] **Carrier CPU Characterization:** Confirm that steady-state carrier CPU utilization reflects active processing rather than idle wait-queue captivity.

---

## 7.6 The Migration Decision Table and Decision Tree

### 7.6.1 Master Architectural Migration Decision Table

### Table 7.2: Architectural Migration Triage and Action Matrix

| Observed Code / Architectural Pattern | Direct Empirical / Theoretical Evidence | Risk Classification | Required Verification Check | Safe Architectural Action | Evidential Classification |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **`synchronized` block wrapping socket / database I/O** | `jdk.VirtualThreadPinned` events $\ge 20\text{ ms}$ in JFR ([`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L54)) | **CRITICAL** | Verify whether critical section serializes a shared domain resource | Refactor to `ReentrantLock` (`Pattern 1`) if carriers are starved; or evaluate Java 24 (JEP 491), while auditing residual blocking mechanisms. | `[MEASURED & EXTERNALLY SUPPORTED]` |
| **`synchronized` block protecting fast in-memory state** | Zero JFR pinning events; duration $< 10\text{ }\mu\text{s}$ | **LOW** | Verify that no I/O, sleep, or network calls exist inside lock | **Retain `synchronized`**. Avoid refactoring to prevent AQS non-fair barging jitter. | `[HEURISTIC / LITERATURE]` |
| **Foreign function call via JNI (blocking system call)** | In the measured direct JNI path: carrier starvation, ~1% CPU, and 0 JFR pinning events ([`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L161)) | **CRITICAL** | Audit C/C++ source and determine whether it calls back into Java or performs blocking/native CPU work | **Isolate materially blocking or unpredictable native calls to a dedicated platform pool** (`Pattern 2`). Direct invocation requires bounded execution time and concurrency plus implementation-specific validation. | `[MEASURED & THEORETICAL / CONDITIONAL]` |
| **HikariCP database pool under high virtual thread load** | Empirically validated queueing bottleneck: pool 1 yields 15,123 ms p50 at 3.27 req/s; pool 10 scales to 32.60 req/s at 1,431 ms p50 while carriers unmount cleanly ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192)) | **HIGH** | Measure connection hold time, arrival rate, active/pending counts, timeout rates, database limits, and query latency | Calibrate pool size and `connectionTimeout` to database capacity and service SLOs; enforce application-level semaphores; do not scale pool mechanically with virtual threads. | `[MEASURED & EXTERNALLY SUPPORTED]` |
| **Heavy `ThreadLocal` usage in per-request filter chains** | Theoretical heap expansion under load; uncollected ThreadLocal maps ([`CLM-RQ2-07`](../docs/evidence-freeze/claim-evidence-ledger.md#L239-L253)) | **MEDIUM** | Audit heap dump under $10^5$ concurrent requests for `ThreadLocalMap` | Enforce `finally { remove(); }` cleanup (`Pattern 3A`) or evaluate Scoped Values for Java 25 JEP 506 / preview (`Pattern 3B`). | `[THEORETICAL / CONDITIONAL]` |
| **Legacy database driver (`pgjdbc < 42.6.0`, `mysql < 9.0`)** | Internal monitor pinning reported in driver socket read methods | **HIGH** | Run `mvn dependency:tree`; inspect socket read call stacks in JFR | Upgrade dependency to evaluated version threshold (Table 7.1). | `[EXTERNALLY SUPPORTED]` |

---

### 7.6.2 The Master Architectural Migration Decision Tree

The Mermaid flowchart below is an audit pipeline, not a mutually exclusive
classification tree. Each request path must pass through the relevant
synchronization, native, database, context, dependency, and observability
checks; a remediation node never replaces the remaining checks.

```mermaid
graph TD
    Start["Begin component/request-path audit"] --> CheckDeps{"Third-party dependencies meet version/risk checks?"}
    CheckDeps -- "No or unknown" --> UpgradeDeps["Resolve versions and inspect documented risk paths"]
    CheckDeps -- "Yes" --> CheckJNI
    UpgradeDeps --> CheckJNI

    CheckJNI{"JNI or foreign-function boundary?"}
    CheckJNI -- "Yes" --> JNIBlock{"Blocking, unpredictable, or high-cost native work?"}
    JNIBlock -- "Yes" --> Offload["Offload to bounded platform pool"]
    JNIBlock -- "No, bounded and verified" --> DirectJNI["Direct call remains conditional"]
    CheckJNI -- "No" --> NoJNI["No native-boundary action"]
    Offload --> CheckSync
    DirectJNI --> CheckSync
    NoJNI --> CheckSync

    CheckSync{"Synchronized monitor around blocking work?"}
    CheckSync -- "Yes" --> CheckJDK{"Target JDK?"}
    CheckJDK -- "Java 24+" --> Monitor24["JEP 491 changes monitor pinning; audit residual native/class-init paths"]
    CheckJDK -- "Java 21-23" --> CheckMutex{"Does the lock serialize a domain bottleneck?"}
    CheckMutex -- "Yes" --> SerialRule["Preserve serialization; do not expect lock replacement to raise endpoint capacity"]
    CheckMutex -- "No, carrier starvation measured" --> RefactorLock["Evaluate non-fair ReentrantLock with try-finally"]
    CheckSync -- "No" --> CheckDB
    Monitor24 --> CheckDB
    SerialRule --> CheckDB
    RefactorLock --> CheckDB

    CheckDB{"Database connection checkout?"}
    CheckDB -- "Yes" --> PoolAudit["Measure hold time, arrival rate, pool limits, DB capacity, and SLOs"]
    CheckDB -- "No" --> NoDB["No database-pool action"]
    PoolAudit --> CheckContext
    NoDB --> CheckContext

    CheckContext{"ThreadLocal context?"}
    CheckContext -- "Yes" --> ContextAudit["Require finally remove(); evaluate ScopedValue by target JDK"]
    CheckContext -- "No" --> NoContext["No context action"]
    ContextAudit --> Verify
    NoContext --> Verify

    CheckCPU{"Compute-bound work?"}
    Verify["Run dependency, correctness, JFR, application, and OS verification"] --> CheckCPU
    CheckCPU -- "Yes" --> CPUQualify["Benchmark CPU work separately; virtual threads do not imply compute speedup"]
    CheckCPU -- "No" --> Final["Complete migration review with measured evidence"]
    CPUQualify --> Final
```

---

## 7.7 Boundaries and Limitations of the Guidance

While this migration framework provides comprehensive protection against known runtime and architectural failure modes, software architects must recognize that certain systemic capacity constraints require external architectural interventions:

1.  **Database Server Scaling:** Virtual thread migration may improve servlet-thread utilization, but does not increase database CPU, disk I/O, or lock capacity. If an enterprise backend is constrained by write-ahead-log (WAL) contention or unindexed scans, increasing offered concurrency may increase queueing; the magnitude and remedy are workload-dependent and must be measured. Possible interventions include read replicas, caching, or CQRS where appropriate.
2.  **Downstream Network and Socket Starvation:** Multiplying concurrent outbound client requests by a factor of 100x can saturate downstream HTTP microservices, network NAT tables, and local ephemeral port ranges (`TIME_WAIT` socket exhaustion). Outbound HTTP clients (`RestClient`, `WebClient`) must configure strict connection pool bounds.
3.  **Kernel and Scheduler Costs:** Virtual-thread mount/unmount costs and operating-system scheduling costs depend on JDK version, hardware, OS, workload, and contention. Carrier threads remain subject to kernel scheduling; repeated native blocking or page faults can create measurable degradation and must be evaluated with platform-appropriate telemetry.
4.  **Database Administrator (DBA) Review:** Any alteration to HikariCP pool configurations or transaction demarcation boundaries must be coordinated with database administration teams to ensure server connection limits (`max_connections`) and shared buffer allocations are not exceeded.

---

*(End of Chapter 7 Draft Text)*

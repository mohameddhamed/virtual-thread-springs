# Chapter 1: Introduction

## 1.1 Industrial Motivation and The Virtual Thread Bottleneck Fallacy

### 1.1.1 The Dominance and Limits of Synchronous Thread-per-Request Concurrency

For over two decades, enterprise Java backend architectures have overwhelmingly relied upon the synchronous, **thread-per-request** programming model. Standardized by the Java Servlet API and realized in production web servers such as Apache Tomcat, Eclipse Jetty, and Spring Framework Model-View-Controller (MVC) containers, this paradigm assigns each incoming client HTTP connection to a dedicated worker thread.

The widespread dominance of the thread-per-request architecture stems from its straightforward mental model and operational ergonomics:
1.  **Sequential Imperative Execution:** Business logic executes sequentially down a single, predictable call stack. Control flow conforms directly to standard procedural constructs (`if`, `for`, `try-catch`), eliminating the cognitive friction of asynchronous callbacks.
2.  **Context and Diagnostic Transparency:** Contextual state—such as authentication principals, distributed tracing tokens (`TraceId`, `SpanId`), and transactional boundaries—can be implicitly propagated across service layers using thread-local storage ([`ThreadLocal`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L28)). Diagnostic stack traces captured upon an exception provide a continuous, unbroken chronology of the failed request.
3.  **Broad Ecosystem Alignment:** Enterprise persistence abstractions (e.g., JDBC, Hibernate, Spring Data) and third-party utility libraries were engineered natively around blocking input/output (I/O) primitives and synchronous thread context.

Despite these advantages, the physical foundation of traditional Java concurrency imposes a severe architectural bottleneck: **a 1:1 mapping between Java threads and operating system (OS) kernel platform threads**. In the OpenJDK HotSpot Virtual Machine, every instance of `java.lang.Thread` historically represented an OS-managed thread (such as a POSIX `pthread` on Linux and macOS, or a Win32 thread on Windows).

Operating system threads are heavyweight computational resources:
*   **Memory Overhead:** Each platform thread reserves a fixed, contiguous virtual memory stack allocated outside the Java garbage-collected heap. HotSpot defaults to a 1,024 KB (`-Xss1m`) stack reservation per thread. A server concurrently handling 2,000 platform threads immediately allocates approximately 2.0 GB of memory solely for thread call stacks, irrespective of actual stack depth.
*   **Scheduling and Context-Switching Latency:** The OS kernel scheduler maintains scheduling queues, transitions between user space and kernel space (`ring 3` to `ring 0`), and invalidates CPU instruction and data caches (L1/L2 caches and Translation Lookaside Buffers [TLB]) when preemptively switching between platform threads.
*   **Thread Pool Exhaustion:** To protect the host operating system from catastrophic memory exhaustion and scheduler thrashing, enterprise servlet containers strictly constrain concurrency using bounded thread pools (e.g., Apache Tomcat's default `maxThreads = 200`). When concurrent client requests exceed this threshold or downstream dependencies (such as external payment gateways or relational databases) experience latency spikes, worker threads rapidly block while waiting for I/O. The container thread pool exhausts, newly arriving requests queue up in container backlogs, client-perceived latency escalates exponentially, and the service inevitably suffers from cascading connection timeouts and collapse.

```
+-----------------------------------------------------------------------------------+
|               TRADITIONAL PLATFORM THREAD CONCURRENCY (1:1 MAPPING)               |
+-----------------------------------------------------------------------------------+
  HTTP Requests      Tomcat Worker Pool (maxThreads=200)       OS Kernel Threads
  [Req 1]  ───────>  [Platform Thread 1 (1 MB Stack)]  ──1:1──>  [Kernel Thread A]
  [Req 2]  ───────>  [Platform Thread 2 (1 MB Stack)]  ──1:1──>  [Kernel Thread B]
  [Req ...] ───────>  [Platform Thread ...]             ──1:1──>  [Kernel Thread ...]
  [Req 201] ───────>  [WAITING IN TOMCAT QUEUE]         ───────>  *THREAD EXHAUSTION*
+-----------------------------------------------------------------------------------+
```

### 1.1.2 The Reactive Divergence and Its Operational Costs

To circumvent the concurrency limitations of platform thread pools, the software industry turned toward reactive, event-driven architectures during the 2010s. Frameworks such as Node.js, Netty, Spring WebFlux, and Project Reactor decoupled request handling from dedicated threads by multiplexing concurrent connections over a tiny, fixed pool of non-blocking event-loop threads (typically matching the physical CPU core count).

When a reactive service encounters an I/O operation (such as an HTTP call or reactive database query), it registers an asynchronous callback and yields the event loop thread immediately. While this approach dramatically increased concurrent connection capacity and resource efficiency, it introduced steep architectural, cognitive, and operational penalties:
*   **Cognitive Friction and "Coloring":** Reactive programming forces developers to abandon standard imperative idioms in favor of monadic functional pipelines (`Mono`, `Flux`, `CompletableFuture`). Code readability deteriorates, and synchronous abstractions can no longer be invoked without complex bridging (`block()`), which risks deadlocking the event loop.
*   **Broken Stack Traces and Obscured Debuggability:** Because tasks hop across event-loop worker threads at each asynchronous stage, standard exception stack traces become fragmented and uninformative. Reconstructing request flow across thread boundaries requires specialized distributed tracing machinery and reactor-specific debug hooks that incur notable runtime overhead.
*   **Ecosystem Incompatibility:** The overwhelming majority of enterprise Java infrastructure—most notably relational database access via standard JDBC drivers and connection pools (such as HikariCP)—relies upon synchronous, blocking sockets. Integrating blocking relational databases into reactive pipelines requires offloading queries to isolated thread pools (e.g., `Schedulers.boundedElastic()`), which fundamentally re-introduces thread pool management complexity.

Consequently, enterprise software engineering remained caught in an architectural dilemma: accept the throughput ceilings and memory waste of synchronous platform threads, or absorb the deep cognitive and infrastructural complexity of reactive event loops.

### 1.1.3 The Promise of Project Loom and Java 21 Virtual Threads

**Project Loom**, integrated into the Java platform as a production-ready feature in **Java 21 LTS** via **JEP 444** (Virtual Threads), was designed to resolve this architectural dilemma. Virtual Threads introduce lightweight, user-mode threads managed directly by the Java Virtual Machine (JVM) runtime rather than the host operating system.

Under Project Loom, the JVM implements an $M:N$ scheduling architecture:
*   **User-Mode Tasks ($M$):** Millions of ephemeral Virtual Threads can be instantiated dynamically. A virtual thread possesses an initial memory footprint of less than 1 KB, with its call stack allocated as a chain of `Continuation` objects directly on the garbage-collected Java heap.
*   **Carrier Threads ($N$):** A small, fixed pool of standard OS platform threads—managed by an internal HotSpot `ForkJoinPool` instance (`java.lang.VirtualThread.DEFAULT_SCHEDULER`)—acts as **carrier threads** that physically execute virtual thread instructions on CPU cores.
*   **Cooperative Runtime Unmounting:** When a virtual thread executes a blocking operation within standard Java libraries (such as `Socket.read()`, `Thread.sleep()`, or locking a `java.util.concurrent` lock), the runtime captures and freezes the virtual thread's stack frames to the heap. The virtual thread **unmounts** from its carrier thread, releasing the underlying OS platform thread back to the scheduler to execute other ready virtual threads. Once the blocking I/O or sleep completes, the runtime unparks the virtual thread, which is subsequently remounted onto an available carrier thread to resume execution.

In Spring Boot 3.2.0 and later (evaluated in this research using Spring Boot 3.5.12), enabling Virtual Threads requires only a single declarative property in [`application.yml`](../src/main/resources/application.yml):

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

Upon setting this property, Spring Boot configures Apache Tomcat's embedded protocol handlers to dispatch every incoming HTTP connection to an ephemeral virtual thread generated by `Executors.newVirtualThreadPerTaskExecutor()`. To software engineering organizations, this promised the best of both worlds: the full scalability benefits of reactive programming alongside the straightforward imperative programming model, synchronous JDBC persistence, and diagnostic transparency of traditional Spring MVC.

```
+-----------------------------------------------------------------------------------+
|               VIRTUAL THREAD COOPERATIVE SCHEDULING (M:N MAPPING)                 |
+-----------------------------------------------------------------------------------+
  HTTP Requests          Virtual Threads (Heap)              Carrier Pool (ForkJoin)
  [Req 1]   ───────>   [VT 1: Continuation]  ──Mounts───>  [Carrier Thread 1 (OS)]
  [Req 2]   ───────>   [VT 2: Continuation]  ──Mounts───>  [Carrier Thread 2 (OS)]
  ...                  ...                                  ...
  [Req 1000]───────>   [VT 1000: Continuation]             [Carrier Pool: N Cores]
                             │
                             ▼ Blocks on I/O (e.g. Socket Read)
                       *UNMOUNTS TO HEAP*
                       Carrier Thread 1 is immediately freed for [VT 3]!
+-----------------------------------------------------------------------------------+
```

### 1.1.4 The Virtual Thread Bottleneck Fallacy

The simplicity of enabling Virtual Threads led to a widespread industry belief: that toggling `spring.threads.virtual.enabled: true` would universally eliminate concurrency bottlenecks, drastically reduce latencies, and deliver immediate order-of-magnitude throughput gains for legacy Spring Boot applications.

This dissertation terms this assumption **The Virtual Thread Bottleneck Fallacy**. The fallacy presumes that the primary limiting factor in enterprise backend performance is always *thread pool concurrency capacity* at the web container tier. In reality, removing the platform thread ceiling does not eliminate performance bottlenecks; rather, it shifts the operational pressure points deeper into the system architecture:

```
+-----------------------------------------------------------------------------------+
|                    THE VIRTUAL THREAD BOTTLENECK FALLACY                          |
+-----------------------------------------------------------------------------------+
  NAIVE EXPECTATION:
  [Platform Threads (max 200)]  ─── Enable Loom ───>  [Unbounded Virtual Threads]
                                                            │
                                                            ▼
                                                      10x Throughput? (NO)

  ARCHITECTURAL REALITY:
  [Unbounded Virtual Threads]  ─── Floods Downstream ───>  [Downstream Bottlenecks]
                                                            ├── Domain Lock Serialization
                                                            ├── Connection Pool Limits
                                                            ├── Foreign JNI Captivity
                                                            └── Database Engine Capacity
+-----------------------------------------------------------------------------------+
```

1.  **Shift from Thread Scarcity to Domain Serialization:** In real-world enterprise applications, execution is frequently constrained by business domain invariants, consistency boundaries, and shared mutable state protected by mutual exclusion primitives (such as Java `synchronized` blocks or explicit database table locks). By Amdahl's Law (1967), if an operation contains a serialized critical section, allocating 10,000 concurrent threads cannot increase throughput beyond the physical service rate of that critical section.
2.  **Downstream Finite Resource Contention:** While the JVM can allocate millions of virtual threads in user-space heap memory, external physical resources—such as relational database connections managed by HikariCP, database transaction engines, disk I/O channels, and physical CPU cores—remain strictly finite. Unbounded virtual threads dispatching concurrent requests simply transfer the queueing backlog from Tomcat's thread pool to the database connection pool or backend datastore, inducing connection starvation, lock contention, and elevated tail latencies.
3.  **Hidden JVM-OS Boundary Frictions:** Virtual thread cooperative unmounting is not an absolute invariant; it relies upon HotSpot runtime cooperation. In Java 21 LTS, legacy synchronization constructs—specifically intrinsic object monitors (`synchronized`) and foreign function calls via the Java Native Interface (JNI)—prevent the JVM from unmounting the virtual thread. In these scenarios, the virtual thread **pins** or captures its underlying carrier thread, actively starving the carrier pool and degrading system performance below that of a well-tuned platform thread pool.

Understanding, isolating, and navigating these architectural friction points is the central objective of this dissertation.

---

## 1.2 Research Problem Statement

### 1.2.1 The Architectural Disconnect

The fundamental research problem addressed in this study is the **architectural disconnect between high-level runtime virtual thread abstractions and low-level execution mechanics in enterprise Spring Boot MVC systems**.

While Project Loom re-engineers thread scheduling inside the JVM, enterprise applications are complex socio-technical artifacts consisting of layered abstractions: Spring MVC dispatchers, transactional service proxies, relational persistence engines, connection pools, third-party libraries, and operating system interfaces. When a legacy application is transitioned to Virtual Threads without architectural re-engineering:
*   Legacy concurrency primitives designed under the assumption of scarce platform threads produce unintended runtime hazards (such as monitor pinning and carrier starvation).
*   Unbounded thread concurrency overwhelms downstream relational databases lacking elastic connection scaling.
*   Standard diagnostic and observability tools (e.g., CPU profilers, Java Flight Recorder) fail to detect or accurately attribute new failure modes (such as silent carrier captivity during native JNI blocking).

Currently, software engineering practitioners lack an empirical, mechanism-grounded foundation to predict when a virtual thread migration will succeed, when it will yield zero performance benefit, and when it will introduce catastrophic availability failures.

### 1.2.2 The Symptom-to-Mechanism Disambiguation Vocabulary

A critical methodological vulnerability in existing virtual thread literature and industrial post-mortems is the **conflation of observable symptoms with underlying execution mechanisms**. When an application experiences elevated response times or reduced throughput under Virtual Threads, practitioners frequently misdiagnose the issue—often attributing any performance regression to "monitor pinning" or assuming that eliminating pinning will automatically improve throughput.

To establish scientific rigor, this dissertation establishes an authoritative **Symptom-to-Mechanism Disambiguation Vocabulary**. Every performance observation must be grounded in verified low-level execution evidence before attributing causality.

### Table 1.1: Symptom-to-Mechanism Disambiguation Matrix

| Observed Symptom | Naive / Conflated Hypothesis | True Underlying Mechanism | Direct Evidentiary Requirement | Thesis Claim Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Throughput Plateau at $\approx 2\text{ req/s}$** | "Virtual threads are failing to unmount due to monitor pinning" | **Application Domain Serialization:** A 500 ms critical section bounds service rate to $\mu = 1/D = 2.0\text{ req/s}$ via Amdahl's Law, regardless of thread model or unmounting. | Throughput remains identical ($\approx 1.96\text{ req/s}$) when pinning is completely eliminated via `ReentrantLock`. | [`CLM-RQ1-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L86-L98) |
| **Median Latency Inflation ($\approx 5000\text{ ms}$)** | "High context switching overhead or scheduler inefficiency" | **Closed-Loop Queueing Saturation:** Under 10 closed-loop Virtual Users and 100 ms think time, Little's Law gives $N = X(R + Z)$, hence $R = N/X - Z = 10/1.967 - 0.100 \approx 4.985\text{ s}$. | Mathematical convergence between Little's Law derivation and k6 steady-state response time distributions. | [`CLM-METH-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L312-L322) |
| **Zero JFR Pinning Events but Full Throughput Collapse** | "Virtual threads are functioning correctly; problem must be network I/O" | **Silent JNI Carrier Captivity:** POSIX `nanosleep()` in native C code captures the OS carrier thread in `_thread_in_native`; HotSpot freeze logic is bypassed, suppressing JFR pinning events. | k6 throughput collapses to $1.97\text{ req/s}$ while JFR `jdk.VirtualThreadPinned` event count is strictly **0**. | [`CLM-RQ2-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L148-L160) |
| **Silent Carrier Starvation with Low Process CPU ($\approx 1\%$)** | "Carrier threads are in a 100% busy-spin CPU loop" | **Kernel Wait-Queue Suspension:** The tested direct JNI POSIX `nanosleep()` path transitions the carrier thread to a Darwin/Mach wait state, consuming little active CPU while occupying the scheduler carrier. | Host process telemetry capturing steady-state process CPU utilization of $1.04\% \pm 0.12\%$. | [`CLM-RQ2-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L164-L176) |
| **Database pool contention not established: pre-acquisition delay construct flaw** | "Virtual threads overwhelm HikariCP connection pool" | **Connection Checkout Hold-Time Contention:** In `/orders`, query execution was $< 0.1\text{ ms}$ while 300 ms delay executed *before* connection checkout, leaving pool utilization and exhaustion unmeasured. | Source audit confirming the pre-acquisition sleep construct flaw; no HikariCP occupancy telemetry was captured. | [`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192) |
| **Elevated Tail Latency Dispersion in Refactored Locks** | "ReentrantLock is fundamentally slower than intrinsic monitors" | **AQS Non-Fair Direct-CAS Barging:** `ReentrantLock`'s default `NonfairSync` permits newly arriving threads to bypass the wait queue, increasing latency standard deviation by $\approx 23\times$. | Latency standard deviation spread of $\approx 16\text{--}30\text{ ms}$ for `ReentrantLock` vs. $\le 7.4\text{ ms}$ for `synchronized`. | [`CLM-RQ1-05`](../docs/evidence-freeze/claim-evidence-ledger.md#L101-L111) |

---

## 1.3 Research Questions

To provide a structured, empirical investigation into the interaction between virtual thread scheduling, synchronization mechanics, and architectural dependencies, this dissertation establishes two canonical Research Questions:

### 1.3.1 Canonical Research Questions

> **Research Question 1 (RQ1):**
> *How does synchronization (specifically monitor pinning) interact with carrier-thread availability, application-level serialization, and runtime throughput in Java 21 Spring Boot MVC systems?*

> **Research Question 2 (RQ2):**
> *What architectural risks—including native boundaries, connection pool management, context propagation, and observability limits—must engineering teams evaluate before enabling Virtual Threads in existing Spring Boot MVC systems?*

### 1.3.2 Operational Construct Deconstruction

To transition these research questions from abstract inquiries into empirically verifiable hypotheses, each question is operationalized around explicit independent treatments, dependent metrics, and mechanism boundaries:

*   **Deconstruction of RQ1 (Synchronization and Pinning Mechanics):**
    *   *Independent Variables:* Concurrency model (Platform Threads vs. Virtual Threads), Synchronization primitive (Language-level monitor `synchronized`, Explicit lock `ReentrantLock`, Diagnostic baseline `no-lock`), Runtime JDK version (Java 21 LTS vs. Java 24 with JEP 491 object monitor unpinning).
    *   *Dependent Performance Metrics:* Sustained request throughput ($req/s$), Median response time ($p50$ latency in $ms$), Tail response times ($p95$ and $p99$ latency in $ms$), Within-treatment variance/dispersion across independent process trials.
    *   *Low-Level Mechanism Indicators:* HotSpot Java Flight Recorder (JFR) `jdk.VirtualThreadPinned` event counts, Pinning hold durations, Stack trace attribution.
    *   *Core Operational Hypothesis:* While refactoring `synchronized` to `ReentrantLock` eliminates monitor pinning events in Java 21, it will not increase system throughput if the critical section represents an application-level serialization bottleneck.

*   **Deconstruction of RQ2 (Architectural Migration Risks):**
    *   *Independent Variables:* Execution boundary (Pure Java managed blocking vs. JNI native POSIX blocking), Foreign function duration (Fast native transition `/native-short` vs. Long native sleep `/native`), Relational database pool sizing (HikariCP maximum pool size 1 vs. 10), Context storage patterns (`ThreadLocal` retention vs. clean teardown).
    *   *Dependent Metrics and Indicators:* k6 client failure rates and timeouts, Host process CPU telemetry (`%cpu` via `ps`), JFR flight recordings, HikariCP connection acquisition latency.
    *   *Core Operational Hypothesis:* Foreign function boundaries (JNI) induce silent carrier thread starvation that completely evades JFR pinning detection, while relational database pools shift concurrency bottlenecks from the web tier to database connection checkout queues.

---

## 1.4 Scope, Constraints, and Explicit Exclusions

To ensure scientific defensibility, reproducibility, and high internal validity, the experimental boundaries of this research are strictly defined.

### 1.4.1 Architectural and Framework Scope

1.  **Framework Stack:** The primary software artifact is an instrumented enterprise benchmark application implemented on **Spring Boot 3.5.12**, compiled with **Java 21 LTS**, and executed on an embedded **Apache Tomcat 10.1.52** servlet container.
2.  **Concurrency Dispatch:** Request handling is evaluated across two explicit modes: standard bounded platform thread execution (Tomcat default pool of 200 threads) and virtual thread dispatching via Spring Boot's `spring.threads.virtual.enabled: true` (`Executors.newVirtualThreadPerTaskExecutor()`).
3.  **Persistence Layer:** Relational database access is modeled using Spring's `JdbcTemplate` backed by HikariCP (version 6.3.3), evaluated across embedded in-memory H2 databases and containerized Docker PostgreSQL 15-alpine instances.
4.  **Workload Representation:** Workloads represent core enterprise patterns: transactional state modification with mutual exclusion ([`PaymentController`](../src/main/java/com/thesis/virtualthreadsdemo/controller/PaymentController.java) at `/payments`), relational query execution ([`OrderController`](../src/main/java/com/thesis/virtualthreadsdemo/controller/OrderController.java) at `/orders`), native C system call execution ([`NativeController`](../src/main/java/com/thesis/virtualthreadsdemo/controller/NativeController.java) at `/native`), fast catalog lookups (`/products`), and compute-bound hashing (`/cpu`).

### 1.4.2 Hardware and Host Environment Constraints (`CLM-METH-01`)

All primary benchmark trials were executed on a dedicated bare-metal host environment:
*   **Processor:** Apple M1 (8 logical processing cores: 4 high-performance cores, 4 energy-efficient cores).
*   **Memory:** 8 GB unified system memory.
*   **Operating System:** Darwin 25.2.0 (macOS 15.2 arm64).

> [!IMPORTANT]
> **The Scheduler Constraint vs. Container Quota Distinction (`CLM-METH-01`):**
> To isolate synchronization mechanics and observe carrier starvation with absolute clarity, primary experimental trials applied JVM scheduler flags:
> ```bash
> -Djdk.virtualThreadScheduler.parallelism=1
> -Djdk.virtualThreadScheduler.maxPoolSize=1
> ```
> This configuration represents an **in-process JVM scheduler constraint** that forces the virtual thread `ForkJoinPool` carrier worker count to exactly one. **It is not a Linux cgroup CPU bandwidth quota (`cpu.cfs_quota_us`)**. The JVM process, garbage collector, JFR telemetry daemon, Tomcat acceptor threads, and the k6 load generator continued to execute concurrently across all 8 host cores of the Apple M1 processor. The thesis explicitly rejects describing `parallelism=1` as "1-vCPU container equivalence."

### 1.4.3 Closed-Loop Workload Model (`CLM-METH-05`)

Workload generation is executed using **k6** in a **closed-loop concurrency model** (10 to 50 concurrent Virtual Users [VUs]):
*   In closed-loop testing, each virtual user issues an HTTP request, synchronously awaits the response, then performs the configured 100 ms think time ($Z = 0.100\text{ s}$) before dispatching the subsequent request.
*   Consequently, client arrival rate is structurally coupled to system response time by Little's Law ($N = X(R + Z)$, or $R = N/X - Z$). When response time inflates due to a serialized critical section, the client self-throttles. This model reflects client behavior in synchronous batch processing and microservice RPC pipelines, but does not simulate open-loop Poisson arrival spikes.

### 1.4.4 Explicit Exclusions

The following domains are explicitly excluded from the primary scope of this dissertation:
1.  **Reactive Asynchronous Runtimes:** Non-blocking event-loop architectures (Spring WebFlux, Project Reactor, Netty, Akka/Pekko) are evaluated comparatively in theoretical discussions (Chapter 8), but are not benchmarked as empirical treatments.
2.  **Distributed Network Topologies:** Multi-node clustered deployments, Kubernetes service meshes, and wide-area network latency jitter are excluded to eliminate non-deterministic network noise from JVM scheduler measurements.
3.  **Inferential Statistical Modeling on Small Samples (`CLM-METH-03`):** Primary benchmark conditions were executed across $N=3$ independent process-level repetitions. While within-treatment latency spread is exceptionally tight ($< 0.7\%$), $N=3$ samples are presented strictly as **descriptive engineering bounds**; inferential hypothesis testing (e.g., ANOVA, Student's t-tests, p-values) is explicitly excluded.
4.  **Construct-Flawed or Unmanifested Executions:** Historical exploratory runs (such as local H2 pool tests affected by YAML indentation defects or Docker PostgreSQL runs lacking JFR flags) are formally partitioned into Stratum 7 and excluded from quantitative claims.

---

## 1.5 Contribution Ledger and Foundational Architectural Principles

### 1.5.1 Primary Empirical and Theoretical Contributions

This dissertation delivers five primary contributions to the academic literature and industrial engineering practice, mapped directly to the ratified [Claim-to-Evidence Ledger](../docs/evidence-freeze/claim-evidence-ledger.md):

```
+-----------------------------------------------------------------------------------+
|                        THESIS CONTRIBUTION LEDGER MAPPING                         |
+-----------------------------------------------------------------------------------+
  Contribution 1: Decoupling Carrier Unpinning from Domain Serialization
  ├── Claim: CLM-RQ1-04 (Unpinning != Unserializing)
  ├── Evidence: Stratum 1 (12 executions, Delta TP < 0.3%)
  └── Theory: Amdahl's Law and Single-Server Saturation Invariant
           │
           ▼
  Contribution 2: Silent Carrier Starvation via Foreign Functions (JNI)
  ├── Claim: CLM-RQ2-01 & CLM-RQ2-02 (JNI Carrier Captivity & ~1% CPU)
  ├── Evidence: Stratum 3 (27 executions, JFR Pinning Events = 0)
  └── Theory: Continuation Bypass in _thread_in_native State
           │
           ▼
  Contribution 3: Methodological Rigor and Forensic Discrepancy Auditing
  ├── Claim: CLM-METH-01 to CLM-METH-05, DISC-01 to DISC-12
  ├── Evidence: 119-run census, 504 artifacts, Dual-Window Mandate (25.8% shift)
  └── Theory: Epistemic Stratification and Forensic Defect Disambiguation
           │
           ▼
  Contribution 4: Authoritative Engineering Migration Framework
  ├── Claim: CLM-MIG-01 to CLM-MIG-04
  ├── Evidence: Evaluated dependency thresholds (Table 7.1)
  └── Practice: 5 Core Rules, 4 Production Patterns, Comprehensive Decision Tree
+-----------------------------------------------------------------------------------+
```

1.  **Decoupling Carrier Unpinning from Domain Serialization (`CLM-RQ1-04`):**
    This study proves empirically and mathematically that refactoring Java `synchronized` monitors to `ReentrantLock` completely eliminates HotSpot monitor pinning events (`CLM-RQ1-03`), yet yields **zero throughput improvement** ($\approx 1.96\text{ req/s}$) under domain contention. Throughput remains constrained by Amdahl's Law and queueing saturation theory. Carrier unpinning frees carrier threads for unrelated tasks, but cannot accelerate serialized domain entities.
2.  **Discovery of Silent Carrier Starvation in Foreign Function Interfaces (`CLM-RQ2-01`, `CLM-RQ2-02`):**
    This study proves that native POSIX blocking calls (`nanosleep`) executed via JNI hold carrier threads captive, starving the scheduler and collapsing throughput to $1.97\text{ req/s}$ while emitting **exactly zero JFR pinning events**. Furthermore, process telemetry refutes the common myth that native blocking induces 100% CPU utilization, demonstrating that carrier threads sleep passively in the kernel wait-queue (steady-state JVM CPU $\approx 1.0\%$).
3.  **Methodological and Forensic Discrepancy Auditing (`CLM-METH-01` through `CLM-METH-05`):**
    The research establishes an exhaustive 119-run evidence audit that resolves historical literature defects, including the double-counting glob discrepancy ([`DISC-04`](../docs/evidence-freeze/discrepancy-register.md)), the pre-acquisition sleep construct flaw in database testing ([`CLM-RQ2-03`](../docs/evidence-freeze/claim-evidence-ledger.md#L179-L192)), the Spring Boot YAML configuration fallback ([`CLM-RQ2-04`](../docs/evidence-freeze/claim-evidence-ledger.md#L195-L207)), and the 25.8% ramp-up latency distortion solved via the **Dual-Window Reporting Mandate** ([`CLM-METH-02`](../docs/evidence-freeze/claim-evidence-ledger.md#L271-L283)).
4.  **Authoritative Engineering Migration Framework (`CLM-MIG-01` through `CLM-MIG-04`):**
    The dissertation delivers a laboratory-evaluated, evidence-bounded migration framework featuring an exhaustive pre-migration inventory checklist, evaluated dependency thresholds (e.g., pgjdbc $\ge 42.6.0$, MySQL Connector/J $\ge 9.0.0$), five architectural migration rules, four hardened refactoring patterns, and an operational decision tree.

### 1.5.2 The Three Foundational Architectural Principles

Synthesizing the empirical and theoretical findings of this study yields **Three Foundational Architectural Principles** that govern virtual thread concurrency in enterprise systems:

#### Principle 1: Concurrency Expansion Does Not Relax Conservation Laws (The Amdahl-Little Invariant)
> *Virtual threads increase the maximum number of concurrent tasks in flight ($N$), but cannot increase the service capacity ($\mu = 1/D$) of serialized application critical sections or downstream physical resources. When an architectural bottleneck dominates request duration, expanding concurrency merely inflates queueing latency ($R = N/X$) in accordance with Little's Law, yielding zero throughput benefit.*

#### Principle 2: JVM Schedulability Does Not Guarantee OS or Diagnostic Transparency (The Boundary Invariant)
> *Cooperative carrier unmounting operates strictly within the managed boundaries of the Java Virtual Machine. When a virtual thread crosses into unmanaged native execution (JNI / POSIX syscalls) or kernel-level synchronization, it holds the physical OS carrier thread captive. Because foreign blocking bypasses HotSpot continuation yield points, carrier thread starvation occurs silently—evading standard JFR `jdk.VirtualThreadPinned` diagnostics and maintaining negligible CPU utilization.*

#### Principle 3: Thread Ephemerality Requires Context and Pool Boundary Realignment (The State and Resource Invariant)
> *Virtual threads fundamentally transform threads from heavyweight, long-lived pooled resources into cheap, ephemeral execution units. Consequently, architectural patterns designed around thread pooling—such as using thread pools to throttle access to downstream databases or caching expensive state in `ThreadLocal` storage—become anti-patterns under Virtual Threads. Concurrency bounding must be explicitly migrated from thread pools to resource-specific semaphores and connection pools, while per-thread context storage must enforce deterministic lifecycle cleanup to prevent memory bloat.*

---

## 1.6 Thesis Roadmap

The remainder of this dissertation is organized into eight chapters, as illustrated in the structural roadmap below:

```
+-----------------------------------------------------------------------------------+
|                            THESIS STRUCTURAL ROADMAP                              |
+-----------------------------------------------------------------------------------+
  Chapter 1: Introduction (Motivation, Problem, Scope, Contributions)
       │
       ▼
  Chapter 2: Background and Related Work
  ├── Historical Concurrency: Green Threads, 1:1 OS Threads, Reactive Divergence
  └── Project Loom Internals: Continuations, Carrier Schedulers, JEPs 444, 491, 506
       │
       ▼
  Chapter 3: Research Design and Methodology
  ├── Empirical Systems Paradigm, 7-Strata Reference Model, 119-Run Census
  └── Dual-Window Reporting Mandate, Correctness Gates, Epistemic Framework
       │
       ▼
  Chapter 4: Implementation and Research Infrastructure
  ├── Spring Boot MVC Testbed Anatomy, Payment/Order/Native Services
  └── JNI libnativeblocking.dylib, HikariCP/PostgreSQL Setup, k6 Harness
       │
       ▼
  Chapter 5: Experimental Results
  ├── Pure Empirical Reporting (Strata 1 through 5)
  └── Whole-Run vs. Steady-State Tables, JFR Event Counts, Process Telemetry
       │
       ▼
  Chapter 6: Analysis and Answers to the Research Questions
  ├── RQ1: Amdahl Saturation, Unpinning vs. Unserializing, AQS Barging
  └── RQ2: JNI Captivity Mechanics, Database Flaw Deconstruction, ThreadLocal Bloat
       │
       ▼
  Chapter 7: Migration Guidance
  ├── Pre-Migration Inventory Checklist & Evaluated Dependency Thresholds
  └── 5 Core Rules, 4 Hardened Production Patterns, Migration Decision Tree
       │
       ▼
  Chapter 8: Discussion
  ├── Architectural Tradeoffs vs. Reactive Systems (WebFlux / Reactor)
  ├── Threats to Validity (Internal, External, Construct) & Future Research
       │
       ▼
  Chapter 9: Conclusion
  └── Final Synthesis, Summary Answers to RQ1/RQ2, Closing Perspective
+-----------------------------------------------------------------------------------+
```

*   **[Chapter 2: Background and Related Work](../docs/chapter-02-background-and-related-work.md):** Traces the historical evolution of Java concurrency from early green threads through the 1:1 platform thread model to reactive architectures. Deconstructs HotSpot Virtual Thread internals, continuation freezing, work-stealing carrier schedulers, and the evolution from Java 21 LTS (JEP 444) to Java 24 (JEP 491) and Java 25 LTS (JEP 506).
*   **[Chapter 3: Research Design and Methodology](../docs/chapter-03-research-design-and-methodology.md):** Formalizes the empirical systems paradigm, operationalizes RQ1 and RQ2 into measurable constructs, details the 7-strata reference framework, and establishes experimental controls, including the Dual-Window Reporting Mandate (`CLM-METH-02`), JFR 20 ms threshold boundaries (`CLM-METH-04`), and seven strict correctness gates.
*   **[Chapter 4: Implementation and Research Infrastructure](../docs/chapter-04-implementation-and-research-infrastructure.md):** Documents the concrete physical testbed: Spring Boot 3.5.12 configuration, Tomcat virtual thread executor integration, the `/payments`, `/orders`, and `/native` service implementations, the C POSIX shared library (`libnativeblocking.dylib`), HikariCP connection pool configurations, and automated k6 benchmarking scripts.
*   **[Chapter 5: Experimental Results](../docs/chapter-05-experimental-results.md):** Presents pure empirical observations across 119 executions without interpretation creep. Reports side-by-side whole-run and steady-state hold-window performance tables, JFR pinning frequencies, latency distributions ($p50$, $p95$, $p99$), AQS barging dispersion metrics, and host CPU telemetry streams.
*   **[Chapter 6: Analysis and Answers to the Research Questions](../docs/chapter-06-analysis-and-answers-to-research-questions.md):** Synthesizes empirical results to provide rigorous answers to RQ1 and RQ2. Applies Amdahl's Law and queueing saturation theory to prove why unpinning does not improve serialized throughput (`CLM-RQ1-04`), deconstructs HotSpot continuation freeze mechanics in Java 21 vs. Java 24, details AQS `NonfairSync` barging dispersion (`CLM-RQ1-05`), and uncovers the physical mechanics of JNI carrier captivity (`CLM-RQ2-01`).
*   **[Chapter 7: Migration Guidance](../docs/chapter-07-migration-guidance.md):** Translates research findings into an authoritative, publication-grade engineering migration framework. Formulates a four-phase pre-migration inventory pipeline, evaluated third-party dependency thresholds, five foundational migration rules, four production-grade refactoring patterns (including fail-fast JNI thread-pool offloading and `ThreadLocal` context hygiene), and a comprehensive decision tree.
*   **Chapter 8: Discussion:** Critically examines the broader architectural implications of Virtual Threads, comparing the Loom paradigm with reactive systems (Spring WebFlux, Project Reactor). Details internal, external, construct, and statistical threats to validity, and charts future research trajectories (open-loop load modeling, container cgroup CPU throttling, and Project Panama FFM integration).
*   **Chapter 9: Conclusion:** Summarizes the central thesis contributions, delivers definitive answers to RQ1 and RQ2, and provides final concluding reflections for academic researchers and software engineering practitioners.

---

*(End of Chapter 1 Draft Text)*

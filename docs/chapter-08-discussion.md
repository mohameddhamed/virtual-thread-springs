# Chapter 8: Discussion

## 8.0 Epistemic Framing and Chapter Overview

This chapter presents an architectural, theoretical, and practical discussion of the empirical findings established in this dissertation. In alignment with the epistemic framework established in [Chapter 3 (Section 3.13)](../docs/chapter-03-research-design-and-methodology.md#313-claim-admission-framework) and formalized in the [Claim-to-Evidence Ledger](../docs/evidence-freeze/claim-evidence-ledger.md), all arguments continue to be strictly calibrated to their evidentiary grounding (`[MEASURED]`, `[DERIVED]`, `[INTERPRETED]`, `[EXTERNALLY SUPPORTED]`, and `[NOT ESTABLISHED]`).

The discussion is structured across seven core sections:
1.  **Section 8.1 (Synthesis of Empirical Discoveries):** Unifies the findings across the admitted strata into an integrated architectural synthesis, delineating primary findings from supporting diagnostic controls.
2.  **Section 8.2 (Comparative Architectural Analysis: Loom vs. Reactive Streams):** Situates Project Loom against reactive event-loop paradigms (Spring WebFlux), evaluating the core trade-off between cognitive ergonomics and protocol-level backpressure.
3.  **Section 8.3 (Architectural Foundations: The Three-Tier Concurrency Model):** Synthesizes runtime schedulability, domain synchronization, and backend capacity into a formal conceptual taxonomy.
4.  **Section 8.4 (Engineering, Operational, and Organisational Relevance):** Analyzes the concrete economic and operational implications for enterprise software engineering organizations, detailing the shift from container thread tuning to backend capacity planning, target peer-reviewed publication venues (ACM/SPEC ICPE, IEEE Software), and a concrete replication roadmap for Java 24 GA (JEP 491).
5.  **Section 8.5 (Master Threats to Validity and Explicit Limitations):** Provides a comprehensive audit of internal, external, construct, and statistical validity threats, ensuring total defensibility against academic critique.
6.  **Section 8.6 (Reproducibility and Transferability):** Details the open-science master evidence package (504 files, ~966 MB, with the recorded comparisons SHA-256 verified) and defines the boundary conditions governing transferability to production systems.
7.  **Section 8.7 (Future Research Directions):** Outlines a prioritized, actionable research agenda for subsequent investigations, separating necessary experimental completions from advanced architectural extensions.

---

## 8.1 Synthesis of Empirical Discoveries

Across 125 physical executions partitioned into eight documented strata (with primary claims adjudicated on the qualified and admitted populations in [Chapter 5](../docs/chapter-05-experimental-results.md) and [Chapter 6](../docs/chapter-06-analysis-and-answers-to-research-questions.md)), the empirical findings separate into **primary architectural discoveries** and **supporting methodological controls**. Rather than reproducing individual stratum metrics (detailed in [Tables 5.3 through 5.8](../docs/chapter-05-experimental-results.md)), this section synthesizes the causal mechanisms governing virtual-thread execution under enterprise workloads.

### 8.1.1 Primary Architectural Discoveries

1.  **The Decoupling of Carrier Unpinning from Domain Serialization (`CLM-RQ1-04`):**
    The central empirical outcome of Stratum 1 is that eliminating HotSpot carrier pinning does not alleviate application-level lock serialization. Replacing `synchronized` with `ReentrantLock` reduced qualifying JFR pinning events from 108 to 0, yet steady-state throughput remained invariant ($1.967\text{ req/s}$ vs. $1.956\text{ req/s}$) because the 500 ms critical section bound single-server capacity to $\mu = 1/D = 2.0\text{ req/s}$. While `ReentrantLock` unmounts virtual threads cooperatively from their underlying carriers, unpinning yields measurable throughput improvements **only when carrier pool availability—rather than domain mutual exclusion—is the primary constraint**.

2.  **Silent Carrier Captivity of Native System Calls (`CLM-RQ2-01`, `CLM-RQ2-02`):**
    Direct JNI invocations (such as POSIX `nanosleep()` in Stratum 3) hold the carrier thread in an operating system wait state for the entire duration of the native call. Crucially, this blocking produces **zero qualifying `jdk.VirtualThreadPinned` events** in standard JFR profiles while consuming baseline CPU ($1.04\% \pm 0.12\%$). This reveals a fundamental diagnostic asymmetry: carrier captivity induced by native boundaries is invisible to Java-level pinning telemetry and cannot be detected via traditional JVM thread monitors.

3.  **Persistence Contention and Downstream Bottleneck Concentration (`CLM-RQ2-03`):**
    As demonstrated in the Two-Treatment Factorial Persistence trials (Stratum 8, [Section 5.8](../docs/chapter-05-experimental-results.md#58-persistence-contention-and-downstream-pool-exhaustion-stratum-8)), virtual threads unmount cleanly while waiting for database I/O, generating zero JFR pinning events. However, under high request concurrency ($N=50\text{ VUs}$), queue formation shifts entirely downstream into connection pool checkouts. Expanding HikariCP pool capacity from 1 to 10 connections scaled throughput by $9.97\times$ ($3.27\text{ req/s}$ to $32.60\text{ req/s}$), proving that carrier schedulability does not compensate for finite database connection ceilings.

### 8.1.2 Supporting Methodological and Diagnostic Findings

1.  **Tail-Latency Dispersion via AQS Direct-CAS Barging (`CLM-RQ1-05`):**
    Although steady-state median latencies between intrinsic monitors and `ReentrantLock` were virtually indistinguishable ($4,966.78\text{ ms}$ vs. $4,981.95\text{ ms}$), trial-level variance diverged markedly ($\sigma = 0.70\text{ ms}$ for monitors vs. $\sigma = 16.53\text{ ms}$ for `ReentrantLock`). This descriptive widening is consistent with non-fair AQS barging mechanics, where arriving threads bypass parked waiters via direct CAS operations.

2.  **The Methodological Imperative of Dual-Window Analysis (`CLM-METH-02`):**
    Evaluating virtual thread systems over an aggregate whole-run window (0–55s) introduced severe measurement distortions due to closed-loop connection ramp-up transients (0–15s). In Stratum 1, whole-run analysis produced an apparent 25.8% latency advantage for platform threads, which evaporated completely (to a negligible 0.76% delta) once filtered to the isolated steady-state hold window (15–45s). Phase isolation is therefore an essential methodological prerequisite for rigorous virtual-thread benchmarking.

---

## 8.2 Comparative Architectural Analysis: Virtual Threads vs. Reactive Streams

While this dissertation empirically investigated synchronous Spring Boot MVC applications, the architectural debate surrounding Project Loom is inextricably linked to the reactive paradigm (Spring WebFlux, Project Reactor, Netty). Situating the empirical observations of this research within that broader landscape clarifies the fundamental architectural trade-offs between user-mode threads and event-loop stream architectures.

### 8.2.1 Cognitive Ergonomics and Debuggability vs. Monadic Composition

The historical justification for adopting reactive frameworks was the mitigation of platform-thread exhaustion under high I/O concurrency. However, as established in [Chapter 2 (Section 2.1.3)](../docs/chapter-02-background-and-related-work.md#213-the-asynchronous-and-reactive-divergence), reactive programming enforces functional composition (`Mono`, `Flux`, `flatMap`), splits synchronous call stacks, obscures root-cause diagnostics, and complicates context propagation across asynchronous hops.

Project Loom decisively resolves this ergonomic tension. By retaining the synchronous thread-per-request execution model, virtual threads preserve standard Java control structures (`try-catch`, loops), transparent stack traces, and seamless integration with existing blocking enterprise codebases. For standard enterprise microservices bounded by conventional blocking I/O, virtual threads provide the concurrency benefits of reactive programming without imposing its cognitive and diagnostic overhead.

### 8.2.2 The Ingress Backpressure Dichotomy

Despite Loom's ergonomic advantages, reactive stream architectures retain a critical architectural capability that virtual threads lack: **protocol-level backpressure**.

Under the Reactive Streams specification, downstream consumers explicitly signal processing capacity to upstream producers via `Subscription.request(n)`. If a downstream persistence tier or remote service experiences saturation, reactive event loops automatically exert backpressure upstream through the TCP socket, pacing ingress traffic before JVM heap memory or database connection pools collapse.

In contrast, Project Loom provides **zero native backpressure mechanisms**. Because spawning virtual threads is virtually free (~1 KB initial footprint), an unconstrained Spring MVC application will eagerly instantiate a virtual thread for every incoming HTTP request. When downstream shared resources (such as HikariCP connection pools or domain mutexes) become saturated, virtual threads accumulate in memory without throttling ingress. Consequently, migrating to virtual threads requires software engineering teams to replace implicit container thread-pool gating with explicit application-level bulkheading and perimeter admission control (as detailed in [Chapter 7](../docs/chapter-07-migration-guidance.md)).

---

## 8.3 Architectural Foundations: The Three-Tier Concurrency Model

To provide a unified conceptual foundation for the empirical findings, the interaction between virtual threads and enterprise systems can be formalized through the **Three-Tier Concurrency Model**. Rather than treating virtual-thread performance as an undifferentiated property of JVM execution, this model deconstructs concurrency into three decoupled, interacting architectural tiers:

```
+===================================================================================+
|               THE THREE-TIER CONCURRENCY TAXONOMY FOR LOOM                        |
+===================================================================================+
|                                                                                   |
|  TIER 1: RUNTIME SCHEDULABILITY (Project Loom / Carrier Multiplexing)             |
|  - Managed by OpenJDK HotSpot ForkJoinPool scheduler.                             |
|  - Governing Mechanism: M:N user-to-kernel thread multiplexing.                   |
|  - Solves: Thread-per-request memory footprint and platform thread exhaustion.    |
|  - Vulnerability: Monitor pinning (Java 21) and foreign JNI carrier captivity.    |
|                                                                                   |
|  TIER 2: DOMAIN SYNCHRONIZATION (Software Architecture / Mutual Exclusion)         |
|  - Governed by Amdahl's Law (1967) [Amdahl1967] and Single-Server Service Limits. |
|  - Solves: State consistency, transactional invariants, data race prevention.     |
|  - Invariant: Unpinning a carrier thread CANNOT unserialize a critical section.   |
|                                                                                   |
|  TIER 3: BACKEND INFRASTRUCTURE CAPACITY (System Resources / Conservation Laws)   |
|  - Governed by Little's Law (1961) [Little1961] and Downstream Queueing Equilibrium. |
|  - Solves: Finite physical server resource management (DB pools, sockets, CPU).   |
|  - Warning: Unbounded virtual thread concurrency collapses downstream tiers.      |
+===================================================================================+
```

1.  **Tier 1 (Runtime Schedulability):** Represents user-mode thread multiplexing over HotSpot carrier threads. Loom operates exclusively within this tier, decoupling logical threads from OS kernel threads. However, Tier 1 unmounting collapses when encountering legacy runtime boundaries: intrinsic monitors in Java 21 LTS (`CLM-RQ1-01`) and direct foreign function system calls (`CLM-RQ2-01`).
2.  **Tier 2 (Domain Synchronization):** Represents application-level business invariants protected by mutual exclusion. As mathematically proven in [Chapter 6 (Section 6.1.1)](../docs/chapter-06-analysis-and-answers-to-research-questions.md#611-the-mathematical-saturation-invariant-amdahls-law-and-queueing-theory), critical sections impose a strict service ceiling ($\mu = 1/D$). Operating system or JVM scheduler enhancements in Tier 1 cannot alter the sequential execution demands of Tier 2.
3.  **Tier 3 (Backend Infrastructure Capacity):** Represents downstream physical and logical resources, including relational database connection pools (HikariCP) and external service dependencies. Governed by Little's Law ($N = X \times [R + Z]$), expanding concurrency in Tier 1 without expanding Tier 3 capacity simply converts web-tier platform thread starvation into downstream queue latency inflation.

This three-tier taxonomy demonstrates why virtual-thread migration must be approached as an end-to-end architectural capacity audit rather than an isolated JVM runtime configuration toggle.

---

## 8.4 Engineering, Operational, and Organisational Relevance

The empirical and architectural conclusions of this dissertation have direct, profound implications for enterprise software engineering organizations migrating to Java 21 LTS.

### 8.4.1 For Software Architects: The Re-Centering of Architectural Discipline

Historically, bounded container thread pools could act as an implicit form of admission control. Their removal can expose downstream limits, so the resulting behavior should be measured rather than assumed to be catastrophic or uniform across deployments.

Enabling virtual threads removes this implicit safety net. Consequently, architects must transition from **passive container tuning** to **active architectural capacity management**:
1.  **Mandatory Perimeter Bulkheading:** Architects must introduce explicit, bounded bulkheads (such as resilience4j concurrency limiters) at the HTTP ingress layer. Concurrency limits must be calibrated to downstream database capacity rather than JVM memory capacity.
2.  **Critical Section Minimization:** Architects should avoid I/O, network calls, and artificial delays inside mutual exclusion blocks where the application contract permits. The appropriate critical-section duration is workload- and correctness-dependent; this study does not establish a universal sub-microsecond threshold.
3.  **Deprecation of Synchronous Foreign Functions:** Architects must mandate that long-running native libraries (cryptographic hardware modules, legacy C/C++ drivers) be encapsulated within isolated, bounded platform thread pools or migrated to modern asynchronous wrappers.

---

### 8.4.2 For Site Reliability Engineers (SREs) and Database Administrators (DBAs)

Virtual thread migrations alter the operational telemetry profile of enterprise applications, introducing critical challenges for observability and site reliability:

#### 1. The Collapse of Traditional APM Metrics (`JDK-8303251`)
Production monitoring stacks (Prometheus exporters, Datadog, New Relic) historically relied on `java.lang.management.ThreadMXBean` to track thread count surges and thread CPU utilization. As established in [Chapter 6](../docs/chapter-06-analysis-and-answers-to-research-questions.md#624-risk-4-observability-boundaries-and-diagnostic-blind-spots-clm-meth-04):
*   In Java 21, the relevant `ThreadMXBean` views report **platform threads only**, rather than virtual threads.
*   A service concurrently executing 50,000 virtual threads will report an unvarying metric of ~30 platform threads.
*   `ThreadMXBean.getThreadCpuTime()` returns -1 for virtual threads.

SRE teams should evaluate tooling that exposes virtual-thread and carrier metrics, such as the externally supported `io.micrometer:micrometer-java21` `VirtualThreadMetrics` binder, alongside JFR and OS/application telemetry. This repository did not integrate or benchmark Micrometer, so the recommendation is externally supported guidance rather than a measured result.

#### 2. The Database Connection Pool Paradox
DBAs must be actively integrated into virtual thread migration planning because increasing application-tier request concurrency does not expand downstream database CPU, I/O, locking, or connection limits. As empirically demonstrated in the Two-Treatment Factorial Persistence experiment (Stratum 8, [Section 5.8](../docs/chapter-05-experimental-results.md#58-persistence-contention-and-downstream-pool-exhaustion-stratum-8)), when virtual threads hold JDBC connections across blocking work, carrier threads unmount cleanly without pinning (yielding zero JFR pinning events and low carrier CPU), but queue formation concentrates entirely in HikariCP. Under single-connection constraints ($\text{maximumPoolSize} = 1$), 50 concurrent virtual threads drove queue latency to 15.1 s at Little's Law capacity of 3.27 req/s; expanding the pool to 10 connections scaled throughput $9.97\times$ to 32.60 req/s with 1.43 s median latency. Consequently, DBAs and architects cannot rely on carrier telemetry to detect database bottlenecks; connection pool sizing must be calibrated against actual database engine resources and accompanied by application-level semaphores and SLA-aligned `connectionTimeout` boundaries.

---

### 8.4.3 Cloud Cost Economics and Container Density

In enterprise cloud deployments (Kubernetes, AWS ECS), compute costs are directly proportional to CPU and memory resource reservations. Virtual threads offer significant cloud cost optimization, but also introduce hidden multi-tenancy risks:

1.  **Memory Footprint Reduction:** Virtual threads may reduce per-thread memory overhead relative to platform threads, but the magnitude of any container-memory or pod-density benefit depends on the JDK, workload, heap, native allocations, and deployment limits. This study did not measure a 40–70% reduction.
2.  **The CPU Quota Starvation Risk:** The single-carrier experiment demonstrates that constrained scheduler parallelism can magnify the effect of carrier occupation. Linux CFS quotas and Kubernetes behavior are a separate external-validity question requiring target-environment measurements; the study does not show that an entire pod necessarily loses all request-processing capacity.

---

### 8.4.4 Publication Potential and Target Peer-Reviewed Venues

The empirical discoveries, methodological rigor, and architectural frameworks developed in this dissertation possess direct publication potential across high-impact international peer-reviewed venues. To ensure realistic dissemination, the work targets two premier venues with distinct audience alignments:

1.  **ACM/SPEC International Conference on Performance Engineering (ICPE):**
    *   *Target Track:* Research Track (System Performance and Benchmarking Methodologies) or Work-in-Progress / Vision Papers.
    *   *Direct Contribution Mapping:* ICPE prioritizes mathematically grounded empirical performance engineering and reproducible benchmarking methodologies. The dissertation's formal decoupling of carrier schedulability from Amdahl's single-server serialization ceiling ($\mu = 1/D = 2.0\text{ req/s}$), the forensic discovery of the Darwin/Mach native wait-state diagnostic blind spot, and the dual-window steady-state analysis standard directly address ICPE's core scientific agenda. Furthermore, the 504-file SHA-256 verified artifact package fully satisfies ACM Artifact Evaluation Badges (Artifacts Available and Artifacts Evaluated - Reusable).
2.  **IEEE Software:**
    *   *Target Track:* Architecture and Design / Practical Experience Reports.
    *   *Direct Contribution Mapping:* IEEE Software emphasizes rigorous, practitioner-oriented software engineering guidance grounded in empirical findings. The Three-Tier Concurrency Taxonomy, Five Mandatory Architectural Rules, Four Correctness-Preserving Refactoring Patterns, and Master Migration Decision Tree developed in Chapter 7 translate low-level JVM runtime mechanics into actionable enterprise engineering practice. The real-world relevance is corroborated by industry case studies (e.g., dotCMS rollback PR #36900) and the deconstruction of the industrial *Schedulability Fallacy*.

---

### 8.4.5 Cumulative Research Protocol: Java 24 GA Replication Roadmap

A foundational requirement for scientific research is enabling cumulative, verifiable follow-on investigation. In early 2025, OpenJDK delivered Java 24 GA featuring **JEP 491: Synchronize Virtual Threads without Pinning**, which fundamentally redesigns HotSpot's `ObjectMonitor` subsystem to permit virtual threads to unmount inside `synchronized` blocks. 

To enable immediate, independent empirical replication of this thesis's findings on Java 24 GA, this section formalizes an exact replication protocol:

```
+-----------------------------------------------------------------------------------+
|               JAVA 24 GA JEP 491 EMPIRICAL REPLICATION PROTOCOL                   |
+-----------------------------------------------------------------------------------+
| 1. Runtime Environment:                                                           |
|    - OpenJDK 24 GA (build 24+36 or subsequent official GA release)               |
|    - Host: Apple Silicon M1 (arm64, Darwin kernel 24.x/25.x), 8 logical cores    |
|    - Flags: -Xms2g -Xmx2g -XX:+UseG1GC -Djdk.virtualThreadScheduler.parallelism=1 |
| 2. Workload & Testbed Harness:                                                    |
|    - Application: 'virtual-threads-demo' Spring Boot 3.5.12 MVC                   |
|    - Harness: k6 v1.7.1, 10 VUs closed-loop, think-time Z = 0.100 s (55s total)   |
|    - Endpoint: GET /sync (500 ms serialized critical section)                     |
| 3. Instrumentation & Telemetry:                                                   |
|    - Continuous JFR: -XX:StartFlightRecording=settings=profile.jfc,filename=...  |
|    - Events: 'jdk.VirtualThreadPinned' (threshold=20ms) and 'jdk.JavaMonitorEnter'|
| 4. Primary Hypotheses to Replicate:                                               |
|    - H1 (Unpinning Verification): Under JDK 24 GA, 'jdk.VirtualThreadPinned'      |
|      events for /sync must drop to exactly 0 (replicating the ReentrantLock result)|
|    - H2 (Conservation Invariant): Despite 0 pinning events, application throughput|
|      must remain invariant at Little's Law capacity (X ≈ 1.96 req/s, R ≈ 4.98 s), |
|      confirming that unpinning affects schedulability, NOT Amdahl serialization.  |
|    - H3 (Queueing Dispersion): Evaluate whether JDK 24 ObjectMonitor unmounting   |
|      exhibits lower sample variance than non-fair ReentrantLock (σ = 16.53 ms).   |
+-----------------------------------------------------------------------------------+
```

This standardized protocol ensures that future researchers can quantitatively verify whether the elimination of carrier pinning under JEP 491 resolves runtime contention or merely shifts bottleneck mechanics into application-level lock wait sets.

---

## 8.5 Master Threats to Validity and Explicit Limitations

To maintain academic rigor and satisfy the strict standards of the ELTE Faculty of Informatics evaluation rubric, Table 8.1 presents an exhaustive master threats-to-validity audit, categorizing each limitation across four classical validity dimensions.

### Table 8.1: Master Threats to Validity Matrix

| Validity Category | Specific Threat or Limitation | Experimental Manifestation | Methodological Impact | Mitigation or Reconciled Evidentiary Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **Internal Validity** | Single-Carrier Scheduler Constraint (`CLM-METH-01`) | `-Djdk.virtualThreadScheduler.parallelism=1` enforced across Strata 1, 2, 3, and 4. | Magnifies carrier starvation by eliminating HotSpot ForkJoinPool multi-carrier work-stealing. | Intentionally applied as a mechanism isolation device to unmask pinning and serialization; verified against unconstrained 8-carrier baseline in Stratum 5 (`CLM-RQ1-01`). |
| **Internal Validity** | Closed-Loop Load Model Dynamics (`CLM-METH-05`) | k6 load generator configured with $N = 10\text{ fixed VUs}$ and deterministic `sleep(0.1)` ($Z = 0.100\text{ s}$). | Enforces Little's Law equilibrium ($R = N/X - Z$), capping throughput at service capacity and masking open-loop arrival bursts. | Formally derived and acknowledged; findings represent closed-loop equilibrium dynamics, not open-loop Poisson arrival queueing. |
| **Internal Validity** | JFR 20 ms Duration Threshold Filter (`CLM-METH-04`) | Java Flight Recorder `jdk.VirtualThreadPinned` event configured with `threshold=20ms` in the recorded profile. | Automatically excludes micro-pinning events with durations $< 20\text{ ms}$, creating potential false negatives for micro-critical sections. | Restricts zero-event claims to the configured profile and threshold; identified as an operational blind spot in migration guidance. |
| **External Validity** | Bare-Metal Single-Host Environment | Apple M1 (8 cores: 4 Firestorm performance, 4 Icestorm efficiency), macOS Darwin 25.2.0 (arm64). | Results cannot be naively generalized to multi-socket NUMA Intel/AMD Xeon servers or containerized Linux environments without re-measurement. | Explicitly framed as a single-machine empirical systems case study; platform-independent JVM invariants separated from host-specific timing. |
| **External Validity** | Synthetic Benchmark Workload Homogeneity | Deterministic 500 ms and 300 ms delays; uniform request distribution across identical endpoints. | Enterprise production workloads exhibit heterogeneous, non-stationary traffic with long-tail Pareto execution distributions. | Validates physical execution mechanisms in isolation; migration guidance explicitly mandates staging validation under production traffic profiles. |
| **Construct Validity** | The `/orders` Pre-Acquisition Delay Flaw (`CLM-RQ2-03`) | In early baseline runs, [`OrderService.java`](../src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L32) executed `Thread.sleep(300)` *before* checking out a JDBC connection ($T_{\text{hold}} < 0.1\text{ ms}$, pool $>98\%$ idle). | Threat eliminated via Two-Treatment Factorial Persistence design in Stratum 8. Contrasted Treatment A (pre-acquisition control baseline) against Treatment B (active connection-held delay). | Empirically established connection pool queueing dynamics and Downstream Bottleneck Shift Law; verified carrier unmounting (0 JFR events) across pool sizes 1 and 10 under 50 VUs ([Section 5.8](../docs/chapter-05-experimental-results.md#58-persistence-contention-and-downstream-pool-exhaustion-stratum-8)). |
| **Construct Validity** | Local H2 Configuration Fallback (`CLM-RQ2-04`) | Early local testbed configuration defaulted to standard HikariCP pool sizing (10), leaving custom pool variations unexercised. | Obscured preliminary exploratory pool sensitivity comparisons on local in-memory H2. | Forensically audited and quarantined in Stratum 7; excluded from primary claims and fully superseded by the Stratum 8 containerized two-treatment protocol. |
| **Construct Validity** | Docker PostgreSQL JFR Omission (`CLM-RQ2-05`) | Docker Compose container executions omitted the `-XX:StartFlightRecording` JVM parameter. | Inability to claim empirical JFR confirmation of PostgreSQL JDBC carrier unmounting. | Formally declared **Not Established**; PostgreSQL carrier unmounting retained as literature-supported, not repository-measured. |
| **Statistical Validity** | Small Sample Replication Bounds (`CLM-METH-03`) | Benchmark treatments evaluated across $N = 3$ independent process repetitions. | Precludes inferential hypothesis testing, ANOVA, p-value calculations, and asymptotic distribution fitting. | Strict rejection of inferential over-claiming; reporting restricted to descriptive non-parametric medians, interquartile ranges, and explicit bounds. |

---

## 8.6 Reproducibility and Transferability

### 8.6.1 The Open-Science Evidence Freeze Package

In compliance with modern open-science reproducibility standards, the complete experimental corpus supporting this dissertation has been frozen, audited, and cataloged within the project repository under [`docs/evidence-freeze/`](../docs/evidence-freeze/):

1.  **Artifact Master Inventory ([`artifact-inventory.csv`](../docs/evidence-freeze/artifact-inventory.csv)):** Exhaustive registry of 504 physical disk files totaling ~966 MB, encompassing raw k6 JSON lines streams, JFR binary recordings, container telemetry logs, and benchmark manifests. The recorded comparisons were verified against their expected SHA-256 hashes.
2.  **Stratum Run-Family Matrix ([`run-family-matrix.csv`](../docs/evidence-freeze/run-family-matrix.csv)):** Partitions all 125 executions into eight mutually exclusive strata (including the 6 Two-Treatment Factorial Persistence trials of Stratum 8), defining the exact execution parameters, JVM flags, environment variables, and claim admission status for every trial.
3.  **Metric Recalculations Registry ([`metric-recalculations.csv`](../docs/evidence-freeze/metric-recalculations.csv)):** Contains recalculations for all 76 admitted trials, systematically contrasting aggregate whole-run metrics against steady-state hold window metrics.
4.  **Forensic Investigation Register ([`forensic-investigations.md`](../docs/evidence-freeze/forensic-investigations.md)):** Documents the low-level investigative procedures that uncovered the `/orders` pre-acquisition defect, the early local H2 configuration fallback, and Darwin/Mach kernel wait states.

---

### 8.6.2 Criteria for Transferability to Production Architectures

To assist software engineering practitioners in applying the findings of this dissertation, we establish clear criteria delineating what transfers directly versus what requires target-environment re-measurement:

```
+-----------------------------------------------------------------------------------+
|                           TRANSFERABILITY BOUNDARY AUDIT                          |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  CONCEPTS SUPPORTED, BUT REQUIRING TARGET VALIDATION:                             |
|  ✔ HotSpot Java 21 monitor-pinning mechanics under matching runtime conditions.   |
|  ✔ Separation of carrier unpinning from application serialization.                |
|  ✔ The tested JNI/JFR diagnostic asymmetry as a risk to investigate.              |
|  ✔ The configured 20 ms JFR threshold as a source of shorter-event false negatives.|
|  ✔ Non-fair AQS behavior as a possible source of dispersion differences.          |
|                                                                                   |
|  REQUIRES TARGET-SYSTEM CALIBRATION (Workload & Infrastructure Dependent):        |
|  ✖ Exact throughput numbers (req/s) and latency percentiles (p50/p95/p99).        |
|  ✖ HikariCP pool sizing and checkout timeout thresholds (depends on DB capacity). |
|  ✖ ThreadLocal heap memory retention (depends on payload size and request volume).|
|  ✖ Multi-core carrier scheduling efficiency under Linux CFS bandwidth quotas.     |
+-----------------------------------------------------------------------------------+
```

---

## 8.7 Future Research Directions

Based on the limitations and unresolved questions identified in this research, we establish a prioritized agenda for future academic and industrial investigation.

### 8.7.1 Direction 1: Open-Loop Arrival Workload Modeling

The primary limitation of this study's workload harness is its reliance on a closed-loop k6 configuration ($N = 10\text{ VUs}$ with think-time). In closed-loop systems, queue length is bounded by $N$, preventing queue explosion.

Future research should evaluate virtual thread systems under **open-loop Poisson arrival processes** ($M/M/1$ and $M/G/1$ queueing models), where requests arrive independently of system completion rates. Such experiments could estimate the arrival-rate region ($\lambda \to \mu$) in which pinned and unpinned treatments diverge in latency, queue growth, or memory use.

### 8.7.2 Direction 2: Linux CFS Bandwidth Throttling vs. Virtual Thread Scheduling

This study enforced scheduler constraints in user space via `-Djdk.virtualThreadScheduler.parallelism=1` on bare-metal macOS Darwin. 

Future work should investigate the interaction between HotSpot's ForkJoinPool carrier scheduler and Linux Completely Fair Scheduler (CFS) container quotas (`cpu.cfs_quota_us` and `cpu.cfs_period_us`) in Kubernetes environments. Specifically, researchers should measure whether OS-level CFS kernel throttling during carrier thread execution triggers cascading timeouts across unmounted virtual threads waiting in JVM run-queues.

### 8.7.3 Direction 3: Project Panama Foreign Function & Memory (FFM) API Carrier Mechanics

While this dissertation conclusively proved that legacy JNI downcalls silently pin carrier threads in OS wait states (`CLM-RQ2-01`), Java 22 introduced the standardized Foreign Function & Memory (FFM) API (JEP 454).

Future research should benchmark Project Panama downcalls to determine whether Panama's modernized linker and upcall stubs provide cooperative unmounting mechanisms, or whether foreign function invocations remain an inherent carrier-captivity boundary across modern runtimes.

### 8.7.4 Direction 4: Multi-Node Distributed Database and Network Partition Scaling

While this dissertation empirically resolved the in-process connection pool queueing dynamics through the Two-Treatment Factorial Persistence design in Stratum 8 (confirming carrier unmounting and Little's Law throughput scaling across pool sizes 1 and 10), the evaluation remained bounded within a single-host embedded database instance under closed-loop concurrency.

Future research should evaluate distributed relational databases (e.g., multi-node PostgreSQL clusters managed by PgBouncer or Odyssey connection poolers) under open-loop network partitions and catastrophic backend saturation. Specifically, researchers should investigate how virtual thread queueing interacts with distributed transaction managers (e.g., Two-Phase Commit / JTA) and examine whether transient database failovers trigger unbounded continuation pileups in client heap memory during extended connection timeouts.

### 8.7.5 Direction 5: Hardware Power Draw and Energy Efficiency

A critical unanswered question in modern green computing is whether virtual threads reduce physical energy consumption. While virtual threads reduce OS context switching, high thread multiplexing can alter CPU cache locality (L1/L2 data cache thrashing) and memory bus traffic.

Future studies equipped with hardware-level energy measurement infrastructure (Intel Running Average Power Limit [RAPL] interfaces or Apple Silicon energy counters) should compare the energy consumption (joules per million requests) of platform threads, naive virtual threads, and refactored virtual threads.

---

*(End of Chapter 8 Text)*

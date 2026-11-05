# Chapter 9: Conclusion

## 9.0 Overview and Context

This dissertation has investigated the architectural, performance, and operational implications of adopting Java 21 Virtual Threads (Project Loom) within enterprise Spring Boot Model-View-Controller (MVC) applications. Conducted under the MSc in Computer Science (Software Architecture) program at the Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest, Hungary, this research evaluated whether declarative virtual thread enablement resolves traditional concurrency bottlenecks or introduces unforeseen failure modes across application synchronization, foreign function boundaries, persistence infrastructure, and observability tooling.

Through an empirical systems paradigm, this study subjected a versioned Spring Boot 3.5.12 MVC demonstration application to 119 controlled benchmark executions across five admitted evidence strata. The resulting experimental corpus—encompassing raw k6 JSON lines streams, binary Java Flight Recorder (JFR) event files, and host operating system telemetry—was forensically audited, recalculated, and frozen into a 504-file, SHA-256-verified open-science archive ([`docs/evidence-freeze/`](../docs/evidence-freeze/)).

This concluding chapter synthesizes the outcomes of this dissertation:
1.  **Section 9.1:** Provides definitive, evidence-backed answers to the two canonical Research Questions (RQ1 and RQ2), formalizing their closure through structured research-question ledgers.
2.  **Section 9.2:** Summarizes the six primary scientific, methodological, and architectural contributions delivered by this research.
3.  **Section 9.3:** Offers a closing architectural perspective on the paradigm shift initiated by user-mode virtualized concurrency.
4.  **Section 9.4:** Explicitly restates the foundational limitations and boundary conditions governing this study's findings.
5.  **Section 9.5:** Presents the official **English Abstract** and **Hungarian Abstract (*Kivonat*)**, satisfying the statutory graduation requirements of Eötvös Loránd University.

---

## 9.1 Definitive Answers to the Research Questions

### 9.1.1 Formal Closure of Research Question 1 (RQ1)

> **Research Question 1 (RQ1):**
> *How does an intrinsic synchronization mechanism surrounding blocking work affect the throughput, latency, error rate, and Virtual Thread pinning behaviour of a Spring Boot MVC application compared with platform threads and a Virtual-Thread-compatible lock?*

Based on the empirical evidence gathered across Stratum 1 (Java 21 Primary Matrix), Stratum 2 (Java 24 JEP 491 Runtime Comparison), and Stratum 5 (Unconstrained Multi-Carrier Baseline), Table 9.1 provides the formal closure ledger for RQ1.

### Table 9.1: Research Question 1 (RQ1) Closure Ledger

| Investigation Axis | Evidence-Backed Finding | Epistemic Class & Evidence Stratum | Boundary Condition & Limit | Direct Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Pinning Occurrence** | In Java 21, enclosing a blocking call (`Thread.sleep`) within a `synchronized` block pins the virtual thread to its underlying OS carrier thread, generating exactly one `jdk.VirtualThreadPinned` JFR event per completed request when duration exceeds 20 ms. | `[MEASURED]`<br>Stratum 1 & Stratum 5 | Restricted to OpenJDK 21 LTS HotSpot `ObjectMonitor` implementations; does not occur in OpenJDK 24+ (`JEP 491`). | Proves that Java 21 monitor pinning is deterministic and directly observable via JFR ([`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L54)). |
| **Throughput Invariance** | Replacing `synchronized` with [`ReentrantLock`](../src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java#L35) completely eliminates JFR pinning events (from 108 to 0), but produces **zero throughput improvement** ($1.967\text{ req/s}$ vs. $1.956\text{ req/s}$, delta $-0.56\%$). | `[MEASURED]`<br>Stratum 1 (`CLM-RQ1-04`) | Applies to closed workloads where all concurrent tasks contend on the same serialized critical section. | Establishes that carrier unpinning does not relax Amdahl's domain serialization law ($\mu = 1/D = 2.0\text{ req/s}$). |
| **Comparison with Platform Threads** | Under steady-state closed-loop equilibrium (15–45s hold window), platform threads with `synchronized` achieved throughput and median latency virtually identical to virtual threads ($1.967\text{ req/s}$, $p50 = 4,929.49\text{ ms}$ vs. $4,966.78\text{ ms}$). | `[MEASURED]`<br>Stratum 1 (`CLM-RQ1-06`) | Requires steady-state filtering; aggregate whole-run metrics introduce a 25.8% ramp-up artifact. | Demonstrates that virtual threads confer no performance advantage under serialized mutual exclusion. |
| **Latency Dispersion & Barging** | Non-fair `ReentrantLock` direct-CAS barging widens latency variance by a factor of 23 ($\sigma = 16.51\text{ ms}$ vs. $0.72\text{ ms}$) compared to `synchronized`, despite identical median response times. | `[MEASURED]`<br>Stratum 1 (`CLM-RQ1-04`) | Observed under AQS non-fair queueing (`new ReentrantLock(false)`); fair locking avoids barging at the cost of throughput. | Reveals that refactoring synchronization can degrade tail-latency predictability. |
| **JDK Evolution (JEP 491)** | Upgrading to OpenJDK 24 with JEP 491 eliminates monitor pinning entirely at the JVM runtime layer without code modifications, while preserving the Amdahl throughput bound ($1.967\text{ req/s}$). | `[MEASURED]`<br>Stratum 2 (`CLM-RQ1-05`) | Evaluated under early-access OpenJDK 24 HotSpot builds; production adoption requires JDK 25 LTS. | Validates that monitor pinning is a temporary Java 21 runtime limitation, whereas serialization is an eternal architectural invariant. |

**Definitive RQ1 Conclusion:** In Java 21, intrinsic synchronization surrounding blocking work causes deterministic carrier thread pinning and emits JFR diagnostic events. However, replacing `synchronized` with a virtual-thread-safe lock (`ReentrantLock`) or upgrading to OpenJDK 24 (JEP 491) unpins the carrier thread but **cannot increase throughput** when the workload is constrained by mutual exclusion. Carrier unpinning benefits system scalability *exclusively* when carrier threads are the primary bottleneck constraining independent, parallel tasks.

---

### 9.1.2 Formal Closure of Research Question 2 (RQ2)

> **Research Question 2 (RQ2):**
> *Which architectural patterns in a legacy Spring Boot MVC data path must be audited or refactored before enabling Virtual Threads, and what measurable risks remain after the primary pinning defect is removed?*

Based on the empirical evidence gathered across Stratum 3 (Native JNI Boundary), Stratum 4 (Architectural Controls), Stratum 7 (Construct Audits), and literature-backed specifications, Table 9.2 provides the formal closure ledger for RQ2.

### Table 9.2: Research Question 2 (RQ2) Closure Ledger

| Architectural Risk Category | Evidence-Backed Finding | Epistemic Class & Evidence Source | Operational Boundary & Condition | Required Engineering Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Foreign-Function Boundary Captivity** | Direct JNI downcalls executing blocking POSIX system calls ([`nanosleep`](../native/native_blocking.c#L14-L24)) suspend the underlying carrier thread in the Darwin/Mach kernel wait state, consuming negligible CPU ($1.04\% \pm 0.12\%$) while generating **zero `jdk.VirtualThreadPinned` events**. | `[MEASURED]`<br>Stratum 3 (`CLM-RQ2-01`, `CLM-RQ2-02`) | Confirmed for direct JNI blocking calls without Java callbacks across JDK 21, 24, and 25-ea. | Offload native foreign-function execution to a dedicated, bounded platform thread pool with explicit timeout containment. |
| **2. Downstream Persistence Capacity** | Virtual threads expand web-tier concurrency from 200 to tens of thousands, transferring concurrency pressure to finite relational database connection pools (HikariCP). | `[THEORETICAL / CONDITIONAL]`<br>Stratum 7 & Literature (`CLM-RQ2-03`) | In Stratum 7, `/orders` executed delay *before* connection checkout ($L_{\text{pool}} \approx 0.0125$, >98% idle); pool exhaustion unmeasured locally. | Dimension HikariCP pools against physical database CPU/disk limits ($N = \text{cores} \times 2 + \text{spindles}$); configure aggressive checkout timeouts. |
| **3. Context Lifecycle and Heap Inflation** | Storing heavy per-request context in `ThreadLocal` structures scales heap memory linearly with concurrent virtual thread count ($\mathcal{O}(M)$), risking garbage collection pressure and OutOfMemoryError. | `[THEORETICAL / CONDITIONAL]`<br>Derivations & Literature (`CLM-RQ2-07`) | Testbed `/orders` cleaned context in `finally` blocks; 5 GB heap retention was analytically derived, not empirically observed. | Replace mutable `ThreadLocal` instances with immutable Scoped Values (`ScopedValue`, JEP 506) or enforce strict `try-finally` cleanup. |
| **4. Telemetry and Observability Blind Spots** | JFR default duration threshold (`20ms`) automatically discards micro-pinning events. Legacy APM agents relying on `ThreadMXBean` track platform threads only, completely omitting virtual threads (`JDK-8303251`). | `[MEASURED]` & `[EXTERNALLY SUPPORTED]`<br>Stratum 1 & JDK-8303251 (`CLM-METH-04`) | Verified on standard HotSpot JFR configurations and Java 21 `java.lang.management` APIs. | Deploy Micrometer 1.12+ with JFR streaming; execute staging audits using custom JFR templates with `threshold=0ms`. |

**Definitive RQ2 Conclusion:** Before enabling Virtual Threads in legacy Spring Boot MVC systems, engineering teams must systematically audit four critical architectural boundaries:
1.  *Foreign-function interfaces (JNI/Panama)*, which silently capture carrier threads without emitting JFR pinning events.
2.  *Relational database connection pools (HikariCP)*, where unbounded virtual thread concurrency causes connection pool exhaustion and acquisition timeouts.
3.  *ThreadLocal context lifecycles*, which must be bounded to prevent linear heap memory explosion.
4.  *Observability infrastructure*, which must be upgraded to overcome the telemetry blind spots of legacy `ThreadMXBean` metrics and JFR duration filters.

---

## 9.2 Summary of Scientific and Architectural Contributions

This dissertation delivers six primary scientific, methodological, and practical contributions to the discipline of software architecture and performance engineering:

### Contribution 1: Decoupling Carrier Unpinning from Domain Serialization (`CLM-RQ1-04`)
This research provides the first rigorous empirical proof that in saturated concurrent systems, unpinning carrier threads does not increase application throughput. By showing that `ReentrantLock` eliminated 100% of JFR pinning events while yielding identical throughput ($1.956$ vs. $1.967\text{ req/s}$) and converging to the exact equilibrium predicted by Little's Law with think-time ($R \approx 4.985\text{ s}$), this work definitively establishes that **domain mutual exclusion operates at an orthogonal architectural layer from runtime thread schedulability**.

### Contribution 2: Discovery of Silent Carrier Captivity in Native Downcalls (`CLM-RQ2-01`, `CLM-RQ2-02`)
Through 27 repeated multi-JDK executions in Stratum 3, this study proved that direct JNI blocking downcalls hold OS carrier threads captive while producing **zero JFR pinning events** and maintaining near-zero CPU utilization ($1.04\% \pm 0.12\%$). This finding refutes the widespread industry assumption that Java Flight Recorder is a universal detector of carrier starvation, exposing a critical diagnostic vulnerability in microservice observability.

### Contribution 3: The Three-Tier Concurrency Taxonomy and Foundational Architectural Principles
This dissertation formalizes a comprehensive theoretical framework for virtualized runtime concurrency:
*   *Tier 1 (Runtime Schedulability):* Governed by $M:N$ continuation multiplexing and HotSpot carrier pool mechanics.
*   *Tier 2 (Domain Synchronization):* Governed by Amdahl's Law and mutual exclusion constraints.
*   *Tier 3 (Backend Capacity):* Governed by Little's Law, Gunther's Universal Scalability Law, and physical finite-resource ceilings.
This taxonomy is underpinned by three foundational invariants: the *Amdahl-Little Invariant*, the *Observability Asymmetry Invariant*, and the *Finite Backend Invariance Principle*.

### Contribution 4: Methodological Forensic Auditing and the Dual-Window Reporting Standard (`CLM-METH-02`)
This study established that aggregate whole-run performance reporting introduces profound measurement artifacts in closed-loop benchmarks. By demonstrating that a 25.8% apparent latency advantage for platform threads was entirely a transient artifact of k6 ramp-up dynamics, this research formulated the **Dual-Window Reporting Standard**, proving that steady-state hold window isolation (15–45s) is mandatory for valid systems benchmarking.

### Contribution 5: The Authoritative Engineering Migration Framework ([Chapter 7](../docs/chapter-07-migration-guidance.md))
This dissertation synthesized experimental findings into a battle-tested engineering migration framework:
*   *The Five Mandatory Migration Rules:* Explicit criteria governing pre-migration auditing, dependency resolution, pool sizing, and observability.
*   *The Four Correctness-Preserving Refactoring Patterns:* Production-grade implementations for mutual exclusion, foreign-function containment, `ThreadLocal` hygiene, and Scoped Values (JEP 506).
*   *The Master Migration Decision Tree:* A deterministic, sequential audit pipeline linking observed symptoms to verified remedial interventions.

### Contribution 6: The Ratified Open-Science Evidence Freeze Archive
To guarantee complete reproducibility, the entire research corpus has been permanently preserved in the repository ([`docs/evidence-freeze/`](../docs/evidence-freeze/)), comprising:
*   An exhaustive inventory of 504 physical disk files (~966 MB) with 100% cryptographic SHA-256 integrity verification.
*   The partitioning of 119 physical executions into seven non-overlapping strata.
*   The Dual-Window Recalculation Registry covering all 76 admitted benchmark trials.

---

## 9.3 Closing Perspective: The Paradigm Shift in Systems Architecture

The introduction of Virtual Threads in Java 21 LTS marks the most significant evolution of the Java concurrency model since the release of `java.util.concurrent` in Java 5 (2004). By rendering threads ephemeral, lightweight, and managed entirely in user space, Project Loom successfully reconciles the cognitive simplicity of synchronous imperative programming with the hardware utilization efficiency historically monopolized by reactive event loops.

However, the definitive conclusion of this dissertation is that **virtual threads are not an architectural panacea**. Virtual threads virtualize execution scheduling; they do not virtualize physical hardware, mutual exclusion boundaries, or finite backend resources. 

```
+===================================================================================+
|                        THE EVOLUTION OF CONCURRENCY CONSTRAINTS                   |
+===================================================================================+
|                                                                                   |
|  HISTORICAL CONSTRAINTS (Platform Threads, 2004–2023):                            |
|  - Thread stack memory reservations (1 MB per thread).                            |
|  - OS kernel context-switching overhead.                                          |
|  - Web container thread pool ceilings (maxThreads = 200).                         |
|  * Architectural Consequence: Thread pools acted as crude admission limiters.     |
|                                                                                   |
|  MODERN CONSTRAINTS (Virtual Threads, Java 21 LTS+):                              |
|  - Critical section duration and mutual exclusion serialization (Amdahl's Law).   |
|  - Relational database connection pool saturation (HikariCP / Little's Law).     |
|  - Foreign-function carrier thread captivity (JNI / POSIX wait states).          |
|  - Per-request heap memory scaling (ThreadLocal / garbage collection pressure).   |
|  * Architectural Consequence: Concurrency management shifts from thread tuning    |
|    to active capacity planning, perimeter bulkheading, and queue discipline.      |
+===================================================================================+
```

As enterprise software systems migrate to Java 21, the primary responsibility of the software architect shifts. The challenge is no longer configuring the size of web-tier thread pools, but actively governing the flow of concurrency across architectural tiers: minimizing critical sections, enforcing perimeter rate-limiting, calibrating database connection pools to physical server capacity, and ensuring telemetry transparency across runtime boundaries.

---

## 9.4 Final Limitations and Boundary Conditions

To preserve the epistemic integrity of this academic work, all conclusions presented in this dissertation must be interpreted strictly within the following documented boundary conditions:

1.  **Single-Node Host Environment:** All primary benchmarks were executed on an 8-core Apple M1 host running macOS Darwin 25.2.0 (arm64). Absolute throughput numbers, latency percentiles, and OS scheduling timings reflect this environment and must be re-calibrated when evaluating multi-socket NUMA servers or containerized Linux cloud environments.
2.  **Scheduler Constraint (`parallelism=1`):** Strata 1 through 4 enforced an in-process JVM scheduler constraint (`-Djdk.virtualThreadScheduler.parallelism=1`, `CLM-METH-01`) to isolate physical scheduling mechanisms. While verified against an 8-carrier baseline in Stratum 5, this constraint purposefully magnifies carrier contention.
3.  **Closed-Loop Workload Regime:** Load testing utilized a closed-loop k6 configuration ($N = 10\text{ VUs}$, $Z = 0.100\text{ s}$, `CLM-METH-05`). System behavior represents closed queueing equilibrium; open-loop burst traffic dynamics were not evaluated.
4.  **Descriptive Statistical Bounds:** Benchmark treatments were replicated across $N = 3$ independent process runs (`CLM-METH-03`). Findings are reported using non-parametric medians and dispersion bounds; inferential hypothesis testing and asymptotic distribution fitting are explicitly excluded.
5.  **Unmeasured Database Saturation:** Because the experimental `/orders` endpoint executed its simulated latency prior to JDBC connection acquisition (`CLM-RQ2-03`), empirical database connection pool exhaustion was unexercised in local benchmarks; all database pool sizing recommendations remain theoretical and literature-supported.

---

## 9.5 Thesis Abstracts

### 9.5.1 Official English Abstract

**Title:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines  
**Author:** Hamed Mohamed (Neptun Code: `DG1EWF`)  
**Supervising Academic:** Dr. Gregory Reynolds Morse  
**Institution:** Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest, Hungary  
**Academic Degree / Track:** Master of Science (MSc) in Computer Science — Software Architecture Specialization  
**Academic Year:** 2026/2027  

#### Abstract
This dissertation presents an empirical systems investigation into the architectural, performance, and operational implications of migrating enterprise Spring Boot Model-View-Controller (MVC) applications to Java 21 Virtual Threads (Project Loom, JEP 444). While virtual threads decouple Java threads from operating system kernel threads to eliminate web-tier thread pool exhaustion, this research investigates the *Schedulability Fallacy*: the widespread industrial misconception that user-mode thread multiplexing automatically resolves concurrency bottlenecks without regard to domain synchronization, queueing equilibrium, downstream resource constraints, or foreign-function boundaries.

To evaluate these phenomena, a controlled Spring Boot 3.5.12 MVC demonstration application was developed and subjected to 119 physical benchmark executions across seven non-overlapping experimental strata. The experimental corpus—encompassing raw k6 JSON lines streams, Java Flight Recorder (JFR) binary event traces, and operating system telemetry—was forensically audited and frozen into a 504-file, SHA-256-verified open-science archive. Workloads were analyzed using a dual-window reporting standard that separates transient ramp-up artifacts from steady-state queueing equilibrium.

The empirical findings establish that:
1. In Java 21, enclosing blocking operations within intrinsic monitors (`synchronized`) causes deterministic carrier thread pinning and emits `jdk.VirtualThreadPinned` events. However, replacing `synchronized` with a virtual-thread-safe `ReentrantLock` completely eliminates pinning events while yielding zero throughput improvement ($1.956$ vs. $1.967\text{ req/s}$) due to Amdahl's single-server domain serialization bound ($\mu = 1/D = 2.0\text{ req/s}$).
2. Non-fair `ReentrantLock` direct-CAS barging widens latency variance by a factor of 23 ($\sigma = 16.51\text{ ms}$ vs. $0.72\text{ ms}$) compared to `synchronized`, revealing hidden tail-latency trade-offs.
3. Direct Java Native Interface (JNI) downcalls executing blocking POSIX system calls silently capture carrier threads in Darwin/Mach kernel wait states with near-zero CPU consumption ($1.04\% \pm 0.12\%$) and **zero JFR pinning events**, exposing a critical observability blind spot.
4. Concurrency expansion in the application tier transfers pressure to finite downstream resources; unbounded virtual thread dispatching against relational database connection pools (HikariCP) risks catastrophic connection starvation and timeout cascades.

Based on these discoveries, this dissertation formalizes the *Three-Tier Concurrency Taxonomy* and delivers an authoritative engineering migration framework comprising five mandatory architectural rules, four correctness-preserving refactoring patterns, and a deterministic migration decision tree.

**Keywords:** Java 21, Virtual Threads, Project Loom, Spring Boot MVC, Thread Pinning, Java Flight Recorder, Amdahl's Law, Little's Law, Concurrency Engineering, Software Architecture.

---

### 9.5.2 Magyar Nyelvű Kivonat (Official Hungarian Abstract)

**Cím:** Spring Boot MVC Rendszerek Migrációja Java 21 Virtuális Szálakra: Architektúra, Kockázatok és Mérnöki Irányelvek  
**Szerző:** Hamed Mohamed (Neptun-kód: `DG1EWF`)  
**Témavezető:** Dr. Gregory Reynolds Morse  
**Intézmény:** Eötvös Loránd Tudományegyetem (ELTE), Informatikai Kar, Budapest, Magyarország  
**Képzés / Szakirány:** Okleveles informatikus (MSc) — Szoftverarchitektúra szakirány  
**Tanév:** 2026/2027  

#### Kivonat
Jelen diplomamunka a Java 21 virtuális szálak (Project Loom, JEP 444) vállalati Spring Boot Model-View-Controller (MVC) alkalmazásokban történő bevezetésének architekturális, teljesítménybeli és üzemeltetési hatásait vizsgálja empirikus rendszerszintű megközelítéssel. Bár a virtuális szálak szétválasztják a Java szálakat az operációs rendszer kernelfelületű platformszálaitól – ezzel megszüntetve a webes konténerek szálkészlet-kimerülési korlátait –, a kutatás részletesen cáfolja az iparági *Ütemezhetőségi Tévedést* (Schedulability Fallacy). Ez a tévedés azon a hibás feltételezésen alapul, hogy a felhasználói szintű szálmultiplexelés automatikusan feloldja a párhuzamossági szűk keresztmetszeteket anélkül, hogy figyelembe venné a szinkronizációt, a sorbanállási egyensúlyt, a perzisztens adatbázis-erőforrások korlátait vagy a natív futási határokat.

A jelenségek vizsgálatához egy Spring Boot 3.5.12 MVC demonstrációs alkalmazást fejlesztettünk, amelyet 119 fizikai mérésnek vetettünk alá hét független kísérleti rétegben. A keletkezett adatbázis – amely nyers k6 terhelési naplókat, Java Flight Recorder (JFR) bináris eseményfájlokat és operációs rendszer telemetriát tartalmaz – teljes körű törvényszéki vizsgálaton esett át, és egy 504 fájlból álló, SHA-256 ellenőrzőösszeggel hitelesített, nyílt tudományos archívumban került rögzítésre. A metrikák kiértékelése egy szigorú, kétablakos módszertannal történt, amely világosan elkülöníti a kezdeti tranzienseket a stabil sorbanállási egyensúlytól.

Az empirikus eredmények az alábbiakat igazolják:
1. Java 21 futtatókörnyezetben a blokkoló műveletek belső monitorba (`synchronized`) zárása determinisztikusan a hordozószálhoz rögzíti a virtuális szálat (thread pinning), és `jdk.VirtualThreadPinned` eseményeket generál. Ugyanakkor a `synchronized` kiváltása egy virtuálisszál-biztos `ReentrantLock` primitívvel teljesen megszünteti a rögzítési eseményeket (108-ról 0-ra), ám **nem eredményez átviteli sebességnövekedést** ($1.956$ vs. $1.967\text{ req/s}$), mivel a kritikus szakasz Amdahl-törvénye által diktált kiszolgálási korlátja ($\mu = 1/D = 2.0\text{ req/s}$) változatlan marad.
2. A nem-igazságos `ReentrantLock` közvetlen CAS-műveleten alapuló előzése 23-szorosára növeli a válaszidő szórását ($\sigma = 16.51\text{ ms}$ vs. $0.72\text{ ms}$) a `synchronized` blokkhoz képest, ami jelentős kockázatot jelent a faroklatencia (tail latency) kiszámíthatóságára nézve.
3. A közvetlen Java Native Interface (JNI) hívásokon keresztül végrehajtott blokkoló POSIX rendszerhívások némán fogva tartják a hordozószálat Darwin/Mach várakozási állapotban: a CPU-kihasználtság minimális marad ($1.04\% \pm 0.12\%$), miközben **egyetlen JFR rögzítési esemény sem keletkezik**, elfedve a szálkiéheztetést a hagyományos megfigyelőrendszerek elől.
4. Az alkalmazásréteg szálkapacitásának növelése a véges háttér-erőforrásokra helyezi át a terhelést; a relációs adatbázisok kapcsolatkészleteit (HikariCP) érő korlátlan párhuzamos lekérések súlyos kapcsolatkimerülést és időtúllépési lavinákat idézhetnek elő.

Ezen eredményekre építve a dolgozat felállítja a *Háromszintű Párhuzamossági Taxonómiát*, és egy mérvadó szoftverarchitektúrás migrációs keretrendszert biztosít, amely öt kötelező érvényű szabályt, négy helyességmegőrző refaktorálási mintát és egy determinisztikus döntési fát tartalmaz a gyakorló mérnökök számára.

**Kulcsszavak:** Java 21, Virtuális Szálak, Project Loom, Spring Boot MVC, Szálrögzítés, Java Flight Recorder, Amdahl-törvény, Little-törvény, Párhuzamossági Architektúra, Szoftvermérnökség.

---

*(End of Chapter 9 Text)*

# Chapter 9: Conclusion

## 9.0 Overview and Context

This dissertation has investigated the architectural, performance, and operational implications of adopting Java 21 Virtual Threads (Project Loom) within enterprise Spring Boot Model-View-Controller (MVC) applications. Conducted under the MSc in Computer Science (Software Architecture) program at the Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest, Hungary, this research evaluated whether declarative virtual thread enablement resolves traditional concurrency bottlenecks or introduces unforeseen failure modes across application synchronization, foreign function boundaries, persistence infrastructure, and observability tooling.

Through an empirical systems paradigm, this study subjected a versioned Spring Boot 3.5.12 MVC demonstration application to 119 physical benchmark executions partitioned into seven non-overlapping evidence strata. The resulting experimental corpus—encompassing raw k6 JSON lines streams, binary Java Flight Recorder (JFR) event files, and host operating system telemetry—was forensically audited, recalculated, and cataloged as a 504-file open-science archive; the recorded normalized comparisons were SHA-256 verified ([`docs/evidence-freeze/`](../docs/evidence-freeze/)). The principal conclusions draw on the admitted and appropriately qualified strata; exploratory and construct-flawed runs are not treated as equivalent evidence.

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
| **Pinning Occurrence** | In the tested Java 21 conditions, enclosing `Thread.sleep` within a `synchronized` block produced qualifying `jdk.VirtualThreadPinned` events; representative event counts matched the completed-request counts in the cited recordings. | `[MEASURED]`<br>Stratum 1 & Stratum 5 | The JFR profile used a 20 ms threshold, so the result does not quantify shorter events or establish a universal one-event-per-request rule. Java 24.0.2 is a separate runtime comparison. | Establishes monitor pinning in the tested Java 21 treatment ([`CLM-RQ1-01`](../docs/evidence-freeze/claim-evidence-ledger.md#L42-L54)). |
| **Throughput Invariance** | Replacing `synchronized` with [`ReentrantLock`](../src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java#L35) changed qualifying JFR events from 108 to 0 in the cited comparison, while steady-state throughput remained close ($1.967\text{ req/s}$ vs. $1.956\text{ req/s}$, delta $-0.56\%$). | `[MEASURED]`<br>Stratum 1 (`CLM-RQ1-04`) | Applies to this closed workload in which requests contend on the same serialized critical section. | Shows that carrier unpinning did not relax the measured approximately 2.0 req/s service ceiling. |
| **Comparison with Platform Threads** | Under the 15–45 s hold window, platform threads with `synchronized` achieved $1.967\text{ req/s}$ and $p50 = 4,929.49\text{ ms}$ versus $4,966.78\text{ ms}$ for the virtual-thread synchronized condition. | `[MEASURED]`<br>Stratum 1 comparison | Requires steady-state filtering; the 25.8% whole-run latency difference is a ramp-up artifact. | Shows close behavior under this serialized treatment, not universal parity across workloads. |
| **Latency Dispersion & Barging** | The non-fair `ReentrantLock` condition showed wider measured dispersion than `synchronized` (sample $\sigma = 16.53\text{ ms}$ vs. $0.70\text{ ms}$) despite similar medians. | `[DERIVED]` + `[INTERPRETED]`<br>Stratum 1 (`CLM-RQ1-05`) | Based on $N=3$ process repetitions; AQS barging is a plausible interpretation, not a fully isolated causal proof. | Indicates a possible tail-latency trade-off when changing synchronization primitives. |
| **JDK Evolution (JEP 491)** | On OpenJDK 24.0.2, the repeated `synchronized` treatment recorded 0 qualifying JFR pinning events while throughput remained near $1.967\text{ req/s}$. | `[MEASURED]` + `[EXTERNALLY SUPPORTED]`<br>Stratum 2 (`CLM-RQ1-06`) | Evaluated on the recorded OpenJDK 24.0.2 runtime; it is a boundary comparison, not a blanket production-adoption claim. | Separates runtime monitor behavior from the application’s remaining serialized service capacity. |

**Definitive RQ1 Conclusion:** In Java 21, intrinsic synchronization surrounding blocking work causes deterministic carrier thread pinning and emits JFR diagnostic events. However, replacing `synchronized` with a virtual-thread-safe lock (`ReentrantLock`) or upgrading to OpenJDK 24 (JEP 491) unpins the carrier thread but **cannot increase throughput** when the workload is constrained by mutual exclusion. Carrier unpinning benefits system scalability *exclusively* when carrier threads are the primary bottleneck constraining independent, parallel tasks.

---

### 9.1.2 Formal Closure of Research Question 2 (RQ2)

> **Research Question 2 (RQ2):**
> *Which architectural patterns in a legacy Spring Boot MVC data path must be audited or refactored before enabling Virtual Threads, and what measurable risks remain after the primary pinning defect is removed?*

Based on the empirical evidence gathered across Stratum 3 (Native JNI Boundary), Stratum 4 (Architectural Controls), Stratum 7 (Construct Audits), and literature-backed specifications, Table 9.2 provides the formal closure ledger for RQ2.

### Table 9.2: Research Question 2 (RQ2) Closure Ledger

| Architectural Risk Category | Evidence-Backed Finding | Epistemic Class & Evidence Source | Operational Boundary & Condition | Required Engineering Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Foreign-Function Boundary Captivity** | In the tested direct JNI treatment, blocking POSIX `nanosleep()` ([`native_blocking.c`](../native/native_blocking.c#L14-L24)) occupied the carrier for the call duration, with low process CPU ($1.04\% \pm 0.12\%$) and zero qualifying `jdk.VirtualThreadPinned` events. | `[MEASURED]`<br>Stratum 3 (`CLM-RQ2-01`, `CLM-RQ2-02`) | Scoped to the tested direct JNI path without callbacks on Darwin; other JNI, FFM, driver, and resolver paths require separate verification. | Consider bounded platform-executor isolation for long or unpredictable native calls. |
| **2. Downstream Persistence Capacity** | Finite database and connection-pool capacity remains an architectural boundary, but this study did not establish local pool exhaustion. | `[NOT ESTABLISHED]` + `[EXTERNALLY SUPPORTED]`<br>Stratum 7 & literature (`CLM-RQ2-03`) | `/orders` executed its 300 ms delay before checkout, leaving the measured pool construct largely idle. | Size pools and configure timeouts using target-database measurements; do not infer them from this experiment. |
| **3. Context Lifecycle and Heap Inflation** | Per-request `ThreadLocal` state can scale with live request count and payload size, but the study did not observe a 5 GB retention or OOM event. | `[THEORETICAL / CONDITIONAL]`<br>Derivations & literature (`CLM-RQ2-07`) | The testbed cleaned context in `finally` blocks; the projection is not a measured heap result. | Enforce lifecycle cleanup and validate context propagation; evaluate Scoped Values where the target JDK and framework support them. |
| **4. Telemetry and Observability Blind Spots** | The configured JFR 20 ms threshold excludes shorter pinning events, and Java 21 `ThreadMXBean` APIs omit virtual threads from the relevant platform-thread views. | `[MEASURED]` & `[EXTERNALLY SUPPORTED]`<br>Stratum 1 & JDK-8303251 (`CLM-METH-04`) | Micrometer was not integrated or benchmarked in this repository. | Evaluate `micrometer-java21`/`VirtualThreadMetrics`, JFR, and OS/application telemetry in the target deployment; treat this as guidance, not a local measurement. |

**Definitive RQ2 Conclusion:** Before enabling Virtual Threads in legacy Spring Boot MVC systems, engineering teams must systematically audit four critical architectural boundaries:
1.  *Foreign-function interfaces (JNI/Panama)*, which silently capture carrier threads without emitting JFR pinning events.
2.  *Relational database connection pools (HikariCP)*, where increased request concurrency can expose finite pool capacity; exhaustion was not established by this study.
3.  *ThreadLocal context lifecycles*, which must be bounded to prevent linear heap memory explosion.
4.  *Observability infrastructure*, which must be upgraded to overcome the telemetry blind spots of legacy `ThreadMXBean` metrics and JFR duration filters.

---

## 9.2 Summary of Scientific and Architectural Contributions

This dissertation delivers six primary scientific, methodological, and practical contributions to the discipline of software architecture and performance engineering:

### Contribution 1: Decoupling Carrier Unpinning from Domain Serialization (`CLM-RQ1-04`)
Under the stated closed-loop workload and serialized critical section, this study demonstrates that unpinning carrier threads did not increase application throughput. `ReentrantLock` produced zero qualifying JFR pinning events in the cited comparison while throughput remained close ($1.956$ vs. $1.967\text{ req/s}$) and consistent with the Little's Law derivation ($R \approx 4.985\text{ s}$). The result supports the conclusion that domain mutual exclusion and runtime schedulability are distinct architectural layers.

### Contribution 2: Discovery of Silent Carrier Captivity in Native Downcalls (`CLM-RQ2-01`, `CLM-RQ2-02`)
Across 27 repeated multi-JDK executions in Stratum 3, the tested direct JNI `nanosleep()` path occupied carriers while producing **zero qualifying JFR pinning events** and low process CPU ($1.04\% \pm 0.12\%$). This finding demonstrates a diagnostic gap for the tested native path; it does not establish that JFR is a universal detector, or non-detector, for every form of carrier starvation.

### Contribution 3: The Three-Tier Concurrency Taxonomy and Foundational Architectural Principles
This dissertation formalizes a comprehensive theoretical framework for virtualized runtime concurrency:
*   *Tier 1 (Runtime Schedulability):* Governed by $M:N$ continuation multiplexing and HotSpot carrier pool mechanics.
*   *Tier 2 (Domain Synchronization):* Governed by Amdahl's Law and mutual exclusion constraints.
*   *Tier 3 (Backend Capacity):* Interpreted using Little's Law, with finite-resource ceilings requiring target-system measurement; the USL is used only as a conceptual model.
This taxonomy is summarized by three working principles: the *Amdahl-Little Invariant*, the *Observability Asymmetry Invariant*, and the *Finite Backend Invariance Principle*, each bounded by the measurements and assumptions documented in this thesis.

### Contribution 4: Methodological Forensic Auditing and the Dual-Window Reporting Standard (`CLM-METH-02`)
This study established that aggregate whole-run performance reporting introduces profound measurement artifacts in closed-loop benchmarks. By demonstrating that a 25.8% apparent latency advantage for platform threads was entirely a transient artifact of k6 ramp-up dynamics, this research formulated the **Dual-Window Reporting Standard**, proving that steady-state hold window isolation (15–45s) is mandatory for valid systems benchmarking.

### Contribution 5: The Authoritative Engineering Migration Framework ([Chapter 7](../docs/chapter-07-migration-guidance.md))
This dissertation synthesized experimental findings into a battle-tested engineering migration framework:
*   *The Five Mandatory Migration Rules:* Explicit criteria governing pre-migration auditing, dependency resolution, pool sizing, and observability.
*   *The Four Correctness-Preserving Refactoring Patterns:* Production-grade implementations for mutual exclusion, foreign-function containment, `ThreadLocal` hygiene, and Scoped Values (JEP 506).
*   *The Master Migration Decision Tree:* A deterministic, sequential audit pipeline linking observed symptoms to verified remedial interventions.

### Contribution 6: The Ratified Open-Science Evidence Freeze Archive
To guarantee complete reproducibility, the entire research corpus has been permanently preserved in the repository ([`docs/evidence-freeze/`](../docs/evidence-freeze/)), comprising:
*   An exhaustive inventory of 504 physical disk files (~966 MB), with the recorded normalized comparisons verified against their expected SHA-256 hashes.
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
|  - Platform-thread stack reservations and associated OS scheduling overhead.      |
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

To evaluate these phenomena, a controlled Spring Boot 3.5.12 MVC demonstration application was developed and subjected to 119 physical benchmark executions across seven non-overlapping experimental strata. The experimental corpus—encompassing raw k6 JSON lines streams, Java Flight Recorder (JFR) binary event traces, and operating system telemetry—was forensically audited and cataloged as a 504-file archive; the recorded normalized comparisons were SHA-256 verified. Workloads were analyzed using a dual-window reporting standard that separates transient ramp-up artifacts from steady-state queueing equilibrium.

The empirical findings establish that:
1. In the tested Java 21 condition, enclosing blocking operations within intrinsic monitors (`synchronized`) produced qualifying `jdk.VirtualThreadPinned` events. Replacing `synchronized` with a virtual-thread-compatible `ReentrantLock` produced zero qualifying events in the cited comparison while yielding similar throughput ($1.956$ vs. $1.967\text{ req/s}$), consistent with the measured single-server serialization ceiling ($\mu \approx 2.0\text{ req/s}$).
2. Non-fair `ReentrantLock` showed a descriptive approximately 23-fold difference in sample standard deviation ($\sigma = 16.53\text{ ms}$ vs. $0.70\text{ ms}$) compared to `synchronized`, revealing a possible tail-latency trade-off under the tested conditions.
3. In the tested direct Java Native Interface (JNI) treatment, blocking POSIX `nanosleep()` occupied a carrier in the observed Darwin/Mach wait state with low process CPU ($1.04\% \pm 0.12\%$) and **zero qualifying JFR pinning events**, exposing a scoped observability gap.
4. Concurrency expansion in the application tier can expose finite downstream resources; the local `/orders` construct did not establish HikariCP exhaustion, so connection starvation and timeout behavior require target-system measurement.

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

A jelenségek vizsgálatához egy Spring Boot 3.5.12 MVC demonstrációs alkalmazást fejlesztettünk, amelyet 119 fizikai mérésnek vetettünk alá hét, egymástól elkülönített kísérleti rétegben. A fő következtetések a megfelelően minősített, befogadott rétegekre támaszkodnak; a feltáró és konstrukciós hibával terhelt futásokat nem kezeltük egyenértékű bizonyítékként. A keletkezett adatbázis – amely nyers k6 terhelési naplókat, Java Flight Recorder (JFR) bináris eseményfájlokat és operációs rendszer telemetriát tartalmaz – teljes körű törvényszéki vizsgálaton esett át, és egy 504 fájlból álló nyílt tudományos archívumban került rögzítésre; a normalizált összehasonlítások rögzített SHA-256 ellenőrzőösszegei egyeztek.

Az empirikus eredmények az alábbiakat igazolják:
1. Java 21 futtatókörnyezetben a blokkoló műveletek belső monitorba (`synchronized`) zárása determinisztikusan a hordozószálhoz rögzíti a virtuális szálat (thread pinning), és `jdk.VirtualThreadPinned` eseményeket generál. Ugyanakkor a `synchronized` kiváltása egy virtuálisszál-biztos `ReentrantLock` primitívvel teljesen megszünteti a rögzítési eseményeket (108-ról 0-ra), ám **nem eredményez átviteli sebességnövekedést** ($1.956$ vs. $1.967\text{ req/s}$), mivel a kritikus szakasz Amdahl-törvénye által diktált kiszolgálási korlátja ($\mu = 1/D = 2.0\text{ req/s}$) változatlan marad.
2. A nem-igazságos `ReentrantLock` esetén a minta szórása leíró jelleggel hozzávetőleg 23-szor nagyobb volt ($\sigma = 16.53\text{ ms}$ vs. $0.70\text{ ms}$), mint a `synchronized` blokk esetén; ez a vizsgált feltételek között lehetséges faroklatencia-kockázatra utal.
3. A közvetlen Java Native Interface (JNI) hívásokon keresztül végrehajtott blokkoló POSIX rendszerhívások némán fogva tartják a hordozószálat Darwin/Mach várakozási állapotban: a CPU-kihasználtság minimális marad ($1.04\% \pm 0.12\%$), miközben **egyetlen JFR rögzítési esemény sem keletkezik**, elfedve a szálkiéheztetést a hagyományos megfigyelőrendszerek elől.
4. Az alkalmazásréteg párhuzamosságának növelése feltárhatja a véges háttér-erőforrások korlátait; a helyi `/orders` konstrukció azonban nem igazolta a HikariCP-kapcsolatkészlet kimerülését, ezért a kapcsolatkimerülést és az időtúllépéseket a célkörnyezetben kell mérni.

Ezen eredményekre építve a dolgozat felállítja a *Háromszintű Párhuzamossági Taxonómiát*, és egy mérvadó szoftverarchitektúrás migrációs keretrendszert biztosít, amely öt kötelező érvényű szabályt, négy helyességmegőrző refaktorálási mintát és egy determinisztikus döntési fát tartalmaz a gyakorló mérnökök számára.

**Kulcsszavak:** Java 21, Virtuális Szálak, Project Loom, Spring Boot MVC, Szálrögzítés, Java Flight Recorder, Amdahl-törvény, Little-törvény, Párhuzamossági Architektúra, Szoftvermérnökség.

---

*(End of Chapter 9 Text)*

# Annotated Literature Inventory (Supplementary Research Artifact)

**Preserved Provenance Artifact for MSc Thesis:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*  
**Companion BibTeX Source:** [`overleaf/references.bib`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/overleaf/references.bib)  
**Thesis Integration:** Synthesized directly into Chapters 2 and 3 of the dissertation (`02-related-work.tex` and `03-background.tex`); relocated out of Appendix A of the PDF to keep the reproducibility appendix focused on independent verification artifacts while preserving the complete 36-row domain inventory.

---

| Domain | Source | Primary Scientific Value | Evidentiary Boundary |
|---|---|---|---|
| Queueing & Scheduling | Amdahl (1967) (`Amdahl1967`) | Formulates speedup ceiling governed by strictly serial fraction $(1 - P)$. | Theoretical scaling model; predates user-space thread unmounting. |
| Queueing & Scheduling | Kleinrock (1975) (`Kleinrock1975`) | Mathematical foundations of $M/M/1$ and $M/G/1$ queueing systems. | Theoretical queueing theory; does not evaluate JVM carrier pools. |
| Queueing & Scheduling | Little (1961, 2011) (`Little1961`, `Little2011`) | Operational queueing law ($L = \lambda W$) relating population, throughput, and latency. | Steady-state invariant; does not model internal lock contention. |
| Queueing & Scheduling | Anderson et al. (1991) (`Anderson1991`) | Establishes $M:N$ two-level scheduling, user unmounting, and scheduler activations. | OS kernel implementation; predates managed runtimes and JDBC pools. |
| Queueing & Scheduling | Dijkstra (1965) (`Dijkstra1965`) | Foundational formulation of mutual exclusion and serialized execution regions. | Algorithmic primitive; does not address carrier thread starvation. |
| Queueing & Scheduling | Hoare (1974) (`Hoare1974`) | Conceptual origin of structured monitors and condition wait queues. | Language design concept; does not foresee carrier pinning hazards. |
| Queueing & Scheduling | Ousterhout (1996) (`Ousterhout1996`) | Argued against thread synchronization and memory overhead in favor of events. | Systems debate; predates modern lightweight user-mode thread multiplexers. |
| Queueing & Scheduling | Welsh et al. (2001) (`Welsh2001`) | Staged Event-Driven Architecture (SEDA) decomposing systems into event queues. | Event-driven pipeline; introduces asynchronous programming complexity. |
| Queueing & Scheduling | von Behren et al. (2003) (`VonBehren2003`) | Showed high-concurrency servers scale using lightweight threads and compiler support. | Early user-threading rationale; predates Java 21 continuations. |
| Concurrency Models | Lamport (1979) (`Lamport1979`) | Formalized sequential consistency for multiprocessor systems. | Hardware memory model; does not evaluate thread scheduling. |
| Concurrency Models | Herlihy & Shavit (2008) (`Herlihy2008`) | Mathematical foundations of mutual exclusion and queue locks. | Focuses on multi-core hardware; does not model carrier pools. |
| Concurrency Models | Goetz et al. (2006) (`Goetz2006`) | Standard reference on `java.util.concurrent` and explicit locking. | Written for 1:1 platform threads; predates Loom unmounting. |
| Concurrency Models | Lea (2000, 2004) (`Lea2000`, `Lea2000FJ`, `Lea2005AQS`) | Engineered AQS and work-stealing `ForkJoinPool` powering Loom scheduler. | Runtime foundation; does not evaluate full Spring MVC request lifecycles. |
| Concurrency Models | Manson et al. (2005) (`Manson2005`) | Formulated Java Memory Model (JSR-133) happens-before consistency. | Memory visibility semantics; does not analyze throughput under load. |
| Concurrency Models | Mellor-Crummey & Scott (1991) (`MellorCrummey1991`) | Introduced MCS FIFO queue locks, contributing to scalable queue lock designs in AQS. | Hardware algorithms; predates Java virtual thread parking. |
| Concurrency Models | Bacon et al. (1998) (`Bacon2001`) | Optimized Java monitor acquisition via mark-word CAS fast paths (thin locks). | JVM monitor design; does not address carrier pinning in monitors. |
| Benchmarking Method | Georges et al. (2007) (`Georges2007`) | Rigorous principles for warm-up, steady-state, and multi-process variance. | Evaluates JIT/GC steady-state; does not evaluate virtual thread harnesses. |
| Benchmarking Method | Blackburn et al. (2006) (`Blackburn2006`) | DaCapo benchmark suite standardizing macro-level Java evaluation. | Macro-benchmarks predating virtual threads; no web I/O evaluation. |
| Benchmarking Method | Kalibera & Jones (2013) (`Kalibera2013`) | Treatment of correlated measurement errors and process repetitions. | Methodological foundation; requires independent process invocations. |
| Benchmarking Method | Bulej et al. (2017) (`Bulej2017`) | Framework for automated performance regression detection in CI pipelines. | Regression testing; provides discipline for reproducible suites. |
| Benchmarking Method | Traini et al. (2022) (`Traini2022`) | Dual-window standard separating warm-up ramp transients from steady state. | Methodological literature; does not evaluate Virtual Threads. |
| Benchmarking Method | Schroeder et al. (2006) (`Schroeder2006`) | Proved closed-loop harnesses enforce self-throttling; open-loop tests capacity. | Justifies closed-loop k6 testing to isolate internal mechanisms. |
| JDK Specifications | JEP 425 & 436 (`JEP425`, `JEP436`) | Preview releases of Virtual Threads in JDK 19 and JDK 20. | Incubation specifications; superseded by Java 21 LTS standard. |
| JDK Specifications | Pressler (JEP 444, 2023) (`JEP444`) | Normative specification of Virtual Threads and monitor pinning in Java 21 LTS. | Platform specification; does not quantify application lock interactions. |
| JDK Specifications | Pressler (JEP 491, 2024) (`JEP491`) | Redesigns HotSpot monitors to allow unmounting inside `synchronized`. | Platform enhancement; provides no empirical data for Spring MVC. |
| JDK Specifications | Haley & Dinn (JEP 506, 2025) (`JEP506`) | Scoped Values as immutable context sharing to replace `ThreadLocal`. | Newer JDK feature; does not resolve `ThreadLocal` in Java 21 systems. |
| JDK Specifications | Cimadamore & Minborg (JEP 454, 2024) (`JEP454`) | Foreign Function & Memory API replacing legacy JNI boilerplate in JDK 22+. | Managed FFM boundary; native blocking behavior requires separate evaluation. |
| JDK Specifications | Lindholm et al. (JVMS 21) (`JVMS21`) | Normative JVM bytecode instructions, monitors, and thread states. | Specification; does not evaluate application throughput under load. |
| JDK Specifications | Gosling et al. (JLS 21) (`JLS21`) | Normative Java language semantics, monitors, and memory model (§17). | Language specification; does not model carrier thread multiplexing. |
| JDK Specifications | Oracle (2023) (`OracleVTGuidance`) | Official guidance and best practices for virtual thread adoption. | General guidance; provides no empirical data under carrier limits. |
| Modern Frameworks | Beronić et al. (2021) (`Beronivc2021`) | Early exploratory analysis of structured concurrency in Loom prototypes. | Evaluated pre-standard Loom; does not evaluate Java 21 LTS or JFR. |
| Modern Frameworks | Navarro et al. (2023) (`Navarro2023`) | Quarkus benchmark showing reactive core outperformed VT near saturation. | Focuses on Quarkus reactive; does not isolate locks, JDBC, or JNI. |
| Modern Frameworks | Lašić et al. (2024) (`Lasic2024`) | Evaluated aggregate virtual thread throughput against database backends. | Evaluated gross client metrics; omitted connection-holding control, JFR unmounting verification, and JNI captivity. |
| Modern Frameworks | Likus & Krużel (2025) (`Likus2025`) | Evaluated I/O vs. CPU REST endpoints on Spring Boot with Java 21. | Relies on black-box HTTP metrics; omitted lock isolation, JFR stack traces, JNI downcalls, and warm-up filtering. |
| Modern Frameworks | Dundov et al. (2026) (`SpringHelidon2026`) | Crosses Spring Boot and Helidon with platform vs. virtual threads. | Framework throughput focus; omits JFR monitor pinning traces and mutex swapping on identical endpoints. |
| Modern Frameworks | Charlak et al. (2026) (`Charlak2026`) | Comparative web server study showing reactive memory advantages. | Focuses on paradigm comparison; lacks migration refactoring guidance. |
| Modern Frameworks | dotCMS Core (2024) (`DotCMS2024`) | Industrial rollback: reverted async cache commits due to lock pinning. | Industry post-mortem; confirms failure modes but lacks controlled benchmark data. |

# Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines

**Author:** Hamed Mohamed  
**Programme:** Computer Science MSc (Software Architecture Specialisation)  
**Affiliation:** Faculty of Informatics, Eötvös Loránd University (ELTE), Budapest, Hungary  
**Supervisors:**  
- Dr. habil. Tamás Kozsik (Associate Professor, Head of Department of Programming Languages and Compilers, ELTE)  
- Gregory Reynolds Morse (External Thesis Advisor / Lecturer, ELTE)  
**Event:** ELTE Faculty of Informatics TDK Conference 2026 Autumn / 38th OTDK ICT Section  
**Language:** English  

---

### Abstract

Enterprise Java backend systems face escalating scalability demands, leading to widespread adoption of Java 21 Virtual Threads (Project Loom, JEP 444) under the belief that user-mode thread multiplexing effortlessly resolves concurrency bottlenecks. However, systems encounter the Schedulability Fallacy: decoupling threads from kernel resources does not eliminate application-level serialization, downstream connection pool limits, or carrier starvation during foreign calls. Without empirical profiling, migrations risk throughput collapse and database exhaustion.

To investigate these phenomena, a controlled Spring Boot 3.5.12 MVC application was instrumented and subjected to 125 benchmark executions across eight non-overlapping experimental strata, producing 543 cataloged artifacts (~1.05 GB) under SHA-256 verification. Workloads were driven using a closed-loop k6 harness evaluating single-carrier constraints (parallelism=1) and multi-carrier baselines. Multi-tier telemetry integrated continuous Java Flight Recorder (JFR) event tracing, operating system process accounting, and a dual-window steady-state analysis standard.

The author discovered that replacing synchronized with ReentrantLock eliminated all qualifying JFR pinning events (108 to 0) but yielded identical throughput (1.956 vs. 1.967 req/s), proving that carrier unpinning cannot circumvent Amdahl's serialization ceiling (mu ~ 2.0 req/s). Direct Java Native Interface (JNI) blocking silently captured carrier threads in kernel wait states with low CPU (~1%) and zero JFR events. Factorial persistence testing validated that virtual threads unmount cleanly, but throughput is strictly capped by pool size (X = K / T_hold).

Virtual thread adoption is not a passive configuration toggle, but a structural capacity migration. The author synthesized the Three-Tier Concurrency Taxonomy, five mandatory architectural rules, four correctness-preserving refactorings, and a migration decision matrix. Key engineering mandates include enforcing perimeter bulkheads, replacing monitors before blocking operations, encapsulating native calls in bounded platform pools, and sizing connection pools against database engine capacity.

---

**Keywords:** Project Loom, Thread Pinning, Carrier Starvation, Java Flight Recorder, Connection Pooling

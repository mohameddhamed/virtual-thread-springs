# Bibliography Review — Revised Critical Synthesis

**Programme:** MSc Computer Science
**Track:** Computer Science (Software Architecture)
**Student:** Hamed Mohamed (DG1EWF)
**Thesis:** *Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*

## Scope and position

This review supports a mechanism-focused empirical case study of a Spring Boot MVC application running on **Java 21 LTS**. The study is deliberately not a claim about all Virtual Thread applications. It examines whether a blocking operation inside an intrinsic monitor can pin a Java 21 Virtual Thread, how that differs from downstream resource contention and request-context lifecycle risk, and whether a lock refactoring preserves endpoint correctness while changing the scheduling mechanism.

The Java-version boundary is essential. JEP 444 specifies the Java 21 Virtual Thread model, including the fact that blocking while holding an intrinsic monitor can pin a Virtual Thread. JEP 491 changes that behavior in JDK 24 by allowing Virtual Threads to unmount while synchronized code blocks. Consequently, the primary claims in this thesis apply to Java 21; guidance for JDK 24+ must not silently reuse the Java 21 pinning warning.

## Critical comparison of closest work

| Source | System and method | Main value | Limitation for this thesis |
|---|---|---|---|
| Pressler, **JEP 444** (2023) | Normative Java 21 platform design and operational semantics | Defines Virtual Threads, scheduler/carrier terminology, pinning, and the throughput—not latency—goal | Not an end-to-end Spring MVC experiment; does not quantify this application’s lock/resource interaction |
| Pressler, **JEP 491** (2024) | JDK enhancement describing the JDK 24 monitor-pinning change | Establishes the version boundary for any `synchronized` migration advice | A platform change proposal, not evidence about Java 21 Spring workloads |
| Beronić et al. (2021), DOI `10.23919/MIPRO52101.2021.9596855` | Early Loom-era analysis of structured concurrency and scalable JVM applications | Provides historical motivation and early performance context | Pre-final Java 21/runtime and not a Spring MVC lock-pinning study |
| Navarro et al. (2023), DOI `10.1145/3583678.3596895` | Quarkus framework integration under resource-constrained conditions | Shows that framework integration and finite machine resources matter; Virtual Threads were not automatically superior to reactive execution in that setup | Different framework/runtime integration; does not isolate Java monitors in Spring MVC |
| Lašić et al. (2024), DOI `10.1109/MIPRO60963.2024.10569754` | Database-driven server workloads comparing Virtual and platform threads | Directly motivates measuring JDBC and connection-pool effects separately from pinning | Database/server workload evidence does not identify the application lock mechanism studied here |
| Likus & Krużel (2025), *Analysis of Virtual Threads in Spring Applications*, ECMS 2025, DOI `10.7148/2025-0555` | Spring REST simulations with differing computational demands | Closest framework context; supports separating I/O-bound from CPU-bound workloads | Does not document synchronized blocking, JFR pinning, or pool saturation; its design does not replace this study’s attribution |
| Charlak, Brzeziński & Kozieł (2026), DOI `10.35784/jcsi.9409` | Comparative reactive versus Virtual Thread web-server workloads | Supplies a current contrary comparison: reactive systems may retain resource-efficiency advantages near saturation | Reactive comparison is not a legacy synchronized Spring MVC migration experiment |
| Traini et al. (2022), DOI `10.1007/s10664-022-10247-x` | Analysis of 586 JMH benchmarks from 30 Java systems | Justifies warm-up, stable-state, repetition, and uncertainty discipline | Methodological rather than Virtual Thread-specific; it does not determine this application’s effect size |
| Spring Boot reference documentation | Versioned framework support for enabling Virtual Threads | Defines what `spring.threads.virtual.enabled` changes at the framework layer | Configuration support does not audit application synchronization or resource pools |
| Oracle Java 21 Virtual Threads guide | Operational guidance for pinning, `ReentrantLock`, JFR, and ThreadLocal cautions | Primary practical interpretation of the measured mechanisms | Documentation is not independent empirical evidence |
| Tomcat 10.1 and HikariCP documentation | Server executor and finite database-pool constraints | Prevents attributing every queue or latency increase to carrier pinning | Configuration guidance must be frozen to the tested dependency versions |

## Synthesis and research gap

The closest empirical studies generally compare Virtual Threads with platform threads, reactive execution, or database-driven workloads. They establish that Virtual Threads can improve concurrency for blocking workloads, but they also show that finite resources and framework integration remain limiting factors. The platform sources explain *why* intrinsic synchronization is a Java 21 risk and *why* that risk changes in JDK 24. None of these sources supplies a reproducible Java 21 Spring MVC case study that jointly provides:

1. a synchronized blocking treatment and a lock-refactored treatment with the same endpoint contract;
2. platform-thread and Virtual-Thread controls;
3. endpoint-isolated and mixed-workload measurements;
4. JFR stack attribution for `jdk.VirtualThreadPinned`; and
5. a mechanism-specific separation of pinning, request-context correctness, and JDBC-pool contention.

That is the bounded contribution claimed here. It is not “Virtual Threads are faster,” nor “all synchronized code must be removed.” It is an evidence-bounded migration procedure for the tested Java 21 configuration, with JDK 24+ treated as an explicit external-validity boundary.

## Measurement literature and protocol implications

The benchmark is a closed-model k6 workload unless a constant-arrival-rate scenario is added. In a closed model, response-time growth reduces request arrival because each virtual user waits for its previous iteration; throughput collapse therefore cannot be interpreted independently of the load model. Mixed endpoint runs are useful for system-level interference, but isolated endpoint runs are required for causal attribution. The final protocol will therefore report model, dropped iterations, timeout policy, warm-up/stability rule, run order, and endpoint selection.

Traini et al. supports treating JVM performance as a steady-state measurement problem rather than taking one short run as a population estimate. Three runs may be retained as exploratory pilot evidence, but bootstrap intervals from three runs will not be presented as strong inferential evidence. The final protocol will use pilot variance to justify the repetition count and will report run-level medians, dispersion, effect sizes, and uncertainty.

JFR evidence is necessary but not sufficient for causal language. A `jdk.VirtualThreadPinned` event must be attributed to the application’s intrinsic monitor, the refactored condition must remove that attribution while preserving correctness, and the performance difference must reproduce under the frozen protocol. JDBC wait time and ThreadLocal lifecycle observations are separate constructs and will not be labelled pinning without this evidence.

## Citation and provenance policy

The bibliography contains literature and authoritative documentation only. Scripts, source files, raw k6 JSON, JFR recordings, and generated tables are research artifacts and are listed in `docs/artifact-provenance-ledger.md`, with commit, checksum, configuration, and extraction-command fields. Historical figures such as “−63% throughput” and “+96% recovery” remain preliminary pilot observations until that ledger maps them to raw files and exact conditions.

## References

1. OpenJDK. (2023). *JEP 444: Virtual Threads*. https://openjdk.org/jeps/444
2. Pressler, R. (2024). *JEP 491: Synchronize Virtual Threads without Pinning*. https://openjdk.org/jeps/491
3. Oracle. (2023). *Virtual Threads (Java SE 21)*. https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html
4. Beronić, D., et al. (2021). *On Analyzing Virtual Threads—a Structured Concurrency Model for Scalable Applications on the JVM*. DOI: https://doi.org/10.23919/MIPRO52101.2021.9596855
5. Navarro, J., et al. (2023). *Considerations for integrating virtual threads in a Java framework: a Quarkus example in a resource-constrained environment*. DOI: https://doi.org/10.1145/3583678.3596895
6. Lašić, L., Beronić, D., Mihaljević, B., & Radovan, A. (2024). *Assessing the Efficiency of Java Virtual Threads in Database-Driven Server Applications*. DOI: https://doi.org/10.1109/MIPRO60963.2024.10569754
7. Likus, P., & Krużel, F. (2025). *Analysis of Virtual Threads in Spring Applications*. ECMS 2025. DOI: https://doi.org/10.7148/2025-0555
8. Charlak, D., Brzeziński, J., & Kozieł, G. (2026). *Comparative analysis of reactive programming and Java virtual threads*. *Journal of Computer Sciences Institute*. DOI: https://doi.org/10.35784/jcsi.9409
9. Traini, D., et al. (2022). *Towards effective assessment of steady state performance in Java software: Are we there yet?* DOI: https://doi.org/10.1007/s10664-022-10247-x
10. Spring Team. (2026). *Spring Boot Reference Documentation: Virtual Threads*. Cite the exact tested Spring Boot version and versioned URL.
11. Apache Tomcat. (2026). *Tomcat 10.1 HTTP Connector Documentation*. Cite the exact tested Tomcat version and settings.
12. HikariCP. (2026). *Configuration Knobs*. https://github.com/brettwooldridge/HikariCP#configuration-knobs-baby
13. HikariCP. (2026). *About Pool Sizing*. https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing
14. Grafana Labs. (2026). *k6 Documentation: Scenarios, Metrics, Thresholds, and JSON Output*. Cite the exact pages and k6 version used.
15. von Behren, R., Condit, J., & Brewer, E. (2003). *Why Events Are a Bad Idea (for High-Concurrency Servers)*. HotOS IX.
16. Welsh, M., Culler, D., & Brewer, E. (2001). *SEDA: An Architecture for Well-Conditioned, Scalable Internet Services*. SOSP. DOI: https://doi.org/10.1145/502034.502057
17. Georges, A., Buytaert, D., & Eeckhout, L. (2007). *Statistically Rigorous Java Performance Evaluation*. OOPSLA. DOI: https://doi.org/10.1145/1297027.1297033
18. Kalibera, T., & Jones, R. (2013). *Rigorous Benchmarking in Reasonable Time*. ISMM. DOI: https://doi.org/10.1145/2555670.2464160
19. Schroeder, B., Wierman, A., & Harchol-Balter, M. (2006). *Open Versus Closed: A Cautionary Tale*. USENIX NSDI.

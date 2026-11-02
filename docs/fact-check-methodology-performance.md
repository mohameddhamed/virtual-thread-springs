# Technical Fact-Check Report: Benchmarking Methodology, Performance Metrics, and Interpretation of Experimental Results

**Evaluation Target:** MSc Thesis Research Materials (*Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*)  
**Documents Audited:**
- [docs/virtual-threads-research-scout-report.md](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/virtual-threads-research-scout-report.md)
- [docs/research-triage.md](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/research-triage.md)
- [docs/thesis-draft-skeleton.md](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md)
- Benchmark scripts and pipeline: [run-benchmark.sh](file:///Users/mohamedhamed/Documents/virtual-thread-springs/run-benchmark.sh), [k6/load-test.js](file:///Users/mohamedhamed/Documents/virtual-thread-springs/k6/load-test.js), [k6/isolated-load-test.js](file:///Users/mohamedhamed/Documents/virtual-thread-springs/k6/isolated-load-test.js), [scripts/normalize_evidence.py](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/normalize_evidence.py)

---

## 1. Executive Summary

This audit evaluates the factual accuracy, theoretical consistency, and methodological defensibility of claims concerning benchmarking methodology, queueing models, performance metrics, and statistical interpretation across the research scout report and triage register. 

The audit identified two critical theoretical errors, one implementation discrepancy in the data normalization pipeline, and three overextensions of cited literature that directly affect the thesis's conclusions:

1. **Contradiction on Server Capacity vs. Generator Self-Throttling (Finding 5.1.1 & Triage CL-03):**  
   The scout report and triage register assert that the 2.0 req/s throughput floor observed on `/payments` is *"a generator self-throttling artifact (coordinated omission), not an inherent server capacity ceiling."* This claim is **mathematically false**. The endpoint encapsulates a 500 ms critical section under mutual exclusion. By the asymptotic bounds analysis of queueing networks ([Denning & Buzen 1978](https://doi.org/10.1145/356744.356747); [Lazowska et al. 1984](http://web.cs.ucla.edu/~kwh/courses/common/Lazowska.QSP.pdf)), a single-server bottleneck with service demand $S = 500\text{ ms}$ has a theoretical saturation ceiling of $\mu = 1 / S = 2.0\text{ req/s}$. In *any* steady-state environment (open or closed), the server cannot process more than 2.0 req/s. The closed-loop workload model bounds the maximum queue length to $N=10$ and self-throttles the arrival rate to match throughput, preventing unbounded queue accumulation; it does not artificially depress the server's maximum processing capacity.
2. **Measurement Pipeline Inconsistency (Manifest vs. Normalization Code):**  
   The benchmark manifests ([run-benchmark.sh](file:///Users/mohamedhamed/Documents/virtual-thread-springs/run-benchmark.sh#L118-L119)) assert that k6 ramp-up (15 s) is *"excluded from steady-state interpretation"* and that the measurement interval is strictly the *"30s hold stage."* However, inspection of [scripts/normalize_evidence.py](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/normalize_evidence.py#L40-L69) shows that `k6_metrics()` aggregates every Point in the k6 JSON stream across the entire 55-second run (ramp-up, hold, and ramp-down) without timestamp filtering. The reported request totals (108–110) and latency percentiles fold cold-start iterations and draining intervals directly into steady-state metrics, contradicting the manifest contract.
3. **Misapplication of the CALM Theorem to Local Mutexes (Finding 10.9 & Triage CL-21):**  
   The scout report invokes the CALM Theorem ([Hellerstein & Alvaro 2020](https://doi.org/10.1145/3397885)) to "prove" why `ReentrantLock` cannot eliminate serialization delay in `/payments`. The CALM theorem formally proves when *distributed programs across asynchronous networks* can achieve eventual consistency without distributed coordination (consensus/two-phase commit). Local single-process lock serialization is governed by [Bernstein's Conditions (1966)](https://doi.org/10.1109/PGEC.1966.264565) and [Amdahl's Law (1967)](https://doi.org/10.1145/1465482.1465560). Applying CALM to in-memory monitors is a category mistake.
4. **Conflation of Little's Law / Interactive Response Time Law with Coordinated Omission:**  
   The report equates closed-loop self-throttling directly with *Coordinated Omission*. Closed-loop self-throttling is an architectural characteristic of closed queueing systems ($X = N / (R + Z)$); Coordinated Omission ([Gil Tene](https://www.azul.com/resources/presentations/how-not-to-measure-latency/)) is a measurement sampling bias where test generators omit un-issued scheduled requests during server pauses, distorting high-percentile latency histograms.
5. **Defensible Methodological Stance on 3-Trial Sample Sizes (Finding 5.2.1 & Triage CL-05):**  
   The triage register correctly identifies that 3 process trials cannot support inferential confidence intervals or parametric significance tests on non-stationary JVMs ([Georges et al. 2007](https://doi.org/10.1145/1297027.1297033); [Kalibera & Jones 2013](https://doi.org/10.1145/2464157.2464160)). Reframing the 3-trial dataset as *qualitative mechanism-isolation engineering trials* is scientifically sound and defensible.
6. **JFR Profile 20 ms Event Filtering (Finding 11.2.A.4 & Triage CL-02):**  
   Verified via OpenJDK source code: `profile.jfc` and `default.jfc` suppress `jdk.VirtualThreadPinned` events lasting < 20 ms. Because the test harness used 500 ms synthetic pauses, primary pinning events were captured; however, short sub-20 ms pinning remains unobserved, representing a construct validity threat that must be documented.

---

## 2. Claim-by-Claim Audit

| ID | Claim as stated | Verdict | Evidence and source | Version/scope qualification | Thesis impact | Recommended action |
|---|---|---|---|---|---|---|
| **METH-01** | The 2 req/s throughput floor on `/payments` is an artifact of closed-loop VU self-throttling, not an inherent server capacity ceiling. | **CONTRADICTED** | [Denning & Buzen (1978)](https://doi.org/10.1145/356744.356747); [Lazowska et al. (1984)](http://web.cs.ucla.edu/~kwh/courses/common/Lazowska.QSP.pdf), Ch. 3. Asymptotic bounds dictate $X_{max} = 1 / D_{max}$. For a 500 ms exclusive critical section ($D = 0.5\text{ s}$), maximum steady-state throughput is strictly $1 / 0.5 = 2.0\text{ req/s}$ in both open and closed systems. | Holds for any workload model where mutual exclusion serializes a 500 ms operation. | Directly affects RQ1 interpretation ([Section 6.2](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L486-L510)). Claiming 2 req/s is not a server capacity limit is mathematically erroneous. | Correct claim: 2 req/s is the absolute capacity ceiling of the serialized endpoint. Closed-loop load bounds queue length ($N=10$) and prevents queue explosion, but does not depress maximum capacity. |
| **METH-02** | In a closed-loop system ($N=10$, $Z=0$), Little's Law dictates throughput as $\lambda = N / R$. | **PARTIALLY SUPPORTED** | [Kleinrock (1976)](https://www.wiley.com/en-us/Queueing+Systems%2C+Volume+2%3A+Computer+Applications-p-9780471491118), Ch. 4; [Denning & Buzen (1978)](https://doi.org/10.1145/356744.356747), p. 235. The operational law governing interactive closed systems is the **Interactive Response Time Law**: $R = (N / X) - Z$. When $Z = 0$, $X = N / R$. | Operational analysis of closed networks. Little's Law ($L = \lambda W$) is the foundational theorem from which it is derived. | Background and methodology formulation ([Section 2.10.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L255-L269) and [3.8.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L376-L384)). | Qualify formula name: refer to it as the Interactive Response Time Law (derived from Little's Law). State clearly that $X$ is achieved throughput, $N$ is concurrency, and $R$ is residence/response time. |
| **METH-03** | Closed-loop generator self-throttling is identical to Coordinated Omission. | **PARTIALLY SUPPORTED** | [Gil Tene (2015)](https://www.azul.com/resources/presentations/how-not-to-measure-latency/); [Schroeder et al. (2006)](https://www.usenix.org/legacy/event/nsdi06/tech/schroeder.html). Self-throttling is a physical queueing feedback mechanism. Coordinated Omission is a measurement sampling artifact where load generators fail to log intended arrival intervals during delays. | Applicable to load testing tools executing synchronous client loops (`k6` standard scenarios, `ab`, `wrk`). | Construct validity and metric interpretation ([Section 2.10](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L242-L246), [3.14](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L421-L427)). | Disentangle terms: Closed-loop testing limits queue depth via user-level feedback. Coordinated omission is the resulting measurement failure to sample the virtual queue, biasing latency histograms downward. |
| **METH-04** | Reporting means across only 3 process trials cannot establish statistical significance or confidence intervals on the non-stationary JVM. | **SUPPORTED** | [Georges, Buytaert, & Eeckhout (OOPSLA 2007)](https://doi.org/10.1145/1297027.1297033); [Kalibera & Jones (ISMM 2013)](https://doi.org/10.1145/2464157.2464160). 3 trials yield $df=2$, giving Student's $t$ multiplier $t_{0.025, 2} = 4.303$. Non-stationary JIT optimizations and bimodal GC pauses invalidate normality assumptions. | Valid for all managed runtimes with adaptive JIT compilation (HotSpot C1/C2). | Justifies experimental design in [Section 3.12](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L409-L414) and prevents methodological rejection by thesis examiners. | Retain methodological qualification: classify 3-trial datasets as *qualitative mechanism-isolation engineering trials* confirming discrete JFR/carrier phenomena, not inferential population samples. Report min/max/median, not confidence intervals. |
| **METH-05** | The k6 ramp-up stage (15 s) was excluded from steady-state metric calculations. | **CONTRADICTED** | [scripts/normalize_evidence.py](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/normalize_evidence.py#L40-L69) lines 44–69. `k6_metrics()` iterates through all lines of raw k6 JSON and aggregates every request and duration point from timestamp 0 to end-of-test without stage filtering. | Benchmark execution in `run-benchmark.sh`. | Affects accuracy of reported steady-state throughput and percentiles across all matrix results ([Section 5](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L480-L560)). | Correct the claim in thesis text: acknowledge that the summary evidence represents the whole test window (55 s) including ramp-up and ramp-down, or update the script to filter metrics between $T+15\text{s}$ and $T+45\text{s}$. |
| **METH-06** | An 8-second startup delay plus a single GET `/products` health check provides adequate JVM warm-up. | **PARTIALLY SUPPORTED** | [Georges et al. (2007)](https://doi.org/10.1145/1297027.1297033), Section 3.2. A single request to `/products` initializes Tomcat acceptors and Spring container beans, but does not warm up the C2 compiler, Jackson serializers, or Hibernate caches for `/payments` or `/orders`. | Java 21 HotSpot Tiered Compilation (`-XX:+TieredCompilation`). | Threats to validity ([Section 3.14](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L421-L427)). Cold-start execution occurs during the initial 15s ramp-up. | Qualify in methodology: document that initial requests execute in the interpreter or C1 compiler. Emphasize that because `/payments` is dominated by a 500 ms `sleep`, JIT compilation overhead is negligible compared to sleep duration. |
| **METH-07** | The CALM Theorem proves that no runtime optimization can eliminate coordination delay in `/payments`. | **CONTRADICTED** | [Hellerstein & Alvaro (CACM 2020)](https://doi.org/10.1145/3397885); [Ameloot et al. (PODS 2011)](https://doi.org/10.1145/1989484.1989491). CALM establishes when distributed programs can have consistent, coordination-free distributed implementations. In-memory locking is governed by [Bernstein (1966)](https://doi.org/10.1109/PGEC.1966.264565) and [Amdahl (1967)](https://doi.org/10.1145/1465482.1465560). | Single-node multi-threading vs. distributed consensus protocols. | Theoretical framing in [Section 2.1.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L160-L175) and [3.6.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L340-L355). | Remove CALM theorem citation as proof for local mutex serialization. Replace with Amdahl's Law (1967) and Bernstein's Conditions (1966) for data access hazards on shared mutable state. |
| **METH-08** | Neil Gunther's Universal Scalability Law (USL) directly models k6 closed-loop VU saturation on `/payments`. | **PARTIALLY SUPPORTED** | [Holtman & Gunther (arXiv:0809.2541, 2008)](https://arxiv.org/abs/0809.2541). USL models throughput scaling $C(N)$ across concurrency levels $N$ using contention ($\sigma$) and coherency ($\kappa$) parameters. | Applies to multi-node or multi-core concurrency scaling curves across varied load levels. | Background in [Section 2.10.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L255-L269). | Qualify citation: cite USL as general context for concurrency contention, but avoid claiming the thesis empirically validated USL parameters, since the testbed tested fixed concurrency without non-linear curve fitting. |
| **METH-09** | OpenJDK container detection truncates carrier parallelism to 1 when cgroup quota is $\le 1.0$ CPU. | **SUPPORTED** | OpenJDK source `src/hotspot/os/linux/osContainer_linux.cpp`; `VirtualThread.java` (`ForkJoinPool.defaultForkJoinWorkerThreadFactory`). JBS [JDK-8281181](https://bugs.openjdk.org/browse/JDK-8281181). | Linux cgroups v1 (`cpu.cfs_quota_us`) and cgroups v2 (`cpu.max`) with quota $\le$ period. | Validates realism of the one-carrier stress configuration in [Section 3.9](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L385-L390) and [7.2](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L690-L700). | Retain finding: defend `parallelism=1` not as an artificial edge case, but as the exact default JVM behavior in 1-CPU containerized cloud deployments. |
| **METH-10** | Apple Silicon Darwin kernel QoS scheduling demotes HotSpot carrier threads to E-cores, causing 300–400% latency variance. | **PARTIALLY SUPPORTED** | [Oakley (2023–2024)](https://eclecticlight.co/mac-arm/); Apple Darwin XNU QoS specifications. Darwin schedules threads by QoS; background QoS threads run exclusively on E-cores. However, HotSpot carrier threads run under default process QoS, not background QoS. | Apple Silicon (M1–M4) macOS Darwin kernel. | Threats to internal validity in [Section 3.14](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L421-L427) and [8.5](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L720-L735). | Treat Darwin QoS and thermal throttling as a *plausible confounding factor* explaining platform noise, but qualify that HotSpot carrier thread core affinity was not directly instrumented via `ktrace`. |
| **METH-11** | Docker Desktop on macOS introduces 1.5–3.5 ms network jitter and latency skew via user-space VM proxying (`vpnkit`). | **SUPPORTED** | [Docker Desktop macOS Networking Architecture](https://docs.docker.com/desktop/networking/); [VPNKit GitHub Repository](https://github.com/moby/vpnkit). Host-to-container port mapping traverses a user-space proxy rather than native Linux bridge interfaces. | Docker Desktop on macOS (Apple Virtualization/HyperKit VM). | Explains baseline latency skew between embedded H2 (~304 ms) and Dockerized PostgreSQL (~310 ms) in [Section 4.4](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L440-L445) and [5.11](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L540-L550). | Retain finding: use VM proxy translation delay to justify separating H2 and PostgreSQL experimental tracks and warning against generalizing macOS container latency to bare-metal Linux. |
| **METH-12** | Default JFR configuration (`profile.jfc` and `default.jfc`) suppresses `jdk.VirtualThreadPinned` events lasting < 20 ms. | **SUPPORTED** | OpenJDK source `src/jdk.jfr/share/conf/jfr/profile.jfc` line 201; `default.jfc` line 201. Both define `<event name="jdk.VirtualThreadPinned"><setting name="threshold">20 ms</setting></event>`. | JDK 21, 22, 23, 24. | Observability and measurement threats ([Section 3.10](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L391-L396), [3.14](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L421-L427)). | Document the 20 ms threshold in the observability protocol. Note that while 500 ms experimental pins were reliably captured, sub-20 ms pins in real applications would be masked unless overridden with `threshold=0ms`. |
| **METH-13** | Native execution (JNI `nanosleep`) captures carrier threads while emitting zero `jdk.VirtualThreadPinned` events. | **SUPPORTED** | OpenJDK HotSpot source `src/hotspot/share/prims/continuationFreezeThaw.cpp`. `jdk.VirtualThreadPinned` is emitted inside `freeze()` when unmounting fails. Native calls (`_thread_in_native`) never call `VirtualThread.park()` or `freeze()`. | JDK 21 LTS through JDK 25. | Solves the empirical puzzle of 27 `/native` runs showing carrier stalls but zero pinning events ([Section 2.8](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L230-L235), [5.10](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L530-L540)). | Retain finding as a primary contribution: proves that absence of JFR pinning events does not prove absence of carrier occupation. |
| **METH-14** | Carrier thread parking induces Linux CFS bandwidth throttling spikes during container quota replenishment. | **UNVERIFIABLE** | Linux Kernel Mailing List (LKML) discussions (2023). No peer-reviewed paper or reproducible benchmark exists showing carrier unmounting triggering CFS throttling in Java 21 containers. | Linux CFS bandwidth controller (`cpu.cfs_quota_us`). | Speculative lead (P3). | Exclude from core empirical claims and migration guidelines. Mention only as an unverified external hypothesis in future work ([Section 8.7](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L740-L750)). |

---

## 3. Contradictions and Overstatements

### 3.1 The "Generator Artifact vs. Server Capacity" Contradiction
In [Finding 5.1.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/virtual-threads-research-scout-report.md#L237-L244) and [Triage CL-03](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/research-triage.md#L80), the scout report asserts:
> *"The 2 req/s throughput floor on `/payments` is an artifact of the closed-loop load model ($N=10$, $R\approx 5\text{s}$), not a universal server capacity limit. Under an open arrival model, the server would experience an unbounded queue..."*

This statement contains an internal mathematical contradiction:
- If a server experiences an *unbounded queue* when an open arrival rate exceeds 2 req/s, that occurs **precisely because the server's processing capacity ceiling is 2 req/s**.
- In queueing theory, an open $M/M/1$ or $G/G/1$ queue is stable if and only if $\lambda < \mu$. When service time is fixed to $S = 0.5\text{ s}$ inside an exclusive mutex, the maximum service rate is $\mu = 1 / S = 2.0\text{ req/s}$. If offered load $\lambda = 5\text{ req/s}$ is injected, the completion rate remains exactly 2.0 req/s while the queue grows towards infinity at a rate of $\lambda - \mu = 3\text{ req/s}$.
- The 2.0 req/s throughput is **both** the saturation capacity ceiling of the server endpoint **and** the throughput achieved by 10 closed-loop VUs whose round-trip time is forced to $N \times S = 10 \times 0.5 = 5.0\text{ s}$.
- What the closed-loop workload model alters is **not the capacity ceiling**, but the **arrival process**: closed-loop users self-throttle, capping queue length to $N=10$ and preventing memory exhaustion. Stating that 2 req/s is "not a server capacity limit" is mathematically false and would be immediately challenged by performance examiners.

### 3.2 Manifest Contract vs. Normalization Code Implementation Discrepancy
The run manifests generated by `run-benchmark.sh` state:
```json
"stage_definition": "15s ramp-up, 30s hold, 10s ramp-down",
"warmup_rule": "8s application startup plus products health check; k6 ramp-up excluded from steady-state interpretation",
"measurement_interval": "30s hold stage"
```
However, inspecting `scripts/normalize_evidence.py` lines 44–69 reveals:
```python
def k6_metrics(path: Path) -> dict:
    durations: list[float] = []
    requests = failures = 0
    endpoints: set[str] = set()
    for line in path.read_text(errors="replace").splitlines():
        ...
        if item.get("metric") == "http_req_duration" and item.get("type") == "Point":
            ...
            durations.append(float(point.get("value", 0)))
        if item.get("metric") == "http_reqs" and item.get("type") == "Point":
            requests += 1
```
The script aggregates every request point across the entire 55-second run. 
- In the primary synchronization matrix, Virtual Threads + `synchronized` completed 108 requests. Over 55 seconds, this is $108 / 55 = 1.96\text{ req/s}$. Over the 30-second hold stage alone, 108 requests would imply $3.6\text{ req/s}$ (which is physically impossible for a 500 ms serialized lock!).
- Therefore, the 108 requests represent the **entire 55-second run** (including ramp-up and ramp-down).
- The thesis draft must either correct the manifest description (acknowledging that reported metrics represent the full test profile) or modify the Python extractor to filter points within the steady-state interval $[T+15\text{s}, T+45\text{s}]$.

### 3.3 Theoretical Overreach: Citing the CALM Theorem for Local Locking
In [Finding 10.9](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/virtual-threads-research-scout-report.md#L547-L551) and [Triage CL-21](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/research-triage.md#L98), the report invokes the CALM Theorem ([Hellerstein & Alvaro 2020](https://doi.org/10.1145/3397885)) to explain why replacing `synchronized` with `ReentrantLock` does not increase throughput on `/payments`.
- The CALM Theorem (*Consistency As Logical Monotonicity*) applies strictly to **distributed systems**, defining the boundary where distributed nodes can compute consistent views without communication/consensus rounds (e.g. CRDTs vs. Paxos/2PC).
- Applying CALM to single-process Java threads competing for an in-memory lock is a conceptual category error.
- The correct theoretical frameworks for local mutex bottlenecks are:
  1. **Bernstein's Conditions (1966):** Two concurrent operations can execute deterministically without coordination if and only if their read/write sets are disjoint ($I_1 \cap O_2 = \emptyset, O_1 \cap I_2 = \emptyset, O_1 \cap O_2 = \emptyset$).
  2. **Amdahl's Law (1967):** The speedup of an application is bounded by its serialized execution fraction ($1 / s$). If $s = 1.0$, speedup is identically 1, regardless of thread unmounting.

### 3.4 Conflating Queueing Dynamics with Measurement Bias
The scout report repeatedly blurs the line between **closed-loop queueing behavior** and **Coordinated Omission**:
- *Closed-loop self-throttling* is an inherent architectural property of closed systems: an arrival is triggered only by a completion.
- *Coordinated Omission* ([Gil Tene](https://www.azul.com/resources/presentations/how-not-to-measure-latency/)) is a **measurement failure**: when a system pauses, a load tester that measures only completed requests fails to record the time that dropped or backlogged requests *should* have waited, resulting in artificially truncated latency histograms.
- Conflating them obscures whether the thesis is discussing application system dynamics or benchmark tool measurement error.

---

## 4. Highest-Priority Corrections

The following specific corrections should be incorporated into the thesis draft:

1. **Correct the Interpretation of the 2 req/s Floor in [Section 2.10.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L255-L269) and [Section 6.2](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L486-L510):**
   - *Current phrasing:* "2 req/s is an artifact of closed-loop VU self-throttling, not a server capacity limit."
   - *Corrected phrasing:* "The 2.0 req/s throughput floor represents the maximum theoretical service capacity of an exclusive 500 ms critical section ($\mu = 1 / S$). What the closed-loop load model governs is queue accumulation: with 10 VUs, the system stabilizes at an average response time of $R = N / \mu = 10 / 2 = 5.0\text{ s}$, preventing the unbounded queue explosion that an open arrival process with $\lambda > 2\text{ req/s}$ would induce."
2. **Harmonize Manifest Metadata and Metric Normalization in [Section 3.8](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L369-L375) and [Section 3.10](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L391-L396):**
   - Explicitly clarify in Section 3.8 and Section 3.10 whether reported request counts and latency percentiles represent the aggregate 55-second execution window (ramp-up + hold + ramp-down) or strictly the 30-second hold stage. Acknowledge that `normalize_evidence.py` aggregates across the entire file.
3. **Replace the CALM Theorem with Bernstein's Conditions in [Section 2.1.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L160-L175) and [Section 3.6.1](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L340-L355):**
   - Remove references attributing in-memory mutex bottlenecks to the CALM Theorem. Attribute the necessity of mutual exclusion to shared mutable state conflicts under Bernstein's Conditions, and throughput limits to Amdahl's serialized execution fraction.
4. **Clarify Terminology: Interactive Response Time Law vs. Little's Law:**
   - In Section 2.10.1, reference the formula $R = (N / X) - Z$ (or $X = N / R$ when $Z = 0$) as the **Interactive Response Time Law**, noting that it is derived from Little's Law applied to the closed user-system loop.
5. **Acknowledge the 20 ms JFR Threshold as a Construct Validity Threat in [Section 3.14](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L421-L427):**
   - State clearly that benchmark runs utilized `-XX:StartFlightRecording=settings=profile`, which applies a default threshold of 20 ms for `jdk.VirtualThreadPinned`. While this captured the 500 ms synthetic test cases, it leaves pinning events between 1 and 19 ms unrecorded. Recommend `threshold=0ms` for production audit guidelines.

---

## 5. Unresolved Questions

1. **CFS Bandwidth Throttling on Carrier Parking (Finding 11.2.D.1):**  
   - *Status:* Unverified.
   - *Missing Evidence:* No empirical JVM data or kernel traces demonstrating that virtual thread unmounting induces Linux CFS quota throttling bursts.
   - *Thesis Impact:* Non-blocking. The thesis testbed is macOS Darwin; container quota throttling does not affect macOS results. Should be cited only as a speculative consideration for Kubernetes deployments in Future Work ([Section 8.7](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/thesis-draft-skeleton.md#L740-L750)).
2. **Direct Instrumentation of Darwin Core Demotion on Apple Silicon:**  
   - *Status:* Partially Verified.
   - *Missing Evidence:* While Howard Oakley's Darwin kernel analyses establish that low-QoS threads run on E-cores, HotSpot's specific carrier thread pool affinity was not instrumented via macOS `ktrace` or `powermetrics` during test runs.
   - *Thesis Impact:* Low. The thesis properly treats hardware asymmetry as a threat to internal validity explaining inter-run noise rather than a core experimental variable.
3. **True Steady-State Latency Percentiles Excluding Ramp-Up:**  
   - *Status:* Unresolved in existing normalized data.
   - *Missing Evidence:* Metric values filtered strictly to the window $15\text{s} \le t \le 45\text{s}$.
   - *Thesis Impact:* Minor for throughput (since requests during ramp-up and ramp-down were constrained by the same 500 ms lock), but could slightly shift p95 and p99 latency figures.

---

## 6. Sources Consulted

1. **Denning, P. J., & Buzen, J. P. (1978).** *The Operational Analysis of Queuing Network Models.* ACM Computing Surveys, 10(3), 225–261.  
   *URL:* [https://doi.org/10.1145/356744.356747](https://doi.org/10.1145/356744.356747)  
   *Relevance:* Foundational proof of operational laws in closed networks, including the Interactive Response Time Law ($R = N/X - Z$) and asymptotic saturation bounds ($X_{max} = 1 / D_{max}$).
2. **Lazowska, E. D., Zahorjan, J., Graham, G. S., & Sevcik, K. C. (1984).** *Quantitative System Performance: Computer System Analysis Using Queueing Network Models.* Prentice-Hall.  
   *URL:* [http://web.cs.ucla.edu/~kwh/courses/common/Lazowska.QSP.pdf](http://web.cs.ucla.edu/~kwh/courses/common/Lazowska.QSP.pdf)  
   *Relevance:* Chapters 3 and 4 establish asymptotic bounds analysis, proving that bottleneck service centers impose hard capacity ceilings in both open and closed systems.
3. **Schroeder, B., Wierman, A., & Harchol-Balter, M. (2006).** *Open Versus Closed: A Cautionary Tale.* In *Proceedings of the 3rd USENIX Symposium on Networked Systems Design and Implementation (NSDI '06)*, pp. 239–252.  
   *URL:* [https://www.usenix.org/legacy/event/nsdi06/tech/schroeder.html](https://www.usenix.org/legacy/event/nsdi06/tech/schroeder.html)  
   *Relevance:* Primary source demonstrating the divergence in queue length and tail latency between open and closed workload generators.
4. **Georges, A., Buytaert, D., & Eeckhout, L. (2007).** *Statistically Rigorous Java Performance Evaluation.* In *Proceedings of the 22nd ACM SIGPLAN Conference on Object-Oriented Programming, Systems, Languages, and Applications (OOPSLA '07)*, pp. 57–76.  
   *URL:* [https://doi.org/10.1145/1297027.1297033](https://doi.org/10.1145/1297027.1297033)  
   *Relevance:* Landmark paper proving the necessity of distinguishing between-run from within-run variance and verifying steady-state warm-up in HotSpot benchmarking.
5. **Kalibera, T., & Jones, R. (2013).** *Rigorous Benchmarking in Reasonable Time.* In *Proceedings of the International Symposium on Memory Management (ISMM '13)*, pp. 63–74.  
   *URL:* [https://doi.org/10.1145/2464157.2464160](https://doi.org/10.1145/2464157.2464160)  
   *Relevance:* Establishes that small sample sizes ($N=3$) cannot support parametric confidence intervals on modern non-deterministic runtime systems.
6. **Tene, G. (2015).** *How NOT to Measure Latency.* Azul Systems Presentation.  
   *URL:* [https://www.azul.com/resources/presentations/how-not-to-measure-latency/](https://www.azul.com/resources/presentations/how-not-to-measure-latency/)  
   *Relevance:* Original definition and mathematical derivation of *Coordinated Omission* as a measurement sampling bias in load generation tools.
7. **Holtman, J., & Gunther, N. J. (2008).** *Getting in the Zone for Successful Scalability.* arXiv:0809.2541 [cs.PF].  
   *URL:* [https://arxiv.org/abs/0809.2541](https://arxiv.org/abs/0809.2541)  
   *Relevance:* Proves the structural equivalence between the Universal Scalability Law (USL) and load-dependent machine repairman closed queueing networks.
8. **Hellerstein, J. M., & Alvaro, P. (2020).** *Keeping CALM: When Distributed Consistency is Easy.* Communications of the ACM, 63(9), 72–81.  
   *URL:* [https://doi.org/10.1145/3397885](https://doi.org/10.1145/3397885)  
   *Relevance:* Definitive publication of the CALM Theorem, confirming its scope is restricted to distributed program consistency and coordination avoidance.
9. **Bernstein, A. J. (1966).** *Analysis of Programs for Parallel Processing.* IEEE Transactions on Electronic Computers, EC-15(5), 757–763.  
   *URL:* [https://doi.org/10.1109/PGEC.1966.264565](https://doi.org/10.1109/PGEC.1966.264565)  
   *Relevance:* Foundational formalization of read/write sets and data dependence conditions requiring synchronization in shared-memory computing.
10. **Amdahl, G. M. (1967).** *Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities.* In *AFIPS Conference Proceedings*, Vol. 30, pp. 483–485.  
    *URL:* [https://doi.org/10.1145/1465482.1465560](https://doi.org/10.1145/1465482.1465560)  
    *Relevance:* Formal proof that speedup is constrained by the sequential component of an algorithm.
11. **OpenJDK HotSpot Source Code Repository:**
    - `profile.jfc`: [src/jdk.jfr/share/conf/jfr/profile.jfc](https://github.com/openjdk/jdk/blob/master/src/jdk.jfr/share/conf/jfr/profile.jfc) (Verifies 20 ms pinning threshold).
    - `continuationFreezeThaw.cpp`: [src/hotspot/share/prims/continuationFreezeThaw.cpp](https://github.com/openjdk/jdk/blob/master/src/hotspot/share/prims/continuationFreezeThaw.cpp) (Verifies that native calls bypass `freeze()` and emit zero JFR pinning events).
    - `osContainer_linux.cpp`: [src/hotspot/os/linux/osContainer_linux.cpp](https://github.com/openjdk/jdk/blob/master/src/hotspot/os/linux/osContainer_linux.cpp) (Verifies cgroup CPU quota detection and single-carrier parallelism assignment).
12. **Oakley, H. (2023–2024).** *How macOS Manages Threads on Apple Silicon.* The Eclectic Light Company.  
    *URL:* [https://eclecticlight.co/mac-arm/](https://eclecticlight.co/mac-arm/)  
    *Relevance:* Reverse-engineering of Apple Silicon XNU kernel QoS thread scheduling, core allocation policies, and frequency scaling.


---

## 7. Mandatory Review Findings Prior to Thesis Finalization

Before the thesis's results, causal arguments, and engineering guidelines can be considered reliable and defensible against academic scrutiny, the author must review and resolve the following three findings:

1. **Finding METH-01 (Capacity Floor vs. Self-Throttling):**  
   The thesis text in Section 2.10.1 and Section 6.2 must be corrected to state that 2.0 req/s is the **saturation capacity ceiling** of the 500 ms serialized critical section, not merely an artificial generator illusion. If the thesis asserts that 2.0 req/s is "not a server capacity limit," any systems or queueing examiner will reject the claim on mathematical grounds.
2. **Finding METH-05 (Pipeline Aggregation Window):**  
   The thesis must reconcile the discrepancy between the manifest claim ("ramp-up excluded") and the data pipeline implementation in `normalize_evidence.py`. The author must either filter the raw k6 JSON metrics to the 30-second steady-state window ($[15\text{s}, 45\text{s}]$) or explicitly document in Section 3.8 and Section 3.10 that the reported request totals and latencies represent the entire 55-second run window.
3. **Finding METH-07 (CALM Theorem Misapplication):**  
   The author must remove the CALM Theorem citation as the causal justification for local `ReentrantLock` and monitor bottlenecks in Section 2.1.1 and Section 3.6.1, replacing it with Bernstein's Conditions (1966) and Amdahl's Law (1967).

# Independent Referee Review — Adjudication of Stage 1.1 & Formal Decision Record

**Document Identity:** Adversarial Peer Review Adjudication, Evidentiary Stratification & Stage 1.2 Charter  
**Target Document:** Stage 1.1 Evidence Consolidation Reports ([`artifact-inventory-summary.md`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/artifact-inventory-summary.md), [`run-family-analysis.md`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-analysis.md), [`metric-recalculation-audit.md`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/metric-recalculation-audit.md))  
**Auditor / Adjudicator:** Virtual Threads Research & Evidence Auditor  
**Date of Audit & User Ratification:** 2 November 2026  
**Adjudication Scope:** Complete Adversarial Referee Review (Findings 1 through 5, Gates 1 through 3, and Human Ratification Directives)  

---

## 1. Executive Summary & Adjudication Ledger

An adversarial peer review of the Stage 1.1 evidence-consolidation deliverables was conducted by an independent external referee (GPT). Rather than defending previous work or accepting the referee's assertions uncritically, every material finding has been audited against the physical repository tree, execution manifests, source code, and benchmark outputs.

Every substantive finding of the referee has been verified as **technically sound and supported by repository evidence**. The referee correctly identified five material methodological vulnerabilities and imprecise formulations in the Stage 1.1 report:
1. **Conflation of Matrix Rows with Executions:** Manifest `run-manifest-template.json` was counted as an execution in summary text, obscuring that the 120 matrix rows represent **119 actual executions plus 1 schema template**.
2. **Overstated Cryptographic Scope:** The claim of "100% cryptographically verified" conflated local byte-integrity checks of result JSONs and JFR binaries (368 SHA-256 checks) with an end-to-end provenance chain extending from source code and compiled binaries to execution outputs.
3. **Conflation of Scheduler Parallelism with Container Quotas:** Single-carrier runs (`parallelism=1`) were characterized as "1-CPU container equivalence" when they are actually bare-metal macOS host runs with JVM scheduler concurrency constraints.
4. **Unrecorded Inferred Defaults:** The matrix generator assigned default values (`parallelism=8`, `maxPoolSize=256`, and `h2`) without explicitly labeling them as inferred deductions.
5. **Universal Steady-State Assumptions:** Applying a uniform $t \in [15\text{s}, 45\text{s}]$ window filtered by completed-request timestamps ignores boundary queue transit times, definition of $t_0$, and distinct workload equilibrium dynamics.

The table below summarizes the formal adjudication for every finding:

| Review Finding | Referee Observation | Adjudication | Core Justification & Verification Target |
|---|---|:---:|---|
| **1.1 Physical Census** | 504 total result artifacts across 5 types reproduced. | **AGREE** | Verified via [`generate_artifact_inventory.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/generate_artifact_inventory.py); exact match across all 504 files. |
| **1.2 Manifests vs Executions** | 120 matrix rows = 112 executable manifests + 1 template + 6 Docker PG + 1 CPU control. | **AGREE** | Verified in [`generate_run_family_matrix.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/generate_run_family_matrix.py#L70-L96); template is a non-executable reference file. |
| **1.3 Carrier Execution Totals** | 95 (1-carrier) + 18 (8-carrier) + 6 (4-carrier) = 119 executions (+ 1 template). | **AGREE** | Verified by summing carrier columns in [`run-family-matrix.csv`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-matrix.csv); total executions is 119. |
| **2.1 Metric Reproducibility** | Recalculation reproduces 0.7645% throughput delta and 0.184% p50 delta; 368 SHA matches. | **AGREE** | Verified by running [`recalculate_metrics.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/recalculate_metrics.py) and [`validate_normalized_evidence.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/validate_normalized_evidence.py). |
| **2.2 Cryptographic Scope** | "100% cryptographically verified" is too broad; does not verify JAR, dylib, or build chain. | **AGREE** | Verified: [`generate_artifact_inventory.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/generate_artifact_inventory.py#L314-L343) only verifies k6 JSON and JFR files; target JARs have been recompiled. |
| **3.1 Scheduler vs CPU Quota** | `parallelism=1` is a JVM scheduler setting, not a 1-vCPU container quota; host is Apple M1 (8 cores). | **AGREE** | Verified in [`run-manifest-20261015-143108.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/results/run-manifest-20261015-143108.json#L14-L17) and [`docker-compose.yml`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docker-compose.yml#L18-L21). |
| **3.2 Inferred Defaults** | Missing `java_extra_options` mapped to 8 carriers / 256 max pool size and H2 assigned broadly. | **AGREE** | Verified in [`generate_run_family_matrix.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/generate_run_family_matrix.py#L124-L138); deductions are physically valid but unrecorded. |
| **4.1 Arithmetic Soundness** | Recalculation math ($109/55\text{s}$ vs $59/30\text{s}$) is exact; author conflation corrected. | **AGREE** | Verified: exact throughput delta is 0.764526% ($5/654$); median latency delta is 0.183968%. |
| **4.2 Analysis Window Limitations** | 15–45s window has no stage markers, uses completion $t_0$, fixed 55s denominator, and boundary effects. | **AGREE** | Verified in [`isolated-load-test.js`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/k6/isolated-load-test.js#L12-L21) and [`recalculate_metrics.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/recalculate_metrics.py#L87-L133). |
| **5.1 Heterogeneity of Records** | 76 records combine 1-carrier, 8-carrier, Java 21, Java 24, and 1 standalone unmanifested record. | **AGREE** | Verified in [`normalized-evidence.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/resources/static/data/normalized-evidence.json); cannot be treated as one homogeneous primary corpus. |
| **5.2 Admission Status** | Dataset preserves measured evidence but does not encode scientific admission or exclusion gates. | **AGREE** | Verified: normalization is an ingestion mechanism, not a peer-reviewed admission policy. |
| **Gate 1 Decision** | Stratify 119 executions without overlap; separate Java 21 primary matrix from Java 24/25. | **RATIFIED** | Approved in principle by human user; exhaustive 119-execution mapping established in Section 6. |
| **Gate 2 Decision** | Adopt dual reporting (whole-run + derived window); reject universal steady-state label. | **RATIFIED** | Approved by human user; preserves raw baseline numbers while exposing equilibrium analysis. |
| **Gate 3 Decision** | Proceed to Stage 1.2 forensic investigation on JNI, telemetry, datasource, and Docker PG. | **RATIFIED** | Approved by human user; prioritized research charter defined in Section 8. |

---

## 2. Detailed Finding-by-Finding Adjudication

To maintain scientific rigor, each finding is decomposed into **Direct Observations**, **Calculations**, **Interpretations**, and **Assumptions**.

### 2.1 Finding 1: Artifact Census, Template Exclusion, and Run Counts

#### Referee Claims
1. The physical census of 504 result artifacts (113 manifest JSONs, 263 total JSONs, 150 k6 JSONs, 132 JFRs, 104 CSVs, 5 Markdown reports) is reproducible.
2. The matrix contains 120 rows representing 112 executable manifests, 1 manifest template, 6 unmanifested PostgreSQL trials, and 1 standalone CPU control artifact.
3. Carrier totals (95 1-carrier + 18 8-carrier + 6 4-carrier = 119 executions) are correct only when the template is excluded.
4. The report should state "119 executions plus one template", not "120 runs."

#### Adjudication: AGREE

- **Direct Observations:**
  - Filesystem walk of `results/` enumerates exactly 504 files: 113 manifests matching `run-manifest-*.json`, 150 load test JSONs, 132 JFR binaries in `results/jfr/`, 104 telemetry CSVs matching `telemetry-*.csv`, and 5 narrative Markdown reports.
  - Manifest file [`results/run-manifest-template.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/results/run-manifest-template.json) contains schema keys with placeholder values (`"target_vus": "0"`, `"endpoint_or_workload": "orders|payments|products|mixed"`).
  - Six PostgreSQL trials exist as unmanifested k6 outputs: `results/docker-pg-orders-pool{1,10}-trial{1,2,3}.json`.
  - One CPU control artifact exists as an unmanifested k6 output: `results/cpu-control-20261008.json`.
- **Calculations:**
  - Total manifests on disk: 113.
  - Executable process manifests: $113 - 1\text{ (template)} = 112$.
  - Total process executions: $112\text{ manifests} + 6\text{ Docker PG} + 1\text{ CPU control} = \mathbf{119\text{ executions}}$.
  - Carrier sum across executions: $95\text{ (1-carrier)} + 18\text{ (8-carrier)} + 6\text{ (4-carrier)} = \mathbf{119\text{ executions}}$.
  - Total matrix rows in [`run-family-matrix.csv`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-matrix.csv): $119\text{ executions} + 1\text{ template row} = \mathbf{120\text{ rows}}$.
- **Interpretations:**
  - Describing the matrix as "120 runs" in [`run-family-analysis.md#L17`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-analysis.md#L17) was a semantic error that conflated a non-executable orchestration template with an actual benchmark execution.
- **Assumptions:**
  - Previous audits assumed all files matching `run-manifest-*.json` represented completed or attempted benchmark runs.

---

### 2.2 Finding 2: Reproducibility, Cryptographic Integrity, and Hash Verification Scope

#### Referee Claims
1. The reported numbers (76 normalized records, 75 manifest-backed + 1 standalone CPU, 76 k6 JSONs, 75 JFRs, 504 inventory rows, 368 hash matches, validator passing, and 0.7645% / 0.184% deltas) are reproducible.
2. The phrase "100% cryptographically verified" is too broad. It establishes byte identity against locally recorded hashes for k6 result and JFR files, but does not establish an end-to-end provenance chain, nor did the inventory script independently verify application-JAR, native-library, or telemetry hashes.

#### Adjudication: AGREE (with qualification on telemetry integrity)

- **Direct Observations:**
  - Running [`recalculate_metrics.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/recalculate_metrics.py) reproduces the 0.7645% throughput delta and 0.184% p50 latency delta.
  - Running [`validate_normalized_evidence.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/validate_normalized_evidence.py) validates all 76 static dataset records with zero errors.
  - Running [`generate_artifact_inventory.py`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/generate_artifact_inventory.py) executes 368 SHA-256 comparisons (151 against `normalized-evidence.json` and 217 against manifests), finding 0 mismatches.
  - An independent verification of all 92 companion telemetry CSV files against their manifest `telemetry_sha256` keys confirmed **92 matches out of 92 files (0 mismatches, 0 missing)**.
  - Manifests record `application_jar_sha256: "1f0809f0..."` and `native_library_sha256: "2a5e07da..."`.
  - The binary currently located at `target/virtual-threads-demo-0.0.1-SNAPSHOT.jar` has SHA-256 `d7c4c308...`, and `target/native/libnativeblocking.dylib` has SHA-256 `c1926a8e...`.
- **Calculations:**
  - Checked output file hashes: $76\text{ (norm results)} + 75\text{ (norm JFRs)} + 112\text{ (manifest results)} + 105\text{ (manifest JFRs)} = 368\text{ matches}$.
  - Companion telemetry hashes checked: 92 matches.
  - Build artifact hash match rate: 0% match against current `target/` files due to subsequent recompilation.
- **Interpretations:**
  - The 368 checks establish local byte consistency against recorded metadata for benchmark output artifacts. They protect against file truncation, bitrot, and accidental modification.
  - They do **not** establish a closed-chain cryptographic proof connecting the Git source revision to the compiled bytecodes used in the October 2026 test runs. Traceability to source code is maintained via Git commit hashes (`1ccb617`, `5f9936c`), but binary artifact identity cannot be independently re-verified from current disk contents alone.
- **Assumptions:**
  - The Stage 1.1 report assumed that verifying result and JFR outputs was sufficient to claim that the "entire project evidence base is 100% cryptographically verified."

---

### 2.3 Finding 3: Configuration Audit Limitations (Scheduler Parallelism vs. Container Quota & Inferred Defaults)

#### Referee Claims
1. The 1-, 4-, and 8-carrier populations are real, but the report overstates their physical interpretation.
2. `-Djdk.virtualThreadScheduler.parallelism=1` is an internal JVM ForkJoinPool scheduler setting, not a 1-vCPU container quota. The host is an Apple M1 with 8 logical cores; only Docker Compose PostgreSQL declared a CPU limit (`cpus: '0.5'`).
3. Local 1-carrier experiments should be described as scheduler-constrained mechanism-isolation experiments, not genuine one-vCPU container experiments.
4. The matrix generator infers defaults rather than measuring them (e.g., missing `java_extra_options` mapped to 8 carriers / 256 max pool size, assigning H2 database broadly). These should be labeled inferred unless independently recorded.

#### Adjudication: AGREE

- **Direct Observations:**
  - Manifests for local runs record: `"os": "Darwin 25.2.0..."`, `"cpu": "Apple M1"`, `"logical_processors": "8"`.
  - Manifests for single-carrier runs record: `"java_extra_options": "-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1"`.
  - File [`docker-compose.yml#L18-L21`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docker-compose.yml#L18-L21) records: `deploy.resources.limits.cpus: '0.5'`, `memory: 1G`.
  - In [`generate_run_family_matrix.py#L124-L138`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/generate_run_family_matrix.py#L124-L138), lines 124–128 assign `scheduler_parallelism = "8 (default)"` and `scheduler_max_pool_size = "256 (default)"` when `java_extra_options` is empty. Line 131 assigns `db_engine = "h2"` across all non-Docker runs.
- **Calculations:**
  - Apple M1 hardware has 8 physical cores (4 Firestorm performance cores + 4 Icestorm efficiency cores).
  - OpenJDK's default carrier parallelism when unconstrained is `Runtime.getRuntime().availableProcessors() = 8`.
- **Interpretations:**
  - Characterizing local single-carrier runs as "1-CPU container equivalence" ([`run-family-analysis.md#L143`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-analysis.md#L143)) was factually inaccurate. In a cgroup-constrained container, the Linux CFS scheduler throttles cumulative CPU time across all threads. In local runs, only the virtual thread scheduler pool was constrained to 1 carrier thread; JVM GC threads, JIT compilers, Tomcat acceptors, and k6 client processes ran concurrently across all 8 cores.
  - Local single-carrier runs must be scientifically classified as **JVM scheduler-constrained mechanism-isolation experiments**.
- **Assumptions:**
  - The matrix generator assumed HotSpot initialized an 8-carrier pool on all runs where flags were omitted, which is physically consistent with OpenJDK source code on macOS M1, but was not independently measured via a runtime probe.

---

### 2.4 Finding 4: Metric Recalculation Methodology (Arithmetic Soundness, Stage Boundaries, $t_0$, and Completed-Request Timestamps)

#### Referee Claims
1. The arithmetic is correct: $109 / 55\text{s} = 1.981818\text{ req/s}$, $59 / 30\text{s} = 1.966667\text{ req/s}$, relative throughput difference is $0.7645\%$, and p50 difference is $0.184\%$.
2. The proposed $15\text{s} - 45\text{s}$ window is not automatically authoritative across all families:
   - `k6/isolated-load-test.js` defines nominal stages, but emits no stage markers in the JSONL stream.
   - `recalculate_metrics.py` defines $t_0$ as the first metric timestamp, which is a completed-request timestamp, not the actual scenario start.
   - The representative file spans ~54.779s, whereas the script uses a fixed 55.0s denominator.
   - A completed-request timestamp is used for inclusion, so queue formation and ramp effects bleed across stage boundaries.
   - A nominal hold stage does not prove that each endpoint reached equilibrium.
3. The script's results are reproducible under its stated convention, but the convention requires endpoint/family-specific justification.

#### Adjudication: AGREE

- **Direct Observations:**
  - In [`k6/isolated-load-test.js#L12-L21`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/k6/isolated-load-test.js#L12-L21), options specify nominal stages: `{ duration: '15s', target: TARGET_VUS }`, `{ duration: '30s', target: TARGET_VUS }`, `{ duration: '10s', target: 0 }`. The script does not emit stage transition markers.
  - In raw k6 output [`results/run-10vus-20261008-142445.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/results/run-10vus-20261008-142445.json), the earliest timestamp among `Point` metrics is `2026-10-08T14:24:54.397699+02:00` with duration `507.896 ms`. The latest timestamp is `14:25:49.176216+02:00`.
  - In [`recalculate_metrics.py#L87-L92`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/scripts/recalculate_metrics.py#L87-L92), $t_0$ is defined as $\min \tau_k$. Lines 153–157 hardcode `full_duration_s = 55.0` and `steady_duration_s = 30.0`.
- **Calculations:**
  - Actual elapsed time between first completed request and last completed request in run `142445`:
    $$T_{\text{observed}} = 14:25:49.176216 - 14:24:54.397699 = \mathbf{54.778517\text{ s}}$$
  - Relative difference between nominal (55.0s) and observed span (54.78s): $0.403\%$.
  - Exact throughput relative delta:
    $$\Delta X_{\%} = \frac{|109/55 - 59/30|}{109/55} = \frac{5}{654} = \mathbf{0.764526\%}$$
  - Exact p50 latency relative delta:
    $$\Delta p_{50\%} = \frac{|4945.431 - 4954.529|}{4945.431} = \mathbf{0.183968\%}$$
- **Interpretations:**
  - Defining $t_0$ as the timestamp of the first completed request offsets the time window by the service time of that first request (~508 ms for `/native`).
  - Filtering by completion timestamp $\tau_k \in [15.0\text{s}, 45.0\text{s}]$ introduces boundary bleed: requests initiated during the ramp-up stage ($t \in [10\text{s}, 15\text{s}]$) that queued for 4.5 seconds complete inside the steady-state window and are included. Conversely, requests initiated near $t = 44\text{s}$ complete in the ramp-down window and are excluded.
  - Saturated bottleneck endpoints reach queue equilibrium within seconds, whereas uncontented endpoints (`/products`) reach equilibrium as soon as VUs stabilize, and ramp-sensitive platform threads (`platform-synchronized`) experience continuous queue buildup across the first 30 requests.
- **Assumptions:**
  - The recalculation audit assumed that the nominal 15s–45s hold stage defined in k6 configuration could be treated as a universally valid steady-state window across all endpoint types.

---

### 2.5 Finding 5: Scientific Admission of the Evidence Base & Corpus Stratification

#### Referee Claims
1. The 76 records are a valid linked evidence corpus, but not yet one homogeneous "primary corpus."
2. The collection combines 1-carrier and 8-carrier treatments, Java 21 and Java 24 conditions, distinct functional families, and 1 standalone uninstrumented artifact.
3. The normalized dataset preserves all records as measured evidence, but does not itself encode a complete scientific admission decision, correctness gate, or exclusion rationale.

#### Adjudication: AGREE

- **Direct Observations:**
  - Dataset [`src/main/resources/static/data/normalized-evidence.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/resources/static/data/normalized-evidence.json) contains exactly 76 trial records.
  - Of these 76 records:
    - 63 ran on Java 21 LTS, 6 ran on Java 24 GA, 6 ran on Java 25-ea, and 1 has `"jdk": "See CPU control artifact"`.
    - 63 ran with 1 carrier (`parallelism=1`), 12 ran with default 8 carriers (`parallelism=8`), and 1 ran with unrecorded carriers.
    - 75 have matching run manifests and JFR binary files; 1 record (`cpu-control-20261008`) has neither a manifest nor a JFR file.
- **Calculations:**
  - Carrier heterogeneity within normalized set: 82.9% single-carrier (63 runs) vs. 15.8% 8-carrier (12 runs) vs. 1.3% unrecorded (1 run).
  - JDK heterogeneity within normalized set: 82.9% JDK 21 (63 runs) vs. 7.9% JDK 24 (6 runs) vs. 7.9% JDK 25 (6 runs) vs. 1.3% unknown (1 run).
- **Interpretations:**
  - Normalizing records into a JSON document for dashboard presentation is a data-engineering pipeline step, not a scientific admission policy.
  - Treating all 76 records as a single "primary experimental corpus" introduces severe confounding variables: comparing 8-carrier synchronization latencies with 1-carrier latencies conflates carrier concurrency with lock mechanics.
- **Assumptions:**
  - Previous drafts assumed that passing `validate_normalized_evidence.py` constituted proof that the 76 records formed a peer-reviewable, unified primary corpus.

---

## 3. Theoretical Capacity Dynamics: The 2.0 req/s Argument

A central question raised in the referee review is whether the theoretical 2.0 req/s capacity argument has been applied within its valid assumptions. This section formalizes the operational and mathematical foundations of this argument.

### 3.1 Mathematical Derivation of the Bottleneck Ceiling

Let an HTTP endpoint execute a critical section protected by a mutual exclusion primitive (e.g. Java `synchronized`, `ReentrantLock`, or a binary `Semaphore`).
Let:
- $T_{\text{service}}$ be the duration spent holding the mutual exclusion lock. In [`PaymentService.java#L100-L106`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java#L100-L106), $T_{\text{service}} = \text{Thread.sleep}(500) = 0.500\text{ s}$.
- $T_{\text{overhead}}$ be the non-exclusive execution overhead (HTTP framing, JSON serialization, Spring MVC dispatch). In local benchmarks, $T_{\text{overhead}} \le 0.002\text{ s}$.
- $c = 1$ be the capacity of the mutual exclusion lock (strictly single-threaded entry).

By operational laws of computer system performance (Denning & Buzen, 1978), the maximum theoretical saturation service rate $X_{\max}$ of any single server resource is strictly bounded by the inverse of its service demand:
$$X_{\max} = \frac{c}{T_{\text{service}}} = \frac{1}{0.500\text{ s}} = \mathbf{2.000\text{ req/s}}$$

### 3.2 Required Assumptions for Validity

The claim that throughput is capped at $\approx 2.0\text{ req/s}$ is valid **only under the following joint conditions**:
1. **Strict Mutual Exclusion ($c=1$):** A single lock protects the entire slow operation. In [`PaymentService.java`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java#L58), `synchronized (monitor)` uses an instance-level monitor with a single static instance.
2. **Dominant Critical Section ($T_{\text{service}} \gg T_{\text{overhead}}$):** The holding time (500 ms) dwarfs request routing and TCP handshakes by over $250\times$.
3. **Continuous Queue Saturation ($N_{\text{active}} \ge 1$):** There must always be at least one request queued waiting to acquire the lock upon release. Under closed-loop testing with 10 VUs and a 100 ms client sleep (`sleep(0.1)`), the total cycle time per request is:
   $$R = T_{\text{wait}} + T_{\text{service}} + T_{\text{think}} \approx (9 \times 0.5\text{s}) + 0.5\text{s} + 0.1\text{s} = 5.1\text{s}$$
   By Little's Law, the mean queue length $L = X \times R \approx 2.0\text{ req/s} \times 5.0\text{s} = 10\text{ requests}$. The queue is permanently saturated from early ramp-up through ramp-down.

### 3.3 Boundaries and Misinterpretations

The 2.0 req/s argument has distinct boundaries that must not be violated:
1. **Throughput Does NOT Reveal Carrier Pinning:**
   Because the 500 ms critical section is the primary system bottleneck, **throughput is identical ($\approx 1.97\text{ req/s}$) across all three execution models**:
   - Platform threads: $1.97\text{ req/s}$
   - Virtual threads with `synchronized` (pinned): $1.97\text{ req/s}$
   - Virtual threads with `ReentrantLock` (unmounted): $1.96\text{ req/s}$
   Throughput alone *cannot* prove whether a virtual thread was pinned or unmounted.
2. **The True Pinning Signals are Orthogonal:**
   The evidence of carrier pinning is established by:
   - **JFR Recording Events:** 110 `jdk.VirtualThreadPinned` events for `synchronized` vs. 0 events for `ReentrantLock`.
   - **Cross-Endpoint Starvation:** When a virtual thread pins the single carrier on `/payments`, concurrent non-blocking requests on `/products` are completely starved. When `ReentrantLock` is used, `/products` continues serving requests at full speed.
3. **Inapplicability to Other Endpoints:**
   The 2.0 req/s ceiling does **not** apply to:
   - `no-lock-diagnostic`: where $c = \infty$ (concurrent sleep), yielding $X = 10 / (0.500 + 0.100) \approx 16.5\text{ req/s}$.
   - `/products`: in-memory non-blocking ($X \approx 97\text{ req/s}$).
   - `/orders`: database JDBC query ($X \approx 24\text{ req/s}$).
   - `/cpu`: computational SHA-256 loop ($X \approx 90\text{ req/s}$).

---

## 4. Verified Corrections to the Stage 1.1 Report

The following specific corrections to the Stage 1.1 deliverables are formally adopted:

### Correction 1: Manifest and Run Nomenclature
- **Previous Formulation:** "Total Benchmark Executions Tabulated: 120 runs (113 manifests + 6 unmanifested Docker Compose PostgreSQL runs + 1 standalone Oct 8 CPU control artifact)." ([`run-family-analysis.md#L17`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-analysis.md#L17))
- **Corrected Formulation:** The matrix tabulates **120 rows**, comprising **119 benchmark executions** (112 executable process manifests + 6 unmanifested Docker Compose PostgreSQL trials + 1 standalone CPU control artifact) plus **1 reference schema template** ([`run-manifest-template.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/results/run-manifest-template.json)).

### Correction 2: Physical Characterization of Single-Carrier Runs
- **Previous Formulation:** "1-CPU container equivalence. When cgroup quota <= 1.0, OpenJDK container detection sets availableProcessors() = 1." ([`run-family-analysis.md#L143`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-analysis.md#L143))
- **Corrected Formulation:** The local single-carrier experiments are **JVM scheduler-constrained mechanism-isolation experiments** configured via `-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1`. They execute on bare-metal Darwin (macOS Apple M1 with 8 logical cores). Only the Docker Compose PostgreSQL suite enforced an operating system cgroup limit (`deploy.resources.limits.cpus: '0.5'`).

### Correction 3: Scope of Cryptographic Verification
- **Previous Formulation:** "The project evidence base is 100% cryptographically verified." ([`artifact-inventory-summary.md#L192`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/artifact-inventory-summary.md#L192))
- **Corrected Formulation:** All **368 locally recorded SHA-256 checksums** for k6 result files and JFR recordings (151 in normalized evidence and 217 in manifests) match disk files with 100% integrity (0 corruption detected). An additional 92 manifest-linked telemetry CSV files also match their recorded checksums. However, build-artifact provenance for application JARs and native dynamic libraries relies on recorded Git commit metadata rather than immutable binary preservation, as targets in `target/` were recompiled during subsequent builds.

### Correction 4: Labeling of Configuration Defaults
- **Previous Formulation:** Unset JVM options and database settings were listed as measured matrix properties (`parallelism=8`, `maxPoolSize=256`, `db_engine=h2`).
- **Corrected Formulation:** All matrix values derived from JVM defaults or Spring Boot auto-configuration rather than explicit flags must be explicitly labeled **"inferred default"** in matrix documentation.

### Correction 5: Framing of Steady-State Metric Window
- **Previous Formulation:** Proposed replacing whole-run metrics with $t \in [15\text{s}, 45\text{s}]$ steady-state metrics as the definitive values across the thesis.
- **Corrected Formulation:** The $15\text{s} - 45\text{s}$ steady-state window is a **derived analytical filter**, valid for capacity and equilibrium analysis where queue saturation is verified. Both whole-run ($t \in [0, 55\text{s}]$) and steady-state metrics must be reported side-by-side for all ramp-sensitive workloads, explicitly documenting the completed-request timestamp convention.

---

## 5. Root-Cause Clarification of the Previous "18 Runs/Artifacts in Tier 5" Flaw

In the initial draft of the adjudication report, Tier 5 was designated as:
> *"Tier 5: Standalone, Excluded, or Defective Records (18 executions / artifacts)"*

This figure contained an egregious methodological conflation between **physical file counts** and **benchmark process executions**. The root-cause decomposition of this error is documented below:

1. **The Physical Executions Involved (14 Executions):**
   - 6 H2 pool sensitivity runs (`20261015-155050` through `155614`): valid executions, but construct-flawed because simulated sleep occurred before database checkout.
   - 6 Docker Compose PostgreSQL runs (`docker-pg-orders-pool{1,10}-trial{1,2,3}`): valid executions, but construct-flawed and lacking JFR instrumentation.
   - 1 standalone CPU control run (`cpu-control-20261008`): valid execution output, but unmanifested and lacking JFR.
   - 1 aborted run (`20261008-142557`): process execution that failed with k6 exit status 107.
   - Subtotal of actual process executions: $6 + 6 + 1 + 1 = \mathbf{14\text{ executions}}$.

2. **The Accidental Addition of Markdown Files (+4 Files):**
   - The author noticed 4 narrative benchmark reports from April 2026 in `results/`:
     - `results/baseline-platform-threads.md`
     - `results/comparison.md`
     - `results/naive-virtual-threads.md`
     - `results/refactored-virtual-threads.md`
   - The author added these 4 documentation text files to the 14 process executions:
     $$14\text{ executions} + 4\text{ markdown files} = \mathbf{18\text{ "runs/artifacts"}}$$
   - This produced a nonsensical hybrid category adding text documentation to benchmark runs.

3. **The Unquantified Legacy File Appendage (+51 Files):**
   - To compound the confusion, the previous text appended a note: *"April 2026 historical benchmarks (32 k6 JSONs + 19 JFRs; pre-manifest legacy suite)"*.
   - These 51 files were historical outputs from April 14 and April 28, 2026, which were generated before the run-manifest schema was created. None of these 51 files are in the 120-row matrix.

### Authoritative Resolution
Process executions and disk file artifacts are strictly separated:
- **Actual Benchmark Executions Tabulated:** Exactly **119 executions**.
- **Excluded / Flawed / Aborted Executions:** Exactly **13 executions** (6 H2 + 6 Docker PG + 1 aborted).
- **Standalone Diagnostic Execution:** Exactly **1 execution** (`cpu-control-20261008`).
- **Non-Execution Disk Artifacts (57 Files):** 1 manifest schema template, 5 Markdown reports (4 April + 1 October), 32 April unmanifested k6 JSONs, 19 April unmanifested JFRs, and 1 October 8 ISO-named k6 JSON.

---

## 6. Comprehensive 119-Execution Run-ID-to-Tier Mapping Ledger

The table below provides the exhaustive, unambiguous mapping of all **119 actual benchmark executions** in the repository. There is **zero overlap** between strata, and **zero missing executions** ($12 + 10 + 27 + 18 + 12 + 27 + 13 = 119$). Row 120 (the reference template) is cataloged separately.

### Stratum 1: Java 21 Primary Experimental Synchronization Matrix (12 Executions)
*Configuration:* Java 21.0.8 LTS, 1-carrier scheduler (`parallelism=1`, `maxPoolSize=1`), 10 closed-loop VUs, 55s duration. Focus: Core `/payments` synchronization comparisons.

| Run ID | Trial | Condition | Family | JDK | Carrier | VUs | In Norm? | Result File | JFR File |
|---|---|---|---|:---:|:---:|:---:|:---:|---|---|
| `20261015-142222` | `java21-synchronized-1` | `payments-synchronized` | `java21-primary-repeat` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-142222.json` | `results/jfr/recording-20261015-142222.jfr` |
| `20261015-142326` | `java21-synchronized-2` | `payments-synchronized` | `java21-primary-repeat` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-142326.json` | `results/jfr/recording-20261015-142326.jfr` |
| `20261015-142430` | `java21-synchronized-3` | `payments-synchronized` | `java21-primary-repeat` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-142430.json` | `results/jfr/recording-20261015-142430.jfr` |
| `20261015-142534` | `java21-reentrant-lock-1` | `payments-reentrant-lock` | `java21-primary-repeat` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-142534.json` | `results/jfr/recording-20261015-142534.jfr` |
| `20261015-142638` | `java21-reentrant-lock-2` | `payments-reentrant-lock` | `java21-primary-repeat` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-142638.json` | `results/jfr/recording-20261015-142638.jfr` |
| `20261015-142742` | `java21-reentrant-lock-3` | `payments-reentrant-lock` | `java21-primary-repeat` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-142742.json` | `results/jfr/recording-20261015-142742.jfr` |
| `20261015-143108` | `1` | `no-lock-diagnostic` | `java21-primary-matrix` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143108.json` | `results/jfr/recording-20261015-143108.jfr` |
| `20261015-143213` | `2` | `no-lock-diagnostic` | `java21-primary-matrix` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143213.json` | `results/jfr/recording-20261015-143213.jfr` |
| `20261015-143318` | `3` | `no-lock-diagnostic` | `java21-primary-matrix` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143318.json` | `results/jfr/recording-20261015-143318.jfr` |
| `20261015-143422` | `1` | `platform-synchronized` | `java21-primary-matrix` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143422.json` | `results/jfr/recording-20261015-143422.jfr` |
| `20261015-143526` | `2` | `platform-synchronized` | `java21-primary-matrix` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143526.json` | `results/jfr/recording-20261015-143526.jfr` |
| `20261015-143631` | `3` | `platform-synchronized` | `java21-primary-matrix` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143631.json` | `results/jfr/recording-20261015-143631.jfr` |

### Stratum 2: Java 24 & Java 25 Runtime Comparison Experiments (10 Executions)
*Configuration:* Java 24.0.2 GA and Java 25-ea, 1-carrier scheduler (`parallelism=1`), 10 closed-loop VUs, 55s duration. Focus: Verification of JEP 491 object monitor unpinning across JDK releases.

| Run ID | Trial | Condition | Family | JDK | Carrier | VUs | In Norm? | Result File | JFR File |
|---|---|---|---|:---:|:---:|:---:|:---:|---|---|
| `20261015-135200` | `1` | `java25-synchronized` | `spring-java25-sync-boundary` | 25-ea | 1-carrier | 10 | NO | `results/run-10vus-20261015-135200.json` | `results/jfr/recording-20261015-135200.jfr` |
| `20261015-135304` | `1` | `java25-reentrant-lock` | `spring-java25-sync-boundary` | 25-ea | 1-carrier | 10 | NO | `results/run-10vus-20261015-135304.json` | `results/jfr/recording-20261015-135304.jfr` |
| `20261015-140100` | `1` | `java24-synchronized` | `spring-java24-sync-boundary` | 24.0.2 | 1-carrier | 10 | NO | `results/run-10vus-20261015-140100.json` | `results/jfr/recording-20261015-140100.jfr` |
| `20261015-140205` | `1` | `java24-reentrant-lock` | `spring-java24-sync-boundary` | 24.0.2 | 1-carrier | 10 | NO | `results/run-10vus-20261015-140205.json` | `results/jfr/recording-20261015-140205.jfr` |
| `20261015-140927` | `unspecified` | `payments-synchronized` | `java24-sync-repeat` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261015-140927.json` | `results/jfr/recording-20261015-140927.jfr` |
| `20261015-141041` | `java24-sync-2` | `payments-synchronized` | `java24-sync-repeat` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261015-141041.json` | `results/jfr/recording-20261015-141041.jfr` |
| `20261015-141146` | `java24-sync-3` | `payments-synchronized` | `java24-sync-repeat` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261015-141146.json` | `results/jfr/recording-20261015-141146.jfr` |
| `20261015-141321` | `java24-lock-1` | `payments-reentrant-lock` | `java24-lock-repeat` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261015-141321.json` | `results/jfr/recording-20261015-141321.jfr` |
| `20261015-141426` | `java24-lock-2` | `payments-reentrant-lock` | `java24-lock-repeat` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261015-141426.json` | `results/jfr/recording-20261015-141426.jfr` |
| `20261015-141530` | `java24-lock-3` | `payments-reentrant-lock` | `java24-lock-repeat` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261015-141530.json` | `results/jfr/recording-20261015-141530.jfr` |

### Stratum 3: Multi-JDK Native JNI Boundary Matrix (27 Executions)
*Configuration:* 1-carrier scheduler (`parallelism=1`, `--enable-native-access=ALL-UNNAMED`), 10 closed-loop VUs, 55s duration. Focus: Complete $3 \times 3 \times 3$ factorial matrix evaluating native C `nanosleep()` carrier occupation across JDK 21, 24, and 25-ea.

| Run ID | Trial | Condition | Family | JDK | Carrier | VUs | In Norm? | Result File | JFR File |
|---|---|---|---|:---:|:---:|:---:|:---:|---|---|
| `20261008-143638` | `1` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-143638.json` | `results/jfr/recording-20261008-143638.jfr` |
| `20261008-143743` | `2` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-143743.json` | `results/jfr/recording-20261008-143743.jfr` |
| `20261008-143847` | `3` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-143847.json` | `results/jfr/recording-20261008-143847.jfr` |
| `20261008-143952` | `1` | `blocking-jni` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-143952.json` | `results/jfr/recording-20261008-143952.jfr` |
| `20261008-144056` | `2` | `blocking-jni` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144056.json` | `results/jfr/recording-20261008-144056.jfr` |
| `20261008-144201` | `3` | `blocking-jni` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144201.json` | `results/jfr/recording-20261008-144201.jfr` |
| `20261008-144305` | `1` | `native-short` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144305.json` | `results/jfr/recording-20261008-144305.jfr` |
| `20261008-144409` | `2` | `native-short` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144409.json` | `results/jfr/recording-20261008-144409.jfr` |
| `20261008-144513` | `3` | `native-short` | `native-boundary-20261008-repeated` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144513.json` | `results/jfr/recording-20261008-144513.jfr` |
| `20261008-144617` | `1` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144617.json` | `results/jfr/recording-20261008-144617.jfr` |
| `20261008-144722` | `2` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144722.json` | `results/jfr/recording-20261008-144722.jfr` |
| `20261008-144826` | `3` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144826.json` | `results/jfr/recording-20261008-144826.jfr` |
| `20261008-144930` | `1` | `blocking-jni` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-144930.json` | `results/jfr/recording-20261008-144930.jfr` |
| `20261008-145035` | `2` | `blocking-jni` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-145035.json` | `results/jfr/recording-20261008-145035.jfr` |
| `20261008-145140` | `3` | `blocking-jni` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-145140.json` | `results/jfr/recording-20261008-145140.jfr` |
| `20261008-145244` | `1` | `native-short` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-145244.json` | `results/jfr/recording-20261008-145244.jfr` |
| `20261008-145348` | `2` | `native-short` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-145348.json` | `results/jfr/recording-20261008-145348.jfr` |
| `20261008-145452` | `3` | `native-short` | `native-boundary-20261008-repeated` | 24.0.2 | 1-carrier | 10 | YES | `results/run-10vus-20261008-145452.json` | `results/jfr/recording-20261008-145452.jfr` |
| `20261008-145556` | `1` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-145556.json` | `results/jfr/recording-20261008-145556.jfr` |
| `20261008-145701` | `2` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-145701.json` | `results/jfr/recording-20261008-145701.jfr` |
| `20261008-145805` | `3` | `pure-java-sleep` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-145805.json` | `results/jfr/recording-20261008-145805.jfr` |
| `20261008-145909` | `1` | `blocking-jni` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-145909.json` | `results/jfr/recording-20261008-145909.jfr` |
| `20261008-150013` | `2` | `blocking-jni` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-150013.json` | `results/jfr/recording-20261008-150013.jfr` |
| `20261008-150118` | `3` | `blocking-jni` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-150118.json` | `results/jfr/recording-20261008-150118.jfr` |
| `20261008-150222` | `1` | `native-short` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-150222.json` | `results/jfr/recording-20261008-150222.jfr` |
| `20261008-150326` | `2` | `native-short` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-150326.json` | `results/jfr/recording-20261008-150326.jfr` |
| `20261008-150430` | `3` | `native-short` | `native-boundary-20261008-repeated` | 25-ea | 1-carrier | 10 | YES | `results/run-10vus-20261008-150430.json` | `results/jfr/recording-20261008-150430.jfr` |

### Stratum 4: Supporting Architectural Diagnostic Controls (18 Executions)
*Configuration:* Java 21.0.8 LTS, 1-carrier scheduler (`parallelism=1`), 10 closed-loop VUs, 55s duration. Focus: Cross-endpoint head-of-line blocking on `/orders` and `/products`, and compute-bound scheduling on `/cpu`.

| Run ID | Trial | Condition | Family | JDK | Carrier | VUs | In Norm? | Result File | JFR File |
|---|---|---|---|:---:|:---:|:---:|:---:|---|---|
| `20261015-143809` | `1` | `orders-virtual` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143809.json` | `results/jfr/recording-20261015-143809.jfr` |
| `20261015-143913` | `2` | `orders-virtual` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-143913.json` | `results/jfr/recording-20261015-143913.jfr` |
| `20261015-144017` | `3` | `orders-virtual` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144017.json` | `results/jfr/recording-20261015-144017.jfr` |
| `20261015-144121` | `1` | `orders-platform` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144121.json` | `results/jfr/recording-20261015-144121.jfr` |
| `20261015-144225` | `2` | `orders-platform` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144225.json` | `results/jfr/recording-20261015-144225.jfr` |
| `20261015-144329` | `3` | `orders-platform` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144329.json` | `results/jfr/recording-20261015-144329.jfr` |
| `20261015-144433` | `1` | `products-virtual` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144433.json` | `results/jfr/recording-20261015-144433.jfr` |
| `20261015-144537` | `2` | `products-virtual` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144537.json` | `results/jfr/recording-20261015-144537.jfr` |
| `20261015-144641` | `3` | `products-virtual` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144641.json` | `results/jfr/recording-20261015-144641.jfr` |
| `20261015-144745` | `1` | `products-platform` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144745.json` | `results/jfr/recording-20261015-144745.jfr` |
| `20261015-144849` | `2` | `products-platform` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144849.json` | `results/jfr/recording-20261015-144849.jfr` |
| `20261015-144952` | `3` | `products-platform` | `java21-endpoint-isolation` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-144952.json` | `results/jfr/recording-20261015-144952.jfr` |
| `20261015-145454` | `1` | `cpu-virtual` | `java21-cpu-control` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-145454.json` | `results/jfr/recording-20261015-145454.jfr` |
| `20261015-145558` | `2` | `cpu-virtual` | `java21-cpu-control` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-145558.json` | `results/jfr/recording-20261015-145558.jfr` |
| `20261015-145702` | `3` | `cpu-virtual` | `java21-cpu-control` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-145702.json` | `results/jfr/recording-20261015-145702.jfr` |
| `20261015-145806` | `1` | `cpu-platform` | `java21-cpu-control` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-145806.json` | `results/jfr/recording-20261015-145806.jfr` |
| `20261015-145910` | `2` | `cpu-platform` | `java21-cpu-control` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-145910.json` | `results/jfr/recording-20261015-145910.jfr` |
| `20261015-150014` | `3` | `cpu-platform` | `java21-cpu-control` | 21.0.8 | 1-carrier | 10 | YES | `results/run-10vus-20261015-150014.json` | `results/jfr/recording-20261015-150014.jfr` |

### Stratum 5: Stratified 8-Carrier Historical Baseline Matrix (12 Executions)
*Configuration:* Java 21.0.8 LTS, 8-carrier scheduler default (`JAVA_EXTRA_OPTS=""`, Apple M1 8 logical cores), 10 closed-loop VUs, 55s duration. Focus: Historical repeated baseline; segregated to prevent carrier concurrency confounding.

| Run ID | Trial | Condition | Family | JDK | Carrier | VUs | In Norm? | Result File | JFR File |
|---|---|---|---|:---:|:---:|:---:|:---:|---|---|
| `20261008-151440` | `1` | `synchronized` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-151440.json` | `results/jfr/recording-20261008-151440.jfr` |
| `20261008-151545` | `2` | `synchronized` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-151545.json` | `results/jfr/recording-20261008-151545.jfr` |
| `20261008-151650` | `3` | `synchronized` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-151650.json` | `results/jfr/recording-20261008-151650.jfr` |
| `20261008-151755` | `1` | `reentrant-lock` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-151755.json` | `results/jfr/recording-20261008-151755.jfr` |
| `20261008-151859` | `2` | `reentrant-lock` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-151859.json` | `results/jfr/recording-20261008-151859.jfr` |
| `20261008-152003` | `3` | `reentrant-lock` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-152003.json` | `results/jfr/recording-20261008-152003.jfr` |
| `20261008-152107` | `1` | `no-lock-diagnostic` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-152107.json` | `results/jfr/recording-20261008-152107.jfr` |
| `20261008-152212` | `2` | `no-lock-diagnostic` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-152212.json` | `results/jfr/recording-20261008-152212.jfr` |
| `20261008-152316` | `3` | `no-lock-diagnostic` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-152316.json` | `results/jfr/recording-20261008-152316.jfr` |
| `20261008-152421` | `1` | `platform-synchronized` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-152421.json` | `results/jfr/recording-20261008-152421.jfr` |
| `20261008-152526` | `2` | `platform-synchronized` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-152526.json` | `results/jfr/recording-20261008-152526.jfr` |
| `20261008-152631` | `3` | `platform-synchronized` | `java21-synchronization-20261008-repeated` | 21.0.8 | 8-carrier/default | 10 | YES | `results/run-10vus-20261008-152631.json` | `results/jfr/recording-20261008-152631.jfr` |

### Stratum 6: Exploratory, Pilot, and Standalone Diagnostic Executions (27 Executions)
*Configuration:* Diverse exploratory pilots, locking alternatives, single baseline verification, and 1 standalone unmanifested CPU artifact.

| Run ID | Trial | Condition | Family | JDK | Carrier | VUs | In Norm? | Result File | JFR File |
|---|---|---|---|:---:|:---:|:---:|:---:|---|---|
| `20261008-133153` | `N/A` | `pilot-mixed-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 8-carrier/default | 50 | NO | `results/run-50vus-20261008-133153.json` | `results/jfr/recording-20261008-133153.jfr` |
| `20261008-133419` | `N/A` | `pilot-mixed-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 8-carrier/default | 50 | NO | `results/run-50vus-20261008-133419.json` | `results/jfr/recording-20261008-133419.jfr` |
| `20261008-141006` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 8-carrier/default | 10 | NO | `results/run-10vus-20261008-141006.json` | `results/jfr/recording-20261008-141006.jfr` |
| `20261008-141144` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 8-carrier/default | 10 | NO | `results/run-10vus-20261008-141144.json` | `results/jfr/recording-20261008-141144.jfr` |
| `20261008-141301` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 8-carrier/default | 10 | NO | `results/run-10vus-20261008-141301.json` | `results/jfr/recording-20261008-141301.jfr` |
| `20261008-141447` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261008-141447.json` | `results/jfr/recording-20261008-141447.jfr` |
| `20261008-141555` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 25-ea | 1-carrier | 10 | NO | `results/run-10vus-20261008-141555.json` | `results/jfr/recording-20261008-141555.jfr` |
| `20261008-141918` | `N/A` | `pilot-payments-none` | `historical-oct08-pilots` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261008-141918.json` | `results/jfr/recording-20261008-141918.jfr` |
| `20261008-142445` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 24.0.2 | 1-carrier | 10 | NO | `results/run-10vus-20261008-142445.json` | `results/jfr/recording-20261008-142445.jfr` |
| `20261008-142621` | `N/A` | `pilot-native-short-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261008-142621.json` | `results/jfr/recording-20261008-142621.jfr` |
| `20261008-142730` | `N/A` | `pilot-native-short-reentrant-lock` | `historical-oct08-pilots` | 24.0.2 | 1-carrier | 10 | NO | `results/run-10vus-20261008-142730.json` | `results/jfr/recording-20261008-142730.jfr` |
| `20261008-142838` | `N/A` | `pilot-native-short-reentrant-lock` | `historical-oct08-pilots` | 25-ea | 1-carrier | 10 | NO | `results/run-10vus-20261008-142838.json` | `results/jfr/recording-20261008-142838.jfr` |
| `20261008-142959` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261008-142959.json` | `results/jfr/recording-20261008-142959.jfr` |
| `20261008-143105` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 24.0.2 | 1-carrier | 10 | NO | `results/run-10vus-20261008-143105.json` | `results/jfr/recording-20261008-143105.jfr` |
| `20261008-143210` | `N/A` | `pilot-native-reentrant-lock` | `historical-oct08-pilots` | 25-ea | 1-carrier | 10 | NO | `results/run-10vus-20261008-143210.json` | `results/jfr/recording-20261008-143210.jfr` |
| `20261008-143319` | `N/A` | `pilot-payments-none` | `historical-oct08-pilots` | 24.0.2 | 1-carrier | 10 | NO | `results/run-10vus-20261008-143319.json` | `results/jfr/recording-20261008-143319.jfr` |
| `20261008-143427` | `N/A` | `pilot-payments-none` | `historical-oct08-pilots` | 25-ea | 1-carrier | 10 | NO | `results/run-10vus-20261008-143427.json` | `results/jfr/recording-20261008-143427.jfr` |
| `20261015-132618` | `1` | `synchronized` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261015-132618.json` | `results/jfr/recording-20261015-132618.jfr` |
| `20261015-132723` | `1` | `reentrant-lock` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261015-132723.json` | `results/jfr/recording-20261015-132723.jfr` |
| `20261015-132827` | `1` | `fair-reentrant-lock` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `none` *(missing)* | `results/jfr/recording-20261015-132827.jfr` |
| `20261015-132847` | `1` | `synchronized` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261015-132847.json` | `results/jfr/recording-20261015-132847.jfr` |
| `20261015-132952` | `1` | `reentrant-lock` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261015-132952.json` | `results/jfr/recording-20261015-132952.jfr` |
| `20261015-133056` | `1` | `fair-reentrant-lock` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261015-133056.json` | `results/jfr/recording-20261015-133056.jfr` |
| `20261015-133201` | `1` | `semaphore` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261015-133201.json` | `results/jfr/recording-20261015-133201.jfr` |
| `20261015-133305` | `1` | `fair-semaphore` | `java21-lock-semaphore-pilot` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261015-133305.json` | `results/jfr/recording-20261015-133305.jfr` |
| `20261026-175320` | `1` | `vt-synchronized` | `software-lab-baseline-20261026` | 21.0.12.1 | 1-carrier | 10 | NO | `results/run-10vus-20261026-175320.json` | `results/jfr/recording-20261026-175320.jfr` |
| `cpu-control-20261008` | `cpu-control-20261008` | `cpu-control` | `java21-cpu-control` | 21.0.8 | 8-carrier/default | 10 | YES | `results/cpu-control-20261008.json` | `none` *(standalone)* |

### Stratum 7: Excluded, Defective, or Construct-Flawed Executions (13 Executions)
*Configuration:* Executions with severe construct flaws (pre-query sleep), missing application JFR, or abnormal execution termination. Excluded from primary statistical claims.

| Run ID | Trial | Condition | Family | JDK | Carrier | VUs | In Norm? | Result File | JFR File | Exclusion Reason |
|---|---|---|---|:---:|:---:|:---:|:---:|---|---|---|
| `20261008-142557` | `N/A` | `pilot-native-short-reentrant-lock` | `historical-oct08-pilots` | 21.0.8 | 1-carrier | 10 | NO | `results/run-10vus-20261008-142557.json` | `results/jfr/recording-20261008-142557.jfr` | Aborted execution; k6 exit status 107; empty result file (0 requests). |
| `20261015-155050` | `1` | `orders-h2-pool-1` | `h2-pool-sensitivity` | 21.0.8 | 4-carrier | 50 | NO | `results/run-50vus-20261015-155050.json` | `results/jfr/recording-20261015-155050.jfr` | Construct flaw: `Thread.sleep(300)` precedes JDBC query; pool never held. |
| `20261015-155155` | `2` | `orders-h2-pool-1` | `h2-pool-sensitivity` | 21.0.8 | 4-carrier | 50 | NO | `results/run-50vus-20261015-155155.json` | `results/jfr/recording-20261015-155155.jfr` | Construct flaw: `Thread.sleep(300)` precedes JDBC query; pool never held. |
| `20261015-155259` | `3` | `orders-h2-pool-1` | `h2-pool-sensitivity` | 21.0.8 | 4-carrier | 50 | NO | `results/run-50vus-20261015-155259.json` | `results/jfr/recording-20261015-155259.jfr` | Construct flaw: `Thread.sleep(300)` precedes JDBC query; pool never held. |
| `20261015-155404` | `1` | `orders-h2-pool-10` | `h2-pool-sensitivity` | 21.0.8 | 4-carrier | 50 | NO | `results/run-50vus-20261015-155404.json` | `results/jfr/recording-20261015-155404.jfr` | Construct flaw: `Thread.sleep(300)` precedes JDBC query; pool never held. |
| `20261015-155509` | `2` | `orders-h2-pool-10` | `h2-pool-sensitivity` | 21.0.8 | 4-carrier | 50 | NO | `results/run-50vus-20261015-155509.json` | `results/jfr/recording-20261015-155509.jfr` | Construct flaw: `Thread.sleep(300)` precedes JDBC query; pool never held. |
| `20261015-155614` | `3` | `orders-h2-pool-10` | `h2-pool-sensitivity` | 21.0.8 | 4-carrier | 50 | NO | `results/run-50vus-20261015-155614.json` | `results/jfr/recording-20261015-155614.jfr` | Construct flaw: `Thread.sleep(300)` precedes JDBC query; pool never held. |
| `docker-pg-orders-pool1-trial1` | `1` | `orders-docker-pg-pool-1` | `docker-pg-orders` | 21.0.8 | 1-carrier | 50 | NO | `results/docker-pg-orders-pool1-trial1.json` | `none` | Unmanifested; lacks application JFR; same construct flaw. |
| `docker-pg-orders-pool1-trial2` | `2` | `orders-docker-pg-pool-1` | `docker-pg-orders` | 21.0.8 | 1-carrier | 50 | NO | `results/docker-pg-orders-pool1-trial2.json` | `none` | Unmanifested; lacks application JFR; same construct flaw. |
| `docker-pg-orders-pool1-trial3` | `3` | `orders-docker-pg-pool-1` | `docker-pg-orders` | 21.0.8 | 1-carrier | 50 | NO | `results/docker-pg-orders-pool1-trial3.json` | `none` | Unmanifested; lacks application JFR; same construct flaw. |
| `docker-pg-orders-pool10-trial1` | `1` | `orders-docker-pg-pool-10` | `docker-pg-orders` | 21.0.8 | 1-carrier | 50 | NO | `results/docker-pg-orders-pool10-trial1.json` | `none` | Unmanifested; lacks application JFR; same construct flaw. |
| `docker-pg-orders-pool10-trial2` | `2` | `orders-docker-pg-pool-10` | `docker-pg-orders` | 21.0.8 | 1-carrier | 50 | NO | `results/docker-pg-orders-pool10-trial2.json` | `none` | Unmanifested; lacks application JFR; same construct flaw. |
| `docker-pg-orders-pool10-trial3` | `3` | `orders-docker-pg-pool-10` | `docker-pg-orders` | 21.0.8 | 1-carrier | 50 | NO | `results/docker-pg-orders-pool10-trial3.json` | `none` | Unmanifested; lacks application JFR; same construct flaw. |

### Non-Execution Matrix Row (Row 120)
- **File:** [`results/run-manifest-template.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/results/run-manifest-template.json)  
  *Classification:* Manifest Schema Template. Target VUs: 0. Duration: 0. Not an execution.

---

## 7. Formal Adoption of User Decisions on the Three Decision Gates

The human researcher has reviewed the referee review and formally ratified the five decision gates, establishing the binding rules for all subsequent research phases:

### Ratified Decision 1: Evidence Stratification (Gate 1)
- **Status:** **APPROVED IN PRINCIPLE WITH MODIFICATIONS.**
- **Enacted Rules:**
  1. The five-tier summary counts are **not finalized**.
  2. The exact run-ID-to-tier mapping covering all **119 actual executions** established in Section 6 is formally adopted.
  3. The Java 21 primary experimental matrix (Stratum 1, 12 runs) is **strictly separated** from the Java 24/25 runtime comparison experiments (Stratum 2, 10 runs).
  4. Single-carrier configurations (`parallelism=1`) must **never be described as a one-vCPU container** or an operating system CPU quota; they must be explicitly designated as **JVM scheduler-constrained mechanism-isolation experiments**.
  5. The previous report's "18 runs/artifacts in Tier 5" flaw is conclusively resolved (13 flawed/aborted executions, 1 standalone CPU execution, and 4 text Markdown reports).

### Ratified Decision 2: Standalone CPU Control (`cpu-control-20261008`)
- **Status:** **APPROVED FOR EXCLUSION FROM PRIMARY COMPARISONS.**
- **Enacted Rules:**
  1. Record 76 (`cpu-control-20261008`) is **excluded from primary quantitative matrices**.
  2. It is retained as a diagnostic/exploratory baseline artifact in Stratum 6.
  3. Its missing execution metadata (absence of a run manifest, absence of a JFR recording, unmeasured carrier pool, and unrecorded runtime JVM parameters) must be explicitly stated whenever cited.

### Ratified Decision 3: Metric Reporting Policy (Gate 2)
- **Status:** **APPROVED WITH MODIFICATIONS.**
- **Enacted Rules:**
  1. **Dual Whole-Run and Derived-Window Reporting:** Mandatory side-by-side reporting of whole-run ($0-55\text{s}$) and derived hold-window ($15-45\text{s}$) metrics for all ramp-sensitive experimental families (`products`, `orders`, `cpu`, `platform-synchronized`).
  2. **No Universal Authority:** The $15\text{s}-45\text{s}$ window must **not be declared universally authoritative** across all experimental families.
  3. **No Unqualified "Steady State" Labeling:** The derived window must **not be labeled "steady state"** without empirically validating the timestamp convention ($t_0$ definition), request completion boundary bleed, and queue equilibrium assumptions for each individual family.
  4. **Preservation of Existing Assets:** The existing normalized evidence dataset ([`normalized-evidence.json`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/resources/static/data/normalized-evidence.json)) and static dashboard outputs must remain **completely unchanged**.

### Ratified Decision 4: Cryptographic Integrity Formulation
- **Status:** **APPROVED WITH QUALIFIED WORDING.**
- **Enacted Rules:**
  1. Hash verification establishes **byte consistency against recorded checksums for the files actually checked** (368 result/JFR checks and 92 telemetry CSV checks).
  2. Git and source revision metadata (`1ccb617`, `5f9936c`) provide source-level traceability.
  3. **No claim of exact executable binary provenance** may be made unless the compiled JAR or dynamic library identity is independently established.

### Ratified Decision 5: Authorization of Stage 1.2 (Gate 3)
- **Status:** **APPROVED TO PROCEED.**
- **Enacted Rules:**
  1. Stage 1.2 forensic investigation is formally authorized to commence.
  2. Research efforts must strictly focus on the four priority questions defined in the Stage 1.2 Investigation Charter.

---

## 8. Stage 1.2 Forensic Investigation Charter

With the formal ratification of Gate 3, Stage 1.2 commences. Its purpose is strictly to establish **what physically occurred during the October 2026 experiments**, rather than attempting to retroactively sanitize the data.

### 8.1 Prioritized Forensic Research Objectives

1. **Investigation 1 (Priority P1) — JNI Nanosleep, Carrier Occupation, Telemetry, and JFR Omission:**
   - **Code Target:** `src/main/c/native_blocking.c` and HotSpot C++ sources (`jvm.cpp`, `synchronizer.cpp`).
   - **Questions:** Why does `nanosleep(500ms)` completely monopolize the carrier thread while producing exactly zero `jdk.VirtualThreadPinned` events in JFR? Is JFR pinning instrumentation exclusive to Java object monitors?
   - **Telemetry Target:** 92 companion telemetry CSV files (`results/telemetry-*.csv`). What was the physical OS thread attribution and host CPU percentage during JNI execution on Apple M1?

2. **Investigation 2 (Priority P1) — Effective Spring Boot Datasource Configuration:**
   - **Code Target:** `src/main/resources/application.yml` and `docker-compose.yml`.
   - **Questions:** In `application.yml`, lines 18–25 indent `datasource` under `demo:`. Did Spring Boot recognize custom HikariCP pool parameters, or did it silently fall back to defaults? What was the effective runtime pool size during local H2 runs?

3. **Investigation 3 (Priority P1) — OrderService Transaction Boundaries & Connection Checkout:**
   - **Code Target:** [`OrderService.java#L40-L48`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L40-L48).
   - **Questions:** Line 198 calls `simulateSlowQuery()` (`Thread.sleep(300)`) prior to `jdbcTemplate.queryForList(...)`. Did connection checkout occur before or after the sleep? Does this explain why pool size 1 vs 10 exhibited identical throughput and latency?

4. **Investigation 4 (Priority P2) — Container PostgreSQL Trial Instrumentation & JFR Absence:**
   - **Code Target:** `docker-compose.yml` and PostgreSQL trial outputs (`docker-pg-orders-pool*.json`).
   - **Questions:** Why were JFR binary recordings omitted or failed to dump during Docker Compose runs? Was container CPU throttling (`cpus: '0.5'`) verified via cgroup telemetry?

### 8.2 Operational Constraints for Stage 1.2
- **Raw Evidence Immutability:** No original files in `results/` may be edited, moved, renamed, or deleted.
- **No Full Reruns:** Do not re-execute the full 119-run benchmark matrix; forensic work consists of source inspection, bytecode decompilation, telemetry parsing, and targeted diagnostic probes.
- **Epistemological Separation:** Maintain strict separation between Direct Observations, Calculations, Interpretations, and Assumptions.
- **Deliverables:** All findings must be written to dedicated forensic reports under `docs/evidence-freeze/`.

*(End of Adjudication Report & Formal Decision Record)*

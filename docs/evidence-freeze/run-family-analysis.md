# Experimental Run Family Matrix & Configuration Divergence Audit

**Document:** `docs/evidence-freeze/run-family-analysis.md`  
**Companion CSV:** [`run-family-matrix.csv`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/docs/evidence-freeze/run-family-matrix.csv)  
**Audited Codebase:** `/Users/mohamedhamed/Documents/virtual-thread-springs`  
**Audit Stage:** Stage 1.1 — Workstream 2 (Configuration Matrix & Reproducibility Audit)  
**Date of Audit:** 2 November 2026  

---

## Executive Summary

This report documents the exhaustive configuration audit of all benchmark manifests (`results/run-manifest-*.json`), raw k6 execution streams, and telemetry/JFR recordings generated throughout the MSc thesis research (*Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines*).

### Key Audit Metrics
- **Total Manifest Files Parsed:** 113 manifests (112 process execution manifests + 1 reference template).
- **Total Benchmark Executions Tabulated:** 120 runs (113 manifests + 6 unmanifested Docker Compose PostgreSQL runs + 1 standalone Oct 8 CPU control artifact).
- **Normalized Dashboard Records:** 76 runs (75 manifest trials + 1 CPU control artifact verified in `src/main/resources/static/data/normalized-evidence.json`).
- **Primary Git Commits:** `5f9936c` (2026-10-08, 57 manifests), `1ccb617` (2026-10-15, 54 manifests + 6 Docker runs), `a9bd454` (2026-10-26, 1 manifest).
- **Carrier Concurrency Divergences:**
  - **1-Carrier (`parallelism=1`, `maxPoolSize=1`):** 95 runs (Primary matrix, JNI boundary, endpoint isolation, CPU controls, JDK 24/25 GA comparisons).
  - **8-Carrier / Default (`parallelism=8`, `maxPoolSize=256`):** 18 runs (Oct 8 repeated synchronization matrix and historical exploratory pilots).
  - **4-Carrier (`parallelism=4`, `maxPoolSize=4`):** 6 runs (H2 connection pool sensitivity matrix).

---

## 1. Run Families Breakdown & Exact Configurations

The 120 tabulated experimental runs fall into **15 distinct Run Families** (plus the reference template). The table below summarizes each family's experimental purpose, runtime environment, carrier configuration, and evidence normalization status.

| Run Family | Run Count | Target JDK(s) | Carrier Pool | Endpoint(s) | Load (VUs / Dur) | Hikari Pool | Normalized Set? |
|---|---:|---|---|---|---|---|:---:|
| `java21-primary-matrix` | 6 | 21.0.8 | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | Yes (All) |
| `java21-primary-repeat` | 6 | 21.0.8 | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | Yes (All) |
| `java21-synchronization-20261008-repeated` | 12 | 21.0.8 | 8-carrier/default | `payments` | 10 VUs / 55s | 10 (default) | Yes (All) |
| `native-boundary-20261008-repeated` | 27 | 21.0.8, 24.0.2, 25-ea | 1-carrier | `native, native-short, payments` | 10 VUs / 55s | 10 (default) | Yes (All) |
| `java21-endpoint-isolation` | 12 | 21.0.8 | 1-carrier | `orders, products` | 10 VUs / 55s | 10 (default) | Yes (All) |
| `java21-cpu-control` | 7 | 21.0.8 | 1-carrier, 8-carrier/default | `cpu` | 10 VUs / 55s | 10 (default), none | Yes (All) |
| `h2-pool-sensitivity` | 6 | 21.0.8 | 4-carrier | `orders` | 50 VUs / 55s | 1, 10 | No |
| `docker-pg-orders` | 6 | 21.0.8 | 1-carrier | `orders` | 50 VUs / 55s | 1, 10 | No |
| `java24-sync-repeat` | 3 | 24.0.2 | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | Yes (All) |
| `java24-lock-repeat` | 3 | 24.0.2 | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | Yes (All) |
| `spring-java24-sync-boundary` | 2 | 24.0.2 | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | No |
| `spring-java25-sync-boundary` | 2 | 25-ea | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | No |
| `java21-lock-semaphore-pilot` | 8 | 21.0.8 | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | No |
| `software-lab-baseline-20261026` | 1 | 21.0.12.1 | 1-carrier | `payments` | 10 VUs / 55s | 10 (default) | No |
| `historical-oct08-pilots` | 18 | 21.0.8, 24.0.2, 25-ea | 1-carrier, 8-carrier/default | `mixed, native, native-short, payments` | 10, 50 VUs / 55s | 10 (default) | No |
| `template` | 1 | none | unspecified | `orders|payments|products|mixed` | 0 VUs / N/A | none | No |

### Detailed Family Characterization

#### 1. `java21-primary-matrix` (6 runs)
- **Purpose:** Evaluates baseline synchronization controls on Java 21 LTS under single-carrier stress.
- **Conditions:** `no-lock-diagnostic` (virtual threads, negative diagnostic control, 3 trials), `platform-synchronized` (platform threads baseline, 3 trials).
- **Scheduler:** `-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1` (1 carrier).
- **Load Model:** 10 closed-loop VUs, 55s (15s ramp, 30s steady, 10s ramp-down).
- **Status in Normalized Evidence:** Formally included (`records` in `normalized-evidence.json`).

#### 2. `java21-primary-repeat` (6 runs)
- **Purpose:** Evaluates the primary synchronization comparison: `synchronized` (monitor pinning) vs `reentrant-lock` (clean unmounting) under 1-carrier constraint.
- **Conditions:** `payments-synchronized` (3 trials), `payments-reentrant-lock` (3 trials).
- **Scheduler:** `-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1` (1 carrier).
- **Pinning Profile:** Emits 108–110 `jdk.VirtualThreadPinned` events for `synchronized`; emits exactly 0 events for `reentrant-lock`.
- **Status in Normalized Evidence:** Formally included.

#### 3. `java21-synchronization-20261008-repeated` (12 runs)
- **Purpose:** First repeated matrix ($N=3$) of synchronization treatments conducted on October 8.
- **Conditions:** `synchronized` (3 trials), `reentrant-lock` (3 trials), `no-lock-diagnostic` (3 trials), `platform-synchronized` (3 trials).
- **Scheduler:** `JAVA_EXTRA_OPTS=""` (Unset). HotSpot initialized default carrier pool: `parallelism=8`, `maxPoolSize=256`.
- **Divergence Warning:** These runs ran with **8 carrier threads**, whereas the later primary replication runs ran with **1 carrier thread**. Direct numerical throughput comparison between this set and `java21-primary-matrix` is invalid without qualifying carrier parallelism.
- **Status in Normalized Evidence:** Formally included.

#### 4. `native-boundary-20261008-repeated` (27 runs)
- **Purpose:** Multi-JDK evaluation of native JNI carrier occupancy vs pure Java sleep controls across OpenJDK 21 LTS, OpenJDK 24 GA, and OpenJDK 25-ea.
- **Conditions ($3 \times 3 \times 3 = 27$ runs):**
  1. `pure-java-sleep`: `/payments` endpoint, 500 ms `Thread.sleep()` unmounting cleanly.
  2. `blocking-jni`: `/native` endpoint, C native `nanosleep(500ms)` completely capturing carrier.
  3. `native-short`: `/native-short` endpoint, negligible JNI boundary crossing overhead.
- **Scheduler:** `-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1 --enable-native-access=ALL-UNNAMED` (1 carrier).
- **Critical Finding:** `blocking-jni` emitted **0 pinning events** on all 3 JDKs despite completely halting the single carrier thread (construct defect of `jdk.VirtualThreadPinned`).
- **Status in Normalized Evidence:** Formally included.

#### 5. `java21-endpoint-isolation` (12 runs)
- **Purpose:** Measures cross-endpoint interference and starvation on unrelated endpoints (`/orders` and `/products`) under virtual threads vs platform threads.
- **Conditions:** `orders-virtual` (3), `orders-platform` (3), `products-virtual` (3), `products-platform` (3).
- **Scheduler:** `1-carrier` (`parallelism=1`, `maxPoolSize=1`).
- **Status in Normalized Evidence:** Formally included.

#### 6. `java21-cpu-control` (6 manifest runs + 1 standalone artifact)
- **Purpose:** Evaluates computational CPU saturation without synchronization locks.
- **Conditions:** `cpu-virtual` (3), `cpu-platform` (3) + historical `cpu-control-20261008.json`.
- **Scheduler:** `1-carrier` (`parallelism=1`, `maxPoolSize=1`).
- **Status in Normalized Evidence:** Formally included.

#### 7. `h2-pool-sensitivity` (6 runs)
- **Purpose:** Evaluates HikariCP connection pool sizing sensitivity on embedded H2.
- **Conditions:** `orders-h2-pool-1` (3 trials), `orders-h2-pool-10` (3 trials).
- **Scheduler:** `-Djdk.virtualThreadScheduler.parallelism=4 -Djdk.virtualThreadScheduler.maxPoolSize=4` (4 carriers).
- **Workload:** 50 VUs, closed-loop, 55s.
- **Status in Normalized Evidence:** Not included in normalized dashboard set (exploratory sensitivity suite).

#### 8. `docker-pg-orders` (6 unmanifested runs)
- **Purpose:** Evaluates connection pool constraints against containerized PostgreSQL 15 in Docker Compose.
- **Conditions:** `orders-docker-pg-pool-1` (3 trials), `orders-docker-pg-pool-10` (3 trials).
- **Container Runtime:** `deploy.resources.limits.cpus: '0.5'`, `memory: 1G` -> OpenJDK cgroup detection instantiates 1 carrier thread.
- **Database Engine:** PostgreSQL 15 Alpine (`jdbc:postgresql://postgres:5432/thesis_db`).
- **Artifacts:** `results/docker-pg-orders-pool{1,10}-trial{1,2,3}.json`.
- **Status in Normalized Evidence:** Excluded from `normalized-evidence.json` (no JFR captured).

#### 9. `java24-sync-repeat` & `java24-lock-repeat` (6 runs)
- **Purpose:** Evaluates Java 24 GA with JEP 491 (Virtual Threads unmount from ObjectMonitors).
- **Findings:** Running `synchronized` on Java 24 emits **0 pinning events**, matching `ReentrantLock` unmounting behavior.
- **Scheduler:** `1-carrier` (`parallelism=1`, `maxPoolSize=1`).
- **Status in Normalized Evidence:** Formally included.

#### 10. `spring-java24-sync-boundary` & `spring-java25-sync-boundary` (4 runs)
- **Purpose:** Exploratory boundary spikes for Java 24 GA and Java 25-ea.
- **Status in Normalized Evidence:** Exploratory; superseded by repeated suites.

#### 11. `java21-lock-semaphore-pilot` (8 runs)
- **Purpose:** Compares alternative synchronization constructs: `synchronized`, `reentrant-lock`, `fair-reentrant-lock`, `semaphore`, and `fair-semaphore`.
- **Findings:** Both fair and non-fair `ReentrantLock` and `Semaphore` avoid carrier pinning, but all yield the identical 2.0 req/s serialization saturation ceiling on `/payments`.
- **Status in Normalized Evidence:** Exploratory.

#### 12. `software-lab-baseline-20261026` (1 run)
- **Purpose:** Single verification baseline on OpenJDK 21.0.12.1.
- **Status in Normalized Evidence:** Exploratory.

#### 13. `historical-oct08-pilots` (18 runs)
- **Purpose:** Exploratory single-process pilot trials executed on October 8 prior to standardizing repeated matrices.
- **Status in Normalized Evidence:** Exploratory.

---

## 2. Critical Configuration Divergences

### 2.1 The Carrier Concurrency Divergence: 1-Carrier vs. 8-Carrier vs. 4-Carrier

The most consequential experimental divergence identified across the codebase is the carrier thread concurrency setting:

| Setting | Parallelism (`-Djdk.virtualThreadScheduler.parallelism`) | Max Pool Size (`-Djdk.virtualThreadScheduler.maxPoolSize`) | Run Families Exercised | Physical / Container Rationale |
|---|:---:|:---:|---|---|
| **1-Carrier Stress** | `1` | `1` | `java21-primary-matrix`, `java21-primary-repeat`, `native-boundary-20261008-repeated`, `java21-endpoint-isolation`, `java21-cpu-control`, `java24-*-repeat` (89 manifests) | **Mechanism isolation** and **1-CPU container equivalence**. When cgroup quota $\le 1.0$, OpenJDK container detection sets `availableProcessors() = 1`. |
| **8-Carrier Default** | Unset (defaults to `8`) | Unset (defaults to `256`) | `java21-synchronization-20261008-repeated` (12 manifests), early October 8 pilots (5 manifests) | **Unconstrained host default**. HotSpot queries `Runtime.getRuntime().availableProcessors()`, binding to all 8 cores on Apple Silicon M1. |
| **4-Carrier Intermediate** | `4` | `4` | `java21-h2-pool-sensitivity` (6 manifests) | **Intermediate container sizing**. Simulates a 4-core container environment under moderate concurrency. |

#### Architectural Implications for the Thesis
1. **The Invalidation Risk of Cross-Family Comparisons:**
   - In `java21-synchronization-20261008-repeated`, `synchronized` pinned a virtual thread to 1 of 8 carrier threads, leaving 7 carrier threads available for scheduling.
   - In `java21-primary-matrix`, `synchronized` pinned the **only available carrier thread**, starving all concurrent virtual threads completely.
   - *Consequence:* Directly presenting October 8 synchronization latencies alongside October 15 primary matrix latencies without grouping by carrier count would mislead reviewers into attributing carrier-starvation effects to synchronization overhead.
2. **The 'Carrier Compensation' Misconception Purged:**
   - Early thesis drafts hypothesized that HotSpot normally spawns extra carrier threads to compensate for monitor pinning, and claimed `maxPoolSize=1` was necessary to 'disable' compensation.
   - In reality, [JEP 444](https://openjdk.org/jeps/444) confirms HotSpot **never** expands carrier parallelism for monitor pinning or JNI execution. Setting `maxPoolSize=1` only constrained `ForkJoinPool.ManagedBlocker` calls.

---

## 3. Historical October 8 Runs vs. October 15 Replication Runs

Between October 8 and October 15, the project evolved through three major methodology revisions:

### 3.1 Chronological Evolution Matrix

| Dimension | October 8 Historical Runs (`5f9936c`) | October 15 Replication Runs (`1ccb617`) | Audit Verdict & Thesis Consequence |
|---|---|---|---|
| **Run Structure** | 18 uncoordinated single pilots followed by two repeated matrices (`native-boundary` and `java21-synchronization`). | Standardized $N=3$ repeated process launches for all matrix conditions. | Pilot runs must be labeled exploratory; only $N=3$ repeated suites represent thesis evidence. |
| **Carrier Asymmetry** | JNI matrix ran with 1 carrier (`parallelism=1`); sync matrix ran with 8 carriers (`parallelism=8`). | Standardized 1-carrier configuration across primary matrix, primary repeat, endpoint isolation, and CPU controls. | Resolved scheduler asymmetry; enabled valid comparison across endpoints under 1-carrier constraint. |
| **Workload Scope** | Restricted to `/payments` (lock contention) and `/native` (JNI blocking). | Broadened to `/products` (in-memory uncontented), `/orders` (database JDBC), and `/cpu` (computational sha256). | Allowed empirical proof of cross-endpoint starvation on multi-route Spring controllers. |
| **JDK Target Comparison** | Compared Java 21 LTS with early JDK 24 and 25 EA builds on JNI only. | Formally evaluated JDK 24 GA with JEP 491 on primary `/payments` endpoint. | Empirically proved JEP 491 eliminates monitor pinning (0 JFR pinning events on Java 24). |
| **Manifest Completeness** | Early pilots omitted `run_set`, `trial_id`, and `condition_id`. Run `133153` had invalid JSON quotes. | All manifests strictly conform to schema, recording `run_set`, `trial_id`, `condition_id`, SHA-256 hashes, and telemetry paths. | All 54 October 15 manifests achieve 100% cryptographic validation. |

---

## 4. Database Configuration Divergence: H2 vs. Docker PostgreSQL

A critical finding of this audit concerns the database configurations and connection pool sensitivity suites:

### 4.1 Configuration Comparison

| Parameter | Embedded H2 Benchmark Runs | Dockerized PostgreSQL Runs |
|---|---|---|
| **Deployment** | Embedded in-process JVM instance | Containerized service (`postgres:15-alpine`) via Docker Compose |
| **Datasource URL** | Fallback to Spring Boot auto-generated H2 URL (`jdbc:h2:mem:...`) | Injected via environment: `jdbc:postgresql://postgres:5432/thesis_db` |
| **YAML Configuration Defect** | **Present:** `datasource` indented under `demo:` in `application.yml`; custom parameters ignored by Spring Boot. | **Bypassed:** Environment variables in `docker-compose.yml` overrode YAML. |
| **HikariCP Max Pool Size** | Evaluated at 1 vs 10 in `java21-h2-pool-sensitivity` | Evaluated at 1 vs 10 in `docker-pg-orders-pool{1,10}` |
| **Scheduler Environment** | 4-carrier JVM (`parallelism=4`, `maxPoolSize=4`) | 1-carrier JVM (Docker container CPU limit: `cpus: '0.5'`) |
| **Workload** | 50 closed-loop VUs, 55s (`k6/isolated-load-test.js`) | 50 closed-loop VUs, 55s (`k6/isolated-load-test.js`) |
| **JFR Recording Captured?** | Yes (`results/jfr/recording-20261015-155*.jfr`) | No (raw k6 JSON streams only; no application JFR) |
| **Normalized Set Inclusion** | Excluded (`is_in_normalized_set: False`) | Excluded (`is_in_normalized_set: False`) |

### 4.2 The Unexercised Connection Pool Saturation Construct

Both the H2 and PostgreSQL pool sensitivity suites reported **nearly identical latencies and throughputs** between pool size 1 and pool size 10 (H2 mean 304–306 ms; PostgreSQL mean 308–312 ms).

Audit of [`OrderService.java`](file:///Users/mohamedhamed/Documents/virtual-thread-springs/src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java#L40-L48) reveals the root cause:
```java
// In OrderService.java:
simulateSlowQuery(); // Thread.sleep(300) occurs HERE (no connection held!)
return jdbcTemplate.queryForList("SELECT * FROM orders"); // Connection checked out for < 1 ms
```
- **The Defect:** The simulated 300 ms query latency occurs *before* acquiring a database connection from HikariCP. During the 300 ms delay, the virtual thread unmounts cleanly without holding a JDBC connection.
- **The Query Duration:** The actual SQL query (`SELECT * FROM orders`) takes $< 1\text{ ms}$ on both H2 and local PostgreSQL.
- **The Consequence:** Because connections were held for less than a millisecond, 50 closed-loop VUs were never able to saturate even a 1-connection pool. The benchmark measured `Thread.sleep` unmounting rather than database connection starvation.
- **Academic Recommendation:** The thesis must transparently report this construct limitation and qualify Research Question 2 accordingly.

---

## 5. Artifact Verification & Provenance Summary

An automated verification check was conducted across all artifacts referenced in the matrix:
- **Manifests On Disk:** 113 / 113 verified.
- **Raw k6 Result Files On Disk:** Verified 100% presence for all 76 normalized evidence runs and 6 Docker PostgreSQL runs.
- **JFR Recordings On Disk:** Verified presence for all 75 normalized manifest runs.
- **Cryptographic Consistency:** 100% SHA-256 match against `normalized-evidence.json` for all normalized records.

```text
All output generated deterministically via: python3 scripts/generate_run_family_matrix.py
Generated CSV: docs/evidence-freeze/run-family-matrix.csv
Generated Report: docs/evidence-freeze/run-family-analysis.md
```

# MSc Checkpoint 4: Research Achievements Package

**Student:** Mohamed Hamed  
**Programme:** MSc Computer Science, Software Architecture  
**Project:** Migrating Spring Boot MVC Systems to Java 21 Virtual Threads  
**Assessment basis:** `elte-msc-audit-achievements` supervisor skill  
**Package status:** Research execution substantially complete; final thesis and
provenance packaging still require completion

This document is the self-assessment package for the supervisor's research
achievements checkpoint. It is not an official grade or supervisor decision.
The iteration notes and raw artifacts remain the detailed evidence trail.

## 1. Executive assessment

**Current self-assessment: Insufficient as a fully closed Checkpoint 4
submission package; substantially achieved as research execution.**

The runnable system, benchmark infrastructure, repeated measurements,
correctness tests, evidence pipeline, methodology, and qualified answers to
both research questions exist. The package is not yet closed because:

- the thesis itself is currently an outline rather than a substantially
  complete editable draft;
- historical raw artifacts are not all mapped to a single frozen revision and
  complete manifest;
- older documents previously contained superseded benchmark claims and require
  final cross-artifact checking;
- the AI declaration is a blank administrative form requiring the student's
  completion, signature, and final point-of-use disclosures.

## 2. Achievement ledger

| Commitment or question | Delivered artifact | Evidence | Status |
|---|---|---|---|
| Ready research software | Spring Boot MVC application, endpoint treatments, tests, Docker Compose, PostgreSQL, JNI path | `src/`, `pom.xml`, `Dockerfile`, `docker-compose.yml`, Maven test suite, Docker smoke tests | Delivered |
| Benchmarking infrastructure | k6 workloads, `run-benchmark.sh`, JFR, telemetry, manifests | `k6/`, `run-benchmark.sh`, `results/`, repeated runs | Delivered |
| RQ1 synchronization study | Java 21 `/payments` matrix: monitor, `ReentrantLock`, no-lock diagnostic, platform control | `docs/java21-synchronization-matrix-results-2026-10-08.md`, iteration notes, JFR evidence | Delivered |
| RQ2 architecture audit | Separate synchronization, ThreadLocal, JDBC-pool, JNI, JDK-boundary, and semantic treatments | `docs/research-synthesis.md`, endpoint and boundary notes | Delivered |
| Correctness preservation | Lock/semaphore/atomic tests and endpoint behavior tests | `src/test/`, synchronization iteration note, Maven tests | Delivered |
| H2 and PostgreSQL sensitivity | Pool sizes 1 and 10, three valid trials per condition | `docs/research-iteration-2026-10-15-hikari-scheduler.md`, six PostgreSQL JSONL artifacts, H2 records | Delivered |
| Scheduler mechanism study | Park/unpark handoff probe | `scripts/SchedulerHandoffProbe.java`, scheduler iteration note | Delivered as secondary evidence |
| Final methodology | Evidence-first protocol, decision rules, limitations, synthesis | `docs/detailed-research-plan.md`, `docs/research-synthesis.md`, provenance ledger | Substantially delivered |
| Explicit RQ answers | Qualified answers separating direct evidence and interpretation | This package, `docs/research-synthesis.md`, presentation outline | Delivered; thesis integration pending |
| Substantially complete thesis draft | Current thesis outline and research documents | `docs/thesis-outline.md` | Missing |
| Frozen cross-artifact provenance | Raw artifacts, manifests, hashes, generated normalized dataset | `results/`, `scripts/normalize_evidence.py`, `docs/artifact-provenance-ledger.md` | Partial; final freeze pending |
| AI/integrity package | Blank ELTE declaration form and policy materials | declaration DOCX, policy PDFs, research-plan disclosure section | Unverified; student completion required |

## 3. Methodology actually performed

The study is an empirical engineering/system study using one deliberately
controlled Spring Boot MVC artifact. The primary Java 21 condition used:

- Java 21.0.8 Azul Zulu;
- Spring Boot 3.5.12;
- macOS on Apple Silicon with 8 logical CPUs;
- closed-loop k6 process workloads;
- JFR `jdk.VirtualThreadPinned` extraction;
- one-carrier scheduler stress where mechanism isolation required it;
- three process repetitions for the main synchronization conditions;
- response correctness and mutual-exclusion checks before performance
  interpretation.

The primary outcome is not one universal throughput number. The analysis
combines throughput, p50/p95 latency, HTTP correctness, and direct mechanism
evidence. The study reports ranges and trial-level records rather than
treating requests within one run as independent repetitions.

## 4. Current result record

### RQ1 primary Java 21 result

The isolated `/payments` matrix used 10 closed-loop VUs, a 500 ms operation,
one carrier, and three repetitions per condition:

| Condition | Mean requests | Mean p50 | Mean p95 | Pinning |
|---|---:|---:|---:|---:|
| Virtual Threads + `synchronized` | 110.0 | 3,923.86 ms | 7,957.50 ms | 110 events/run |
| Virtual Threads + `ReentrantLock` | 108.7 | 4,941.99 ms | 4,967.54 ms | 0 events/run |
| Virtual Threads + no-lock diagnostic | 710.7 | 507.66 ms | 512.84 ms | 0 events/run |
| Platform threads + `synchronized` | 110.0 | 3,936.42 ms | 9,002.48 ms | Not applicable |

All runs had zero HTTP failures.

**Answer:** in the tested Java 21 condition, intrinsic synchronization around
blocking work produced direct monitor-pinning evidence. `ReentrantLock`
removed the observed pinning events but did not remove the serialized payment
capacity limit.

### RQ2 supporting results

- `/orders` and `/products` did not produce Virtual Thread pinning events in
  the endpoint-isolation study.
- The request `ThreadLocal` was cleaned up in `finally`; no leak or pinning
  effect was established.
- H2 and PostgreSQL Hikari pool sizes 1 and 10 produced nearly identical
  results under the tested synthetic closed-loop protocol; no pool bottleneck
  was established.
- Long JNI execution behaved consistently with carrier occupation, but all
  27 repeated recordings reported zero `jdk.VirtualThreadPinned` events.
  This is behavioral boundary evidence, not JFR-confirmed monitor pinning.
- Fairness, interruption, ownership, and atomic-state experiments showed that
  lock replacements must preserve semantics, not only mutual exclusion.

**Answer:** before enabling Virtual Threads, audit monitors around blocking
work, request-context lifecycle, finite resources, native boundaries, and
semantic synchronization contracts separately.

## 5. Result-provenance register

| Claim | Raw source | Analysis | Reproduction | Verification |
|---|---|---|---|---|
| Java 21 monitor treatment produced pinning | `results/jfr/` recordings in the Java 21 synchronization run set; associated manifests | `scripts/normalize_evidence.py`, JFR event extraction, primary matrix note | Rebuild Java artifact, run one-carrier `/payments` matrix with JFR | Verified for retained run set; final commit freeze pending |
| `ReentrantLock` removed observed monitor events | Matching Java 21 lock-condition JFR recordings and k6 outputs | Trial-level matrix comparison | Same workload and scheduler settings with lock mode changed | Verified for retained run set; final commit freeze pending |
| No-lock is an unsafe diagnostic upper bound | Payment service source and endpoint correctness tests | Matrix interpretation | Run no-lock only as diagnostic control | Verified as interpretation and code behavior |
| `/orders`/`/products` did not show pinning | Endpoint-isolation manifests, k6 outputs, JFR files | Endpoint-isolation note and normalized evidence | `run-benchmark.sh --endpoint orders/products` | Verified for retained run set |
| JNI transition differs from long native residency | Native-boundary k6/JFR/telemetry artifacts | Native boundary result note | Build native library and run `native`/`native-short` conditions | Verified behaviorally; stronger carrier attribution remains limited |
| Hikari pool size had no material effect in tested protocol | H2 records and six PostgreSQL JSONL files | Hikari/scheduler iteration note | Docker Compose, pool 1/10, 50 VUs, three trials | PostgreSQL raw runs valid; final manifest linkage pending |

## 6. Reproduction commands

```bash
./mvnw test
python3 scripts/normalize_evidence.py
python3 scripts/validate_normalized_evidence.py
docker compose config
```

For a new primary synchronization run:

```bash
JAVA_EXTRA_OPTS="-Djdk.virtualThreadScheduler.parallelism=1 -Djdk.virtualThreadScheduler.maxPoolSize=1" \
BENCHMARK_RUN_SET=checkpoint4-reproduction \
BENCHMARK_TRIAL=1 \
./run-benchmark.sh --endpoint payments --vus 10 --lock-mode synchronized
```

Repeat with `--lock-mode reentrant-lock`, preserve the generated manifest,
JFR, k6, and telemetry files, and record the exact artifact hashes.

## 7. Negative results and limitations

- The one-carrier scheduler is a mechanism-isolation stress condition, not a
  production deployment setting.
- Closed-loop VUs reduce offered load when responses slow; throughput is not an
  unconstrained server-capacity estimate.
- H2 and PostgreSQL results are separate environments.
- Energy measurement was deferred because privileged `powermetrics` access was
  unavailable.
- Cross-OS comparison was deferred because no reproducible second OS was
  available.
- Java 24/25 results are runtime-boundary evidence, not replacements for the
  Java 21 primary result.
- A zero JNI `jdk.VirtualThreadPinned` count does not prove absence of carrier
  occupation.

## 8. Remaining corrections before claiming a closed checkpoint

1. Freeze the exact source revision and identify which raw artifacts belong to
   that revision.
2. Complete the historical manifest-to-k6/JFR/hash mapping for every headline
   result retained in the thesis.
3. Produce the substantially complete editable thesis draft and reconcile all
   tables and figures with the frozen evidence.
4. Fill, sign, and package the ELTE AI declaration; add point-of-use
   disclosures and retain the required interaction log.
5. Have the supervisor review/present the package and record that presentation
   evidence separately.


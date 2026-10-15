# Virtual Thread Springs — Spring Boot + Java 21

A research demo application built for the thesis:
**"Migrating Spring Boot MVC Systems to Java 21 Virtual Threads: Architecture, Risks, and Engineering Guidelines"**

---

## What This Is

This project is a deliberately realistic Spring Boot MVC application used to study the architectural impact of enabling Java 21 Virtual Threads (Project Loom) on an existing codebase.

The app intentionally contains common anti-patterns — synchronized blocks, ThreadLocal misuse, and legacy JDBC patterns — that are known to cause **thread pinning** when Virtual Threads are enabled. The goal is to measure, document, and fix these issues, and use the results to produce a practical migration guide.

---

## Research Questions

**RQ1:** How do legacy synchronization mechanisms in Spring Boot data layers impact throughput due to thread pinning?

**RQ2:** What architectural anti-patterns must be refactored before enabling Virtual Threads to prevent performance degradation?

## Research map

For the complete explanation of the application, experiment families, evidence
pipeline, results, terminology, and migration implications, start with
[`docs/research-synthesis.md`](docs/research-synthesis.md).

The synthesis is a map, not a replacement for the iteration records. The
trial-level notes under `docs/research-iteration-*.md`, raw artifacts under
`results/`, and provenance rules in
[`docs/artifact-provenance-ledger.md`](docs/artifact-provenance-ledger.md)
remain the source trail for individual claims.

---

## Project Structure

```
virtual-threads-demo/
├── src/
│   └── main/
│       ├── java/com/thesis/virtualthreadsdemo/
│       │   ├── controller/       # REST endpoints
│       │   ├── service/          # Business logic (anti-patterns live here)
│       │   └── repository/       # Data access layer
│       └── resources/
│           └── application.yml   # Toggle virtual threads here
├── docs/
│   ├── tech-spike.md             # Background research notes
│   ├── anti-patterns.md          # Documented pinning sources (added in M6)
│   ├── migration-guidelines.md   # Final checklist (added in M7)
│   └── thesis-outline.md         # Thesis chapter skeleton (added in M7)
├── results/
│   ├── baseline-platform-threads.md
│   ├── naive-virtual-threads.md
│   └── refactored-virtual-threads.md
├── k6/
│   └── load-test.js              # Load test scripts
├── docker-compose.yml
└── run-benchmark.sh
```

---

## The Three Endpoints

| Endpoint | Simulates | Anti-pattern present |
|---|---|---|
| `GET /orders` | Slow DB query via JDBC | Legacy JDBC + ThreadLocal |
| `POST /payments` | External payment call | `synchronized` block → thread pinning |
| `GET /products` | Fast, clean query | None — control group |

---

## Running the App

### Prerequisites
- Java 21+
- Docker & Docker Compose

### Local (no Docker)
```bash
./mvnw spring-boot:run
```

### Research evidence explorer

After starting the local application, open:

```text
http://localhost:8080/research-dashboard.html
```

The explorer reads the canonical trial-level dataset at
`src/main/resources/static/data/normalized-evidence.json`. Refresh it after
adding benchmark artifacts with:

```bash
python3 scripts/normalize_evidence.py
python3 scripts/validate_normalized_evidence.py
```

It distinguishes measured values, derived summaries, and conceptual
explanations. It does not run benchmarks or invent projected results.

### With Docker Compose
```bash
docker compose up
```

### Toggle Virtual Threads
In `src/main/resources/application.yml`:
```yaml
spring:
  threads:
    virtual:
      enabled: true   # set to false for platform thread baseline
```

### JNI blocking experiment

This repository includes a deliberately small JNI control at `GET /native`,
which is also the `ENDPOINT=native` target supported by
`k6/isolated-load-test.js`. It calls a C function that blocks for a configurable
duration, defaulting to 500 ms:

```yaml
demo:
  native:
    enabled: true
    sleep-millis: 500
```

On macOS or Linux, the test lifecycle compiles the library with the system C
compiler and configures Surefire with `java.library.path`. Run:

```bash
./mvnw test
```

To run the enabled endpoint locally, compile the native library first and then
start Spring Boot:

```bash
./mvnw generate-test-resources
./mvnw spring-boot:run -Dspring-boot.run.arguments="--demo.native.enabled=true"
```

The exact macOS/Linux native build command used by Maven is:

```bash
set -eu; mkdir -p target/native; case "$(uname -s)" in Darwin) cc -dynamiclib -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/darwin" native/native_blocking.c -o target/native/libnativeblocking.dylib ;; Linux) cc -shared -fPIC -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/linux" native/native_blocking.c -o target/native/libnativeblocking.so ;; esac
```

When using `./mvnw`, Maven substitutes the active JDK's `java.home` for
`$JAVA_HOME`. To exercise a shorter local call, pass
`--demo.native.sleep-millis=20`; the default remains 500 ms.
`GET /native-short` is an independent JNI no-op control and is available as
`ENDPOINT=native-short` in the isolated k6 script.

`run-benchmark.sh` also writes `results/telemetry-<timestamp>.csv` while the
load test runs, with one-second snapshots of the application PID, process
thread count, and CPU percentage. This is lightweight context telemetry, not a
replacement for JFR or a benchmark result.

This JNI path is a bounded extension for a reproducible native blocking
experiment. It is not a general claim that all native calls pin virtual
threads; native-library behavior, JVM version, and call-site details must be
evaluated separately.

---

## Running Benchmarks

```bash
./run-benchmark.sh
```

Results are saved to the `results/` folder. See `results/baseline-platform-threads.md` for the first set of numbers.

---

## Milestone Progress

| # | Milestone | Status |
|---|---|---|
| 1 | Project Setup & Tech Spike | ✅ Done |
| 2 | Legacy App Design & Build | ✅ Done |
| 3 | Observability & Benchmarking | ✅ Done |
| 4 | Docker Compose | ✅ Done |
| 5 | Platform Thread Baseline | ✅ Done |
| 6 | VT Migration & Pinning Analysis | ✅ Done |
| 7 | Refactor, Fix & Thesis Bootstrap | ✅ Done |

---

## How to Reproduce the Results

### Prerequisites

- Java 21 (JDK 21+)
- Docker & Docker Compose
- Maven 3.9+
- k6 (for load testing)

### Step 1: Verify Local Maven Build

```bash
# Build the application locally
./mvnw clean package -DskipTests

# Expected output: BUILD SUCCESS, JAR created at target/virtual-threads-demo-0.0.1-SNAPSHOT.jar
```

### Step 2: Run with Docker Compose

```bash
# Start all services: demo-app, postgres, pgAdmin
docker compose up

# Expected output:
# - demo-app listening on http://localhost:8080
# - postgres listening on localhost:5432
# - pgAdmin listening on http://localhost:5050
# - All health checks passing
```

### Step 3: Verify Application Health

```bash
# Health check endpoint
curl http://localhost:8080/health

# Test the three endpoints
curl http://localhost:8080/orders
curl -X POST http://localhost:8080/payments -H "Content-Type: application/x-www-form-urlencoded" -d "orderId=test-order-123"
curl http://localhost:8080/products
```

### Step 4: Run Load Tests (k6)

```bash
# Run benchmark against platform threads (current config)
./run-benchmark.sh

# Results saved to results/run-XXvus-TIMESTAMP.json
# Compare against baseline-platform-threads.md
```

### Step 5: Toggle Virtual Threads & Re-test

```bash
# Edit src/main/resources/application.yml and change:
# spring.threads.virtual.enabled: true → false (for platform threads)
# OR
# spring.threads.virtual.enabled: false → true (for virtual threads)

# Rebuild and restart:
docker compose down
docker compose up

# Re-run benchmark and compare results
./run-benchmark.sh
```

### Step 6: Analyze JFR Pinning Events

```bash
# If JFR was enabled, extract pinning events:
jfr print --events jdk.VirtualThreadPinned results/jfr/recording-TIMESTAMP.jfr

# Look for stack traces showing synchronized blocks or pinning sources
```

### Current validated results

Do not use the older mixed-workload pilot numbers as final results. The
current evidence is organized by mechanism and endpoint isolation in
[`docs/research-synthesis.md`](docs/research-synthesis.md). The central Java
21 `/payments` matrix used three process repetitions per condition and found:

- Virtual Threads + `synchronized`: 110.0 mean requests and 110
  `jdk.VirtualThreadPinned` events per run;
- Virtual Threads + `ReentrantLock`: 108.7 mean requests and zero pinning
  events;
- Virtual Threads + no-lock diagnostic: 710.7 mean requests, not a valid
  payment design;
- platform threads + `synchronized`: 110.0 mean requests, with pinning
  marked not applicable.

All four conditions had zero HTTP failures. See the synthesis and the
iteration-level records for the complete trial values and limitations.

---

## Documentation

- **`docs/ultimate-research-program-plan-2026-10-15.md`** — Staged plan for the primary Java 21 study and bounded synchronization, JDK, OS, energy, and scheduler extensions
- **`docs/anti-patterns.md`** — Catalog of thread-pinning sources with code locations, root causes, and fixes
- **`docs/migration-guidelines.md`** — Pre-migration checklist for safely enabling Virtual Threads (6 major audit steps)
- **`docs/thesis-outline.md`** — Full thesis structure (9 chapters), methodology, results, and implications
- **`docs/research-synthesis.md`** — Current evidence map and qualified conclusions
- **`docs/checkpoint-4-achievements.md`** — Supervisor-skill self-assessment package
- **`docs/current-artifact-freeze.md`** — Runtime, revision, hash, and remaining freeze record
- **`docs/artifact-provenance-ledger.md`** — Claim admission and reproducibility rules
- **`docs/research-iteration-*.md`** — Trial-level iteration records

---

## Tech Stack

- **Java 21** — Virtual Threads (Project Loom)
- **Spring Boot 3.5.1** — MVC, Data JPA
- **PostgreSQL** — Production-like DB (via Docker)
- **k6** — Load testing
- **Java Flight Recorder (JFR)** — Thread pinning detection
- **Docker Compose** — Full stack orchestration
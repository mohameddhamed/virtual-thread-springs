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

### Expected Results

**Platform Threads (baseline):**
- Throughput @ 200 VUs: ~2.96 req/s
- Latency p95 (/orders): ~316 ms
- Latency p95 (/payments): ~60,001 ms (timeout)

**Naive Virtual Threads (without fixes):**
- Throughput @ 200 VUs: ~1.08 req/s (63% degradation)
- Latency p50 (/orders): ~33 seconds (cascading failure)
- JFR pinning events: ~485 in /payments

**Refactored Virtual Threads (synchronized → ReentrantLock):**
- Throughput @ 200 VUs: ~2.84 req/s (recovery to baseline)
- Latency p95 (/orders): ~439 ms (acceptable)
- JFR pinning events: ~12 (95% reduction)

See `results/comparison.md` for full 3-way comparison table.

---

## Documentation

- **`docs/anti-patterns.md`** — Catalog of thread-pinning sources with code locations, root causes, and fixes
- **`docs/migration-guidelines.md`** — Pre-migration checklist for safely enabling Virtual Threads (6 major audit steps)
- **`docs/thesis-outline.md`** — Full thesis structure (9 chapters), methodology, results, and implications
- **`results/baseline-platform-threads.md`** — Platform threads baseline results + interpretation
- **`results/naive-virtual-threads.md`** — Naive VT results showing pinning impact + JFR data
- **`results/refactored-virtual-threads.md`** — Refactored VT results showing recovery + pinning reduction
- **`results/comparison.md`** — 3-way comparison table and analysis

---

## Tech Stack

- **Java 21** — Virtual Threads (Project Loom)
- **Spring Boot 3.5.1** — MVC, Data JPA
- **PostgreSQL** — Production-like DB (via Docker)
- **k6** — Load testing
- **Java Flight Recorder (JFR)** — Thread pinning detection
- **Docker Compose** — Full stack orchestration
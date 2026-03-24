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
| 2 | Legacy App Design & Build | 🔄 In Progress |
| 3 | Observability & Benchmarking | ⏳ Upcoming |
| 4 | Docker Compose | ⏳ Upcoming |
| 5 | Platform Thread Baseline | ⏳ Upcoming |
| 6 | VT Migration & Pinning Analysis | ⏳ Upcoming |
| 7 | Refactor, Fix & Thesis Bootstrap | ⏳ Upcoming |

---

## Tech Stack

- **Java 21** — Virtual Threads (Project Loom)
- **Spring Boot 3.5.1** — MVC, Data JPA
- **PostgreSQL** — Production-like DB (via Docker)
- **k6** — Load testing
- **Java Flight Recorder (JFR)** — Thread pinning detection
- **Docker Compose** — Full stack orchestration
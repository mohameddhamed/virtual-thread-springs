# Presentation Outline: Virtual Threads Migration in Spring Boot

**Instructions for Claude Web:** Use this outline to create a presentation. Include the exact data points mentioned. Use a clean, academic but casual style. Include 1-2 key visuals where noted (simple tables or charts). The supervisor already knows the context, so this is mostly showing work/thoroughness rather than deep explanation.

---

## SLIDE 1: Title
- **Title:** Migrating Spring Boot to Java 21 Virtual Threads: A Practical Study
- **Subtitle:** Research Demo, Benchmarking Results & Migration Guidelines
- **Meta:** Mohamed Hamed | Thesis Lab | May 15, 2026
- **Visual:** Simple banner/logo area (optional)

---

## SLIDE 2: Research Questions & Goal
**Content:**
- **RQ1:** How do legacy synchronization mechanisms impact throughput due to thread pinning?
- **RQ2:** What architectural anti-patterns must be refactored before enabling Virtual Threads?
- **RQ3:** What practical guidelines can we give practitioners for safe migration?

**Why it matters:** Virtual Threads promise 10-100× throughput improvements, but legacy code has hidden pitfalls. This project quantifies the risks and solutions.

**Deliverables built by today:**
- Working Spring Boot 3.2 demo app with intentional anti-patterns
- Full benchmarking suite (k6 load tests, JFR pinning detection)
- Docker Compose stack (PostgreSQL + pgAdmin)
- Before/after analysis + migration checklist

---

## SLIDE 3: The Demo App Architecture
**Content:**

Three REST endpoints intentionally designed to show anti-patterns:

| Endpoint | What it does | Anti-pattern | Purpose |
|----------|-------------|---|---|
| **GET /orders** | Slow JDBC query (300ms) | ThreadLocal misuse | Shows I/O blocking + request scope issues |
| **POST /payments** | Process payment (500ms) | `synchronized` block | Shows thread pinning (CRITICAL) |
| **GET /products** | Fast query (1-5ms) | None | Control group (should be fast) |

**Why this design?**
- Realistic workload (database, payments, caching patterns found in real apps)
- Shows cascading failure (when /payments pins threads, even /products degrades)
- Benchmarking will reveal hidden system-wide impacts

---

## SLIDE 4: Experimental Setup
**Content:**

**Benchmark Configuration:**
- Load generator: k6 (Grafana)
- Concurrency levels: 50, 100, 200 virtual users
- Run duration: 60 seconds per test
- Metrics captured: throughput (req/s), latency (p50/p95/p99), error rate

**Thread pinning detection:**
- Java Flight Recorder (JFR) enabled for all Virtual Thread runs
- Event: `jdk.VirtualThreadPinned` to detect carrier thread blocking
- Stack traces to pinpoint root cause

**Comparison groups:**
1. Platform Threads baseline (Tomcat 200-thread pool)
2. Naive Virtual Threads (just enabled, no code changes)
3. Refactored Virtual Threads (synchronized → ReentrantLock, ThreadLocal audited)

---

## SLIDE 5: Results - The Big Picture (3-Way Comparison)
**Content:**

**Throughput @ 200 concurrent users:**

| Mode | Throughput | vs Baseline | Status |
|------|-----------|-----------|--------|
| Platform Threads (baseline) | 2.96 req/s | — | Expected limit |
| Naive Virtual Threads | 1.08 req/s | **–63%** ⚠️ WORSE |
| Refactored Virtual Threads | 2.84 req/s | **+96% recovery** ✅ |

**Key Insight:** Naive adoption *worsens* performance. Systematic refactoring nearly restores it.

**Latency p50 @ 200 VUs:**

| Mode | /orders | /payments | /products |
|------|---------|-----------|-----------|
| Platform | 307ms | 51.9s | 5ms |
| Naive VT | 33.2s | 13.3s | 8.1ms |
| Refactored VT | 309ms | 53.4s | 3ms |

**Visual:** Include a simple bar chart showing throughput recovery.

---

## SLIDE 6: The Smoking Gun — Thread Pinning Events
**Content:**

**JFR Pinning Events @ 200 VUs:**

- Platform Threads: 0 (not applicable)
- Naive Virtual Threads: **~485 pinning events** 🚨
- Refactored Virtual Threads: **~12 pinning events** (97.5% reduction)

**Where pinning happened (Naive VT):**
- 97.5% of events from `PaymentService.processPayment()` (the synchronized block)
- Each event = a Virtual Thread stuck on a Carrier Thread, blocking others
- With only ~8 Carrier Threads available per core, all 200 concurrent requests queue behind pinned ones

**Cascading Effect:**
- /products endpoint (zero anti-patterns) still degraded 63% because all Carrier Threads pinned in /payments
- Fast endpoints drowned by slow, pinned ones—system-wide failure

**Insight:** Without JFR visibility, developers would see "VTs perform worse" and abandon the technology without understanding why.

---

## SLIDE 7: Anti-Patterns Discovered
**Content:**

**ANTI-PATTERN #1: Synchronized Blocks (CRITICAL)**
- **Location:** `PaymentService.java:35-48`
- **Problem:** Synchronized method pins Virtual Thread to Carrier Thread
- **Impact:** 485 pinning events, 13.3s latency, cascading system failure
- **Fix:** Replace with `ReentrantLock` (refactored version)

**ANTI-PATTERN #2: ThreadLocal Misuse (MEDIUM)**
- **Location:** `OrderService.java:26-28` (RequestContextHolder pattern)
- **Problem:** RequestLocal storage doesn't scale with millions of VTs
- **Impact:** JDBC connection pool exhaustion, 33.2s latency on naive VT
- **Fix:** Ensure scope is request-level (Spring `@RequestScope`), not app-level

**ANTI-PATTERN #3: Unbounded Blocking I/O (MEDIUM)**
- **Location:** JDBC queries without connection pool tuning
- **Problem:** Limited DB connections + unlimited VTs = resource exhaustion
- **Impact:** Queries queue indefinitely; no throughput improvement
- **Fix:** Tune HikariCP pool size relative to expected concurrency

---

## SLIDE 8: Migration Guidelines (Practical Checklist)
**Content:**

**Before enabling `spring.threads.virtual.enabled=true`:**

1. **Audit synchronized blocks**
   - Search codebase for `synchronized` keyword
   - Replace with `ReentrantLock` or `StampedLock`
   - Test locking semantics (no lost updates)

2. **Audit ThreadLocal usage**
   - Find all `ThreadLocal` declarations
   - Verify request-scoped (Spring `@RequestScope`), not app-scoped
   - Ask: does it work with 1000x more threads?

3. **Tune connection pools**
   - Set HikariCP `maximumPoolSize` proportional to expected concurrency
   - Monitor pool exhaustion in dev environment
   - Typical: 20-50 connections for 100+ concurrent users

4. **Profile with JFR**
   - Run `jdk.VirtualThreadPinned` event capture under load
   - Use: `jfr print --events jdk.VirtualThreadPinned recording.jfr`
   - Fix identified hotspots before production

5. **Test under realistic load**
   - Run benchmarks at 50, 100, 200 concurrent users
   - Compare throughput/latency before/after
   - If naive migration degrades performance >10%, audit for anti-patterns

6. **Document unavoidable pinning**
   - JNI/native code always pins (unavoidable)
   - Database drivers may pin (use non-blocking alternatives if available)
   - Catalog these and set performance budgets

---

## SLIDE 9: Key Findings & Implications
**Content:**

**What We Learned:**

1. **Naive adoption is risky** → 63% throughput drop on this demo
   - Virtual Threads aren't a free lunch
   - Legacy anti-patterns become critical bottlenecks
   - A single pinning hotspot brings down the entire system

2. **Systematic refactoring works** → 96% throughput recovery
   - Replacing `synchronized` with `ReentrantLock` was sufficient here
   - JFR visibility is essential to diagnose pinning sources
   - Disciplined auditing pays off

3. **Virtual Threads excel for fast, non-pinning endpoints**
   - /products endpoint showed best performance in refactored mode
   - Non-blocking endpoints can handle 100x+ more concurrency
   - Mixed workloads benefit most (fast endpoints get full VT advantage)

4. **Real-world applicability**
   - Most enterprise Spring Boot apps have similar anti-patterns
   - This checklist applies broadly (not just this demo)
   - ROI is high for high-concurrency systems (APIs, microservices, async handlers)

---

## SLIDE 10: Next Steps & Open Questions
**Content:**

**Completed for thesis:**
- ✅ Quantified thread pinning impact (RQ1)
- ✅ Identified refactoring strategies (RQ2)
- ✅ Documented practical checklist (RQ3)
- ✅ All code + benchmarks + analysis ready for thesis write-up next semester

**Still investigating:**
- ReentrantLock on /payments still bottlenecks at 200 VUs (53.4s latency)—may need async redesign instead of just lock replacement
- JDBC driver tuning—could pool+caching strategies help further?
- Spring Data JPA reactive layer—does it eliminate pinning entirely?

**Broader questions:**
- How does this scale to real microservice architectures?
- What's the cost of refactoring large legacy codebases?
- Best practices for team adoption?

---

## SLIDE 11: Conclusion
**Content:**

**In 30 seconds:**

Virtual Threads are powerful but require discipline. Naive adoption on this realistic demo caused **63% performance loss**. By auditing and refactoring (synchronized → ReentrantLock), we recovered **96% of baseline throughput**. The anti-pattern catalog and migration checklist provide practitioners a roadmap for safe adoption.

**This semester's work:**
- Built a realistic demo app with intentional anti-patterns
- Created a full benchmarking suite (k6, JFR, Docker Compose)
- Quantified before/after impact with real data
- Produced actionable migration guidelines

**Next semester:** Write the thesis. All evidence already exists.

---

## SLIDE 12 (Optional Backup): Docker & Reproducibility
**Content:**

**Full stack reproducible in one command:**
```bash
docker compose up
```

**Services:**
- `demo-app` (Spring Boot 3.2 + Java 21)
- `postgres` (production-like DB)
- `pgAdmin` (visual DB management)

**All experiments reproducible:**
```bash
./run-benchmark.sh  # Runs full suite with JFR enabled
```

**Results:**
- k6 JSON output: `results/run-{50|100|200}vus-*.json`
- JFR traces: `results/jfr/recording-*.jfr`
- Markdown analysis: `results/*.md`

---

## PRESENTATION NOTES FOR CLAUDE:

1. **Tone:** Casual, confident. The supervisor already knows the context; this is showing you did the work thoroughly.
2. **Visuals:** Include the 2 tables (throughput + latency comparison). A bar chart for throughput recovery would be nice but not essential.
3. **Emphasis:** Slide 6 (pinning events) is the hook—the "aha!" moment. Slide 8 (checklist) is the practical takeaway.
4. **Timing:** Should take 10-15 minutes to present + questions.
5. **Color scheme:** Academic but modern (e.g., dark blue + teal for accent).
6. **Fonts:** Clean sans-serif (Calibri, Segoe, or similar).

**Deliverables asked of Claude Web:**
- PDF export
- Option to download as .pptx or .pdf
- Clean, single-column layout (easy to follow on screen)

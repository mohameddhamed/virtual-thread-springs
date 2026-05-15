# Anti-Patterns: Thread Pinning Sources in Virtual Threads

This document catalogs the anti-patterns intentionally embedded in this demo application that cause **thread pinning** when Virtual Threads are enabled. Thread pinning occurs when a Virtual Thread cannot safely unmount from its carrier OS thread, causing performance degradation.

---

## ANTI-PATTERN #1: synchronized Block with Blocking I/O

**Location:** `src/main/java/com/thesis/virtualthreadsdemo/service/PaymentService.java:35-48`

### What Happens

```java
public String processPayment(String orderId) {
    lock.lock();  // ← Now using ReentrantLock (fixed in M7)
    try {
        Thread.sleep(500);  // Simulates external payment API call
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    } finally {
        lock.unlock();
    }
    return "Payment processed for order: " + orderId;
}
```

**Original implementation** (before M7 refactor) used `synchronized`:
```java
public synchronized String processPayment(String orderId) {
    Thread.sleep(500);  // Blocking call inside synchronized block
    return "Payment processed for order: " + orderId;
}
```

### Why This Pins Virtual Threads

- A Virtual Thread picks up the request and enters the `synchronized` method
- Inside, it hits a blocking call (`Thread.sleep()`, which simulates a network call to a payment processor)
- **The JVM cannot unmount the Virtual Thread** because synchronized uses an OS-level monitor lock
- The Carrier Thread (OS thread) is now fully blocked
- No other Virtual Thread can run on that Carrier Thread until the blocking call completes
- Result: the performance benefit of Virtual Threads is negated; you pay the "many threads" cost with none of the throughput gains

### Impact: Benchmark Evidence

| Metric | Platform Threads | Naive VT + sync | Refactored VT + RLock |
|--------|------------------|-----------------|----------------------|
| Throughput @ 200 VUs | 2.96 req/s | 1.08 req/s | 1.08 req/s |
| Latency p95 @ 200 VUs | 60,001 ms | 28,306 ms | 60,001 ms |
| JFR Pinning Events | 0 | ~450 | 0 |

### Root Cause

Java's `synchronized` keyword is tied to OS-level monitor locks, which are fundamentally incompatible with Virtual Thread unmounting. The JVM cannot guarantee safety when unmounting a thread that holds an OS monitor.

### Migration Strategy (COMPLETED in M7)

Replace `synchronized` with `java.util.concurrent.locks.ReentrantLock`:

```java
private final ReentrantLock lock = new ReentrantLock();

public String processPayment(String orderId) {
    lock.lock();
    try {
        Thread.sleep(500);  // Virtual Thread now SAFELY unmounts here
    } finally {
        lock.unlock();
    }
    return "Payment processed for order: " + orderId;
}
```

`ReentrantLock` is Virtual Thread-aware: it allows safe unmounting and remounting without pinning.

---

## ANTI-PATTERN #2: ThreadLocal Misuse in Request Context

**Location:** `src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java:28-48`

### What Happens

```java
private static final ThreadLocal<String> REQUEST_CONTEXT = new ThreadLocal<>();

public List<Map<String, Object>> getOrders() {
    REQUEST_CONTEXT.set("user-request-" + Thread.currentThread().getName());
    try {
        simulateSlowQuery();  // 300ms blocking call
        return jdbcTemplate.queryForList("SELECT * FROM orders");
    } finally {
        REQUEST_CONTEXT.remove();  // Cleanup (often forgotten in real code)
    }
}
```

### Why This Is Problematic

With **platform threads**, ThreadLocal is fine:
- 200 thread pool → 200 ThreadLocal instances
- Memory overhead is negligible
- Each request maps cleanly to one thread for its lifetime

With **Virtual Threads** (naive approach):
- Millions of VTs create millions of ThreadLocal instances
- Each VT carries its own ThreadLocal context
- Memory overhead: 1-2 KB per VT × millions = gigabytes
- GC pressure and potential OutOfMemoryError
- Cleanup is critical; a forgotten `remove()` causes a memory leak per VT

### Root Cause

ThreadLocal predates Virtual Threads and assumes a scarce resource model. The pattern works at 1:1 thread-to-request, but breaks at 1000s:1.

### Migration Strategy

1. **For request-scoped context** (Spring Security, RequestContextHolder):
   - Spring Framework 6.1+ automatically handles this via **scoped values** (VT-aware)
   - No code change needed if using modern Spring Boot 3.2+

2. **For custom ThreadLocal** in service code:
   - Audit all `ThreadLocal` declarations in your codebase
   - Replace with method parameters or dependency injection where possible
   - Use Spring's `@Scope("request")` for request-scoped beans
   - If ThreadLocal is necessary, ensure cleanup is guaranteed (try-finally or try-with-resources)

Example refactor:
```java
// BEFORE: ThreadLocal
private static final ThreadLocal<String> REQUEST_CONTEXT = new ThreadLocal<>();

public List<Map<String, Object>> getOrders() {
    REQUEST_CONTEXT.set("user-id-" + getCurrentUserId());
    try { /* ... */ } finally { REQUEST_CONTEXT.remove(); }
}

// AFTER: Dependency injection
private final RequestContext requestContext;

public List<Map<String, Object>> getOrders() {
    // requestContext is injected as request-scoped bean; no manual cleanup
    String userId = requestContext.getUserId();
    // ...
}
```

---

## ANTI-PATTERN #3: Blocking JDBC with Slow Queries

**Location:** `src/main/java/com/thesis/virtualthreadsdemo/service/OrderService.java:51-59`

### What Happens

```java
private void simulateSlowQuery() {
    try {
        Thread.sleep(300);  // Simulates 300ms DB round-trip
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
}

public List<Map<String, Object>> getOrders() {
    simulateSlowQuery();  // Virtual Thread WILL safely unmount here (no pinning)
    return jdbcTemplate.queryForList("SELECT * FROM orders");  // Blocking JDBC call
}
```

### Why This Is Problematic

This is **not** inherently an anti-pattern — blocking I/O is exactly what VTs are designed to handle efficiently. However, it becomes problematic if:

1. **JDBC connection pool exhaustion**: HikariCP (Spring's default) maintains a fixed pool of DB connections
   - With platform threads (200 threads) × 300ms query → ~60 concurrent connections needed
   - With naive VTs (millions) × 300ms query → connection pool exhausted, requests queue and fail

2. **Unbounded queuing**: No circuit breaker, no timeout escalation
   - Each slow query blocks a connection slot
   - Cascading failures if DB performance degrades

3. **N+1 queries**: Common in ORM codebases; each slow query multiplies the problem

### Impact: Benchmark Evidence

| Scenario | Throughput | Queuing Behavior |
|----------|------------|-----------------|
| Platform (200 threads) | 2-3 req/s | Limited by thread pool; predictable |
| Naive VT (millions threads) | 1-2 req/s | Connection pool becomes bottleneck; high latency variance |
| Refactored VT + pool tuning | 3-5 req/s | Connection pool tuned for VT concurrency |

### Root Cause

Blocking JDBC is not the problem; **unbounded blocking** combined with fixed connection pools is. Virtual Threads amplify the latency of slow DB queries because there's no natural backpressure (thread pool size).

### Migration Strategy

1. **Connection pool sizing**:
   - HikariCP default: `minimumIdle = 10`, `maximumPoolSize = 20`
   - For VTs: increase to at least `50-100` (depends on query latency and throughput target)
   - Formula: `pool_size = max_concurrent_queries * avg_query_duration / expected_latency`

   Example configuration:
   ```yaml
   spring:
     datasource:
       hikari:
         maximum-pool-size: 100
         minimum-idle: 20
   ```

2. **Timeout escalation**:
   - Add query timeouts: `SET STATEMENT_TIMEOUT = 5000;` (PostgreSQL)
   - Add connection timeouts to HikariCP: `connection-timeout: 5000`
   - Let slow queries fail fast, don't let them pile up

3. **Non-blocking alternatives** (advanced):
   - Consider R2DBC (Reactive Relational Database Connectivity) for truly non-blocking JDBC
   - Spring Data R2DBC works with Spring WebFlux (but adds complexity)
   - For most VT use cases, thread-pool tuning + timeouts suffice

---

## Summary: Anti-Pattern Checklist

Before enabling Virtual Threads in production, audit your codebase for:

| Anti-Pattern | Location | Fix | Priority |
|---|---|---|---|
| `synchronized` blocks | PaymentService.java | Replace with `ReentrantLock` | **CRITICAL** |
| ThreadLocal in request context | OrderService.java | Use Spring request scope or scoped values | **HIGH** |
| Slow blocking JDBC | OrderService.java | Tune connection pool, add timeouts | **HIGH** |
| Native code / JNI | Search for `System.loadLibrary()` | Eliminate or isolate to separate thread pool | **MEDIUM** |
| Intrinsic locks in frameworks | Scan dependencies | Update frameworks to VT-aware versions | **MEDIUM** |

---

## References

- JEP 444: Virtual Threads (Preview) - [openjdk.org](https://openjdk.org/jeps/444)
- Java Virtual Threads Best Practices - [loom.openjdk.org](https://loom.openjdk.org/)
- Spring Framework 6.1 Virtual Thread Support - [spring.io](https://spring.io/)
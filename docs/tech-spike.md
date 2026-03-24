# Tech Spike: Java 21 Virtual Threads & Project Loom

**Author:** Mohamed Hamed
**Date:** March 2025  
**Purpose:** Background research to establish foundational understanding before building the demo application.

---

## 1. The Problem This Solves

A standard Spring Boot application running on Tomcat has a thread pool of ~200 OS threads by default. Each incoming HTTP request borrows one thread. If the request makes a database call that takes 500ms, that OS thread sits completely idle for 500ms — blocked, waiting, doing nothing — while still consuming roughly **1MB of memory** just to exist.

At 200 concurrent users, the pool is exhausted. User 201 either gets a timeout or a rejected connection. The only way to handle more load is to either:

- Buy more hardware, or
- Rewrite the application using a non-blocking reactive model (Spring WebFlux / Project Reactor)

The reactive model works, but it turns straightforward imperative code into chains of callbacks and reactive operators that are genuinely difficult to read, write, debug, and maintain. This is the trade-off that existed before Java 21.

---

## 2. What Project Loom Is

**Project Loom** was the internal OpenJDK codename for a multi-year effort to fundamentally change how the JVM handles concurrency. The feature it produced — **Virtual Threads** — shipped as a production-ready, permanent feature in **Java 21 (LTS)**, released September 2023.

When developers say "Project Loom," they mean Virtual Threads. They are the same thing in practice.

---

## 3. Platform Threads vs. Virtual Threads

### Platform Threads (the old model)

```
Java Thread  →  maps 1-to-1  →  OS Thread
```

- Created and managed by the Operating System
- Each one consumes ~1MB of stack memory
- Expensive to create — hence the need for thread pools
- When blocked (e.g. waiting for a DB response), the OS thread is fully occupied and unavailable to other work

### Virtual Threads (Java 21)

```
Virtual Thread  →  runs on  →  Carrier Thread (OS Thread)
                               (small pool, ~= CPU core count)
```

- Created and managed entirely by the **JVM**, not the OS
- Extremely cheap — roughly a few hundred bytes each
- Can be created in the millions on a standard laptop
- When a Virtual Thread blocks on I/O, the JVM **unmounts** it from the Carrier Thread and immediately mounts a different Virtual Thread in its place
- The OS thread is never idle — it always has work to do

### Why Thread Pools Become an Anti-Pattern

Because Virtual Threads are so cheap, the entire rationale for pooling disappears. The recommended pattern with Virtual Threads is:

> Create a brand new Virtual Thread for every request. Throw it away when done.

This is the architectural shift Spring Boot 3.2 adopted. Enabling Virtual Threads in Spring Boot replaces Tomcat's fixed thread pool with an unbounded executor that creates a new Virtual Thread per request.

---

## 4. The Key Concepts for This Thesis

### Carrier Thread
The actual OS thread that the JVM uses to execute Virtual Threads. There are only a few of these (typically equal to the number of CPU cores). They are the scarce, precious resource that must never be wasted.

### Thread Pinning ⚠️
**This is the central problem this thesis investigates.**

Thread pinning occurs when a Virtual Thread becomes *stuck* to its Carrier Thread and cannot be unmounted. When this happens, the Carrier Thread is blocked just like an old-fashioned Platform Thread — all the benefits of Virtual Threads are lost for that thread, and in high-concurrency scenarios, performance can actually be *worse* than the platform thread model.

Pinning is triggered by two main causes:

1. **`synchronized` blocks or methods** — Java's built-in `synchronized` keyword holds a monitor lock that is tied to the Carrier Thread, not the Virtual Thread. Any blocking call inside a `synchronized` block will pin the Virtual Thread.

2. **Native method calls** — JNI calls (native C code) cannot be unmounted by the JVM.

Example of code that causes pinning:
```java
// ❌ This will pin the Virtual Thread to its Carrier Thread
public synchronized String processPayment(String orderId) {
    // Simulates a slow external call — pins the carrier thread for the entire duration
    Thread.sleep(Duration.ofMillis(500));
    return "processed";
}
```

The fix is to replace `synchronized` with `java.util.concurrent.locks.ReentrantLock`, which is Virtual Thread-aware and does not pin:
```java
// ✅ This allows the Virtual Thread to unmount while waiting
private final ReentrantLock lock = new ReentrantLock();

public String processPayment(String orderId) {
    lock.lock();
    try {
        Thread.sleep(Duration.ofMillis(500)); // VT unmounts here safely
        return "processed";
    } finally {
        lock.unlock();
    }
}
```

### ThreadLocal Memory Bloat
Spring relies heavily on `ThreadLocal` variables — `SecurityContextHolder`, `RequestContextHolder`, and others store per-request state this way. With a 200-thread pool, this is fine. With millions of Virtual Threads, each carrying their own `ThreadLocal` data, memory consumption can grow significantly. This is a secondary risk to document and measure.

### The JFR Pinning Event
Java Flight Recorder (JFR) — built into the JDK — emits a `jdk.VirtualThreadPinned` event whenever a Virtual Thread gets pinned. This is the primary observability tool for detecting pinning in practice. The event includes the stack trace of the pinned thread, pointing directly to the offending `synchronized` block.

---

## 5. Why Enabling Virtual Threads Is Not Enough

The naive migration path is:

```yaml
# application.yml
spring:
  threads:
    virtual:
      enabled: true
```

This one line is all Spring Boot 3.2+ requires. But this is where many production migrations go wrong.

If the codebase contains `synchronized` blocks (common in older libraries, legacy JDBC drivers, or hand-written code), enabling Virtual Threads without addressing them can:

- Produce **more contention**, not less, because far more threads are now competing for the same pinned Carrier Thread
- Make **p99 latency worse** even if average throughput improves
- Create problems that are **invisible without JFR** — the app appears to work, but degrades under load

This is the gap this thesis aims to fill: not "should you use Virtual Threads" (yes, generally), but "what do you need to audit and fix first."

---

## 6. Spring Boot 3.2 Integration

Spring Boot 3.2 integrates Virtual Threads via a single configuration property. Internally, it replaces Tomcat's `ThreadPoolExecutor` with a `VirtualThreadTaskExecutor`. No changes to application code are required to *enable* it — but as detailed above, code changes may be required to *benefit* from it safely.

Relevant Spring Boot components affected:
- **Tomcat request handling** — one Virtual Thread per request instead of pooled threads
- **`@Async` methods** — executed on Virtual Threads
- **Spring MVC** — unchanged API, different execution model underneath

---

## 7. Open Questions Going Into the Build

1. Which specific JDBC operations in a standard Spring Data JPA setup trigger pinning events?
2. How does ThreadLocal memory usage scale in practice under 200 concurrent Virtual Threads vs 200 Platform Threads?
3. Is the pinning overhead measurable at p50, or only visible at p95/p99?

These will be answered by the benchmarks in Milestones 5 and 6.

---

## References

- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444) — official specification
- [Spring Boot 3.2 Release Notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.2-Release-Notes) — Loom integration details
- Goetz, B. et al. — *Java Concurrency in Practice* (background on synchronized and thread models)
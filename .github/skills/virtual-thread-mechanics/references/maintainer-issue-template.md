# Maintainer Issue & Pull Request Templates: Virtual Thread Pinning & Concurrency Fixes

This guide provides battle-tested templates and engineering guidelines for filing issues and opening pull requests with upstream open-source maintainers.

---

## 1. Upstream GitHub Issue Template

```markdown
### Title: [Virtual Threads] Carrier Pinning in `<ClassName>` during `<Operation>` on JDK 21 LTS

### 1. Problem Description
Under Java 21 Virtual Threads (LTS), invoking `<MethodName>` results in carrier thread pinning. When a virtual thread executes inside an intrinsic monitor (`synchronized`), HotSpot cannot unmount the continuation if the thread blocks on `<I/O / sleep / condition wait>`.

In resource-constrained deployments (such as 1-CPU container quotas where `parallelism=1`), this monopolizes the carrier worker pool and starves unrelated virtual threads across the JVM.

### 2. Specification & Runtime Invariants
- **JEP 444 Invariant:** The ForkJoinPool scheduler does *not* expand carrier parallelism to compensate for monitor pinning or native boundaries.
- **LTS Boundary:** JEP 491 (ObjectMonitor unmounting in JDK 24) is strictly ineligible for upstream backporting to OpenJDK 21 LTS (`jdk21u-dev`). Applications running on Java 21 LTS permanently require non-pinning locks.
- **JFR Signature:** Emits `jdk.VirtualThreadPinned` events (recorded when threshold set to `0ms`):
  - Stack trace pinned at `<ClassName>.<MethodName>(<File>:<Line>)`

### 3. Minimal Standalone Reproduction
The following self-contained Java program reproduces the carrier starvation under single-carrier isolation (`-Djdk.virtualThreadScheduler.parallelism=1`):

```java
// Paste self-contained reproduction with self-invoking single-carrier isolation
```

### 4. Proposed Remediation
Refactor the internal monitor (`synchronized`) to `java.util.concurrent.locks.ReentrantLock`, wrapping the critical section in a standard `try-finally` block.

```

---

## 2. Upstream Pull Request Template

```markdown
### Title: Fix carrier thread pinning in `<ClassName>` under Virtual Threads (JDK 21 LTS)

### 1. Description of Change
Refactors `<ClassName>` from intrinsic monitor synchronization (`synchronized`) to `java.util.concurrent.locks.ReentrantLock`.

- Replaces `synchronized (this)` / `synchronized (monitor)` with `private final ReentrantLock lock = new ReentrantLock()`.
- Guarantees lock release via strict `try { ... } finally { lock.unlock(); }` scoping.
- (If applicable) Replaces `wait()` / `notifyAll()` with `Condition.await()` / `Condition.signalAll()`.

### 2. Surgical Diff Guidelines Followed
- [x] Zero API breaking changes: Public interfaces, method signatures, and exception types remain identical.
- [x] Scope minimalization: Only the synchronized critical section is modified; no unrelated refactoring.
- [x] Strict exception safety: `lock.unlock()` placed in `finally` block immediately following `lock.lock()`.
- [x] Thread interruptibility preserved: Behavior under `Thread.interrupt()` matches original semantics.

### 3. Verification & Test Evidence
- **Environment:** OpenJDK 21.0.12 LTS, `-Djdk.virtualThreadScheduler.parallelism=1`.
- **Existing Test Suite:** All existing regression tests pass: `mvn test` / `gradle test`.
- **JFR Pinning Verification:** JFR recording with `threshold=0ms` verifies 0 `jdk.VirtualThreadPinned` events during concurrent execution.
- **Carrier Starvation Test:** Verified that independent virtual threads continue to execute concurrently while the lock is held.

```

---

## 3. Surgical Diff Engineering Guidelines

When replacing intrinsic monitors with `ReentrantLock` in production libraries, adhere strictly to these patterns:

### Pattern A: Standard Mutual Exclusion
```java
// BEFORE (Hazardous on JDK 21 LTS):
public synchronized void updateState(Payload payload) {
    doBlockingIoOrWait();
    this.state = payload;
}

// AFTER (Safe on JDK 21 LTS):
private final ReentrantLock lock = new ReentrantLock();

public void updateState(Payload payload) {
    lock.lock();
    try {
        doBlockingIoOrWait();
        this.state = payload;
    } finally {
        lock.unlock();
    }
}
```

### Pattern B: Condition Wait / Signal Replacement
```java
// BEFORE:
synchronized (this) {
    while (!ready) {
        wait();
    }
    notifyAll();
}

// AFTER:
private final ReentrantLock lock = new ReentrantLock();
private final Condition readyCondition = lock.newCondition();

public void awaitReady() throws InterruptedException {
    lock.lock();
    try {
        while (!ready) {
            readyCondition.await();
        }
    } finally {
        lock.unlock();
    }
}

public void signalReady() {
    lock.lock();
    try {
        ready = true;
        readyCondition.signalAll();
    } finally {
        lock.unlock();
    }
}
```

### Pattern C: Avoiding Deadlock & Serialization Caveats
1. **Never hold multiple locks across callbacks:** Nested locks can cause circular wait deadlocks (`JDK-8305069`), especially when mixing synchronized methods and `ReentrantLock`.
2. **Clarify Serialization vs. Pinning:** Remind maintainers that `ReentrantLock` eliminates carrier thread pinning (allowing carriers to process other requests), but does not magically eliminate queuing on the critical section itself (governed by Amdahl's Law $X_{max} \le 1 / D_{critical}$).

---

## 4. Defending JDK 21 LTS Support Against "Wait for JDK 24 / JEP 491" Objections

Maintainers may occasionally respond: *"JDK 24 includes JEP 491 which fixes synchronized pinning in HotSpot; why should we refactor to ReentrantLock?"*

Use the following authoritative, fact-checked defense:

> **Why JDK 21 LTS Requires Library-Level Remediations:**
> 1. **LTS Commercial Lifecycles:** OpenJDK 21 is a Long-Term Support (LTS) release supported by major enterprise vendors (Oracle, Red Hat, Azul, Amazon Corretto, Eclipse Temurin) until **2029–2031**. In contrast, JDK 24 is a non-LTS short-term release whose public updates end 6 months after release (September 2025).
> 2. **OpenJDK Backport Rules Forbid JEP 491 in 21u:** Upstream OpenJDK `jdk21u-dev` governance strictly prohibits backporting invasive virtual machine changes that overhaul low-level assembly stubs for `ObjectMonitor` across all CPU architectures. Java 21 LTS will **never** receive JEP 491.
> 3. **Enterprise Spring Boot Adoption:** The vast majority of production microservices deploying Spring Boot 3.x run on Java 21 LTS and cannot upgrade to interim non-LTS JDK releases. Without library-level `ReentrantLock` adoption, these production environments face severe carrier starvation.
> 4. **Residual Pinning in JDK 24+:** Even with JEP 491, HotSpot continues to pin carriers inside native methods (`_thread_in_native`), class initializers (`<clinit>`), and FFM downcalls. Explicit lock management with `ReentrantLock` provides predictable unmounting guarantees.

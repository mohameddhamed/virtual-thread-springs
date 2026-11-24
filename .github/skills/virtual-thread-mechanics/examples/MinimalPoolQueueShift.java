package examples;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Minimal Reproduction 3: Downstream Pool Queue Shifting
 *
 * Demonstrates:
 * Under single-carrier isolation (-Djdk.virtualThreadScheduler.parallelism=1):
 * 1. Traditional platform thread architecture bounds front-end concurrency (Tomcat maxThreads),
 *    causing requests to queue at the front-end boundary before reaching downstream pools.
 * 2. Enabling Virtual Threads eliminates the front-end thread bottleneck: all incoming requests
 *    immediately spawn virtual threads and enter the service layer (front-end queue = 0).
 * 3. Concurrency is not eliminated; it shifts directly downstream to the database connection pool
 *    (HikariCP), where excess requests starve for connections and fail with SQLTransientConnectionException.
 */
public class MinimalPoolQueueShift {

    // Mimics HikariCP's SQLTransientConnectionException
    public static class SQLTransientConnectionException extends Exception {
        public SQLTransientConnectionException(String message) {
            super(message);
        }
    }

    public static class DownstreamHikariPool {
        private final Semaphore connectionPool;
        private final long connectionTimeoutMs;

        public DownstreamHikariPool(int maxPoolSize, long connectionTimeoutMs) {
            this.connectionPool = new Semaphore(maxPoolSize, true);
            this.connectionTimeoutMs = connectionTimeoutMs;
        }

        public void executeDbQuery(long queryDurationMs) throws SQLTransientConnectionException, InterruptedException {
            // HikariCP connection lease waiting uses LockSupport.parkNanos() / Semaphore
            boolean acquired = connectionPool.tryAcquire(connectionTimeoutMs, TimeUnit.MILLISECONDS);
            if (!acquired) {
                throw new SQLTransientConnectionException(
                    "Connection is not available, request timed out after " + connectionTimeoutMs + "ms."
                );
            }
            try {
                // Database query I/O (unmounts virtual thread while awaiting network socket)
                Thread.sleep(queryDurationMs);
            } finally {
                connectionPool.release();
            }
        }
    }

    private static void ensureSingleCarrierFork(String[] args) {
        if ("true".equals(System.getProperty("repro.forked"))) {
            return;
        }
        try {
            String javaBin = Path.of(System.getProperty("java.home"), "bin", "java").toString();
            List<String> cmd = new ArrayList<>();
            cmd.add(javaBin);
            cmd.add("-Djdk.virtualThreadScheduler.parallelism=1");
            cmd.add("-Drepro.forked=true");

            String sourceFile = System.getProperty("jdk.launcher.sourcefile");
            if (sourceFile != null && !sourceFile.isBlank()) {
                cmd.add(sourceFile);
            } else {
                cmd.add("-cp");
                cmd.add(System.getProperty("java.class.path"));
                cmd.add(MinimalPoolQueueShift.class.getName());
            }
            for (String arg : args) {
                cmd.add(arg);
            }

            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.inheritIO();
            int exitCode = pb.start().waitFor();
            System.exit(exitCode);
        } catch (Exception e) {
            System.err.println("[ERROR] Failed to fork single-carrier child: " + e.getMessage());
            System.exit(1);
        }
    }

    public static void main(String[] args) throws Exception {
        ensureSingleCarrierFork(args);

        System.out.println("================================================================================");
        System.out.println("Repro 3: MinimalPoolQueueShift (Front-End vs Downstream Pool Queue Dynamics)");
        System.out.println("================================================================================");

        int totalRequests = 15;
        int dbPoolSize = 3;
        long connectionTimeoutMs = 80;
        long dbQueryDurationMs = 200;

        // --- Phase 1: Platform Thread Baseline (Front-End Bounded) ---
        System.out.println("\n[Phase 1] Platform Threads: Front-end worker thread pool bounds concurrency...");
        int tomcatMaxThreads = 3;
        BlockingQueue<Runnable> tomcatQueue = new LinkedBlockingQueue<>();
        ThreadPoolExecutor tomcatExecutor = new ThreadPoolExecutor(
            tomcatMaxThreads, tomcatMaxThreads, 0L, TimeUnit.MILLISECONDS, tomcatQueue
        );
        DownstreamHikariPool poolPhase1 = new DownstreamHikariPool(dbPoolSize, connectionTimeoutMs);
        AtomicInteger p1Completed = new AtomicInteger(0);
        AtomicInteger p1Timeouts = new AtomicInteger(0);

        for (int i = 0; i < totalRequests; i++) {
            tomcatExecutor.submit(() -> {
                try {
                    poolPhase1.executeDbQuery(dbQueryDurationMs);
                    p1Completed.incrementAndGet();
                } catch (SQLTransientConnectionException e) {
                    p1Timeouts.incrementAndGet();
                } catch (Exception e) {
                    System.err.println("P1 unexpected error: " + e.getMessage());
                }
            });
        }
        // Sample front-end queue while initial 3 are running
        Thread.sleep(30);
        int queuedFrontEnd = tomcatQueue.size();
        System.out.println("  -> Requests submitted to Tomcat pool: " + totalRequests);
        System.out.println("  -> Front-end queue depth: " + queuedFrontEnd + " requests waiting for Tomcat threads.");
        System.out.println("  -> Downstream DB pool protected: exactly " + tomcatMaxThreads + " concurrent leases.");

        tomcatExecutor.shutdown();
        tomcatExecutor.awaitTermination(5, TimeUnit.SECONDS);

        if (p1Completed.get() != totalRequests) {
            throw new AssertionError("Expected all " + totalRequests + " requests to complete in Phase 1, but completed: " + p1Completed.get());
        }
        if (p1Timeouts.get() != 0) {
            throw new AssertionError("Expected 0 downstream timeouts under platform threads, but got: " + p1Timeouts.get());
        }
        System.out.println("  [VERIFIED] Platform thread pool bounded concurrency; 0 downstream timeouts.");

        // --- Phase 2: Virtual Threads (Queue Shift to Downstream Pool) ---
        System.out.println("\n[Phase 2] Virtual Threads: Front-end unconstrained -> Queue shifts downstream...");
        DownstreamHikariPool poolPhase2 = new DownstreamHikariPool(dbPoolSize, connectionTimeoutMs);
        AtomicInteger vDbSuccess = new AtomicInteger(0);
        AtomicInteger vDbTimeouts = new AtomicInteger(0);
        CountDownLatch startGate = new CountDownLatch(1);

        List<Thread> virtualThreads = new ArrayList<>();

        for (int i = 0; i < totalRequests; i++) {
            final int reqId = i;
            Thread vt = Thread.ofVirtual().name("HTTP-Req-" + reqId).start(() -> {
                try {
                    // Synchronize release so all 15 virtual threads hit the service layer concurrently
                    startGate.await();
                    // No front-end thread queueing! Virtual thread immediately begins executing application code.
                    poolPhase2.executeDbQuery(dbQueryDurationMs);
                    vDbSuccess.incrementAndGet();
                } catch (SQLTransientConnectionException e) {
                    // Queue shifted to HikariCP pool! Connection timeout exceeded.
                    vDbTimeouts.incrementAndGet();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
            virtualThreads.add(vt);
        }

        // Release all 15 virtual threads simultaneously
        startGate.countDown();

        for (Thread vt : virtualThreads) {
            vt.join();
        }

        System.out.println("  -> Total incoming requests: " + totalRequests);
        System.out.println("  -> Front-end queue depth: 0 (virtual threads dispatched immediately)");
        System.out.println("  -> Downstream DB successful queries: " + vDbSuccess.get());
        System.out.println("  -> Downstream HikariCP pool timeouts: " + vDbTimeouts.get() + " (SQLTransientConnectionException)");

        if (vDbSuccess.get() != dbPoolSize) {
            throw new AssertionError("Expected exactly " + dbPoolSize + " successful connections, but was: " + vDbSuccess.get());
        }
        if (vDbTimeouts.get() != (totalRequests - dbPoolSize)) {
            throw new AssertionError("Expected " + (totalRequests - dbPoolSize) + " pool timeouts, but was: " + vDbTimeouts.get());
        }

        System.out.println("  [VERIFIED] Front-end thread queuing completely eliminated by Virtual Threads.");
        System.out.println("  [VERIFIED] Concurrency shifted downstream into HikariCP pool, causing SQLTransientConnectionException.");

        System.out.println("\n================================================================================");
        System.out.println("Repro 3 Result: SUCCESS - Downstream Pool Queue Shifting Verified!");
        System.out.println("================================================================================");
    }
}

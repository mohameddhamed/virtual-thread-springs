package examples;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Minimal Reproduction 4: Deterministic AQS Tail Dispersion & Lock Barging
 *
 * Demonstrates:
 * Under single-carrier isolation (-Djdk.virtualThreadScheduler.parallelism=1):
 * 1. Using the deterministic `hasQueuedThread` gate protocol:
 *    - Virtual Thread V1 is enqueued into the AQS wait queue while the lock is held.
 *    - The orchestrator polls `while (!lock.hasQueuedThread(v1)) Thread.sleep(5);`,
 *      guaranteeing V1 is definitively parked in the AQS tail.
 * 2. In default NonfairSync (`new ReentrantLock(false)`):
 *    - When the holder releases the lock, arriving Virtual Thread V2 executes a direct CAS.
 *    - V2 barges ahead of the queued thread V1!
 *    - Deterministic acquisition order: [V2 acquired, V1 acquired].
 * 3. In FairSync (`new ReentrantLock(true)`):
 *    - V2 invokes `tryAcquire`, which queries `hasQueuedPredecessors()`.
 *    - Barging is prohibited; V2 enqueues behind V1.
 *    - Deterministic acquisition order: [V1 acquired, V2 acquired].
 */
public class MinimalAqsTailDispersion {

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
                cmd.add(MinimalAqsTailDispersion.class.getName());
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
        System.out.println("Repro 4: MinimalAqsTailDispersion (Deterministic AQS Direct-CAS Barging vs FIFO)");
        System.out.println("================================================================================");

        // --- Run NonfairSync Test ---
        System.out.println("\n[Test 1] Testing NonfairSync (new ReentrantLock(false))...");
        List<String> nonfairOrder = runAqsGateTrial(false);
        System.out.println("  -> NonfairSync acquisition order: " + nonfairOrder);
        if (!List.of("V2 acquired", "V1 acquired").equals(nonfairOrder)) {
            throw new AssertionError("Expected NonfairSync order [V2 acquired, V1 acquired], but got: " + nonfairOrder);
        }
        System.out.println("  [VERIFIED] Direct-CAS barging observed: V2 barged ahead of queued V1!");

        // --- Run FairSync Test ---
        System.out.println("\n[Test 2] Testing FairSync (new ReentrantLock(true))...");
        List<String> fairOrder = runAqsGateTrial(true);
        System.out.println("  -> FairSync acquisition order: " + fairOrder);
        if (!List.of("V1 acquired", "V2 acquired").equals(fairOrder)) {
            throw new AssertionError("Expected FairSync order [V1 acquired, V2 acquired], but got: " + fairOrder);
        }
        System.out.println("  [VERIFIED] Strict FIFO fairness preserved: V1 acquired before V2!");

        System.out.println("\n================================================================================");
        System.out.println("Repro 4 Result: SUCCESS - AQS Barging and Fairness Invariants Verified!");
        System.out.println("================================================================================");
    }

    private static List<String> runAqsGateTrial(boolean fair) throws Exception {
        ReentrantLock lock = new ReentrantLock(fair);
        List<String> acquisitionOrder = Collections.synchronizedList(new ArrayList<>());

        // Step 1: Main thread holds the lock
        lock.lock();

        // Step 2: Spawn V1, which attempts to acquire the lock and blocks
        Thread v1 = Thread.ofVirtual().name("V1-Queued").start(() -> {
            lock.lock();
            try {
                acquisitionOrder.add("V1 acquired");
            } finally {
                lock.unlock();
            }
        });

        // Step 3: Deterministic Gate Protocol: Wait until V1 is definitively queued in AQS
        while (!lock.hasQueuedThread(v1)) {
            Thread.sleep(5);
        }

        // Step 4: Spawn V2 to compete immediately when the lock is released
        CountDownLatch v2Done = new CountDownLatch(1);
        Thread v2 = Thread.ofVirtual().name("V2-Barger").start(() -> {
            // Spin until the lock is released by holder, preventing V2 from prematurely enqueuing into AQS
            while (lock.isLocked()) {
                Thread.onSpinWait();
            }
            lock.lock();
            try {
                acquisitionOrder.add("V2 acquired");
            } finally {
                lock.unlock();
            }
            v2Done.countDown();
        });

        // Step 5: Release lock, triggering direct-CAS competition in NonfairSync or FIFO in FairSync
        lock.unlock();

        v1.join();
        v2Done.await();

        return new ArrayList<>(acquisitionOrder);
    }
}

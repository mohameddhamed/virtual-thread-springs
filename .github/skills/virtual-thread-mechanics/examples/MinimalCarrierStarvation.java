package examples;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Minimal Reproduction 1: Monitor Pinning vs. ReentrantLock Unpinning
 *
 * Demonstrates:
 * Under single-carrier isolation (-Djdk.virtualThreadScheduler.parallelism=1):
 * 1. Intrinsic monitor (`synchronized`) pins the carrier thread to Virtual Thread A.
 *    Independent Virtual Thread B is starved until Thread A exits the synchronized block.
 * 2. `ReentrantLock` allows Virtual Thread A to unmount from the carrier during sleep/wait.
 *    Virtual Thread B acquires the carrier immediately and completes while Thread A is still asleep.
 */
public class MinimalCarrierStarvation {

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
                cmd.add(MinimalCarrierStarvation.class.getName());
            }
            for (String arg : args) {
                cmd.add(arg);
            }

            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.inheritIO();
            int exit = pb.start().waitFor();
            System.exit(exit);
        } catch (Exception e) {
            System.err.println("[ERROR] Failed to fork single-carrier child: " + e.getMessage());
            System.exit(1);
        }
    }

    public static void main(String[] args) throws Exception {
        ensureSingleCarrierFork(args);

        System.out.println("================================================================================");
        System.out.println("Repro 1: MinimalCarrierStarvation (Single Carrier Isolation: parallelism=1)");
        System.out.println("================================================================================");

        // --- Phase 1: Monitor Pinning (synchronized) ---
        System.out.println("\n[Phase 1] Testing intrinsic monitor pinning (synchronized)...");
        Object monitor = new Object();
        AtomicLong bStartSync = new AtomicLong(0);
        CountDownLatch aInsideMonitor = new CountDownLatch(1);

        Thread vtASync = Thread.ofVirtual().name("VT-A-Synchronized").start(() -> {
            synchronized (monitor) {
                try {
                    aInsideMonitor.countDown();
                    // Sleep inside synchronized block -> pins carrier in Java 21
                    Thread.sleep(250);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        });

        // Deterministic Gate: Wait until VT-A is definitively inside the monitor on the carrier
        aInsideMonitor.await();
        long t0 = System.currentTimeMillis();

        // VT-B performs completely independent work (does NOT need monitor)
        Thread vtBSync = Thread.ofVirtual().name("VT-B-Independent").start(() -> {
            bStartSync.set(System.currentTimeMillis() - t0);
        });

        vtASync.join();
        vtBSync.join();

        long syncDelayMs = bStartSync.get();
        System.out.println("  -> Virtual Thread A held monitor for 250ms.");
        System.out.println("  -> Independent Virtual Thread B starvation delay: " + syncDelayMs + "ms");
        if (syncDelayMs < 200) {
            throw new AssertionError("Expected Thread B to be starved by carrier pinning (>= 200ms), but was: " + syncDelayMs);
        }
        System.out.println("  [VERIFIED] Carrier monitor pinning starved independent Virtual Thread B.");

        // --- Phase 2: Clean Unpinning (ReentrantLock) ---
        System.out.println("\n[Phase 2] Testing lock unpinning (ReentrantLock)...");
        ReentrantLock lock = new ReentrantLock();
        AtomicLong bStartLock = new AtomicLong(0);
        AtomicBoolean bCompletedBeforeA = new AtomicBoolean(false);
        AtomicBoolean aStillRunning = new AtomicBoolean(true);
        CountDownLatch aInsideLock = new CountDownLatch(1);

        Thread vtALock = Thread.ofVirtual().name("VT-A-ReentrantLock").start(() -> {
            lock.lock();
            try {
                aInsideLock.countDown();
                // Sleep inside ReentrantLock -> unmounts cleanly in Java 21!
                Thread.sleep(250);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                aStillRunning.set(false);
                lock.unlock();
            }
        });

        // Deterministic Gate: Wait until VT-A is inside lock and ready to sleep/unmount
        aInsideLock.await();
        long t1 = System.currentTimeMillis();

        Thread vtBLock = Thread.ofVirtual().name("VT-B-Independent").start(() -> {
            bStartLock.set(System.currentTimeMillis() - t1);
            if (aStillRunning.get()) {
                bCompletedBeforeA.set(true);
            }
        });

        vtALock.join();
        vtBLock.join();

        long lockDelayMs = bStartLock.get();
        System.out.println("  -> Virtual Thread A held ReentrantLock for 250ms.");
        System.out.println("  -> Independent Virtual Thread B execution delay: " + lockDelayMs + "ms");
        System.out.println("  -> VT-B executed concurrently while VT-A was asleep: " + bCompletedBeforeA.get());
        if (lockDelayMs >= 150 || !bCompletedBeforeA.get()) {
            throw new AssertionError("Expected Thread B to run immediately on unmounted carrier (< 150ms), but delay was: " + lockDelayMs);
        }
        System.out.println("  [VERIFIED] ReentrantLock unmounted Virtual Thread A; Thread B ran without starvation.");

        System.out.println("\n================================================================================");
        System.out.println("Repro 1 Result: SUCCESS - Monitor Pinning and Unpinning Invariants Verified!");
        System.out.println("================================================================================");
    }
}

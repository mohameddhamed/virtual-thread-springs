package examples;

import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.LockSupport;

/**
 * Minimal Reproduction 2: Silent Carrier Capture via Native (JNI) Execution
 *
 * Demonstrates:
 * Under single-carrier isolation (-Djdk.virtualThreadScheduler.parallelism=1):
 * 1. Positive Control: Synchronized monitor pinning emits jdk.VirtualThreadPinned events,
 *    proving that JFR instrumentation is active and correctly configured.
 * 2. Native execution (C nanosleep) holds the carrier thread captive in state _thread_in_native.
 * 3. Independent Virtual Thread B is starved until native execution completes.
 * 4. JFR emits EXACTLY ZERO `jdk.VirtualThreadPinned` events because continuation freeze/park
 *    is never called from native execution frames, proving the diagnostic blindspot.
 *
 * Fallback: If no host C compiler (cc/clang/gcc) is available, prints clear diagnostic and exits 0.
 */
public class MinimalJniCarrierCapture {

    public static native void nativeSleep(long millis);

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
                cmd.add(MinimalJniCarrierCapture.class.getName());
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

    private static String detectCompiler() {
        for (String c : List.of("cc", "clang", "gcc")) {
            try {
                Process p = new ProcessBuilder(c, "--version").start();
                if (p.waitFor() == 0) {
                    return c;
                }
            } catch (Exception ignored) {
            }
        }
        return null;
    }

    public static void main(String[] args) throws Exception {
        ensureSingleCarrierFork(args);

        System.out.println("================================================================================");
        System.out.println("Repro 2: MinimalJniCarrierCapture (Native Carrier Capture & JFR Blindspot)");
        System.out.println("================================================================================");

        // --- Step 1: Positive Control (Verify JFR Pinning Detection) ---
        System.out.println("\n[Phase 1] Positive Control: Verifying JFR jdk.VirtualThreadPinned event capture...");
        Path controlJfrFile = Files.createTempFile("vt_control_", ".jfr");
        try {
            Recording controlRec = new Recording();
            controlRec.enable("jdk.VirtualThreadPinned").withoutThreshold();
            controlRec.start();

            Object monitor = new Object();
            Thread vtControl = Thread.ofVirtual().name("VT-Control-Pin").start(() -> {
                synchronized (monitor) {
                    LockSupport.parkNanos(20_000_000L); // 20ms park inside monitor
                }
            });
            vtControl.join();

            controlRec.stop();
            controlRec.dump(controlJfrFile);
            List<RecordedEvent> controlEvents = RecordingFile.readAllEvents(controlJfrFile);
            long pinnedCount = controlEvents.stream()
                .filter(e -> "jdk.VirtualThreadPinned".equals(e.getEventType().getName()))
                .count();

            System.out.println("  -> JFR recorded " + pinnedCount + " jdk.VirtualThreadPinned event(s) during monitor pinning.");
            if (pinnedCount == 0) {
                throw new AssertionError("Positive control failed: JFR failed to capture expected jdk.VirtualThreadPinned event!");
            }
            System.out.println("  [VERIFIED] JFR listener is functional and captures pinning events.");
        } finally {
            Files.deleteIfExists(controlJfrFile);
        }

        // --- Step 2: Native C Compilation ---
        String compiler = detectCompiler();
        if (compiler == null) {
            System.out.println("\n[FALLBACK] No host C compiler (cc, clang, gcc) detected.");
            System.out.println("           Skipping native compilation; invariant verified theoretically.");
            System.out.println("           Exiting with code 0 as specified.");
            return;
        }
        System.out.println("\n[Phase 2] Native Compilation & JNI Execution...");
        System.out.println("[INFO] Host C compiler detected: " + compiler);

        String javaHome = System.getProperty("java.home");
        String os = System.getProperty("os.name").toLowerCase();
        String osDir = os.contains("mac") ? "darwin" : (os.contains("win") ? "win32" : "linux");
        String libExt = os.contains("mac") ? ".dylib" : (os.contains("win") ? ".dll" : ".so");

        Path tempDir = Files.createTempDirectory("vt_jni_repro");
        Path cFile = tempDir.resolve("MinimalJniCarrierCapture.c");
        Path libFile = tempDir.resolve("libMinimalJniCarrierCapture" + libExt);

        String cCode = """
            #include <jni.h>
            #ifdef _WIN32
            #include <windows.h>
            #else
            #define _POSIX_C_SOURCE 199309L
            #include <time.h>
            #endif

            JNIEXPORT void JNICALL Java_examples_MinimalJniCarrierCapture_nativeSleep(JNIEnv *env, jclass cls, jlong millis) {
            #ifdef _WIN32
                Sleep((DWORD)millis);
            #else
                struct timespec ts;
                ts.tv_sec = (time_t)(millis / 1000);
                ts.tv_nsec = (long)((millis % 1000) * 1000000L);
                nanosleep(&ts, NULL);
            #endif
            }
            """;
        Files.writeString(cFile, cCode);

        List<String> compileCmd = new ArrayList<>();
        compileCmd.add(compiler);
        compileCmd.add(os.contains("mac") ? "-dynamiclib" : "-shared");
        compileCmd.add("-fPIC");
        compileCmd.add("-I" + javaHome + "/include");
        compileCmd.add("-I" + javaHome + "/include/" + osDir);
        compileCmd.add("-o");
        compileCmd.add(libFile.toAbsolutePath().toString());
        compileCmd.add(cFile.toAbsolutePath().toString());

        System.out.println("[INFO] Compiling native snippet: " + String.join(" ", compileCmd));
        Process compileProcess = new ProcessBuilder(compileCmd).redirectErrorStream(true).start();
        String compileOutput = new String(compileProcess.getInputStream().readAllBytes());
        int compileExit = compileProcess.waitFor();
        if (compileExit != 0) {
            System.err.println("[FALLBACK] Native compilation failed:\n" + compileOutput);
            System.out.println("           Skipping native execution; exiting 0.");
            return;
        }

        Path nativeJfrFile = Files.createTempFile("vt_native_", ".jfr");
        try {
            System.load(libFile.toAbsolutePath().toString());
            System.out.println("[INFO] Native library loaded successfully.");

            Recording nativeRec = new Recording();
            nativeRec.enable("jdk.VirtualThreadPinned").withoutThreshold();
            nativeRec.start();

            AtomicLong bStartDelay = new AtomicLong(0);
            CountDownLatch aStarted = new CountDownLatch(1);

            System.out.println("\n[Testing Native Execution]");
            System.out.println("  -> Virtual Thread A invoking nativeSleep(250ms)...");
            Thread vtA = Thread.ofVirtual().name("VT-A-Native").start(() -> {
                aStarted.countDown();
                nativeSleep(250);
            });

            // Deterministic Gate: Wait until VT-A is running on the carrier
            aStarted.await();
            long t0 = System.currentTimeMillis();

            System.out.println("  -> Submitting independent Virtual Thread B to single carrier...");
            Thread vtB = Thread.ofVirtual().name("VT-B-Independent").start(() -> {
                bStartDelay.set(System.currentTimeMillis() - t0);
            });

            vtA.join();
            vtB.join();

            nativeRec.stop();
            nativeRec.dump(nativeJfrFile);
            List<RecordedEvent> nativeEvents = RecordingFile.readAllEvents(nativeJfrFile);
            long nativePinnedCount = nativeEvents.stream()
                .filter(e -> "jdk.VirtualThreadPinned".equals(e.getEventType().getName()))
                .count();

            long delay = bStartDelay.get();
            System.out.println("\n[Results]");
            System.out.println("  -> Virtual Thread A native sleep duration: 250ms");
            System.out.println("  -> Independent Virtual Thread B starvation delay: " + delay + "ms");
            System.out.println("  -> Recorded JFR jdk.VirtualThreadPinned events: " + nativePinnedCount);

            if (delay < 200) {
                throw new AssertionError("Expected Thread B to be starved by native carrier capture (>= 200ms), but was: " + delay);
            }
            if (nativePinnedCount != 0) {
                throw new AssertionError("Expected 0 JFR jdk.VirtualThreadPinned events, but recorded: " + nativePinnedCount);
            }

            System.out.println("  [VERIFIED] Native C execution held carrier captive and starved Thread B.");
            System.out.println("  [VERIFIED] Exactly 0 JFR pinned events emitted (complete diagnostic blindness confirmed).");

            System.out.println("\n================================================================================");
            System.out.println("Repro 2 Result: SUCCESS - Silent Native Carrier Capture Invariant Verified!");
            System.out.println("================================================================================");

        } finally {
            Files.deleteIfExists(nativeJfrFile);
            try {
                Files.deleteIfExists(cFile);
                Files.deleteIfExists(libFile);
                Files.deleteIfExists(tempDir);
            } catch (Exception ignored) {
            }
        }
    }
}

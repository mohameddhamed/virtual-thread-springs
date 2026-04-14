package com.thesis.virtualthreadsdemo.service;

import org.springframework.stereotype.Service;

/**
 * ANTI-PATTERN #3: synchronized block wrapping a blocking call
 *
 * This is the PRIMARY thread-pinning culprit in this demo.
 *
 * What happens:
 *   - A Virtual Thread picks up a request and enters this synchronized method
 *   - Inside, it hits Thread.sleep() (simulating a slow external API call)
 *   - Because we are inside a synchronized block, the JVM CANNOT unmount the Virtual Thread
 *   - The Carrier Thread (the actual OS thread) is now fully blocked
 *   - No other Virtual Thread can run on that Carrier Thread until sleep() finishes
 *
 * This is exactly what JFR's jdk.VirtualThreadPinned event will report.
 *
 * Why synchronized causes pinning:
 *   Java's synchronized keyword uses an OS-level monitor lock that is tied to the
 *   Carrier Thread. The JVM cannot safely unmount a Virtual Thread that holds one.
 *
 * The fix (implemented in Milestone 7):
 *   Replace synchronized with java.util.concurrent.locks.ReentrantLock,
 *   which is Virtual Thread-aware and allows safe unmounting.
 */
@Service
public class PaymentService {

    // ANTI-PATTERN: synchronized method containing a blocking call
    // Simulates a legacy payment library that uses synchronized internally
    public synchronized String processPayment(String orderId) {
        try {
            // Simulates calling an external payment gateway (slow network call)
            // With synchronized: Carrier Thread is pinned for this entire 500ms
            // JFR will emit a jdk.VirtualThreadPinned event here
            Thread.sleep(500);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        return "Payment processed for order: " + orderId;
    }
}
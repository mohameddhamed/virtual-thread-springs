package com.thesis.virtualthreadsdemo.service;

import org.springframework.stereotype.Service;

import java.util.concurrent.locks.ReentrantLock;

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

    // The modern, Virtual-Thread-safe way to lock
    private final ReentrantLock lock = new ReentrantLock();

    public String processPayment(String orderId) {
        lock.lock();
        try {
            // Virtual Thread will now cleanly unmount here!
            // It will NOT pin the OS Carrier Thread.
            Thread.sleep(500);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            lock.unlock(); // Always unlock in a finally block
        }

        return "Payment processed for order: " + orderId;
    }
}
package com.thesis.virtualthreadsdemo.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;

import java.util.concurrent.Semaphore;
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

    private final String lockMode;
    private final ReentrantLock lock = new ReentrantLock();
    private final ReentrantLock fairLock = new ReentrantLock(true);
    private final Semaphore semaphore = new Semaphore(1);
    private final Semaphore fairSemaphore = new Semaphore(1, true);
    private final Object monitor = new Object();

    public PaymentService(@Value("${demo.payment.lock-mode:reentrant-lock}") String lockMode) {
        if (!lockMode.equals("synchronized")
                && !lockMode.equals("reentrant-lock")
                && !lockMode.equals("fair-reentrant-lock")
                && !lockMode.equals("semaphore")
                && !lockMode.equals("fair-semaphore")
                && !lockMode.equals("none")) {
            throw new IllegalArgumentException(
                    "demo.payment.lock-mode must be synchronized, reentrant-lock, fair-reentrant-lock, "
                            + "semaphore, fair-semaphore, or none");
        }
        this.lockMode = lockMode;
    }

    public String processPayment(String orderId) {
        switch (lockMode) {
            case "synchronized" -> {
                synchronized (monitor) {
                    simulatePaymentCall();
                }
            }
            case "reentrant-lock" -> {
                lock.lock();
                try {
                    simulatePaymentCall();
                } finally {
                    lock.unlock();
                }
            }
            case "fair-reentrant-lock" -> {
                fairLock.lock();
                try {
                    simulatePaymentCall();
                } finally {
                    fairLock.unlock();
                }
            }
            case "semaphore" -> {
                semaphore.acquireUninterruptibly();
                try {
                    simulatePaymentCall();
                } finally {
                    semaphore.release();
                }
            }
            case "fair-semaphore" -> {
                fairSemaphore.acquireUninterruptibly();
                try {
                    simulatePaymentCall();
                } finally {
                    fairSemaphore.release();
                }
            }
            case "none" -> simulatePaymentCall();
        }

        return "Payment processed for order: " + orderId;
    }

    private void simulatePaymentCall() {
        try {
            Thread.sleep(500);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
package com.thesis.virtualthreadsdemo.service;

import org.springframework.stereotype.Service;

/**
 * CPU-bound control: no sleep, JDBC, locks, or ThreadLocal state.
 * It provides a negative control for the claim that Virtual Threads improve
 * blocking workloads; CPU work remains limited by processor parallelism.
 */
@Service
public class CpuService {

    private static final int ITERATIONS = 5_000_000;

    public String compute() {
        double value = 0.0;
        for (int i = 1; i <= ITERATIONS; i++) {
            value = Math.fma(value, 1.0000001, Math.sqrt(i));
        }
        return "CPU checksum: " + Double.toHexString(value);
    }
}

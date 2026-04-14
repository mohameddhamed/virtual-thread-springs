package com.thesis.virtualthreadsdemo.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * ANTI-PATTERN #1: ThreadLocal misuse
 *
 * Spring's RequestContextHolder and SecurityContextHolder both use ThreadLocal internally.
 * Here we simulate that pattern manually to demonstrate the memory implications
 * when millions of Virtual Threads each carry their own ThreadLocal state.
 *
 * ANTI-PATTERN #2: Blocking JDBC with simulated slow query
 *
 * The Thread.sleep() simulates a real slow DB query (e.g. missing index, large table scan).
 * Under platform threads: 200 threads blocked = pool exhausted.
 * Under virtual threads (naive): threads unmount correctly — UNLESS pinning occurs.
 * Under virtual threads + synchronized: pinning occurs, Carrier Thread is blocked.
 */
@Service
public class OrderService {

    // ANTI-PATTERN: ThreadLocal holding per-request context
    // With a 200-thread pool this is fine. With millions of VTs, this can cause memory bloat.
    private static final ThreadLocal<String> REQUEST_CONTEXT = new ThreadLocal<>();

    private final JdbcTemplate jdbcTemplate;

    public OrderService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<Map<String, Object>> getOrders() {
        // Simulate setting request context (like Spring Security would do)
        REQUEST_CONTEXT.set("user-request-" + Thread.currentThread().getName());

        try {
            // Simulate a slow database query (e.g. unindexed table scan)
            simulateSlowQuery();
            return jdbcTemplate.queryForList("SELECT * FROM orders");
        } finally {
            // Always clean up ThreadLocal to avoid memory leaks
            // (in real apps this is often forgotten — that's the bug)
            REQUEST_CONTEXT.remove();
        }
    }

    private void simulateSlowQuery() {
        try {
            // Simulates a 300ms DB round-trip
            // Under Virtual Threads, the VT should unmount here — unless pinned
            Thread.sleep(300);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
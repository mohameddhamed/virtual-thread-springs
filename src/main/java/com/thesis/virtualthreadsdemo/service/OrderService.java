package com.thesis.virtualthreadsdemo.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.util.ArrayList;
import java.util.LinkedHashMap;
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
    private final boolean holdConnectionDuringDelay;

    public OrderService(
            JdbcTemplate jdbcTemplate,
            @Value("${demo.orders.hold-connection-during-delay:false}") boolean holdConnectionDuringDelay) {
        this.jdbcTemplate = jdbcTemplate;
        this.holdConnectionDuringDelay = holdConnectionDuringDelay;
    }

    public List<Map<String, Object>> getOrders() {
        // Simulate setting request context (like Spring Security would do)
        REQUEST_CONTEXT.set("user-request-" + Thread.currentThread().getName());

        try {
            if (holdConnectionDuringDelay) {
                return queryWhileHoldingConnection();
            }

            // Control treatment: the delay occurs before JDBC connection checkout.
            simulateSlowQuery();
            return jdbcTemplate.queryForList("SELECT * FROM orders");
        } finally {
            // Always clean up ThreadLocal to avoid memory leaks
            // (in real apps this is often forgotten — that's the bug)
            REQUEST_CONTEXT.remove();
        }
    }

    private List<Map<String, Object>> queryWhileHoldingConnection() {
        return jdbcTemplate.execute((org.springframework.jdbc.core.ConnectionCallback<List<Map<String, Object>>>) connection -> {
            // Treatment: acquire the connection before introducing the delay.
            simulateSlowQuery();
            try (PreparedStatement statement = connection.prepareStatement("SELECT * FROM orders");
                 ResultSet resultSet = statement.executeQuery()) {
                ResultSetMetaData metadata = resultSet.getMetaData();
                int columnCount = metadata.getColumnCount();
                List<Map<String, Object>> rows = new ArrayList<>();
                while (resultSet.next()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    for (int column = 1; column <= columnCount; column++) {
                        row.put(metadata.getColumnLabel(column), resultSet.getObject(column));
                    }
                    rows.add(row);
                }
                return rows;
            }
        });
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
package com.thesis.virtualthreadsdemo.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * CONTROL GROUP — no anti-patterns present.
 *
 * This service is intentionally clean:
 *   - No synchronized blocks
 *   - No ThreadLocal usage
 *   - Fast query, no artificial delay
 *
 * Purpose: establishes a performance baseline.
 * Any difference in throughput between this endpoint and the others
 * is directly attributable to the anti-patterns in OrderService and PaymentService.
 */
@Service
public class ProductService {

    private final JdbcTemplate jdbcTemplate;

    public ProductService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<Map<String, Object>> getProducts() {
        return jdbcTemplate.queryForList("SELECT * FROM products");
    }
}
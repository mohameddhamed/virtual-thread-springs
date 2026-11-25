package com.thesis.virtualthreadsdemo;

import com.thesis.virtualthreadsdemo.service.PaymentService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ApplicationBehaviorTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private PaymentService paymentService;

    @Autowired
    private org.springframework.jdbc.core.JdbcTemplate jdbcTemplate;

    @Test
    void smokeEndpointsReturnExpectedResponses() throws Exception {
        mockMvc.perform(get("/orders"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith("application/json"));

        mockMvc.perform(post("/payments").param("orderId", "smoke-order"))
                .andExpect(status().isOk())
                .andExpect(content().string("Payment processed for order: smoke-order"));

        mockMvc.perform(get("/products"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith("application/json"));

        mockMvc.perform(get("/cpu"))
                .andExpect(status().isOk())
                .andExpect(content().string(org.hamcrest.Matchers.startsWith("CPU checksum:")));
    }

    @Test
    void nativeEndpointIsDisabledByDefault() throws Exception {
        mockMvc.perform(get("/native"))
                .andExpect(status().isNotFound());
    }

    @Test
    void ordersReturnsSeededRowsWhenHoldingConnectionDuringDelay() {
        com.thesis.virtualthreadsdemo.service.OrderService service =
                new com.thesis.virtualthreadsdemo.service.OrderService(jdbcTemplate, true);
        List<java.util.Map<String, Object>> orders = service.getOrders();
        assertThat(orders).hasSize(5);
    }

    @Test
    void concurrentPaymentsPreserveEachOrderIdAndSerializeCriticalSection() throws Exception {
        int requestCount = 4;
        CountDownLatch ready = new CountDownLatch(requestCount);
        CountDownLatch start = new CountDownLatch(1);
        AtomicInteger completed = new AtomicInteger();

        try (var executor = Executors.newFixedThreadPool(requestCount)) {
            List<? extends java.util.concurrent.Future<String>> results = java.util.stream.IntStream.range(0, requestCount)
                    .mapToObj(index -> executor.submit(() -> {
                        ready.countDown();
                        assertThat(start.await(5, TimeUnit.SECONDS)).isTrue();
                        String orderId = "concurrent-order-" + index;
                        String response = paymentService.processPayment(orderId);
                        completed.incrementAndGet();
                        return response;
                    }))
                    .toList();

            assertThat(ready.await(5, TimeUnit.SECONDS)).isTrue();
            long startNanos = System.nanoTime();
            start.countDown();
            List<String> responses = results.stream().map(this::getResult).toList();
            long elapsedMillis = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - startNanos);

            assertThat(completed).hasValue(requestCount);
            assertThat(responses).containsExactlyInAnyOrder(
                    "Payment processed for order: concurrent-order-0",
                    "Payment processed for order: concurrent-order-1",
                    "Payment processed for order: concurrent-order-2",
                    "Payment processed for order: concurrent-order-3");
            assertThat(elapsedMillis).isGreaterThanOrEqualTo((requestCount * 500L) - 250L);
        }
    }

    @Test
    void allPaymentLockModesEnforceExpectedConcurrencyContract() throws Exception {
        List<String> serializedModes = List.of(
                "synchronized",
                "reentrant-lock",
                "fair-reentrant-lock",
                "semaphore",
                "fair-semaphore");

        for (String mode : serializedModes) {
            long elapsedMillis = runConcurrentPayments(new PaymentService(mode), mode, 2);
            assertThat(elapsedMillis)
                    .as("Serialized lock mode %s should enforce mutual exclusion across 2x500ms calls", mode)
                    .isGreaterThanOrEqualTo(850L);
        }

        long diagnosticElapsedMillis = runConcurrentPayments(new PaymentService("none"), "none", 2);
        assertThat(diagnosticElapsedMillis)
                .as("Diagnostic no-lock mode should execute concurrently without mutual exclusion")
                .isLessThan(850L);
    }

    private long runConcurrentPayments(PaymentService service, String mode, int requestCount) throws Exception {
        CountDownLatch ready = new CountDownLatch(requestCount);
        CountDownLatch start = new CountDownLatch(1);
        try (var executor = Executors.newFixedThreadPool(requestCount)) {
            List<? extends java.util.concurrent.Future<String>> futures = java.util.stream.IntStream.range(0, requestCount)
                    .mapToObj(index -> executor.submit(() -> {
                        ready.countDown();
                        assertThat(start.await(5, TimeUnit.SECONDS)).isTrue();
                        return service.processPayment(mode + "-" + index);
                    }))
                    .toList();

            assertThat(ready.await(5, TimeUnit.SECONDS)).isTrue();
            long startNanos = System.nanoTime();
            start.countDown();
            List<String> responses = futures.stream().map(this::getResult).toList();
            long elapsedMillis = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - startNanos);

            List<String> expected = java.util.stream.IntStream.range(0, requestCount)
                    .mapToObj(index -> "Payment processed for order: " + mode + "-" + index)
                    .toList();
            assertThat(responses).containsExactlyInAnyOrderElementsOf(expected);
            return elapsedMillis;
        }
    }

    private String getResult(java.util.concurrent.Future<String> result) {
        try {
            return result.get(10, TimeUnit.SECONDS);
        } catch (Exception exception) {
            throw new AssertionError("Concurrent payment task failed", exception);
        }
    }
}

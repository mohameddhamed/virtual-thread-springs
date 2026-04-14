import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// ─── Custom Metrics ───────────────────────────────────────────────────────────
const errorRate = new Rate('error_rate');
const ordersDuration = new Trend('orders_duration', true);
const paymentsDuration = new Trend('payments_duration', true);
const productsDuration = new Trend('products_duration', true);

// ─── Test Configuration ───────────────────────────────────────────────────────
// Runs 3 stages: ramp up → hold → ramp down
// Change TARGET_VUS to switch between 50 / 100 / 200 concurrent users
const TARGET_VUS = __ENV.VUS ? parseInt(__ENV.VUS) : 50;

export const options = {
    stages: [
        { duration: '15s', target: TARGET_VUS },  // Ramp up
        { duration: '30s', target: TARGET_VUS },  // Hold — this is where we measure
        { duration: '10s', target: 0 },           // Ramp down
    ],
    thresholds: {
        // These are not pass/fail gates — just reference lines for the thesis results
        http_req_failed: ['rate<0.05'],           // Less than 5% errors
        http_req_duration: ['p(95)<5000'],        // p95 under 5s (generous — we expect slowness)
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

// ─── Virtual User Script ──────────────────────────────────────────────────────
export default function () {
    // 1. GET /orders — slow JDBC + ThreadLocal anti-pattern
    const ordersRes = http.get(`${BASE_URL}/orders`);
    check(ordersRes, { 'orders 200': (r) => r.status === 200 });
    errorRate.add(ordersRes.status !== 200);
    ordersDuration.add(ordersRes.timings.duration);

    // 2. POST /payments — synchronized block (thread pinning)
    const paymentsRes = http.post(`${BASE_URL}/payments?orderId=order-${__VU}-${__ITER}`);
    check(paymentsRes, { 'payments 200': (r) => r.status === 200 });
    errorRate.add(paymentsRes.status !== 200);
    paymentsDuration.add(paymentsRes.timings.duration);

    // 3. GET /products — clean control group
    const productsRes = http.get(`${BASE_URL}/products`);
    check(productsRes, { 'products 200': (r) => r.status === 200 });
    errorRate.add(productsRes.status !== 200);
    productsDuration.add(productsRes.timings.duration);

    sleep(0.1); // Small pause between iterations per VU
}

// ─── Summary ──────────────────────────────────────────────────────────────────
export function handleSummary(data) {
    const vus = TARGET_VUS;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `results/run-${vus}vus-${timestamp}.json`;

    return {
        [filename]: JSON.stringify(data, null, 2),
        stdout: textSummary(data, { indent: ' ', enableColors: false }),
    };
}

function textSummary(data, opts) {
    // k6 built-in summary — prints to stdout after the run
    return JSON.stringify(data.metrics, null, 2);
}
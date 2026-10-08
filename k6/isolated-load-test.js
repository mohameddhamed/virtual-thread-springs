import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const TARGET_VUS = __ENV.VUS ? parseInt(__ENV.VUS) : 50;
const ENDPOINT = __ENV.ENDPOINT || 'products';
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const METRIC_ENDPOINT = ENDPOINT.replace(/[^A-Za-z0-9_]/g, '_');
const endpointDuration = new Trend(`${METRIC_ENDPOINT}_duration`, true);
const errorRate = new Rate('error_rate');

export const options = {
    stages: [
        { duration: '15s', target: TARGET_VUS },
        { duration: '30s', target: TARGET_VUS },
        { duration: '10s', target: 0 },
    ],
    thresholds: {
        http_req_failed: ['rate<0.05'],
    },
};

function request() {
    switch (ENDPOINT) {
        case 'orders':
            return http.get(`${BASE_URL}/orders`);
        case 'payments':
            return http.post(`${BASE_URL}/payments?orderId=isolated-${__VU}-${__ITER}`);
        case 'products':
            return http.get(`${BASE_URL}/products`);
        case 'cpu':
            return http.get(`${BASE_URL}/cpu`);
        case 'native':
            return http.get(`${BASE_URL}/native`);
        case 'native-short':
            return http.get(`${BASE_URL}/native-short`);
        default:
            throw new Error(`Unsupported ENDPOINT: ${ENDPOINT}`);
    }
}

export default function () {
    const response = request();
    check(response, { [`${ENDPOINT} 200`]: (r) => r.status === 200 });
    errorRate.add(response.status !== 200);
    endpointDuration.add(response.timings.duration);
    sleep(0.1);
}

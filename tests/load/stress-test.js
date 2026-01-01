// K6 Load Test - Performance testing for Mozart
// Run with: k6 run tests/load/stress-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTrend = new Trend('response_time');

// Test configuration
export const options = {
    // Test stages
    stages: [
        { duration: '30s', target: 5 },   // Ramp up to 5 users
        { duration: '1m', target: 10 },   // Hold at 10 users
        { duration: '30s', target: 0 },   // Ramp down
    ],

    // Pass/fail thresholds
    thresholds: {
        http_req_duration: ['p(95)<5000'],  // 95% of requests under 5s
        http_req_failed: ['rate<0.05'],      // Less than 5% errors
        errors: ['rate<0.05'],               // Custom error rate
    },
};

// Test URLs - override with K6_RAG_URL environment variable
const RAG_URL = __ENV.RAG_URL || 'https://mozart-rag-203658178245.asia-southeast1.run.app';

export default function () {
    // Test 1: Health check
    const healthRes = http.get(`${RAG_URL}/`);
    check(healthRes, {
        'health status 200': (r) => r.status === 200,
        'health has status': (r) => r.json().status === 'alive',
    });
    errorRate.add(healthRes.status !== 200);

    sleep(1);

    // Test 2: Simple API request
    const askRes = http.post(
        `${RAG_URL}/api/v1/ask`,
        JSON.stringify({
            query: 'มาตรฐาน วสท คืออะไร',
            language: 'th',
        }),
        {
            headers: { 'Content-Type': 'application/json' },
            timeout: '60s',
        }
    );

    check(askRes, {
        'ask status 200': (r) => r.status === 200,
        'ask has answer': (r) => {
            try {
                return r.json().answer !== undefined;
            } catch {
                return false;
            }
        },
    });

    errorRate.add(askRes.status !== 200);
    responseTrend.add(askRes.timings.duration);

    sleep(2);
}

// Lifecycle hooks
export function handleSummary(data) {
    return {
        'stdout': textSummary(data, { indent: '  ', enableColors: true }),
    };
}

function textSummary(data, options) {
    const { metrics } = data;

    let summary = '\n📊 K6 Load Test Summary\n';
    summary += '═'.repeat(50) + '\n';

    if (metrics.http_req_duration) {
        const p95 = metrics.http_req_duration.values['p(95)'];
        summary += `Response Time (p95): ${p95.toFixed(0)}ms\n`;
    }

    if (metrics.http_req_failed) {
        const failRate = metrics.http_req_failed.values.rate * 100;
        summary += `Error Rate: ${failRate.toFixed(2)}%\n`;
    }

    if (metrics.iterations) {
        summary += `Total Requests: ${metrics.iterations.values.count}\n`;
    }

    summary += '═'.repeat(50) + '\n';

    return summary;
}

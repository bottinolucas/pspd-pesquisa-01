import http from 'k6/http';
import { check, sleep } from 'k6';

const GATEWAY_URL = __ENV.GATEWAY_URL || 'http://localhost:8080';

export const options = {
    scenarios: {
        grpc_path: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '5s', target: 50 }, // Ramp-up
                { duration: '20s', target: 50 }, // Sustain
                { duration: '5s', target: 0 },  // Ramp-down
            ],
            exec: 'testGrpcPath',
            tags: { protocol: 'grpc' },
        },
        rest_path: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '5s', target: 50 }, // Ramp-up
                { duration: '20s', target: 50 }, // Sustain
                { duration: '5s', target: 0 },  // Ramp-down
            ],
            exec: 'testRestPath',
            startTime: '35s', // Começa depois do cenário gRPC (5+20+5 + margem)
            tags: { protocol: 'rest' },
        },
    },
    thresholds: {
        'http_req_duration{protocol:grpc}': ['p(95)<500'],
        'http_req_duration{protocol:rest}': ['p(95)<500'],
    },
};

export function testGrpcPath() {
    const res = http.get(`${GATEWAY_URL}/api/v1/livros`);
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
    sleep(1);
}

export function testRestPath() {
    const res = http.get(`${GATEWAY_URL}/api/v2/livros`);
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
    sleep(1);
}

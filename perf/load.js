import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  vus: 20,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<=500'],
    http_req_failed: ['rate<=0.02'],
    checks: ['rate>=0.98'],
  },
};

export default function () {
  const payload = JSON.stringify({ account_id: 'ACC-001', amount: 25.5 });
  const params = { headers: { 'Content-Type': 'application/json' } };

  const create = http.post(`${BASE_URL}/payments`, payload, params);
  check(create, { 'create: status 201': (r) => r.status === 201 });

  if (create.status === 201) {
    const id = create.json('id');
    const get = http.get(`${BASE_URL}/payments/${id}`);
    check(get, { 'get: status 200': (r) => r.status === 200 });
  }

  sleep(0.1);
}

export function handleSummary(data) {
  const p95 = data.metrics.http_req_duration?.values?.['p(95)'] ?? 0;
  const httpErrors = (data.metrics.http_req_failed?.values?.rate ?? 1) * 100;
  const checkErrors = (1 - (data.metrics.checks?.values?.rate ?? 0)) * 100;
  return {
    'k6-summary.json': JSON.stringify(data),
    stdout: `\np95 = ${p95.toFixed(1)} ms | erreurs HTTP = ${httpErrors.toFixed(2)} % | checks en erreur = ${checkErrors.toFixed(2)} %\n`,
  };
}

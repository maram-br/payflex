import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  vus: 20,
  duration: '30s',
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
  return {
    'k6-summary.json': JSON.stringify(data),
    stdout: `\np95 = ${data.metrics.http_req_duration.values['p(95)'].toFixed(1)} ms | erreurs = ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)} %\n`,
  };
}
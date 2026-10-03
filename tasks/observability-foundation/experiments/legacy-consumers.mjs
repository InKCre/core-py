import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';

const webRoot = resolve(process.argv[2]);
const { build } = createRequire(resolve(webRoot, 'package.json'))(
  resolve(webRoot, 'node_modules/.pnpm/esbuild@0.28.1/node_modules/esbuild/lib/main.js')
);
const bundle = await build({
  entryPoints: [resolve(webRoot, 'packages/core/src/job/job.ts')],
  bundle: true, write: false, platform: 'node', format: 'esm',
  plugins: [{
    name: 'no-database-io',
    setup(build) {
      build.onResolve({filter: /\/base\/db-api$/}, () => ({path: 'db-api', namespace: 'probe'}));
      build.onLoad({filter: /.*/, namespace: 'probe'}, () => ({contents: 'export class DBAPIClient {}'}));
    },
  }],
});
// Bundle the actual old schema. Only its I/O dependency is replaced; no live database is used.
const { Job } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString('base64')}`);
const base = {id: 42, type: 'synthetic', parameters: {}, state: {}, timeout_seconds: 30, status: 'pending', created_at: '2026-10-01T00:00:00Z', started_at: null, closed_at: null};
for (const carrier of [{}, {submission_traceparent: null, submission_tracestate: null}, {submission_traceparent: '00-' + '1'.repeat(32) + '-' + '2'.repeat(16) + '-01', submission_tracestate: 'inkcre=synthetic'}]) {
  const job = Job.parse({...base, ...carrier});
  assert.equal(job.id, 42);
  assert.equal(job.status, 'pending');
  assert.equal(job.submission_traceparent, undefined);
}
console.log(JSON.stringify({actual_legacy_ts_schema: 'accepted missing, NULL and additional carrier fields; unknown fields stripped', database_updates: 'not exercised'}, null, 2));

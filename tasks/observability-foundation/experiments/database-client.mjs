// Exercise the actual old JobManager, Job schema and DBAPIClient against disposable PostgREST.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(here, '../../../../client-web');
const { build } = createRequire(resolve(webRoot, 'package.json'))(
  resolve(webRoot, 'node_modules/.pnpm/esbuild@0.28.1/node_modules/esbuild/lib/main.js')
);
globalThis.__o11yLab = JSON.parse(await readFile(resolve(here, 'runtime/database-client.json'), 'utf8'));
const bundle = await build({
  stdin: {contents: "export { Job } from './src/job/job'; export { JobManager } from './src/job/manager'; export { z } from 'zod';", resolveDir: resolve(webRoot, 'packages/core')},
  bundle: true, write: false, platform: 'node', format: 'esm',
  plugins: [{name: 'local-runtime-config', setup(build) {
    build.onResolve({filter: /^\.\.\/(config|auth)$/}, (args) => {
      if (args.importer.endsWith('/base/db-api.ts')) return {path: args.path, namespace: 'lab'};
    });
    build.onLoad({filter: /.*/, namespace: 'lab'}, (args) => ({contents: args.path.endsWith('/config')
      ? 'export const configStore = {metaConfig: {INKCRE_PGREST_URL: globalThis.__o11yLab.baseUrl}};'
      : 'export const authStore = {getToken: async () => globalThis.__o11yLab.token};'}));
  }}],
});
const { Job, JobManager, z } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString('base64')}`);
JobManager.registerHandler('o11y-lab', {
  parameters: z.object({}), canHandle: () => true,
  handle: async (job) => {job.state = {synthetic: 'typescript-finished'};},
});
const old = await JobManager.create('o11y-lab', {}, 30);
const oldRaw = (await Job.dbApi.from().select().eq('id', old.id).single()).data;
assert.equal(oldRaw.submission_traceparent, null);
assert.equal(oldRaw.submission_tracestate, null);
const existing = await Job.get(globalThis.__o11yLab.jobId);
assert.equal(existing.submission_traceparent, undefined);
assert.equal(await JobManager.run(existing.id), true);
const raw = (await Job.dbApi.from().select().eq('id', existing.id).single()).data;
assert.equal(raw.status, 'finished');
assert.deepEqual(raw.state, {synthetic: 'typescript-finished'});
for (const [key, value] of Object.entries(globalThis.__o11yLab.carrier)) assert.equal(raw[key], value);
const report = {legacy_ts_insert_defaults_null: true, legacy_ts_read_ignores_carrier: true, legacy_ts_claim_close_preserve_carrier: true, transport: 'actual DBAPIClient and PostgREST', runtime: 'Node; config/auth sources replaced with dedicated lab values; browser not tested'};
await writeFile(resolve(here, 'runtime/database-client-result.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));

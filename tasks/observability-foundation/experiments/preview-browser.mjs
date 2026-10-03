import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
const client = fileURLToPath(new URL('../../../../client-web', import.meta.url))
const require = createRequire(`${client}/package.json`)
const { chromium } = require('@playwright/test')
const { createServer } = await import(
  `${client}/apps/client-web/node_modules/vite/dist/node/index.js`
)
const jwt = execFileSync(
  'security',
  ['find-generic-password', '-s', 'inkcre/core-py/JWT_SECRET', '-w'],
  { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }
).trim()
const pg = 'https://inkcre-postgrest-pr-124-c8a3abf570a2.herokuapp.com/'
const core = 'https://inkcre-core-py-pr-124-17b00650cc5c.herokuapp.com'
const relay = core + '/telemetry'
const enabled = !process.argv.includes('--off')
const configFault = process.argv.includes('--config-fault')
const label = process.env.INKCRE_PREVIEW_LABEL || (enabled ? 'on' : 'off')
const vite = await createServer({
  configFile: false,
  root: `${client}/packages/core`,
  server: { host: '127.0.0.1', port: 0, fs: { allow: [client] } },
  optimizeDeps: {
    entries: [],
    include: [
      'vue',
      'pinia',
      'zod',
      'zod-class',
      'zod-config',
      'jose',
      '@supabase/postgrest-js',
      '@opentelemetry/api',
      '@opentelemetry/core',
      '@opentelemetry/resources',
      '@opentelemetry/sdk-trace-web',
      '@opentelemetry/exporter-trace-otlp-proto',
      '@opentelemetry/sdk-logs',
      '@opentelemetry/exporter-logs-otlp-proto',
      '@opentelemetry/sdk-metrics',
      '@opentelemetry/exporter-metrics-otlp-proto',
    ],
  },
})
vite.middlewares.use('/probe', (_req, res) => {
  res.setHeader('Content-Type', 'text/html')
  res.end('<html><body>InKCre preview acceptance</body></html>')
})
await vite.listen()
const browser = await chromium.launch({ headless: true })
const report = {
  startedAt: new Date().toISOString(),
  enabled,
  browser: await browser.version(),
  core,
  pg,
  relay,
  exports: [],
  errors: [],
  clientSource: execFileSync('git', ['-C', client, 'rev-parse', 'HEAD'], {
    encoding: 'utf8',
  }).trim(),
}
try {
  const page = await browser.newPage()
  if (configFault) await page.route('**/configs?**', () => {})
  page.on('console', (message) => {
    if (message.text().startsWith('[Telemetry]')) report.errors.push(message.text())
  })
  page.on('requestfinished', (request) => {
    if (request.url().includes('/configs?'))
      console.log(JSON.stringify({ configReadMs: request.timing().responseEnd, path: '/configs' }))
  })
  page.on('requestfailed', (request) => {
    if (request.url().includes('/configs?'))
      console.log(
        JSON.stringify({
          configReadFailure: request.failure()?.errorText,
          duration: request.timing().responseEnd,
        })
      )
  })
  page.on('response', (response) => {
    if (response.url().includes('/configs?'))
      console.log(JSON.stringify({ configReadStatus: response.status() }))
    if (response.url().startsWith(relay + '/v1/'))
      report.exports.push({ signal: response.url().split('/').at(-1), status: response.status() })
  })
  page.on('requestfailed', (request) => {
    if (request.url().startsWith(relay + '/v1/'))
      report.exports.push({
        signal: request.url().split('/').at(-1),
        failure: request.failure()?.errorText,
      })
  })
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/probe`)
  report.business = await page.evaluate(
    async ({ pg, jwt, relay, core, enabled, configFault }) => {
      const t = await import('/src/obsrv/telemetry.ts')
      const { configStore } = await import('/src/config/store.ts')
      const { MetaConfigSchema } = await import('/src/config/schema.ts')
      const { Job } = await import('/src/job/job.ts')
      const { JobManager } = await import('/src/job/manager.ts')
      const { signDatabaseToken } = await import('/src/auth/index.ts')
      configStore.metaConfig = MetaConfigSchema.parse({
        INKCRE_PGREST_URL: pg,
        INKCRE_JWT_SECRET: jwt,
        INKCRE_PEER_ID: '00000000-0000-4000-8000-000000000097',
        telemetry_enabled: enabled,
        telemetry_peer_relay_url: relay,
      })
      const initializationStarted = performance.now()
      await t.initializeTelemetry(configStore.metaConfig, 'preview-acceptance')
      const initializationMs = performance.now() - initializationStarted
      const job = await JobManager.create(
        'core.feature_retrieval.lexical.maintain.v1',
        { options: { max_records: 1, scan_page_size: 1, diagnostic_limit: 0 } },
        60
      )
      let saved = job
      for (let n = 0; n < 24 && ['pending', 'running'].includes(saved.status); n++) {
        await new Promise((r) => setTimeout(r, 2500))
        saved = await Job.get(job.id)
      }
      const invalid = await JobManager.create(
        'core.feature_retrieval.lexical.maintain.v1',
        { options: { max_records: 0 } },
        60
      )
      let rejected = invalid
      for (let n = 0; n < 24 && ['pending', 'running'].includes(rejected.status); n++) {
        await new Promise((r) => setTimeout(r, 2500))
        rejected = await Job.get(invalid.id)
      }
      await new Promise((r) => setTimeout(r, 1000))
      const { DBAPIClient } = await import('/src/base/db-api.ts')
      const logs = await new DBAPIClient('logs')
        .from()
        .select('id,trace_id')
        .eq('trace_id', `job.${invalid.id}`)
        .throwOnError()
      await t.flushTelemetry()
      if (enabled && !configFault) await new Promise((r) => setTimeout(r, 65000))
      await t.shutdownTelemetry()
      return {
        initializationMs,
        id: job.id,
        status: saved.status,
        submissionTraceparent: job.submission_traceparent,
        carrierPreserved: saved.submission_traceparent === job.submission_traceparent,
        invalidJob: { id: invalid.id, status: rejected.status, pgLogs: logs.data.length },
      }
    },
    { pg, jwt, relay, core, enabled, configFault }
  )
  report.finishedAt = new Date().toISOString()
  report.passed =
    report.business.status === 'finished' &&
    report.business.carrierPreserved &&
    (enabled && !configFault
      ? Boolean(report.business.submissionTraceparent)
      : report.business.submissionTraceparent === null)
} finally {
  await browser.close()
  await vite.close()
  await writeFile(
    new URL(`./evidence/preview-browser-${label}.json`, import.meta.url),
    JSON.stringify(report, null, 2) + '\n'
  )
  console.log(JSON.stringify(report))
}
assert(report.passed, 'Preview job must finish and preserve carrier')

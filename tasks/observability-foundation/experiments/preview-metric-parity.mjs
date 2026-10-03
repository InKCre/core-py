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
  res.end('<html><body>InKCre metric parity acceptance</body></html>')
})
await vite.listen()
const browser = await chromium.launch({ headless: true })
const version = 'preview-metric-parity-20261003'
try {
  const page = await browser.newPage()
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/probe`)
  const result = await page.evaluate(
    async ({ pg, jwt, relay, version }) => {
      const t = await import('/src/obsrv/telemetry.ts')
      const { MetaConfigSchema } = await import('/src/config/schema.ts')
      await t.initializeTelemetry(
        MetaConfigSchema.parse({
          INKCRE_PGREST_URL: pg,
          INKCRE_JWT_SECRET: jwt,
          INKCRE_PEER_ID: '00000000-0000-4000-8000-000000000095',
          telemetry_enabled: true,
          telemetry_peer_relay_url: relay,
        }),
        version
      )
      const carrier = await t.observeOperation('job.submit', async (active) => {
        await new Promise((r) => setTimeout(r, 25))
        return t.captureSubmission(active)
      })
      await t.flushTelemetry()
      await new Promise((r) => setTimeout(r, 18000))
      await t.shutdownTelemetry()
      return { traceparent: carrier.submission_traceparent }
    },
    { pg, jwt, relay, version }
  )
  const report = {
    version,
    source: execFileSync('git', ['-C', client, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
    ...result,
    finishedAt: new Date().toISOString(),
  }
  await writeFile(
    new URL('./evidence/preview-metric-parity.json', import.meta.url),
    JSON.stringify(report, null, 2) + '\n'
  )
  console.log(JSON.stringify(report))
  assert(result.traceparent)
} finally {
  await browser.close()
  await vite.close()
}

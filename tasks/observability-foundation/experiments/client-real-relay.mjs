import assert from 'node:assert/strict'
import { readFile, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
const client = fileURLToPath(new URL('../../../../client-web', import.meta.url))
const require = createRequire(`${client}/package.json`)
const { chromium } = require('@playwright/test')
const { createServer } = await import(`${client}/apps/client-web/node_modules/vite/dist/node/index.js`)
const credential = JSON.parse(await readFile(new URL('./runtime/database-credential.json', import.meta.url)))
const relay = 'http://127.0.0.1:35501/telemetry'
const version = 'browser-real-relay-protobuf-v1'
const vite = await createServer({ configFile: false, root: `${client}/packages/core`, server: { host: '127.0.0.1', port: 0, fs: { allow: [client] } }, optimizeDeps: { entries: [], include: ['vue', 'pinia', 'zod', 'zod-class', 'zod-config', 'jose', '@supabase/postgrest-js', '@opentelemetry/api', '@opentelemetry/core', '@opentelemetry/resources', '@opentelemetry/sdk-trace-web', '@opentelemetry/exporter-trace-otlp-proto', '@opentelemetry/sdk-logs', '@opentelemetry/exporter-logs-otlp-proto', '@opentelemetry/sdk-metrics', '@opentelemetry/exporter-metrics-otlp-proto'] } })
vite.middlewares.use('/probe', (_req, res) => { res.setHeader('Content-Type', 'text/html'); res.end('<html><body>InKCre real relay synthetic acceptance</body></html>') })
await vite.listen()
const browser = await chromium.launch({ headless: true })
try {
  const page = await browser.newPage()
  const accepted = [], errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.text().startsWith('[Telemetry]')) console.log(message.text()) })
  page.on('response', response => {
    if (response.url().startsWith(`${relay}/v1/`) && response.status() === 200) {
      const request = response.request()
      const body = request.postDataBuffer()
      assert(!body.includes('PRIVATE_CONTENT_SENTINEL'))
      accepted.push({ signal: response.url().split('/').at(-1), status: response.status(), responseType: response.headers()['content-type'], inputType: request.headers()['content-type'], authenticated: Boolean(request.headers().authorization) })
    }
  })
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/probe`)
  const result = await page.evaluate(async ({ relay, jwt, version }) => {
    const t = await import('/src/obsrv/telemetry.ts')
    const { MetaConfigSchema } = await import('/src/config/schema.ts')
    const meta = MetaConfigSchema.parse({ INKCRE_PGREST_URL: 'http://127.0.0.1:33000', INKCRE_JWT_SECRET: jwt, INKCRE_PEER_ID: '00000000-0000-4000-8000-000000000001', telemetry_enabled: true, telemetry_peer_relay_url: relay })
    const withoutJwt = await fetch(`${relay}/v1/traces`, { method: 'POST', headers: { 'Content-Type': 'application/x-protobuf' }, body: '' })
    const invalidJwt = await fetch(`${relay}/v1/traces`, { method: 'POST', headers: { 'Content-Type': 'application/x-protobuf', Authorization: 'Bearer invalid-synthetic' }, body: '' })
    const { signDatabaseToken } = await import('/src/auth/index.ts')
    const projectionResponse = await fetch('http://127.0.0.1:33000/configs?key=eq.inkcre.observability&select=value', { headers: { Authorization: `Bearer ${await signDatabaseToken(jwt)}`, 'Accept-Profile': 'inkcre' } })
    const projection = (await projectionResponse.json())[0].value
    const projectionResult = t.ObservabilityConfigSchema.safeParse(projection)
    if (!projectionResult.success) throw new Error(JSON.stringify(projectionResult.error.issues.map(issue => ({ path: issue.path, code: issue.code, expected: issue.expected }))))
    const unsupportedJson = await fetch(`${relay}/v1/traces`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${await signDatabaseToken(jwt)}` }, body: '{}' })
    await t.initializeTelemetry(meta, version)
    const carrier = await t.observeOperation('job.submit', async active => {
      await new Promise(resolve => setTimeout(resolve, 5))
      t.emitJobEvent('job.submitted', 900001, active)
      return t.captureSubmission(active)
    })
    const execution = await t.observeOperation('job.execute', async active => {
      await new Promise(resolve => setTimeout(resolve, 5))
      t.emitJobEvent('job.started', 900001, active)
      return t.captureSubmission(active)
    }, t.submissionLinks(carrier), t.ROOT_CONTEXT)
    await t.flushTelemetry()
    await t.shutdownTelemetry()
    return { withoutJwt: withoutJwt.status, invalidJwt: invalidJwt.status, traceparent: carrier.submission_traceparent, executionTraceparent: execution.submission_traceparent, unsupportedJson: unsupportedJson.status }
  }, { relay, jwt: credential.jwt, version })
  assert.equal(errors.length, 0, errors.join('\n'))
  assert.equal(result.withoutJwt, 401)
  assert.equal(result.invalidJwt, 401)
  assert.equal(result.traceparent.length, 55)
  assert.equal(result.unsupportedJson, 415)
  for (const signal of ['traces', 'logs', 'metrics']) {
    const response = accepted.find(item => item.signal === signal)
    assert(response, `${signal} accepted by real relay`)
    assert(response.authenticated)
    assert(response.inputType.startsWith('application/x-protobuf'))
    assert(response.responseType.startsWith('application/x-protobuf'))
  }
  const report = { passed: true, browser: await browser.version(), relay, version, jwtMissingStatus: result.withoutJwt, jwtInvalidStatus: result.invalidJwt, accepted, traceId: result.traceparent.split('-')[1], spanId: result.traceparent.split('-')[2], executionTraceId: result.executionTraceparent.split('-')[1], executionSpanId: result.executionTraceparent.split('-')[2], unsupportedJsonStatus: result.unsupportedJson, sharedConfigMutated: false, cloudExportUsed: false }
  await writeFile(new URL('./client-real-relay-result.json', import.meta.url), JSON.stringify(report, null, 2) + '\n')
  console.log(JSON.stringify(report))
} finally { await browser.close(); await vite.close() }

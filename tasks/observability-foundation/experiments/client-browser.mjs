import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { createServer as httpServer } from 'node:http'
import { readFile, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
const client = fileURLToPath(new URL('../../../../client-web', import.meta.url))
const require = createRequire(`${client}/package.json`)
const { chromium } = require('@playwright/test')
const { createServer } = await import(`${client}/apps/client-web/node_modules/vite/dist/node/index.js`)
const { jwtVerify } = await import(`${client}/apps/client-web/node_modules/jose/dist/webapi/index.js`)
const credential = JSON.parse(await readFile(new URL('./runtime/database-credential.json', import.meta.url)))
let captured = []
const peerRequests = []
let redirectTargetRequests = 0
const relayAuthentication = [], publicAuthentication = []
const redirectTarget = httpServer((_request, response) => { redirectTargetRequests += 1; response.setHeader('Access-Control-Allow-Origin', '*'); response.end('{}') })
await new Promise(resolve => redirectTarget.listen(0, '127.0.0.1', resolve))
const redirectUrl = `http://127.0.0.1:${redirectTarget.address().port}/external`
const sink = httpServer(async (request, response) => {
  response.setHeader('Access-Control-Allow-Origin', '*')
  response.setHeader('Access-Control-Allow-Headers', '*')
  if (request.method === 'OPTIONS') { response.end(); return }
  if (request.url === '/redirect') { response.writeHead(302, { Location: redirectUrl }); response.end(); return }
  if (request.url === '/server-error') { response.writeHead(500); response.end('{}'); return }
  if (request.url === '/not-executed') { response.writeHead(503, { 'InkCre-Peer-Execution': 'not-executed', 'Access-Control-Expose-Headers': 'InkCre-Peer-Execution' }); response.end('{}'); return }
  if (request.url.startsWith('/peer')) {
    peerRequests.push({ traceparent: request.headers.traceparent, tracestate: request.headers.tracestate })
    response.setHeader('Content-Type', 'application/json')
    response.end('{}'); return
  }
  const chunks = []
  for await (const chunk of request) chunks.push(chunk)
  const body = Buffer.concat(chunks)
  if (request.url.startsWith('/relay/')) {
    try { await jwtVerify(request.headers.authorization?.replace(/^Bearer /, ''), new TextEncoder().encode(credential.jwt)); relayAuthentication.push(true) } catch { relayAuthentication.push(false) }
  } else publicAuthentication.push(Boolean(request.headers.authorization))
  captured.push({ signal: request.url.replace('/relay', ''), data: body.toString('base64') })
  response.setHeader('Content-Type', 'application/x-protobuf')
  response.end()
})
await new Promise(resolve => sink.listen(0, '127.0.0.1', resolve))
const endpoint = `http://127.0.0.1:${sink.address().port}`
const vite = await createServer({ configFile: false, root: `${client}/packages/core`, server: { host: '127.0.0.1', port: 0, fs: { allow: [client] } }, optimizeDeps: { entries: [], include: ['vue', 'pinia', 'zod', 'zod-class', 'zod-config', 'jose', '@supabase/postgrest-js', '@opentelemetry/api', '@opentelemetry/core', '@opentelemetry/resources', '@opentelemetry/sdk-trace-web', '@opentelemetry/exporter-trace-otlp-proto', '@opentelemetry/sdk-logs', '@opentelemetry/exporter-logs-otlp-proto', '@opentelemetry/sdk-metrics', '@opentelemetry/exporter-metrics-otlp-proto'] } })
vite.middlewares.use('/probe', (_req, res) => { res.setHeader('Content-Type', 'text/html'); res.end('<html><body>InKCre synthetic browser observability acceptance</body></html>') })
await vite.listen()
const browser = await chromium.launch({ headless: true })
try {
  const page = await browser.newPage()
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/probe`)
  const result = await page.evaluate(async ({ endpoint, client, jwt }) => {
    const t = await import(`/src/obsrv/telemetry.ts`)
    const { configStore } = await import(`/src/config/store.ts`)
    const { DBAPIClient } = await import('/src/base/db-api.ts')
    const { MetaConfigSchema } = await import(`/src/config/schema.ts`)
    const { PeerHTTPOutbound } = await import(`/src/peer/http.ts`)
    const { Job, JobType } = await import(`/src/job/job.ts`)
    const { JobManager } = await import(`/src/job/manager.ts`)
    const { z } = await import('/node_modules/.vite/deps/zod.js')
    const { trace, createTraceState } = await import('/node_modules/.vite/deps/@opentelemetry_api.js')
    const { PeerOutcomeUnknown, PeerRequestNotExecuted } = await import('/src/peer/contracts.ts')
    const ensure = (condition, label) => { if (!condition) throw new Error(label) }
    const peerId = '00000000-0000-4000-8000-000000000001'
    configStore.metaConfig = MetaConfigSchema.parse({ INKCRE_PGREST_URL: 'http://127.0.0.1:33000', INKCRE_JWT_SECRET: jwt, INKCRE_PEER_ID: peerId })
    ensure(configStore.metaConfig.telemetry_enabled === false, 'default off')
    await t.initializeTelemetry(configStore.metaConfig, 'synthetic')
    ensure(!performance.getEntriesByType('resource').some(entry => new URL(entry.name).pathname.endsWith('/configs')), 'disabled does not read shared config')
    const offCarrier = t.captureSubmission(t.ROOT_CONTEXT)
    ensure(offCarrier.submission_traceparent === null, 'disabled carrier')
    const types = await JobType.getAll()
    const type = types[0].id
    let executions = 0
    JobManager.registerHandler(type, { parameters: z.record(z.string(), z.unknown()), canHandle: () => true, async handle(job, parameters, signal) { await new Promise(resolve => setTimeout(resolve, 8)); executions += 1; if (parameters.mode === 'error') throw new Error('PRIVATE_EXCEPTION_SENTINEL'); if (parameters.mode === 'timeout' || parameters.mode === 'abort') await new Promise(resolve => { if (signal.aborted) resolve(); else signal.addEventListener('abort', resolve, { once: true }) }); job.state = { synthetic: true } } })
    const offJob = await JobManager.create(type, { sentinel: 'PRIVATE_BODY_SENTINEL' })
    ensure(offJob.submission_traceparent === null, 'off database defaults')
    const configDb = new DBAPIClient('configs')
    const { data: previousConfig } = await configDb.from().select('schema,value').eq('key', 'inkcre.observability').single().throwOnError()
    const cfg = { deployment_id: previousConfig.value.deployment_id, otlp_http_endpoints: { traces: `${endpoint}/v1/traces`, logs: `${endpoint}/v1/logs`, metrics: `${endpoint}/v1/metrics` }, diagnostics_url: `${endpoint}/diagnostics` }
    await configDb.update({ value: cfg }).eq('key', 'inkcre.observability').throwOnError()
    try {
    configStore.metaConfig.telemetry_enabled = true
    await t.initializeTelemetry(configStore.metaConfig, 'synthetic')
    ensure(t.telemetryDiagnosticsUrl.value === cfg.diagnostics_url, 'real lifecycle reads config')
    const parents = await Promise.all([25, 4].map(delay => t.observeOperation('job.submit', async active => {
      await new Promise(resolve => setTimeout(resolve, delay))
      const parent = t.captureSubmission(active).submission_traceparent
      const outbound = new PeerHTTPOutbound({ id: peerId }, { method: 'POST', url: `${endpoint}/peer` })
      await outbound.execute({ query: { private: ['PRIVATE_QUERY_SENTINEL'] }, body: { secret: 'PRIVATE_BODY_SENTINEL' } }, active)
      return parent
    })))
    ensure(parents[0].split('-')[1] !== parents[1].split('-')[1], 'concurrent context isolated')
    const redirect = new PeerHTTPOutbound({ id: peerId }, { method: 'POST', url: `${endpoint}/redirect` })
    try { await redirect.execute({}); throw new Error('redirect unexpectedly followed') } catch (error) { ensure(error instanceof PeerOutcomeUnknown, 'redirect retains unknown outcome') }
    const rejected = new PeerHTTPOutbound({ id: peerId }, { method: 'POST', url: `${endpoint}/not-executed` })
    try { await rejected.execute({}); throw new Error('non-execution unexpectedly accepted') } catch (error) { ensure(error instanceof PeerRequestNotExecuted, 'not-executed retained') }
    const largeState = Array.from({ length: 8 }).reduce((state, _, i) => state.set(`vendor${i}`, 'a'.repeat(140)), createTraceState())
    const carrierContext = trace.setSpanContext(t.ROOT_CONTEXT, { traceId: 'a'.repeat(32), spanId: 'b'.repeat(16), traceFlags: 0, traceState: largeState })
    const bounded = t.captureSubmission(carrierContext)
    ensure(bounded.submission_traceparent?.endsWith('-00') && bounded.submission_tracestate === null, 'unsampled accepted and oversized optional state omitted')
    ensure(t.submissionLinks(bounded).links[0].context.traceFlags === 0, 'unsampled link flags retained')
    ensure(!t.submissionLinks({ submission_traceparent: 'PRIVATE_INVALID_CARRIER' }).links, 'invalid carrier ignored by SDK')
    const onJob = await JobManager.create(type, { sentinel: 'PRIVATE_BODY_SENTINEL' })
    ensure(onJob.submission_traceparent?.length === 55, 'real job carrier persisted')
    const submittedCarrier = onJob.submission_traceparent
    await JobManager.run(onJob.id)
    const finished = await Job.get(onJob.id)
    ensure(finished.status === 'finished' && finished.submission_traceparent === submittedCarrier, 'claim close preserve carrier')
    await JobManager.run(offJob.id)
    const oldFinished = await Job.get(offJob.id)
    ensure(oldFinished.status === 'finished' && oldFinished.submission_traceparent === null, 'off producer on consumer')
    async function runFailures() {
      const serverError = new PeerHTTPOutbound({ id: peerId }, { method: 'POST', url: `${endpoint}/server-error` })
      const response = await serverError.execute({})
      ensure(response.status === 500, 'readable 500 business envelope retained')
      const failed = await JobManager.create(type, { mode: 'error' })
      await JobManager.run(failed.id)
      ensure((await Job.get(failed.id)).status === 'failed', 'failure result retained')
      const timeout = await JobManager.create(type, { mode: 'timeout' }, 1)
      await JobManager.run(timeout.id)
      ensure((await Job.get(timeout.id)).status === 'timed_out', 'timeout result retained')
      const aborted = await JobManager.create(type, { mode: 'abort' })
      const running = JobManager.run(aborted.id)
      while ((await Job.get(aborted.id)).status === 'pending') await new Promise(resolve => setTimeout(resolve, 10))
      await new Promise(resolve => setTimeout(resolve, 20))
      await Job.dbApi.update({ abort_requested: true }).eq('id', aborted.id).throwOnError()
      await JobManager.checkAbortRequests()
      await running
      ensure((await Job.get(aborted.id)).status === 'aborted', 'abort result retained')
    }
    await runFailures()
    const onOff = await JobManager.create(type, {})
    await t.flushTelemetry()
    await t.shutdownTelemetry()
    await JobManager.run(onOff.id)
    const mixed = await Job.get(onOff.id)
    ensure(mixed.status === 'finished' && mixed.submission_traceparent === onOff.submission_traceparent, 'on producer off consumer preserves carrier')
    const offOutbound = new PeerHTTPOutbound({ id: peerId }, { method: 'POST', url: `${endpoint}/peer` })
    await offOutbound.execute({})
    await t.configureTelemetry({ ...cfg, otlp_http_endpoints: { metrics: `${endpoint}/v1/metrics` } }, peerId, 'metrics-only')
    await runFailures()
    await t.flushTelemetry()
    await t.shutdownTelemetry()
    configStore.metaConfig.telemetry_peer_relay_url = `${endpoint}/relay`
    await t.initializeTelemetry(configStore.metaConfig, 'relay')
    configStore.metaConfig.INKCRE_JWT_SECRET = 'different-connection-synthetic-secret-for-snapshot-probe'
    await t.observeOperation('job.submit', async () => true)
    await t.flushTelemetry()
    await t.shutdownTelemetry()
    configStore.metaConfig.INKCRE_JWT_SECRET = jwt
    const started = performance.now()
    await t.configureTelemetry({ ...cfg, otlp_http_endpoints: { traces: 'http://127.0.0.1:1/v1/traces' } }, peerId, 'synthetic')
    await t.observeOperation('job.submit', async () => true)
    await t.flushTelemetry()
    await t.shutdownTelemetry()
    ensure(performance.now() - started < 3000, 'failed exporter bounded')
    return { parents, jobs: [offJob.id, onJob.id, onOff.id], submittedCarrier, executions, failedExporterElapsedMs: Math.round(performance.now() - started) }
    } finally { configStore.metaConfig.INKCRE_JWT_SECRET = jwt; await t.shutdownTelemetry(); await configDb.update(previousConfig).eq('key', 'inkcre.observability').throwOnError() }
  }, { endpoint, client, jwt: credential.jwt })
  captured = JSON.parse(execFileSync('pdm', ['run', 'python', 'tasks/observability-foundation/experiments/client-decode-protobuf.py'], { cwd: `${client}/../core-py`, input: JSON.stringify(captured), encoding: 'utf8' }))
  assert.equal(errors.length, 0, errors.join('\n'))
  assert.equal(result.executions, 9)
  const traceBatches = captured.filter(item => item.signal === '/v1/traces')
  const spans = traceBatches.flatMap(batch => batch.data.resourceSpans.flatMap(resource => resource.scopeSpans.flatMap(scope => scope.spans)))
  const attr = (span, key) => span.attributes?.find(a => a.key === key)?.value
  const execution = spans.find(span => span.name === 'job.execute' && String(attr(span, 'inkcre.job.id')?.intValue) === String(result.jobs[1]))
  assert(execution, 'job execution span')
  assert.equal(execution.links[0].traceId, result.submittedCarrier.split('-')[1])
  assert.notEqual(execution.traceId, execution.links[0].traceId)
  assert(!execution.parentSpanId, 'independent execution root')
  assert(relayAuthentication.length >= 3 && relayAuthentication.every(Boolean), 'relay dynamic JWT uses captured connection')
  assert(publicAuthentication.every(value => value === false), 'public OTLP receives no Peer JWT')
  assert.equal(redirectTargetRequests, 0, 'cross-origin redirect receives no request or trace context')
  assert.equal(peerRequests.length, 3)
  for (const parent of result.parents) assert(peerRequests.some(request => request.traceparent?.split('-')[1] === parent.split('-')[1]))
  assert.equal(peerRequests[2].traceparent, undefined)
  for (const signal of ['traces', 'logs', 'metrics']) assert(captured.some(item => item.signal === `/v1/${signal}`), `${signal} exported`)
  const serialized = JSON.stringify(captured)
  assert(!serialized.includes('PRIVATE_BODY_SENTINEL') && !serialized.includes('PRIVATE_QUERY_SENTINEL') && !serialized.includes('PRIVATE_EXCEPTION_SENTINEL'))
  const metricResources = captured.filter(item => item.signal === '/v1/metrics').flatMap(batch => batch.data.resourceMetrics)
  for (const version of ['synthetic', 'metrics-only']) {
    const outcomes = metricResources.filter(resource => resource.resource.attributes.some(a => a.key === 'service.version' && a.value.stringValue === version)).flatMap(resource => resource.scopeMetrics.flatMap(scope => scope.metrics.filter(metric => metric.name === 'inkcre.operation.duration').flatMap(metric => metric.histogram.dataPoints))).filter(point => point.attributes.some(a => a.key === 'inkcre.operation' && a.value.stringValue === 'job.execute')).map(point => point.attributes.find(a => a.key === 'inkcre.outcome').value.stringValue)
    for (const outcome of ['error', 'timeout', 'cancelled']) assert(outcomes.includes(outcome), `${version} ${outcome} measured independently of trace export`)
    const httpPoints = metricResources.filter(resource => resource.resource.attributes.some(a => a.key === 'service.version' && a.value.stringValue === version)).flatMap(resource => resource.scopeMetrics.flatMap(scope => scope.metrics.filter(metric => metric.name === 'inkcre.operation.duration').flatMap(metric => metric.histogram.dataPoints)))
    assert(httpPoints.some(point => point.attributes.some(a => a.key === 'inkcre.operation' && a.value.stringValue === 'peer.http') && point.attributes.some(a => a.key === 'inkcre.outcome' && a.value.stringValue === 'error')), `${version} readable HTTP 500 counted as error`)
  }
  const report = { passed: true, encoding: 'application/x-protobuf', browser: await browser.version(), jobIds: result.jobs, spans: spans.length, signals: [...new Set(captured.map(item => item.signal))], independentJobLink: true, concurrentNativeAwaitIsolation: true, mixedPeers: ['off→on', 'on→off'], metadataSentinelsAbsent: true, crossOriginRedirectBlocked: true, unsampledCarrier: true, oversizedTracestateDropped: true, invalidCarrierIgnored: true, metricsOnlyTerminalOutcomes: true, lifecycleInitialization: true, relayJwtCapturedConnection: true, publicOtlpWithoutJwt: true, failedExporterElapsedMs: result.failedExporterElapsedMs }
  await writeFile(new URL('./client-browser-result.json', import.meta.url), JSON.stringify(report, null, 2) + '\n')
  console.log(JSON.stringify(report))
} finally { await browser.close(); await vite.close(); await new Promise(resolve => sink.close(resolve)); await new Promise(resolve => redirectTarget.close(resolve)) }

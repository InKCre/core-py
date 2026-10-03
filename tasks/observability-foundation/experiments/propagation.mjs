import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { ROOT_CONTEXT, trace, defaultTextMapGetter, defaultTextMapSetter } from '@opentelemetry/api';
import { W3CTraceContextPropagator } from '@opentelemetry/core';
import { BasicTracerProvider, InMemorySpanExporter, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';

const propagator = new W3CTraceContextPropagator();
const exporter = new InMemorySpanExporter();
const provider = new BasicTracerProvider({spanProcessors: [new SimpleSpanProcessor(exporter)]});
const tracer = provider.getTracer('contract-probe');
const vectors = JSON.parse(readFileSync(0, 'utf8'));
const results = await Promise.all(vectors.map(async ({name, carrier, valid}) => {
  // Explicit contexts model persisted carriers; ambient polling context must not become a parent.
  const extracted = propagator.extract(ROOT_CONTEXT, carrier, defaultTextMapGetter);
  const context = trace.getSpanContext(extracted);
  assert.equal(Boolean(context), valid, name);
  const linked = tracer.startSpan(name, {links: context ? [{context}] : []}, ROOT_CONTEXT);
  await Promise.resolve();
  assert.notEqual(linked.spanContext().traceId, context?.traceId);
  const outgoing = {};
  propagator.inject(trace.setSpan(ROOT_CONTEXT, linked), outgoing, defaultTextMapSetter);
  const roundtrip = {};
  propagator.inject(extracted, roundtrip, defaultTextMapSetter);
  linked.end();
  return {name, roundtrip, outgoing};
}));
await provider.forceFlush();
const spans = exporter.getFinishedSpans();
for (const vector of vectors) {
  const span = spans.find(s => s.name === vector.name);
  assert.equal(span.parentSpanContext, undefined);
  assert.equal(span.links.length, vector.valid ? 1 : 0);
}
assert.equal(new Set(results.map(r => r.outgoing.traceparent)).size, vectors.length);
await provider.shutdown();
process.stdout.write(JSON.stringify(results));

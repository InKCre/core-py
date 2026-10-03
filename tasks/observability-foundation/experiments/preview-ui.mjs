import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { readFile, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
const client = fileURLToPath(new URL('../../../../client-web', import.meta.url))
const require = createRequire(`${client}/package.json`)
const { chromium } = require('@playwright/test')
const jwt = execFileSync(
  'security',
  ['find-generic-password', '-s', 'inkcre/core-py/JWT_SECRET', '-w'],
  { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }
).trim()
const source = JSON.parse(
  await readFile(new URL('./evidence/preview-browser-on.json', import.meta.url))
)
const origin = 'https://preview-client-web-pr-125.inkcre-client-web.pages.dev'
const browser = await chromium.launch({ headless: true })
const report = {
  origin,
  jobId: source.business.id,
  errorJobId: source.business.invalidJob.id,
  requests: [],
  verified: false,
}
try {
  const page = await browser.newPage()
  await page.addInitScript(
    ({ origin, jwt, pg, relay }) => {
      if (location.origin === origin)
        localStorage.setItem(
          'inkcre_app_config',
          JSON.stringify({
            INKCRE_PGREST_URL: pg,
            INKCRE_JWT_SECRET: jwt,
            INKCRE_PEER_ID: '00000000-0000-4000-8000-000000000096',
            telemetry_enabled: true,
            telemetry_peer_relay_url: relay,
          })
        )
    },
    { origin, jwt, pg: source.pg, relay: source.relay }
  )
  page.on('response', (response) => {
    if (response.url().includes('/telemetry/v1/'))
      report.requests.push({ signal: response.url().split('/').at(-1), status: response.status() })
  })
  await page.goto(origin + '/jobs/' + report.jobId)
  await page.locator('.status--finished').waitFor({ timeout: 60000 })
  report.finishedVisible = true
  await page.goto(origin + '/jobs/' + report.errorJobId)
  await page.locator('.status--failed').waitFor({ timeout: 60000 })
  await page
    .getByText('Persisted Job parameters are invalid', { exact: false })
    .first()
    .waitFor({ timeout: 30000 })
  report.pgLogVisible = true
  report.verified = true
  await page.waitForTimeout(10000)
} finally {
  await browser.close()
  await writeFile(
    new URL('./evidence/preview-ui.json', import.meta.url),
    JSON.stringify(report, null, 2) + '\n'
  )
  console.log(JSON.stringify(report))
}
assert(report.verified)

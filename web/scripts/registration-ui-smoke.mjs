import assert from 'node:assert/strict'
import { spawn, execFileSync } from 'node:child_process'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'node:net'
import { chromium } from 'playwright-core'

const root = fileURLToPath(new URL('../../', import.meta.url))
const directory = await mkdtemp(resolve(tmpdir(), 'librai-registration-ui-'))
assert.ok(directory.startsWith(resolve(tmpdir()) + '\\librai-registration-ui-'))
const socket = createServer().listen(0, '127.0.0.1')
await new Promise(resolve => socket.once('listening', resolve))
const port = socket.address().port
await new Promise(resolve => socket.close(resolve))
const local = `http://127.0.0.1:${port}`
const base = process.env.DESIGN_UI_URL || 'http://127.0.0.1:4190'
const python = spawn(resolve(root, '.venv/Scripts/python.exe'), ['-u', '-c', `
from backend.main import app
from backend.core.database import Base,engine,SessionLocal
from backend.core.security import hash_password
from backend.models.entities import Admin
import uvicorn
Base.metadata.create_all(engine)
with SessionLocal() as db:
 db.add(Admin(username='registration-test',email='test@example.invalid',password_hash=hash_password('TemporaryTestOnly123!'),role='SUPER_ADMIN'));db.commit()
uvicorn.run(app,host='127.0.0.1',port=${port},log_level='warning',access_log=False)
`], { cwd: root, env: { ...process.env, DATABASE_URL: `sqlite:///${resolve(directory, 'test.db').replaceAll('\\', '/')}`, LIBRAI_ENV: 'development', EMAIL_TRANSPORT: 'smtp', EMAIL_AUTOSEND_ENABLED: 'false', MEDIA_BUCKET: '', GEMINI_API_KEY: '', TOKENROUTER_API_KEY: '', SECRET_KEY: 'isolated-registration-ui-test-key-only-not-live' }, stdio: ['ignore', 'pipe', 'pipe'] })
let backendOutput = ''
python.stdout.on('data', data => { backendOutput += data })
python.stderr.on('data', data => { backendOutput += data })
let browser
let page
let phase = 'backend startup'
try {
  let ready = false
  for (let i = 0; i < 80; i++) {
    try { ready = (await fetch(`${local}/health`)).ok } catch {}
    if (ready) break
    await new Promise(resolve => setTimeout(resolve, 500))
  }
  assert.ok(ready, `Isolated backend did not start: ${backendOutput.slice(-1000)}`)
  browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
  const context = await browser.newContext({ viewport: { width: 768, height: 1024 }, reducedMotion: 'reduce' })
  const mutations = []
  // Real API and OCR, synthetic cards, isolated DB: block any unplanned external request.
  await context.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url())
    if (url.origin === new URL(base).origin) return route.continue()
    if (url.pathname === '/health' || url.pathname.startsWith('/api/v1/')) {
      const headers = { 'access-control-allow-origin': new URL(base).origin, 'access-control-allow-headers': 'authorization,content-type', 'access-control-allow-methods': 'GET,POST,PUT,OPTIONS' }
      if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers })
      if (['POST', 'PUT'].includes(request.method())) mutations.push({ path: url.pathname, body: request.postDataJSON() })
      const response = await route.fetch({ url: `${local}${url.pathname}${url.search}` })
      return route.fulfill({ response, headers: { ...response.headers(), ...headers } })
    }
    throw Error(`Unexpected external request: ${url.origin}`)
  })
  page = await context.newPage()
  page.setDefaultTimeout(60_000)
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  async function card(lines) {
    const data = await page.evaluate(lines => {
      const canvas = document.createElement('canvas'); canvas.width = 1200; canvas.height = 700
      const ctx = canvas.getContext('2d'); ctx.fillStyle = 'white'; ctx.fillRect(0, 0, 1200, 700)
      ctx.fillStyle = 'black'; ctx.font = 'bold 42px Arial'
      lines.forEach((line, index) => ctx.fillText(line, 45, 75 + index * 95))
      return canvas.toDataURL('image/png').split(',')[1]
    }, lines)
    return { name: 'synthetic-card.png', mimeType: 'image/png', buffer: Buffer.from(data, 'base64') }
  }
  await page.goto(base)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  phase = 'campus OCR'
  console.log('Checking real campus OCR')
  const form = page.locator('.member-form')
  await page.getByLabel('Choose ID image', { exact: true }).setInputFiles(await card(['SAMPLE STATE UNIVERSITY', '25-1234', 'JUAN P. DELA CRUZ JR.', 'BS Information Technology']))
  await page.getByRole('button', { name: 'Apply scanned details', exact: true }).click()
  assert.equal(await form.locator('[name=student_id]').inputValue(), '25-1234')
  assert.equal(await form.locator('[name=last_name]').inputValue(), 'DELA CRUZ JR.')
  await page.getByLabel('Card to read', { exact: true }).selectOption('library')
  phase = 'library OCR'
  console.log('Checking real library card OCR')
  await page.getByLabel('Choose ID image', { exact: true }).setInputFiles(await card(["BORROWER'S CARD", "Borrower's Card No. 25-9876", 'NAME', 'DELA CRUZ, JR., JUAN, P.', 'ADDRESS Sample town']))
  await page.getByRole('button', { name: 'Apply scanned details', exact: true }).click()
  assert.equal(await form.locator('[name=library_card_number]').inputValue(), '25-9876')
  assert.equal(await form.locator('[name=student_id]').inputValue(), '25-1234')
  assert.equal(await form.locator('[name=first_name]').inputValue(), 'JUAN P.')
  assert.equal(mutations.length, 0, 'OCR and applying results must not save or upload a photo')
  await form.locator('[name=year_level]').fill('3')
  await form.locator('[name=email]').fill('synthetic@example.com')
  await form.locator('[name=first_name]').fill('Juan P.')
  await page.getByLabel('I checked the scanned names and numbers against the card.').check()
  await page.getByLabel('These are my details, and I am submitting them for library staff review.').check()
  await page.screenshot({ path: resolve(root, 'docs/design_previews/registration-review-768.png'), fullPage: true })
  await page.getByRole('button', { name: 'Submit for staff approval' }).click()
  phase = 'pending registration'
  await page.getByRole('heading', { name: 'Registration request received' }).waitFor()
  assert.deepEqual(mutations.map(x => x.path), ['/api/v1/registrations'])
  assert.equal(mutations[0].body.library_card_number, '25-9876')
  assert.equal(mutations[0].body.status, undefined)
  await page.getByRole('button', { name: 'Finish and clear session' }).click()
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  assert.equal(await page.locator('[name=student_id]').inputValue(), '')
  await page.goto(`${base}/admin`)
  phase = 'staff review'
  await page.locator('#username').fill('registration-test')
  await page.locator('#password').fill('TemporaryTestOnly123!')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await page.getByRole('heading', { name: 'Library dashboard', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Menu', exact: true }).click()
  await page.getByRole('navigation').getByRole('button', { name: 'Library users', exact: true }).click()
  await page.getByRole('button', { name: 'Pending registrations', exact: true }).click()
  await page.getByRole('button', { name: 'Review request', exact: true }).click()
  assert.equal(await page.getByRole('button', { name: 'QR', exact: true }).count(), 0)
  await page.getByRole('button', { name: 'Approve registration', exact: true }).click()
  await page.getByRole('button', { name: 'All users', exact: true }).click()
  await page.getByRole('button', { name: 'QR', exact: true }).waitFor()
  assert.ok(mutations.some(m => m.path.startsWith('/api/v1/users/') && m.body.status === 'ACTIVE'))
  await page.getByRole('button', { name: 'Edit', exact: true }).click()
  await page.getByLabel('Choose ID image', { exact: true }).setInputFiles(await card(['SAMPLE STATE UNIVERSITY', '25-0000', 'OTHER TEST PERSON', 'BS Information Technology']))
  await page.getByRole('button', { name: 'Apply scanned details', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'does not match this member' }).waitFor()
  assert.equal(await page.locator('.member-form [name=first_name]').inputValue(), 'Juan P.')
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 768)
  await page.getByRole('button', { name: 'Cancel', exact: true }).click()
  page.once('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: 'Email QR', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Library ID email queued' }).waitFor()
  await page.getByRole('button', { name: 'Menu', exact: true }).click()
  await page.getByRole('navigation').getByRole('button', { name: 'Email deliveries', exact: true }).click()
  await page.getByRole('cell', { name: 'synthetic@example.com', exact: true }).waitFor()
  await page.getByRole('cell', { name: 'pending', exact: true }).waitFor()
  assert.ok(await page.getByRole('button', { name: 'Send now', exact: true }).isEnabled())
  assert.deepEqual(errors, [])
  console.log('PASS real local OCR for two synthetic card types -> review -> pending request -> staff approval -> QR enabled -> admin Email QR -> pending outbox visible; no SMTP delivery or ID image upload, no live record writes')
} catch (error) {
  console.error('Failed phase:', phase, 'OCR status:', await page?.locator('.id-scan-status').innerText({ timeout: 1000 }).catch(() => 'not shown'))
  throw error
} finally {
  await browser?.close()
  if (process.platform === 'win32' && python.exitCode === null) {
    try { execFileSync('taskkill', ['/pid', String(python.pid), '/t', '/f'], { stdio: 'ignore' }) } catch {}
  } else python.kill()
  if (python.exitCode === null) await new Promise(resolve => python.once('exit', resolve))
  assert.ok(directory.startsWith(resolve(tmpdir()) + '\\librai-registration-ui-'))
  await rm(directory, { recursive: true, force: true, maxRetries: 10, retryDelay: 250 })
}

import assert from 'node:assert/strict'
import { spawn, execFileSync } from 'node:child_process'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'node:net'
import { chromium } from 'playwright-core'

const root = fileURLToPath(new URL('../../', import.meta.url))
const directory = await mkdtemp(resolve(tmpdir(), 'librai-ai-ui-'))
assert.ok(directory.startsWith(resolve(tmpdir()) + '\\librai-ai-ui-'))
const socket = createServer().listen(0, '127.0.0.1')
await new Promise(resolve => socket.once('listening', resolve))
const port = socket.address().port
await new Promise(resolve => socket.close(resolve))
const local = `http://127.0.0.1:${port}`
const base = process.env.DESIGN_UI_URL || 'http://127.0.0.1:4190'
const python = spawn(resolve(root, '.venv/Scripts/python.exe'), ['-u', '-c', `
from backend.main import app
from backend.core.database import Base,engine,SessionLocal
from backend.models.entities import User,Book,BookCopy,Category,Borrowing
from datetime import datetime,timedelta,timezone
import uvicorn
Base.metadata.create_all(engine)
with SessionLocal() as db:
 user=User(student_id='TEST-01',first_name='AI',last_name='Tester',course='BSIT',year_level='3',status='ACTIVE',qr_token='USR_QR_ai_test_only_123456789')
 category=Category(name='Programming')
 book=Book(isbn='9780000000010',title='Python Basics',author='Test Author',description='Beginner Python programming',keywords=['beginner','python'],category=category,shelf_location='TEST-01')
 copy=BookCopy(book=book,accession_number='TEST-01',qr_token='BOOK_QR_ai_test_only_123456789',status='AVAILABLE')
 db.add_all([user,copy]);db.flush()
 db.add(Borrowing(user_id=user.id,book_copy_id=copy.id,status='RETURNED',due_at=datetime.now(timezone.utc),returned_at=datetime.now(timezone.utc)));db.commit()
uvicorn.run(app,host='127.0.0.1',port=${port},log_level='warning',access_log=False)
`], { cwd: root, env: { ...process.env, DATABASE_URL: `sqlite:///${resolve(directory, 'test.db').replaceAll('\\', '/')}`, LIBRAI_ENV: 'development', EMAIL_TRANSPORT: 'smtp', EMAIL_AUTOSEND_ENABLED: 'false', MEDIA_BUCKET: '', GEMINI_API_KEY: '', TOKENROUTER_API_KEY: '', SECRET_KEY: 'isolated-registration-ui-test-key-only-not-live' }, stdio: ['ignore', 'pipe', 'pipe'] })
let backendOutput = ''
python.stdout.on('data', data => { backendOutput += data })
python.stderr.on('data', data => { backendOutput += data })
let browser
let page
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
  let failNextAI = false
  let holdNextAI = false
  let releaseAI
  // Real API and OCR, synthetic cards, isolated DB: block any unplanned external request.
  await context.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url())
    if (url.origin === new URL(base).origin) return route.continue()
    if (url.pathname === '/health' || url.pathname.startsWith('/api/v1/')) {
      const headers = { 'access-control-allow-origin': new URL(base).origin, 'access-control-allow-headers': 'authorization,content-type', 'access-control-allow-methods': 'GET,POST,PUT,OPTIONS' }
      if (url.pathname === '/api/v1/ai/search' && request.method() === 'POST' && holdNextAI) {
        holdNextAI = false
        await new Promise(resolve => { releaseAI = resolve })
      }
      if (url.pathname === '/api/v1/ai/search' && failNextAI) {
        failNextAI = false
        return route.fulfill({ status: 503, headers, json: { detail: 'Synthetic temporary outage' } })
      }
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
  async function ask(text, expectedStatus = 200) {
    await page.getByRole('textbox', { name: 'Message LIBRAI' }).fill(text)
    const response = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/ai/search')
    await page.getByRole('button', { name: 'Send', exact: true }).click()
    assert.equal((await response).status(), expectedStatus)
    await page.locator('main[aria-busy="false"]').waitFor()
  }
  await page.goto(base)
  await page.getByRole('button', { name: 'My account', exact: true }).click()
  await page.getByLabel('Use a USB scanner or enter the QR value').fill('USR_QR_ai_test_only_123456789')
  await page.getByRole('button', { name: 'Verify', exact: true }).click()
  await page.getByRole('heading', { name: 'AI Tester', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Home', exact: true }).click()
  await page.getByRole('button', { name: 'Discover books', exact: true }).click()
  await page.getByText('Python Basics', { exact: true }).waitFor()
  const recommend = mutations.find(x => x.path === '/api/v1/ai/recommend').body
  assert.equal(recommend.user_id, 1)
  assert.ok(recommend.user_verification_token)
  await page.getByRole('button', { name: 'Home', exact: true }).click()
  await page.getByRole('button', { name: 'Ask LIBRAI', exact: true }).click()
  await ask('Python programming')
  await page.getByText('Python Basics', { exact: true }).waitFor()
  await page.getByText(/AI ranking is unavailable/).waitFor()
  await page.getByRole('button', { name: /Python Basics Test Author/ }).click()
  await page.getByRole('button', { name: 'Back to chat', exact: true }).click()
  await page.getByLabel('Chat messages').getByText('Python Basics', { exact: true }).waitFor()
  await ask('Show easier ones')
  await page.getByText(/Current topic: python, programming/).waitFor()
  assert.equal(await page.getByLabel('Your message', { exact: true }).count(), 2)
  assert.equal(await page.getByLabel('LIBRAI reply', { exact: true }).count(), 2)
  let requests = mutations.filter(x => x.path === '/api/v1/ai/search')
  assert.deepEqual(requests[1].body.context.topics, ['python', 'programming'])
  assert.equal(requests[1].body.user_id, 1)
  await page.screenshot({ path: resolve(root, 'generated/chat-preview.png'), fullPage: true })
  await ask('Only available books')
  await page.getByText(/beginner.*available only/).waitFor()
  await ask('Ilang libro ang puwedeng hiramin?')
  await page.getByText(/up to 3 active loans/).waitFor()
  await page.getByRole('button', { name: 'Start a new question', exact: true }).click()
  await ask('astronomy')
  await page.getByText(/No matching catalog books/).waitFor()
  assert.equal(await page.getByText('Python Basics', { exact: true }).count(), 0)
  failNextAI = true
  await ask('Python', 503)
  await page.getByText('Message not sent. Check the connection and try again.').waitFor()
  const retried = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/ai/search')
  await page.getByRole('button', { name: 'Retry message', exact: true }).click()
  assert.equal((await retried).status(), 200)
  await page.getByLabel('LIBRAI reply', { exact: true }).last().getByText('Python Basics', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'End session', exact: true }).click()
  await page.getByRole('button', { name: 'Ask LIBRAI', exact: true }).click()
  assert.equal(await page.getByLabel('Your message', { exact: true }).count(), 0)
  await ask('Show easier ones')
  await page.getByText(/Which topic would you like/).waitFor()
  requests = mutations.filter(x => x.path === '/api/v1/ai/search')
  assert.equal(requests.at(-1).body.context, null)
  assert.equal(requests.at(-1).body.user_id, undefined)
  holdNextAI = true
  await page.getByRole('textbox', { name: 'Message LIBRAI' }).fill('Python')
  const lateReply = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/ai/search')
  await page.getByRole('button', { name: 'Send', exact: true }).click()
  await page.getByText('Checking the library...').waitFor()
  await page.waitForTimeout(100)
  assert.ok(releaseAI)
  await page.getByRole('button', { name: 'End session', exact: true }).click()
  releaseAI()
  await lateReply
  await page.locator('main[aria-busy="false"]').waitFor()
  await page.getByRole('button', { name: 'Ask LIBRAI', exact: true }).click()
  assert.equal(await page.getByLabel('Your message', { exact: true }).count(), 0)
  assert.equal(await page.getByLabel('LIBRAI reply', { exact: true }).count(), 0)
  for (const width of [768, 390]) {
    await page.setViewportSize({ width, height: 1024 })
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
  }
  assert.deepEqual(errors, [])
  console.log('PASS real isolated API: scanned-member personalization, topic follow-ups, policy settings, honest no-match, chat history, book-detail return, error/retry, session clearing including late replies, tablet/mobile layout; no live DB writes or email sends')
} finally {
  await browser?.close()
  if (process.platform === 'win32' && python.exitCode === null) {
    try { execFileSync('taskkill', ['/pid', String(python.pid), '/t', '/f'], { stdio: 'ignore' }) } catch {}
  } else python.kill()
  if (python.exitCode === null) await new Promise(resolve => python.once('exit', resolve))
  assert.ok(directory.startsWith(resolve(tmpdir()) + '\\librai-ai-ui-'))
  await rm(directory, { recursive: true, force: true, maxRetries: 10, retryDelay: 250 })
}

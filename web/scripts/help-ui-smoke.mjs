import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const base = process.env.HELP_UI_URL || 'http://127.0.0.1:4191'
if (!base.startsWith('http://127.0.0.1:')) throw new Error('Help tests require a local UI and intercept every API request.')
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
try {
 for (const [width, height] of [[320, 740], [600, 960], [768, 1024], [1024, 768]]) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' })
  let writes = 0
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route(/\/health$|\/api\/v1\//, async route => {
   const path = new URL(route.request().url()).pathname
   const body = route.request().postDataJSON()
   if (path === '/health') return route.fulfill({ json: { status: 'healthy' } })
   if (path.endsWith('/qr/verify-user')) return body.token === 'invalid'
    ? route.fulfill({ status: 400, json: { detail: 'Invalid library ID.' } })
    : route.fulfill({ json: { id: 7, student_id: 'PREVIEW-7', display_name: 'Preview borrower', verification_token: 'mock-user-grant' } })
   if (path.endsWith('/qr/verify-book')) return route.fulfill({ json: { id: 3, book_id: 2, book_copy_id: 3, title: 'Preview library book', accession_number: 'COPY-003', verification_token: 'mock-book-grant', available: true } })
   if (path === '/api/v1/borrowings' && route.request().method() === 'POST') { writes++; return route.fulfill({ json: { id: 1, book_title: 'Preview library book', due_at: '2026-12-01T12:00:00Z', status: 'BORROWED' } }) }
   throw new Error('Unexpected API request: ' + path)
  })
  const guide = page.locator('.help-panel')
  async function accessible(selector) {
   await page.waitForFunction(sel => {
    const panel = document.querySelector('.help-panel')?.getBoundingClientRect()
    const target = document.querySelector(sel)?.getBoundingClientRect()
    if (!panel || !target) return false
    const cx = target.x + target.width / 2, cy = target.y + target.height / 2
    const hit = document.elementFromPoint(cx, cy)
    return target.top >= 0 && target.bottom <= innerHeight && panel.top >= 0 && panel.bottom <= innerHeight && (!hit?.closest('.help-panel')) && !(panel.left < target.right && panel.right > target.left && panel.top < target.bottom && panel.bottom > target.top)
   }, selector, { timeout: 7000 }).catch(async error => {
    console.error(await page.evaluate(sel => ({ target: document.querySelector(sel)?.getBoundingClientRect().toJSON(), panel: document.querySelector('.help-panel')?.getBoundingClientRect().toJSON(), docked: document.querySelector('.help-layer')?.getAttribute('data-docked'), scrollY, height: innerHeight }), selector))
    throw error
   })
   assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width, 'No horizontal overflow')
  }
  async function verify(value) {
   await accessible('[data-help-qr-entry]')
   await page.locator('[data-help-qr-entry] input').fill(value)
   await page.locator('[data-help-qr-entry] button').click()
  }
  await page.goto(base)
  await page.getByRole('button', { name: 'Borrow a book', exact: true }).click()
  await page.getByRole('button', { name: 'Help', exact: true }).click()
  await page.getByRole('button', { name: 'Guide this screen', exact: true }).click()
  await guide.getByRole('heading', { name: 'Step 1 / 4: Library ID' }).waitFor()
  assert.equal(await guide.getByRole('button', { name: 'Done', exact: true }).isDisabled(), true)
  assert.equal(await page.locator('.help-highlight').count(), 2, 'Camera and QR entry are distinct targets')
  if (width === 320) {
   await page.setViewportSize({ width, height: 360 })
   await page.locator('.help-panel.is-minimized').waitFor()
   await accessible('[data-help-qr-entry]')
   await guide.getByRole('button', { name: 'Show tip', exact: true }).waitFor()
   await page.setViewportSize({ width, height })
   await guide.getByRole('heading', { name: 'Step 1 / 4: Library ID' }).waitFor()
  }
  await verify('invalid')
  await page.getByText('Invalid library ID.', { exact: true }).waitFor()
  assert.equal(await page.locator('[data-help-qr-entry] input').inputValue(), 'invalid', 'Invalid QR entry retained')
  await guide.getByRole('heading', { name: 'Step 1 / 4: Library ID' }).waitFor()
  await verify('valid-user')
  await guide.getByRole('heading', { name: 'Step 2 / 4: Book QR' }).waitFor()
  assert.equal(writes, 0)
  await guide.getByLabel('Help language').selectOption('fil')
  await guide.getByRole('heading', { name: 'Hakbang 2 / 4: QR ng libro' }).waitFor()
  await guide.getByLabel('Wika ng gabay').selectOption('en')
  await verify('valid-book')
  await guide.getByRole('heading', { name: 'Step 3 / 4: Review' }).waitFor()
  await accessible('[data-help-borrow-confirm]')
  assert.equal(writes, 0, 'Help must never submit')
  await page.locator('[data-help-borrow-confirm]').click()
  await guide.getByRole('heading', { name: 'Step 4 / 4: Receipt' }).waitFor()
  await accessible('[data-help-borrow-finish]')
  assert.equal(writes, 1)
  // Native modal dialogs temporarily own keyboard and visual focus.
  await page.evaluate(() => { const d = document.createElement('dialog'); d.id = 'test-dialog'; d.innerHTML = '<button>Modal action</button>'; document.body.append(d); d.showModal(); d.querySelector('button').focus() })
  assert.equal(await page.locator('.help-layer').isVisible(), false)
  await page.keyboard.press('Escape')
  assert.equal(await page.locator('.help-layer').isVisible(), true)
  assert.equal(await guide.count(), 1, 'Modal Escape must not exit Help')
  await page.keyboard.press('Escape')
  assert.equal(await guide.count(), 0)
  assert.equal(await page.locator('.help-launch').evaluate(el => el === document.activeElement), true)
  await page.getByRole('button', { name: 'Help', exact: true }).click()
  await page.locator('[data-help-end]').click()
  assert.equal(await guide.count(), 0, 'End session closes Help')
  assert.equal(await page.evaluate(() => document.documentElement.style.getPropertyValue('--help-reserved-space')), '')
  assert.deepEqual(errors, [])
  console.log('PASS Help ' + width + 'x' + height + ': 4-stage progress, precise targets, non-overlap, failed QR recovery, English/Filipino, explicit confirmation, modal precedence, Escape and session clearing')
  await page.close()
 }
} finally { await browser.close() }


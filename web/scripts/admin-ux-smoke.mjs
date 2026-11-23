import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

// Every API request is fulfilled here. No backend, account, database or email provider is contacted.
const base = process.env.ADMIN_UI_URL || 'http://127.0.0.1:4190'
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' })
const writes = [], reads = [], errors = []
const user = { id: 7, name: 'Sample Reader', first_name: 'Sample', last_name: 'Reader', student_id: 'TEST-007', course: 'Test course', year_level: '1', email: 'sample@example.invalid', account_status: 'active' }
let emails = [{ id: 31, recipient: 'sample@example.invalid', subject: 'Sample library message', status: 'failed', error: 'Synthetic delivery failure', created_at: '2026-01-02T10:00:00Z', sent_at: null }]
let reservations = [{ id: 19, user_id: 7, user_name: user.name, student_id: user.student_id, book_title: 'Sample reservation', status: 'active' }]
let fines = [{ id: 8, user_id: 7, book_title: 'Sample fine book', amount: 12.5, status: 'unpaid' }]
const loans = Array.from({ length: 21 }, (_, index) => ({ id: index + 1, transaction_id: `BOR-${String(index + 1).padStart(8, '0')}`, user_name: index ? `Sample Reader ${index}` : 'Zebra Reader', student_id: `TEST-${index}`, book_title: `Sample book ${index}`, due_at: '2020-01-01T00:00:00Z', status: 'active' }))
await context.route('**/*', async route => {
  const request = route.request(), url = new URL(request.url())
  const headers = { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'authorization,content-type', 'access-control-allow-methods': 'GET,POST,PUT,DELETE,OPTIONS' }
  if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers })
  if (url.pathname === '/health') return route.fulfill({ json: { status: 'healthy' }, headers })
  if (!url.pathname.startsWith('/api/v1/')) {
    if (url.origin === new URL(base).origin) return route.continue()
    throw Error(`Blocked unexpected request to ${url.origin}`)
  }
  const path = url.pathname.slice('/api/v1'.length)
  const write = request.method() !== 'GET'
  ;(write ? writes : reads).push(`${request.method()} ${path}${url.search}`)
  let result
  if (path === '/auth/login') result = { access_token: 'mock-only-token', user: { id: 1, name: 'Test Staff', role: 'SUPER_ADMIN' } }
  else if (path === '/admin/dashboard') result = { total_books: 10, available_copies: 5, borrowed_copies: 21, overdue_borrowings: 21, failed_email_deliveries: 1 }
  else if (path === '/users') result = { items: url.searchParams.get('status') === 'PENDING' ? [{ ...user, account_status: 'pending' }] : [user], total: url.searchParams.get('status') === 'PENDING' ? 3 : 1 }
  else if (path === '/borrowings') { const offset = Number(url.searchParams.get('offset') || 0); result = { items: loans.slice(offset, offset + 20), total: loans.length } }
  else if (path === '/notifications/admin/email-deliveries') { const status = url.searchParams.get('status'); const filtered = emails.filter(row => !status || row.status === status); result = { items: filtered, total: filtered.length } }
  else if (path === '/notifications/admin/email-deliveries/31/retry') { emails = [{ ...emails[0], status: 'pending', error: null }]; result = { message: 'Synthetic retry queued.' } }
  else if (path === '/notifications/admin/email-deliveries/31/send') { emails = [{ ...emails[0], status: 'sent' }]; result = { message: 'Synthetic send accepted.' } }
  else if (path === '/users/7/email-qr') result = { message: 'Synthetic QR email queued.' }
  else if (path === '/fines') result = { items: fines, total: fines.length }
  else if (path === '/fines/8/pay') { fines = [{ ...fines[0], status: 'paid' }]; result = fines[0] }
  else if (path === '/reservations' && !write) result = { items: reservations, total: reservations.length }
  else if (path === '/reservations/19' && request.method() === 'DELETE') { reservations = []; result = { status: 'cancelled' } }
  else throw Error(`Unmocked API request: ${request.method()} ${path}`)
  return route.fulfill({ json: result, headers })
})
const page = await context.newPage()
page.on('pageerror', error => errors.push(error.message))
page.on('dialog', () => { throw Error('Native window.confirm must not appear') })
async function navigate(name) {
  if (await page.getByRole('button', { name: 'Menu', exact: true }).isVisible()) await page.getByRole('button', { name: 'Menu', exact: true }).click()
  await page.getByRole('navigation', { name: 'Admin sections' }).getByRole('button', { name, exact: true }).click()
}
async function assertCancel(button, title, text) {
  const count = writes.length
  await button.click()
  const dialog = page.getByRole('dialog', { name: title })
  await dialog.waitFor()
  assert.match(await dialog.innerText(), text)
  assert.equal(writes.length, count, 'Opening confirmation must not mutate')
  await page.keyboard.press('Escape')
  await dialog.waitFor({ state: 'hidden' })
  assert.equal(writes.length, count, 'Escape must cancel without mutation')
  assert.ok(await button.evaluate(element => element === document.activeElement), 'Cancel restores action focus')
}
try {
  await page.goto(`${base}/admin`)
  await page.getByLabel('Username or email').fill('mock-staff')
  await page.getByLabel('Password', { exact: true }).fill('mock-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  const attention = page.getByRole('region', { name: 'Needs attention' })
  await attention.getByRole('button', { name: /3 Pending registrations/ }).waitFor()
  assert.match(await attention.innerText(), /3\s*Pending registrations/)
  await attention.getByRole('button', { name: /Pending registrations/ }).click()
  assert.equal(await page.getByRole('button', { name: 'Pending registrations', exact: true }).getAttribute('aria-pressed'), 'true')
  assert.ok(reads.some(path => /\/users\?.*status=PENDING/.test(path)))
  await navigate('Overview')
  await attention.getByRole('button', { name: /Overdue loans/ }).click()
  assert.ok(reads.some(path => /\/borrowings\?.*overdue=true/.test(path)))
  await page.getByRole('navigation', { name: 'Record pages' }).getByRole('button', { name: 'Next' }).click()
  await page.getByText('21–21 of 21', { exact: true }).waitFor()
  assert.ok(await page.getByRole('navigation', { name: 'Record pages' }).getByRole('button', { name: 'Next' }).isDisabled())
  await page.getByLabel('Filter records by status').selectOption('active')
  await page.getByText('1–20 of 21', { exact: true }).waitFor()
  await page.getByLabel('Sort this page', { exact: true }).selectOption('user_name:asc')
  assert.equal(await page.locator('tbody tr').first().locator('td').nth(1).innerText(), 'Sample Reader 1')
  await page.getByLabel('Find on this page').fill('Zebra')
  assert.equal(await page.locator('tbody tr').count(), 1)
  await navigate('Overview')
  await attention.getByRole('button', { name: /Failed emails/ }).click()
  assert.equal(await page.getByLabel('Filter records by status').inputValue(), 'failed')
  const retry = page.getByRole('button', { name: 'Retry email #31 to sample@example.invalid', exact: true })
  await assertCancel(retry, 'Queue this email for retry?', /sample@example.invalid/)
  await retry.click()
  await page.getByRole('dialog').getByRole('button', { name: 'Queue retry', exact: true }).click()
  await page.getByText('Synthetic retry queued.', { exact: true }).waitFor()
  assert.equal(writes.filter(path => path.includes('/retry')).length, 1)
  assert.equal(writes.filter(path => path.includes('/send')).length, 0, 'Retry must not invoke send endpoint')
  await page.getByLabel('Filter records by status').selectOption('pending')
  const send = page.getByRole('button', { name: 'Send now email #31 to sample@example.invalid', exact: true })
  await assertCancel(send, 'Send this email now?', /Sample library message/)
  await send.click()
  await page.getByRole('dialog').getByRole('button', { name: 'Send email now' }).click()
  await page.getByText('Synthetic send accepted.', { exact: true }).waitFor()
  assert.equal(writes.filter(path => path.includes('/send')).length, 1)
  await navigate('Library users')
  const emailQr = page.getByRole('button', { name: 'Email QR to Sample Reader', exact: true })
  await assertCancel(emailQr, 'Email this member’s library QR?', /TEST-007/)
  await emailQr.click()
  await page.getByRole('dialog').getByRole('button', { name: 'Queue QR email' }).click()
  await page.getByText('Synthetic QR email queued.', { exact: true }).waitFor()
  await navigate('Fines')
  const pay = page.getByRole('button', { name: 'Mark paid record #8' })
  await assertCancel(pay, 'Mark this fine as paid?', /PHP 12.50/)
  await pay.click()
  await page.getByRole('dialog').getByRole('button', { name: 'Confirm payment received' }).click()
  await page.getByText('Fine #8 marked paid.', { exact: true }).waitFor()
  await navigate('Reservations')
  const cancel = page.getByRole('button', { name: 'Cancel record #19', exact: true })
  await assertCancel(cancel, 'Cancel this reservation?', /Sample Reader/)
  await cancel.click()
  await page.getByRole('dialog').getByRole('button', { name: 'Cancel reservation' }).click()
  await page.getByText('0 records', { exact: true }).first().waitFor()
  for (const width of [768, 390]) {
    await page.setViewportSize({ width, height: 900 })
    await navigate('Email deliveries')
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width)
    assert.ok(await page.getByRole('region', { name: 'Records table, scroll horizontally for all columns' }).isVisible())
  }
  assert.deepEqual(errors, [])
  console.log('PASS admin attention links, filters, sorting, search, accurate pagination, keyboard cancellation/focus, explicit QR/email/retry/payment/reservation confirmations, and tablet/mobile containment. All API traffic mocked; no live writes or delivery.')
} finally { await browser.close() }

import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
const base = process.env.DESIGN_UI_URL || 'http://127.0.0.1:4190'
const user = { id: 7, student_id: 'PREVIEW-7', display_name: 'Preview borrower', verification_token: 'preview-user-grant' }
const book = { id: 3, book_id: 2, book_copy_id: 3, title: 'Preview library book', accession_number: 'COPY-003', verification_token: 'preview-book-grant' }

try {
  for (const [width, height] of [[320, 740], [414, 896], [600, 960], [768, 1024], [1024, 768]]) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' })
    const errors = []
    let borrowCount = 0
    let finishBorrow
    let borrowBody
    page.on('pageerror', error => errors.push(error.message))
    // Intercept every API call, including writes. Never change real library records.
    await page.route(/\/health$|\/api\/v1\//, async route => {
      const path = new URL(route.request().url()).pathname
      if (path === '/health') return route.fulfill({ json: { status: 'healthy' } })
      const body = route.request().postDataJSON()
      if (path === '/api/v1/qr/verify-user') {
        if (body.token === 'invalid') return route.fulfill({ status: 400, json: { detail: 'Invalid library ID.' } })
        return route.fulfill({ json: user })
      }
      if (path === '/api/v1/qr/verify-book') return route.fulfill({ json: { ...book, available: body.token !== 'unavailable' } })
      if (path === '/api/v1/borrowings') {
        borrowCount++
        borrowBody = body
        await new Promise(resolve => { finishBorrow = resolve })
        return route.fulfill({ json: { id: 1, book_title: book.title, due_at: '2026-11-01T12:00:00Z', status: 'BORROWED' } })
      }
      throw new Error(`Unexpected API call: ${path}`)
    })
    async function fits() {
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width, `Horizontal overflow at ${width}`)
    }
    async function verify(value) {
      await page.getByLabel('QR code', { exact: true }).fill(value)
      await page.getByRole('button', { name: 'Verify', exact: true }).click()
    }
    await page.goto(base)
    await page.getByRole('button', { name: 'Borrow a book', exact: true }).click()
    await page.getByRole('heading', { name: 'Scan your library ID', exact: true }).waitFor()
    await page.evaluate(() => document.fonts.ready)
    assert.equal(await page.locator('.transaction-progress li').count(), 3)
    assert.equal(await page.locator('.borrow-step-summary').count(), 2)
    await fits()
    if ([414, 600, 768].includes(width)) await page.screenshot({ path: `../docs/design_previews/borrow-reference-${width}.png`, fullPage: true })
    if (width === 600 || width === 768) assert.ok(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight + 1), 'Portrait tablet first step must fit')
    await verify('invalid')
    await page.getByText('Invalid library ID.', { exact: true }).waitFor()
    await page.getByRole('heading', { name: 'Scan your library ID', exact: true }).waitFor()
    await verify('valid-user')
    await page.getByRole('heading', { name: 'Scan a book', exact: true }).waitFor()
    await page.getByText(user.display_name, { exact: true }).waitFor()
    await fits()
    await verify('unavailable')
    await page.getByRole('heading', { name: 'Review your borrowing', exact: true }).waitFor()
    assert.equal(await page.getByRole('button', { name: 'Confirm borrowing' }).isDisabled(), true)
    assert.equal(borrowCount, 0)
    await fits()
    await page.getByRole('button', { name: 'Change book', exact: true }).click()
    await verify('available')
    await page.getByRole('heading', { name: 'Review your borrowing', exact: true }).waitFor()
    assert.equal(borrowCount, 0, 'Scanning must never borrow without confirmation')
    if (width === 768) await page.screenshot({ path: '../docs/design_previews/borrow-review-768.png', fullPage: true })
    await page.getByRole('button', { name: 'Confirm borrowing', exact: true }).click()
    await page.getByRole('button', { name: 'Processing…', exact: true }).waitFor()
    assert.equal(await page.getByRole('button', { name: 'Processing…', exact: true }).isDisabled(), true)
    finishBorrow()
    await page.getByRole('heading', { name: 'Borrowing complete', exact: true }).waitFor()
    assert.equal(borrowCount, 1)
    assert.deepEqual(borrowBody, { user_id: 7, book_copy_id: 3, user_verification_token: user.verification_token, book_verification_token: book.verification_token })
    await fits()
    await page.getByRole('button', { name: 'Finish and clear session' }).click()
    await page.getByRole('button', { name: 'Borrow a book', exact: true }).click()
    await page.getByRole('heading', { name: 'Scan your library ID', exact: true }).waitFor()
    await verify('valid-user')
    await page.getByRole('button', { name: 'Change library ID', exact: true }).click()
    await page.getByRole('heading', { name: 'Scan your library ID', exact: true }).waitFor()
    await page.getByRole('button', { name: 'Home', exact: true }).click()
    await page.getByRole('button', { name: 'Borrow a book', exact: true }).click()
    await page.getByRole('heading', { name: 'Scan your library ID', exact: true }).waitFor()
    assert.deepEqual(errors, [])
    console.log(`PASS ${width}x${height}: layout, invalid QR, verification grants, unavailable copy, explicit confirmation, receipt, session clear`)
    await page.close()
  }
} finally { await browser.close() }

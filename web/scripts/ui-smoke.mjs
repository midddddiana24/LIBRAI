import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const base = process.env.UI_SMOKE_URL || 'http://127.0.0.1:4173'
const userQr = process.env.UI_SMOKE_USER_QR
const bookQr = process.env.UI_SMOKE_BOOK_QR

if (!base.startsWith('http://127.0.0.1:') || !userQr || !bookQr || process.env.UI_SMOKE_ALLOW_WRITE !== '1') {
  throw new Error('Use an isolated localhost backend and set UI_SMOKE_ALLOW_WRITE=1 plus UI_SMOKE_USER_QR and UI_SMOKE_BOOK_QR.')
}

const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
try {
  const page = await browser.newPage({ viewport: { width: 800, height: 1280 } })
  await page.goto(base)
  await page.getByRole('button', { name: /Borrow a book/ }).click()
  await page.locator('input[type=password]').first().fill(userQr)
  await page.locator('.scan-panel').first().getByRole('button', { name: 'Verify' }).click()
  await page.getByText('Verified: Test Reader').waitFor()
  await page.locator('input[type=password]').last().fill(bookQr)
  await page.locator('.scan-panel').last().getByRole('button', { name: 'Verify' }).click()
  await page.getByText(/Verified: Library Integration Guide/).waitFor()
  await page.getByRole('button', { name: 'Confirm borrowing' }).click()
  await page.getByText('Borrowing complete').waitFor()
  assert.match(await page.locator('.success').innerText(), /Due:/)

  await page.getByRole('button', { name: 'Finish and clear session' }).click()
  await page.getByRole('button', { name: /Return a book/ }).click()
  await page.locator('input[type=password]').fill(bookQr)
  await page.getByRole('button', { name: 'Verify' }).click()
  await page.getByText('Borrower: Test Reader').waitFor()
  await page.getByRole('button', { name: 'Confirm return' }).click()
  await page.getByText('Return complete').waitFor()
  console.log('Kiosk browser smoke passed: borrow and return via FastAPI.')
} finally { await browser.close() }

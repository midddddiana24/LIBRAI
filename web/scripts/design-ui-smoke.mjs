import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const base = process.env.DESIGN_UI_URL || 'http://127.0.0.1:4190'
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
const staff = { id: 1, name: 'Library staff', role: 'SUPER_ADMIN' }
const book = { id: 1, title: 'Preview title', author: 'Preview author', isbn: 'PREVIEW', available_copies: 2 }
const dashboard = { total_books: 6, available_copies: 10, borrowed_copies: 1, overdue_borrowings: 0, registered_users: 2, active_reservations: 0, transactions_today: 1, renewals_today: 0 }

async function fits(page, width, height, tabletHome = false) {
  await page.evaluate(() => document.fonts.ready)
  const size = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight }))
  assert.equal(size.width, width, `Horizontal overflow at ${width}`)
  if (tabletHome) assert.ok(size.height <= height + 1, `Tablet home scrolls at ${width}x${height}`)
}

async function snapshot(page, filename) {
  if (!process.env.DESIGN_SCREENSHOTS) return
  await page.mouse.move(0, 0)
  await page.evaluate(() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur() })
  await page.evaluate(() => new Promise(resolve => { window.scrollTo(0, 0); requestAnimationFrame(() => requestAnimationFrame(resolve)) }))
  await page.screenshot({ path: `../docs/design_previews/${filename}.png`, fullPage: true })
}

try {
  for (const [width, height] of [[320, 740], [375, 812], [414, 896], [600, 960], [768, 1024], [960, 600], [1024, 768], [1440, 1000]]) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' })
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    // All API requests are intercepted: this check never writes to a live library.
    await page.route(/\/health$|\/api\/v1\//, route => {
      const path = new URL(route.request().url()).pathname
      const json = path === '/health' ? { status: 'healthy' }
        : path === '/api/v1/auth/login' ? { access_token: 'layout-check-only', user: staff }
          : path === '/api/v1/auth/me' ? staff
            : path === '/api/v1/admin/dashboard' ? dashboard
              : path === '/api/v1/ai/recommend' ? [book]
                : path === '/api/v1/books' || path === '/api/v1/search/books' ? { items: [book], total: 1 }
                  : path === '/api/v1/settings' ? { borrowing_limit: '3' }
                    : { items: [], total: 0 }
      return route.fulfill({ json })
    })
    await page.goto(base)
    await page.getByRole('button', { name: 'Borrow a book', exact: true }).waitFor()
    await fits(page, width, height, width >= 600)
    assert.equal(await page.locator('.kiosk-menu-screen').evaluate(el => getComputedStyle(el).borderWidth), '0px')
    if (width === 768 || width === 1024) await snapshot(page, `modern-kiosk-${width}`)
    for (const [action, heading] of [['Borrow a book', 'Borrow a book'], ['Return a book', 'Return a book'], ['Find a book', 'Find a book'], ['Discover books', 'Explore titles']]) {
      await page.getByRole('button', { name: action, exact: true }).click()
      await page.getByRole('heading', { name: heading, exact: true }).waitFor()
      await fits(page, width, height)
      if (width === 768 && action === 'Borrow a book') await snapshot(page, 'modern-borrow-768')
      await page.getByRole('button', { name: 'End session', exact: true }).click()
    }
    await page.goto(`${base}/admin`)
    await page.locator('#username').waitFor()
    await page.evaluate(() => document.fonts.ready)
    if (width === 1440) await snapshot(page, 'modern-admin-login')
    await fits(page, width, height)
    async function signIn() {
      await page.locator('#username').fill('layout-check')
      await page.locator('#password').fill('layout-check-only')
      await page.getByRole('button', { name: 'Sign in', exact: true }).click()
      await page.locator('.admin-content[aria-busy="false"]').waitFor()
      await page.getByRole('heading', { name: 'Library dashboard', exact: true }).waitFor()
    }
    async function openNavigation() {
      if (width <= 900) {
        await page.getByRole('button', { name: 'Menu', exact: true }).click()
        assert.equal(await page.getByRole('button', { name: 'Close menu' }).getAttribute('aria-expanded'), 'true')
      }
    }
    await signIn()
    await fits(page, width, height)
    if (width === 1440 || width === 375) await snapshot(page, `modern-admin-${width}`)
    await openNavigation()
    await fits(page, width, height)
    await page.getByRole('navigation', { name: 'Admin sections' }).getByRole('button', { name: 'Catalog', exact: true }).click()
    await page.locator('.admin-content[aria-busy="false"]').waitFor()
    await page.getByRole('heading', { name: 'Catalog', exact: true }).waitFor()
    if (width <= 900) assert.equal(await page.locator('#staff-navigation').isVisible(), false)
    await page.getByRole('button', { name: 'Add book', exact: true }).click()
    await page.getByRole('heading', { name: 'Add book', exact: true }).waitFor()
    await fits(page, width, height)
    if (width === 1440) await snapshot(page, 'modern-admin-catalog')
    await page.getByRole('button', { name: 'Cancel', exact: true }).click()
    await openNavigation()
    await page.getByRole('button', { name: 'Sign out', exact: true }).click()
    await page.locator('#username').waitFor()
    await signIn()
    assert.deepEqual(errors, [])
    console.log(`PASS ${width}x${height}: kiosk actions, staff menu, catalog form, sign-out/sign-in, overflow`)
    await page.close()
  }
  const motionPage = await browser.newPage({ viewport: { width: 768, height: 1024 }, reducedMotion: 'no-preference' })
  await motionPage.route(/\/health$/, route => route.fulfill({ json: { status: 'healthy' } }))
  await motionPage.goto(base)
  await motionPage.getByRole('button', { name: 'Borrow a book', exact: true }).waitFor()
  await motionPage.waitForFunction(() => [...document.querySelectorAll('.kiosk-task')].every(el => getComputedStyle(el).opacity === '1' && getComputedStyle(el).transform === 'none'))
  await motionPage.emulateMedia({ reducedMotion: 'reduce' })
  await motionPage.getByRole('button', { name: 'Return a book', exact: true }).hover()
  assert.equal(await motionPage.locator('.kiosk-task-return .kiosk-task-icon').evaluate(el => getComputedStyle(el).transform), 'none')
  console.log('PASS screen entry settles; reduced motion disables spatial hover effects')
  await motionPage.close()
} finally { await browser.close() }

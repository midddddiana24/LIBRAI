import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const base = process.env.DESIGN_UI_URL || 'http://127.0.0.1:4190'
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
try {
  for (const [width, height] of [[320, 740], [375, 812], [414, 896], [600, 960], [768, 1024], [960, 600]]) {
    const page = await browser.newPage({ viewport: { width, height } })
    await page.addInitScript(() => {
      window.__startupStates = []
      new MutationObserver(() => {
        const state = document.querySelector('.startup-screen')?.className
        if (state && window.__startupStates.at(-1) !== state) window.__startupStates.push(state)
      }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] })
    })
    let release
    await page.route('**/health', async route => {
      await new Promise(resolve => { release = resolve })
      await route.fulfill({ json: { status: 'healthy' } })
    })
    await page.goto(base)
    await page.getByText('Connecting to your library…', { exact: true }).waitFor()
    await page.locator('.startup-book > img').evaluate(image => image.decode())
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width)
    assert.ok(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight + 1))
    if (width === 768) await page.screenshot({ path: '../generated/startup-1.7-tablet.png' })
    assert.ok(release)
    release()
    await page.getByRole('button', { name: 'Borrow a book', exact: true }).waitFor()
    assert.ok(await page.evaluate(() => window.__startupStates.some(state => state.includes('startup-ready'))), 'Ready state occurred before home')
    console.log(`PASS startup ${width}x${height}: book asset, connection, ready, home, overflow`)
    await page.close()
  }
  const page = await browser.newPage({ viewport: { width: 768, height: 1024 }, reducedMotion: 'reduce' })
  let attempt = 0
  await page.route('**/health', route => route.fulfill({ status: ++attempt === 1 ? 503 : 200, json: { status: attempt === 1 ? 'unavailable' : 'healthy' } }))
  await page.goto(base)
  await page.getByRole('button', { name: 'Try again', exact: true }).waitFor()
  assert.equal(await page.locator('.startup-book').evaluate(el => getComputedStyle(el).animationName), 'none')
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await page.getByRole('button', { name: 'Borrow a book', exact: true }).waitFor()
  console.log('PASS startup offline → retry → home; reduced motion')
  await page.close()
} finally { await browser.close() }

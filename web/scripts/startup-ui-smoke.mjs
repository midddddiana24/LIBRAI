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
    await page.locator('.startup-cover-front img').evaluate(image => image.decode())
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
  for (const failure of ['delayed', 'missing']) {
    const p = await browser.newPage({ viewport: { width: 768, height: 1024 } })
    await p.route('**/health', route => route.fulfill({ json: { status: 'healthy' } }))
    let releaseImage
    await p.route('**/librai-symbol-v2.png', async route => {
      if (failure === 'missing') return route.abort()
      await new Promise(resolve => { releaseImage = resolve })
      await route.continue()
    })
    await p.goto(base, { waitUntil: 'domcontentloaded' })
    if (failure === 'delayed') {
      await p.locator('.startup-art-loading .startup-cover-front .startup-logo-fallback').waitFor()
      assert.equal(await p.getByRole('button', { name: 'Borrow a book', exact: true }).count(), 0)
      assert.ok(releaseImage)
      releaseImage()
    }
    const art = p.locator(failure === 'missing' ? '.startup-art-fallback' : '.startup-art-ready')
    await art.waitFor()
    const start = Date.now()
    await p.getByRole('button', { name: 'Borrow a book', exact: true }).waitFor()
    assert.ok(Date.now() - start >= 1000, 'Book must finish opening after artwork resolves')
    console.log('PASS startup ' + failure + ' image: visible fallback and complete opening before Home')
    await p.close()
  }
  const reveal = await browser.newPage({ viewport: { width: 768, height: 1024 } })
  await reveal.addInitScript(() => {
    window.__revealTiming = {}
    new MutationObserver(() => {
      if (document.querySelector('.startup-ready')) window.__revealTiming.ready ??= performance.now()
      if (document.querySelector('.kiosk-menu')) window.__revealTiming.home ??= performance.now()
    }).observe(document, { subtree: true, childList: true, attributes: true })
  })
  await reveal.route('**/health', route => route.fulfill({ json: { status: 'healthy' } }))
  await reveal.goto(base, { waitUntil: 'domcontentloaded' })
  await reveal.locator('.startup-art-ready').waitFor()
  assert.equal(await reveal.locator('.startup-cover-front').count(), 1)
  assert.equal(await reveal.locator('.startup-cover-inside').count(), 1)
  assert.equal(await reveal.locator('.startup-page').count(), 2)
  assert.equal(await reveal.locator('.startup-book').evaluate(el => getComputedStyle(el).transformStyle), 'preserve-3d')
  assert.equal(await reveal.locator('.startup-book').evaluate(el => getComputedStyle(el).opacity), '1', 'Do not flatten the 3D book with parent opacity')
  const initial = await reveal.locator('.startup-page-two').evaluate(el => getComputedStyle(el).transform)
  await reveal.waitForTimeout(800)
  assert.notEqual(await reveal.locator('.startup-page-two').evaluate(el => getComputedStyle(el).transform), initial)
  await reveal.screenshot({ path: '../generated/startup-3d-book-fixed.png' })
  await reveal.locator('.startup-ready').waitFor()
  assert.ok(await reveal.locator('.startup-ready-logo').evaluate(el => el.complete && el.naturalWidth > 0))
  await reveal.getByRole('button', { name: 'Borrow a book', exact: true }).waitFor()
  assert.ok(await reveal.evaluate(() => window.__revealTiming.home - window.__revealTiming.ready >= 1150), 'Allow the 3D logo reveal and visible hold to finish')
  console.log('PASS actual 3D book faces/page motion, unflattened parent, decoded logo and full reveal hold')
  await reveal.close()
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

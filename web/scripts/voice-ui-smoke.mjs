import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const base = process.env.VOICE_UI_URL || 'http://127.0.0.1:4173'
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
try {
  const page = await browser.newPage({ viewport: { width: 800, height: 1280 } })
  await page.addInitScript(() => {
    let transcript = 'borrow a book'
    Object.defineProperty(window, '__setFakeTranscript', { value: value => { transcript = value } })
    window.__spoken = []
    Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { cancel() {}, speak(utterance) { window.__spoken.push(utterance.text) } } })
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text } }
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) },
    })
    window.MediaRecorder = class {
      static isTypeSupported() { return true }
      state = 'inactive'
      mimeType = 'audio/webm;codecs=opus'
      start() { this.state = 'recording' }
      stop() {
        this.state = 'inactive'
        this.ondataavailable?.({ data: new Blob([transcript], { type: 'audio/webm' }) })
        this.onstop?.()
      }
    }
  })
  let transcriptions = 0
  let borrowingPosts = 0
  await page.route('http://127.0.0.1:8000/**', async route => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (path === '/health') return route.fulfill({ json: { status: 'ok' } })
    if (path === '/api/v1/speech/transcribe') {
      transcriptions++
      const body = request.postDataBuffer()?.toString() || ''
      assert.match(body, /name="audio"/)
      return route.fulfill({ json: { text: body.includes('history books') ? 'history books' : 'borrow a book' } })
    }
    if (path === '/api/v1/ai/search') return route.fulfill({ json: { answer: 'Try the library history shelf.', books: [] } })
    if (path === '/api/v1/borrowings' && request.method() === 'POST') borrowingPosts++
    return route.fulfill({ status: 404, json: { detail: 'Test route not available.' } })
  })
  await page.goto(base)
  await page.getByRole('button', { name: 'Voice command' }).click()
  await page.getByRole('button', { name: 'Stop recording' }).click()
  await page.getByRole('heading', { name: 'Borrow a book' }).waitFor()
  assert.equal(borrowingPosts, 0)
  await page.getByRole('button', { name: 'End session' }).first().click()
  await page.getByRole('button', { name: 'Ask LIBRAI' }).click()
  await page.evaluate(() => window.__setFakeTranscript('history books'))
  await page.getByRole('button', { name: 'Dictate question' }).click()
  await page.getByRole('button', { name: 'Stop recording' }).click()
  await page.waitForFunction(() => document.querySelector('#ai-query')?.value === 'history books')
  assert.equal(await page.getByRole('textbox', { name: 'What would you like to read?' }).inputValue(), 'history books')
  await page.getByRole('button', { name: 'Ask', exact: true }).click()
  await page.getByText('Try the library history shelf.').waitFor()
  await page.getByRole('button', { name: 'Read answer aloud' }).click()
  assert.deepEqual(await page.evaluate(() => window.__spoken), ['Try the library history shelf.'])
  await page.setViewportSize({ width: 390, height: 844 })
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), true)
  assert.equal(transcriptions, 2)
  console.log('Voice UI smoke passed: command navigation, dictation, and read-aloud control.')
} finally { await browser.close() }

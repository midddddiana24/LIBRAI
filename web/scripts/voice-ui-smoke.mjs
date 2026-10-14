import assert from 'node:assert/strict'
import { chromium } from 'playwright-core'

const base = process.env.VOICE_UI_URL || 'http://127.0.0.1:4173'
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
try {
  const page = await browser.newPage({ viewport: { width: 800, height: 1280 } })
  await page.addInitScript(() => {
    let transcript = 'borrow a book'
    Object.defineProperty(window, '__setFakeTranscript', { value: value => { transcript = value } })
    window.__fakeSilence = false
    window.__spoken = []
    Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { cancel() {}, resume() {}, speak(utterance) { window.__spoken.push(utterance.text) } } })
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text } }
    window.AudioContext = class {
      async decodeAudioData() {
        return { numberOfChannels: 1, sampleRate: 16000, getChannelData: () => Float32Array.from({ length: 16000 }, () => window.__fakeSilence ? 0 : 0.02) }
      }
      async close() {}
    }
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
  // The same UI is built for localhost in development and HTTPS in the APK.
  // Intercept API paths regardless of the compiled origin.
  await page.route(/\/health$|\/api\/v1\//, async route => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    if (path === '/health') return route.fulfill({ json: { status: 'ok' } })
    if (path === '/api/v1/speech/transcribe') {
      transcriptions++
      const body = request.postDataBuffer()?.toString() || ''
      assert.match(body, /name="audio"/)
      return route.fulfill({ json: { text: body.includes('history books') ? 'history books' : body.includes('hello') ? 'hello' : 'borrow a book' } })
    }
    if (path === '/api/v1/ai/search') return route.fulfill({ json: { answer: 'Try the library history shelf.', books: [] } })
    if (path === '/api/v1/borrowings' && request.method() === 'POST') borrowingPosts++
    return route.fulfill({ status: 404, json: { detail: 'Test route not available.' } })
  })
  await page.goto(base)
  await page.getByRole('button', { name: 'Hear instructions' }).click()
  assert.match((await page.evaluate(() => window.__spoken))[0], /Welcome to LIBRAI/)
  await page.evaluate(() => { window.__fakeSilence = true })
  await page.getByRole('button', { name: 'Voice command' }).click()
  await page.getByRole('button', { name: 'Stop recording' }).click()
  await page.getByText(/No clear sound was recorded/).waitFor()
  assert.equal(transcriptions, 0)
  await page.evaluate(() => { window.__fakeSilence = false })
  await page.getByRole('button', { name: 'Voice command' }).click()
  await page.getByRole('button', { name: 'Stop recording' }).click()
  await page.getByRole('button', { name: 'Run command' }).waitFor()
  await page.getByRole('button', { name: 'Run command' }).click()
  await page.getByRole('heading', { name: 'Borrow a book' }).waitFor()
  assert.equal(borrowingPosts, 0)
  await page.getByRole('button', { name: 'End session' }).first().click()
  await page.evaluate(() => window.__setFakeTranscript('hello'))
  await page.getByRole('button', { name: 'Voice command' }).click()
  await page.getByRole('button', { name: 'Stop recording' }).click()
  await page.getByRole('textbox', { name: 'Words heard' }).fill('return a book')
  await page.getByRole('button', { name: 'Run command' }).click()
  await page.getByRole('heading', { name: 'Return a book' }).waitFor()
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
  assert.equal((await page.evaluate(() => window.__spoken)).at(-1), 'Try the library history shelf.')
  await page.setViewportSize({ width: 390, height: 844 })
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), true)
  assert.equal(transcriptions, 3)
  console.log('Voice UI smoke passed: command navigation, dictation, and read-aloud control.')
} finally { await browser.close() }

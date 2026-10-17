import type { Worker, PSM } from 'tesseract.js'
import { parseIdCard, type IdDraft } from './idCardFields'

function textStrip(source: HTMLCanvasElement, x: number, y: number, width: number, height: number, threshold: number) {
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(source.width * width); canvas.height = Math.round(source.height * height)
  const context = canvas.getContext('2d')!
  context.drawImage(source, source.width * x, source.height * y, source.width * width, source.height * height, 0, 0, canvas.width, canvas.height)
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height)
  for (let i = 0; i < pixels.data.length; i += 4) {
    const grey = .299 * pixels.data[i] + .587 * pixels.data[i + 1] + .114 * pixels.data[i + 2]
    pixels.data[i] = pixels.data[i + 1] = pixels.data[i + 2] = grey < threshold ? 0 : 255
  }
  context.putImageData(pixels, 0, 0)
  return canvas
}

export async function recoverCampusText(worker: Worker, canvas: HTMLCanvasElement, alive: () => boolean): Promise<IdDraft> {
  // shortcut: These regions target a tightly framed portrait campus card; other layouts need manual input.
  const ratio = canvas.height / canvas.width
  if (ratio < 1.4 || ratio > 1.8 || !alive()) return {}
  try {
    await worker.setParameters({ tessedit_pageseg_mode: '7' as PSM, tessedit_char_whitelist: '0123456789-' })
    const number = await worker.recognize(textStrip(canvas, .36, .685, .35, .05, 80), { rotateAuto: true })
    if (!alive() || number.data.confidence < 80 || !/^\d{2}-\d{3,8}$/.test(number.data.text.trim())) return {}
    const id = number.data.text.trim()
    await worker.setParameters({ tessedit_char_whitelist: '' })
    const readings: IdDraft[] = []
    for (const threshold of [80, 100]) {
      const name = await worker.recognize(textStrip(canvas, .01, .74, .98, .055, threshold), { rotateAuto: true })
      if (!alive()) return {}
      if (name.data.confidence >= 75) readings.push(parseIdCard(`${id}\n${name.data.text.trim()}`, 'campus'))
    }
    const [first, second] = readings
    // Keep the number, but leave an uncertain name for the student to type.
    return first?.first_name && second?.first_name === first.first_name && second.last_name === first.last_name
      ? first : { student_id: id }
  } finally {
    await worker.setParameters({ tessedit_char_whitelist: '' }).catch(() => undefined)
  }
}

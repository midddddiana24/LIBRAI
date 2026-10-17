import { copyFile, mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../', import.meta.url))
const out = resolve(root, 'public/ocr')
await mkdir(out, { recursive: true })
const assets = {
  'worker.min.js': 'tesseract.js/dist/worker.min.js',
  'eng.traineddata.gz': '@tesseract.js-data/eng/4.0.0_best_int/eng.traineddata.gz',
}
// The app uses the LSTM-only engine; include CPU, SIMD and relaxed-SIMD variants.
for (const flavor of ['lstm', 'simd-lstm', 'relaxedsimd-lstm']) {
  assets[`tesseract-core-${flavor}.wasm.js`] = `tesseract.js-core/tesseract-core-${flavor}.wasm.js`
}
for (const [name, source] of Object.entries(assets)) await copyFile(resolve(root, 'node_modules', source), resolve(out, name))
console.log('Prepared local OCR worker, engine, and English model; no CDN required.')

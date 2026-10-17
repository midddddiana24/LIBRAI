import { useEffect, useRef, useState } from 'react'
import { Camera, LoaderCircle, ScanText, Upload } from 'lucide-react'
import type { Worker } from 'tesseract.js'
import { parseIdCard, type CardKind, type IdDraft } from './idCardFields'

const labels: Record<keyof IdDraft, string> = { student_id: 'Campus student ID', library_card_number: 'Library card number', first_name: 'First name / middle initial', last_name: 'Last name / suffix', course: 'Course' }

export default function IdScanPanel({ onApply, disabled }: { onApply: (draft: IdDraft) => void; disabled: boolean }) {
  const [kind, setKind] = useState<CardKind>('campus')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [draft, setDraft] = useState<IdDraft | null>(null)
  const [preview, setPreview] = useState('')
  const workerRef = useRef<Worker | null>(null)
  const generation = useRef(0)
  const camera = useRef<HTMLInputElement>(null)
  const upload = useRef<HTMLInputElement>(null)
  useEffect(() => () => { generation.current++; void workerRef.current?.terminate().catch(() => undefined) }, [])
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  function clear() {
    generation.current++
    void workerRef.current?.terminate().catch(() => undefined)
    workerRef.current = null
    setBusy(false); setDraft(null); setPreview(''); setMessage('')
  }

  async function read(file: File) {
    if (busy || disabled) return
    const current = ++generation.current
    const alive = () => generation.current === current
    setDraft(null); setPreview(''); setMessage('Reading on this device...'); setBusy(true)
    let worker: Worker | null = null
    try {
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024) throw Error('Choose a JPEG, PNG, or WebP photo smaller than 10 MB.')
      const image = await createImageBitmap(file)
      if (image.width * image.height > 40_000_000) { image.close(); throw Error('Photo dimensions are too large. Take a smaller photo.') }
      const scale = Math.min(1, 2200 / Math.max(image.width, image.height))
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(image.width * scale); canvas.height = Math.round(image.height * scale)
      const context = canvas.getContext('2d')
      if (!context) { image.close(); throw Error('Image processing is unavailable on this device.') }
      context.drawImage(image, 0, 0, canvas.width, canvas.height); image.close()
      if (!alive()) return
      setPreview(URL.createObjectURL(file))
      const { createWorker, OEM } = await import('tesseract.js')
      worker = await createWorker('eng', OEM.LSTM_ONLY, {
        workerPath: `${location.origin}/ocr/worker.min.js`, corePath: `${location.origin}/ocr`, langPath: `${location.origin}/ocr`,
        workerBlobURL: false, cacheMethod: 'none',
        logger: event => { if (alive()) setMessage(event.status === 'recognizing text' ? `Reading text: ${Math.round(event.progress * 100)}%` : 'Preparing local text reader...') },
      })
      if (!alive()) return
      workerRef.current = worker
      const result = await worker.recognize(canvas)
      if (!alive()) return
      const fields = parseIdCard(result.data.text, kind)
      setDraft(fields)
      setMessage(Object.keys(fields).length ? 'Check these suggestions against the card. OCR can misread names and numbers.' : 'No supported fields were found. Use a clear, upright photo of the front of the selected card, or type the details.')
    } catch (error) {
      if (alive()) setMessage(error instanceof Error && /Choose|Photo dimensions|Image processing/.test(error.message) ? error.message : 'Could not read the photo. Try a clearer, upright photo or enter the details manually.')
    } finally {
      await worker?.terminate().catch(() => undefined)
      if (alive()) { workerRef.current = null; setBusy(false) }
    }
  }

  return <section className="id-scan-panel" aria-label="Scan ID details">
    <div className="id-scan-heading"><ScanText aria-hidden="true" /><div><h3>Read details from your ID</h3><p>Photograph the front, keep all text visible, and avoid glare. Photos are processed on this device.</p></div></div>
    <label>Card to read<select aria-label="Card to read" value={kind} disabled={busy || disabled} onChange={e => { clear(); setKind(e.target.value as CardKind) }}><option value="campus">Campus ID front</option><option value="library">Library borrower's card front</option></select></label>
    <div className="id-scan-actions">
      <button type="button" className="icon-button" onClick={() => camera.current?.click()} disabled={busy || disabled}><Camera aria-hidden="true" />Take photo</button>
      <button type="button" className="icon-button" onClick={() => upload.current?.click()} disabled={busy || disabled}><Upload aria-hidden="true" />Choose image</button>
      {(busy || draft || preview) && <button type="button" onClick={clear}>Discard scan</button>}
    </div>
    <input hidden ref={camera} aria-label="Take ID photo" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" disabled={busy || disabled} onChange={e => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void read(f) }} />
    <input hidden ref={upload} aria-label="Choose ID image" type="file" accept="image/jpeg,image/png,image/webp" disabled={busy || disabled} onChange={e => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void read(f) }} />
    {message && <p role="status" className="id-scan-status">{busy && <LoaderCircle className="loading-spinner" aria-hidden="true" />}{message}</p>}
    {preview && <img className="id-photo-preview" src={preview} alt="Selected ID photo for local review" />}
    {draft && Object.keys(draft).length > 0 && <div className="id-scan-results"><dl>{Object.entries(draft).map(([key, value]) => <div key={key}><dt>{labels[key as keyof IdDraft]}</dt><dd>{value}</dd></div>)}</dl><button type="button" onClick={() => { onApply(draft); clear() }}>Apply scanned details</button><p>Applying replaces these fields in the form. Check and correct them before submitting.</p></div>}
    <p className="id-scan-privacy">Only the form fields you submit are sent to LIBRAI. ID photos, signatures, birthday, address, and emergency contacts are not saved by this scan.</p>
  </section>
}

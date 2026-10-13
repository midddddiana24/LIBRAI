import { useState } from 'react'
import { Camera, LoaderCircle, ScanQrCode } from 'lucide-react'

type Props = { label: string; busy: boolean; onToken: (token: string) => void }

export function QrCapture({ label, busy, onToken }: Props) {
  const [manual, setManual] = useState('')
  const [error, setError] = useState('')
  const [scanning, setScanning] = useState(false)

  async function scan() {
    if (scanning || busy) return
    setError('')
    setScanning(true)
    try {
      const { CapacitorBarcodeScanner, CapacitorBarcodeScannerTypeHint } = await import('@capacitor/barcode-scanner')
      const result = await CapacitorBarcodeScanner.scanBarcode({
        hint: CapacitorBarcodeScannerTypeHint.QR_CODE,
        scanInstructions: `Scan ${label}`,
        cancelButtonAccessibilityLabel: 'Cancel QR scan',
      })
      if (result.ScanResult) onToken(result.ScanResult.trim())
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Camera scan was cancelled or unavailable.')
    } finally {
      setScanning(false)
    }
  }

  return <div className="scan-panel">
    <button className="primary large icon-button" type="button" onClick={scan} disabled={busy || scanning}>{scanning ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <Camera aria-hidden="true" />}<span>{scanning ? 'Opening camera…' : `Open camera to scan ${label}`}</span></button>
    <p className="muted">Allow camera access when your tablet asks. Your QR is verified by the library server.</p>
    <form onSubmit={(event) => { event.preventDefault(); if (manual.trim()) { onToken(manual.trim()); setManual('') } }}>
      <label htmlFor={`manual-${label}`}>Use a USB scanner or enter the QR value</label>
      <div className="inline"><input id={`manual-${label}`} type="password" autoComplete="off" value={manual} onChange={event => setManual(event.target.value)} disabled={busy || scanning} /><button className="icon-button" type="submit" disabled={busy || scanning || !manual.trim()}>{busy ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <ScanQrCode aria-hidden="true" />}<span>{busy ? 'Verifying…' : 'Verify'}</span></button></div>
    </form>
    {error && <p role="alert" className="error">{error}</p>}
  </div>
}

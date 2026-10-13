import { useState } from 'react'

type Props = { label: string; busy: boolean; onToken: (token: string) => void }

export function QrCapture({ label, busy, onToken }: Props) {
  const [manual, setManual] = useState('')
  const [error, setError] = useState('')

  async function scan() {
    setError('')
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
    }
  }

  return <div className="scan-panel">
    <button className="primary large" type="button" onClick={scan} disabled={busy}>Open camera to scan {label}</button>
    <p className="muted">Allow camera access when your tablet asks. Your QR is verified by the library server.</p>
    <form onSubmit={(event) => { event.preventDefault(); if (manual.trim()) { onToken(manual.trim()); setManual('') } }}>
      <label htmlFor={`manual-${label}`}>Use a USB scanner or enter the QR value</label>
      <div className="inline"><input id={`manual-${label}`} type="password" autoComplete="off" value={manual} onChange={event => setManual(event.target.value)} disabled={busy} /><button type="submit" disabled={busy || !manual.trim()}>Verify</button></div>
    </form>
    {error && <p role="alert" className="error">{error}</p>}
  </div>
}

import { useState } from 'react'
import { Camera, LoaderCircle, ScanQrCode } from 'lucide-react'

type Props = { label: string; busy: boolean; onToken: (token: string) => void; presentation?: 'default' | 'borrow' }

export function QrCapture({ label, busy, onToken, presentation = 'default' }: Props) {
  const [manual, setManual] = useState('')
  const [error, setError] = useState('')
  const [scanning, setScanning] = useState(false)

  async function scan() {
    if (scanning || busy) return
    setError('')
    setScanning(true)
    try {
      const { CapacitorBarcodeScanner, CapacitorBarcodeScannerTypeHint, CapacitorBarcodeScannerCameraDirection, CapacitorBarcodeScannerAndroidScanningLibrary } = await import('@capacitor/barcode-scanner')
      const result = await CapacitorBarcodeScanner.scanBarcode({
        hint: CapacitorBarcodeScannerTypeHint.QR_CODE,
        cameraDirection: CapacitorBarcodeScannerCameraDirection.BACK,
        // ML Kit decoded the physical test QR on the Infinix; the default engine did not.
        android: { scanningLibrary: CapacitorBarcodeScannerAndroidScanningLibrary.MLKIT },
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

  return <div className={`scan-panel scan-panel-${presentation}`} aria-busy={busy || scanning}>
    {presentation === 'default' && <div className="scan-visual" aria-hidden="true"><ScanQrCode /><span>Ready to scan</span></div>}
    <button className="primary large icon-button" type="button" onClick={scan} aria-label={scanning ? 'Opening camera' : `Open camera to scan ${label}`} disabled={busy || scanning}>{scanning ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <Camera aria-hidden="true" />}<span>{scanning ? 'Opening camera…' : 'Open camera'}</span></button>
    {presentation === 'default' ? <p className="muted">Allow camera access when your tablet asks. Your QR is verified by the library server.</p> : <div className="scan-alternative" aria-hidden="true">or</div>}
    <form onSubmit={(event) => { event.preventDefault(); if (!busy && !scanning && manual.trim()) { onToken(manual.trim()); setManual('') } }}>
      <label htmlFor={`manual-${label}`}>{presentation === 'borrow' ? 'QR code' : 'Use a USB scanner or enter the QR value'}</label>
      <div className="inline"><input id={`manual-${label}`} type="password" autoComplete="off" placeholder={presentation === 'borrow' ? `Enter ${label.replace(/^your |^the /, '')} QR code` : undefined} value={manual} onChange={event => setManual(event.target.value)} disabled={busy || scanning} /><button className="icon-button" type="submit" disabled={busy || scanning || !manual.trim()}>{busy ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : presentation === 'default' ? <ScanQrCode aria-hidden="true" /> : null}<span>{busy ? 'Verifying…' : 'Verify'}</span></button></div>
    </form>
    {error && <p role="alert" className="error">{error}</p>}
  </div>
}

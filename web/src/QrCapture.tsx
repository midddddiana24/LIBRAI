import { useId, useState } from 'react'
import { Camera, LoaderCircle, ScanQrCode } from 'lucide-react'
import { useKioskLanguage } from './kioskLanguage'

type Props = { label: string; busy: boolean; error?: string; onToken: (token: string) => void; presentation?: 'default' | 'borrow' }

export function QrCapture({ label, busy, error: verificationError = '', onToken, presentation = 'default' }: Props) {
  const { t } = useKioskLanguage()
  const [manual, setManual] = useState('')
  const [error, setError] = useState('')
  const [scanning, setScanning] = useState(false)
  const errorId = useId()
  const message = error || verificationError
  const translatedLabel = label === 'your library ID' ? t(label, 'iyong library ID') : t(label, 'QR ng libro')

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
        scanInstructions: t('Scan ' + label, 'I-scan ang ' + translatedLabel),
        cancelButtonAccessibilityLabel: t('Cancel QR scan', 'Kanselahin ang pag-scan'),
      })
      if (result.ScanResult) onToken(result.ScanResult.trim())
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('Camera scan was cancelled or unavailable.', 'Nakansela o hindi available ang camera.'))
    } finally {
      setScanning(false)
    }
  }

  return <div className={'scan-panel scan-panel-' + presentation} aria-busy={busy || scanning} data-help-scanning={scanning}>
    {presentation === 'default' && <div className="scan-visual" aria-hidden="true"><ScanQrCode /><span>{t('Ready to scan', 'Handa nang mag-scan')}</span></div>}
    <button data-help-camera className="primary large icon-button" type="button" onClick={scan} aria-label={scanning ? t('Opening camera', 'Binubuksan ang camera') : t('Open camera to scan ' + label, 'Buksan ang camera para i-scan ang ' + translatedLabel)} disabled={busy || scanning}>{scanning ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <Camera aria-hidden="true" />}<span>{scanning ? t('Opening camera…', 'Binubuksan ang camera…') : t('Open camera', 'Buksan ang camera')}</span></button>
    {presentation === 'default' ? <p className="muted">{t('Allow camera access when your tablet asks. Your QR is verified by the library server.', 'Payagan ang camera kapag hiniling ng tablet. Ive-verify ng library server ang iyong QR.')}</p> : <div className="scan-alternative" aria-hidden="true">{t('or', 'o')}</div>}
    <form onSubmit={(event) => { event.preventDefault(); if (!busy && !scanning && manual.trim()) { setError(''); onToken(manual.trim()) } }}>
      <label htmlFor={'manual-' + label}>{presentation === 'borrow' ? t('QR code', 'QR code') : t('Use a USB scanner or enter the QR value', 'Gumamit ng USB scanner o ilagay ang QR value')}</label>
      <div className="inline" data-help-qr-entry><input id={'manual-' + label} type="password" autoComplete="off" aria-describedby={message ? errorId : undefined} aria-invalid={!!message} placeholder={presentation === 'borrow' ? t('Enter ' + label.replace(/^your |^the /, '') + ' QR code', 'Ilagay ang ' + translatedLabel) : undefined} value={manual} onChange={event => { setManual(event.target.value); setError('') }} disabled={busy || scanning} /><button className="icon-button" type="submit" disabled={busy || scanning || !manual.trim()}>{busy ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : presentation === 'default' ? <ScanQrCode aria-hidden="true" /> : null}<span>{busy ? t('Verifying…', 'Vine-verify…') : t('Verify', 'I-verify')}</span></button></div>
    </form>
    {message && <p id={errorId} role="alert" className="error">{message}</p>}
  </div>
}

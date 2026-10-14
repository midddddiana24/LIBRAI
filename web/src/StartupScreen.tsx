export default function StartupScreen({ mode = 'kiosk' }: { mode?: 'kiosk' | 'admin' }) {
  return <div className="startup-screen" role="status" aria-live="polite" aria-label="Opening LIBRAI">
    <div className="startup-content">
      <div className="startup-symbol"><img src="/images/librai-symbol.png" alt="" /></div>
      <p className="startup-kicker">{mode === 'admin' ? 'LIBRAI ADMINISTRATION' : 'LIBRAI KIOSK'}</p>
      <h1>{mode === 'admin' ? 'Opening your workspace' : 'Opening the library'}</h1>
      <p className="startup-description">One moment while we connect.</p>
      <div className="startup-track" aria-hidden="true"><span /></div>
    </div>
  </div>
}

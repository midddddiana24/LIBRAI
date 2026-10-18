import { useEffect, useRef, useState } from 'react'

type Props = {
  mode?: 'kiosk' | 'admin'
  stage?: 'assets' | 'connecting' | 'ready' | 'offline'
  onReady?: () => void
  onRetry?: () => void
}

export default function StartupScreen({ mode = 'kiosk', stage: requestedStage = 'assets', onReady, onRetry }: Props) {
  const [slow, setSlow] = useState(false)
  const [opened, setOpened] = useState(false)
  const openingStarted = useRef(0)
  const stage = requestedStage === 'ready' && !opened ? 'opening' : requestedStage
  useEffect(() => {
    if (requestedStage === 'assets') return
    if (!openingStarted.current) openingStarted.current = performance.now()
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const timer = window.setTimeout(() => setOpened(true), reduced ? 0 : Math.max(0, 950 - (performance.now() - openingStarted.current)))
    return () => window.clearTimeout(timer)
  }, [requestedStage])
  useEffect(() => {
    if (stage !== 'connecting') return
    const timer = window.setTimeout(() => setSlow(true), 5000)
    return () => window.clearTimeout(timer)
  }, [stage])
  useEffect(() => {
    if (stage !== 'ready' || !onReady) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const timer = window.setTimeout(onReady, reduced ? 100 : 420)
    return () => window.clearTimeout(timer)
  }, [stage, onReady])
  const title = stage === 'ready' ? 'Your library is ready.' : stage === 'offline' ? 'Let’s reconnect.' : mode === 'admin' ? 'Opening your workspace' : 'Opening the library'
  const description = stage === 'ready' ? 'Find a book. Start something new.' : stage === 'offline' ? 'We couldn’t reach the library server. Check your internet connection and try again.' : stage === 'connecting' ? slow ? 'The server is taking a little longer. We’re still checking the connection.' : 'Connecting to your library…' : 'Preparing LIBRAI…'
  return <div className={`startup-screen startup-${stage}`}>
    <div className="startup-content">
      <div className="startup-illustration" aria-hidden="true">
        <div className="startup-book"><img src="/images/librai-startup-book.png" alt="" /><span className="startup-cover" /><span className="startup-page startup-page-one" /><span className="startup-page startup-page-two" /></div>
        <img className="startup-ready-logo" src="/images/librai-symbol-v2.png" alt="" />
      </div>
      <div role="status" aria-live="polite" aria-atomic="true"><h1>{title}</h1><p className="startup-description">{description}</p></div>
      {stage === 'offline' ? <button className="startup-retry" type="button" onClick={() => { setSlow(false); onRetry?.() }}>Try again</button> : <div className="startup-track" aria-hidden="true"><span /></div>}
      <p className="startup-signature">LIBRAI <span>{mode === 'admin' ? 'Library administration' : 'Your library, within reach.'}</span></p>
    </div>
  </div>
}

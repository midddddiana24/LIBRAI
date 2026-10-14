import { ArrowRight, BookOpen, LibraryBig, LoaderCircle, MessageCircle, RotateCcw, Search, Sparkles, UserRound } from 'lucide-react'
import VoiceControl from './VoiceControl'

type Props = {
  query: string
  busy: boolean
  online: boolean | null
  onQuery: (value: string) => void
  onSearch: (query: string) => void
  onBorrow: () => void
  onReturn: () => void
  onAccount: () => void
  onAssistant: () => void
  onDiscover: () => void
  onVoiceCommand: (text: string) => void
  onHearInstructions: () => void
}

export default function KioskHome({ query, busy, online, onQuery, onSearch, onBorrow, onReturn, onAccount, onAssistant, onDiscover, onVoiceCommand, onHearInstructions }: Props) {
  const unavailable = busy || online === false

  return <div className="kiosk-home">
    <section className="kiosk-intro" aria-labelledby="kiosk-intro-title">
      <p className="eyebrow">LIBRAI · Library self service</p>
      <h1 id="kiosk-intro-title">What would you like to do today?</h1>
      <p>Choose an option to begin. Your librarian can help if you need it.</p>
    </section>

    <section className="kiosk-task-grid" aria-label="Borrow or return">
      <button className="kiosk-task" disabled={unavailable} onClick={onBorrow}>
        <span className="kiosk-task-icon" aria-hidden="true"><BookOpen /></span>
        <strong>Borrow a book</strong>
        <span className="kiosk-task-description">Scan your library ID and the book’s QR code.</span>
        <span className="kiosk-task-link">Start borrowing <ArrowRight aria-hidden="true" /></span>
      </button>
      <button className="kiosk-task" disabled={unavailable} onClick={onReturn}>
        <span className="kiosk-task-icon" aria-hidden="true"><RotateCcw /></span>
        <strong>Return a book</strong>
        <span className="kiosk-task-description">Scan the QR code on the borrowed book.</span>
        <span className="kiosk-task-link">Start returning <ArrowRight aria-hidden="true" /></span>
      </button>
    </section>

    <section className="kiosk-explore" aria-label="Explore the library">
      <div className="kiosk-voice-entry"><div><strong>Use your voice</strong><span>Say “borrow a book”, “return a book”, “manghiram ng libro”, or “find history books”.</span><button type="button" className="voice-instructions" onClick={onHearInstructions}>Hear instructions</button></div><VoiceControl label="Voice command" disabled={unavailable} confirmBeforeUse onTranscript={onVoiceCommand} /></div>
      <form className="kiosk-search" role="search" onSubmit={event => { event.preventDefault(); onSearch(query) }}>
        <label htmlFor="kiosk-home-search">Find a book</label>
        <div><input id="kiosk-home-search" value={query} onChange={event => onQuery(event.target.value)} placeholder="Search by title, author, or topic" /><button className="primary icon-button" disabled={unavailable}>{busy ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <Search aria-hidden="true" />}<span>{busy ? 'Loading…' : 'Search'}</span></button></div>
      </form>
      <div className="kiosk-quick-links">
        <button disabled={unavailable} onClick={() => onSearch('')}><LibraryBig aria-hidden="true" />Browse catalog</button>
        <button disabled={unavailable} onClick={onAccount}><UserRound aria-hidden="true" />My account</button>
        <button disabled={unavailable} onClick={onDiscover}><Sparkles aria-hidden="true" />Discover books</button>
        <button disabled={unavailable} onClick={onAssistant}><MessageCircle aria-hidden="true" />Ask LIBRAI</button>
      </div>
    </section>
  </div>
}

import { LoaderCircle, Search, Volume2 } from 'lucide-react'
import LibraryActionIcon from './LibraryActionIcon'
import KioskTileArt from './KioskTileArt'
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

  return <div className="kiosk-home kiosk-menu">
    <div className="kiosk-menu-screen">
      <div className="kiosk-menu-utility"><span>LIBRAI / Self service</span><button type="button" onClick={onHearInstructions}><Volume2 aria-hidden="true" />Hear instructions</button></div>
      <section className="kiosk-intro" aria-labelledby="kiosk-intro-title">
        <p className="eyebrow">Welcome to the library</p>
        <h1 id="kiosk-intro-title">How can we help you today?</h1>
        <p>Tap a card to get started.</p>
      </section>

      <section className="kiosk-task-grid" aria-label="Library services">
        <button className="kiosk-task kiosk-task-borrow" type="button" aria-label="Borrow a book" disabled={unavailable} onClick={onBorrow}>
          <span className="kiosk-task-icon"><KioskTileArt kind="borrow" /></span>
          <strong>Borrow a book</strong>
        </button>
        <button className="kiosk-task kiosk-task-return" type="button" aria-label="Return a book" disabled={unavailable} onClick={onReturn}>
          <span className="kiosk-task-icon"><KioskTileArt kind="return" /></span>
          <strong>Return a book</strong>
        </button>
        <button className="kiosk-task kiosk-task-find" type="button" aria-label="Find a book" disabled={unavailable} onClick={() => onSearch('')}>
          <span className="kiosk-task-icon"><KioskTileArt kind="find" /></span>
          <strong>Find a book</strong>
        </button>
        <button className="kiosk-task kiosk-task-discover" type="button" aria-label="Discover books" disabled={unavailable} onClick={onDiscover}>
          <span className="kiosk-task-icon"><KioskTileArt kind="discover" /></span>
          <strong>Discover books</strong>
        </button>
      </section>

      <section className="kiosk-explore" aria-label="More ways to use the library">
        <form className="kiosk-search" role="search" onSubmit={event => { event.preventDefault(); onSearch(query) }}>
          <label htmlFor="kiosk-home-search">Search the catalog</label>
          <div><input id="kiosk-home-search" value={query} onChange={event => onQuery(event.target.value)} placeholder="Title, author, or topic" /><button className="primary icon-button" disabled={unavailable}>{busy ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <Search aria-hidden="true" />}<span>{busy ? 'Loading...' : 'Search'}</span></button></div>
        </form>
        <div className="kiosk-voice-entry"><div><strong>Use your voice</strong><span>Say "borrow a book", "return a book", or "manghiram ng libro".</span></div><VoiceControl label="Voice command" disabled={unavailable} confirmBeforeUse onTranscript={onVoiceCommand} /></div>
        <div className="kiosk-quick-links">
          <button disabled={unavailable} onClick={onAccount}><LibraryActionIcon kind="account" />My account</button>
          <button disabled={unavailable} onClick={onAssistant}><LibraryActionIcon kind="assistant" />Ask LIBRAI</button>
        </div>
      </section>
    </div>
  </div>
}

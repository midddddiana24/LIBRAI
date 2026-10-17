import { ArrowUpRight, AudioLines, LoaderCircle, Search, Volume2, UserRoundPlus } from 'lucide-react'
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
  onRegister: () => void
  onAccount: () => void
  onAssistant: () => void
  onDiscover: () => void
  onVoiceCommand: (text: string) => void
  onHearInstructions: () => void
}

export default function KioskHome({ query, busy, online, onQuery, onSearch, onBorrow, onReturn, onRegister, onAccount, onAssistant, onDiscover, onVoiceCommand, onHearInstructions }: Props) {
  const unavailable = busy || online === false

  return <div className="kiosk-home kiosk-menu">
    <div className="kiosk-menu-screen">
      <section className="kiosk-intro" aria-labelledby="kiosk-intro-title">
        <div><h1 id="kiosk-intro-title">Welcome to your library.</h1><p>What would you like to do today?</p></div>
        <button className="hear-instructions" type="button" onClick={onHearInstructions}><Volume2 aria-hidden="true" /><span>Hear instructions</span></button>
      </section>

      <section className="kiosk-task-grid" aria-label="Library services">
        <button className="kiosk-task kiosk-task-borrow" type="button" aria-label="Borrow a book" disabled={unavailable} onClick={onBorrow}>
          <span className="kiosk-task-icon"><KioskTileArt kind="borrow" /></span>
          <strong>Borrow a book</strong>
          <span className="kiosk-task-hint">Scan your ID and book.</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
        <button className="kiosk-task kiosk-task-return" type="button" aria-label="Return a book" disabled={unavailable} onClick={onReturn}>
          <span className="kiosk-task-icon"><KioskTileArt kind="return" /></span>
          <strong>Return a book</strong>
          <span className="kiosk-task-hint">Bring a book back.</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
        <button className="kiosk-task kiosk-task-find" type="button" aria-label="Find a book" disabled={unavailable} onClick={() => onSearch(query)}>
          <span className="kiosk-task-icon"><KioskTileArt kind="find" /></span>
          <strong>Find a book</strong>
          <span className="kiosk-task-hint">Search the library catalog.</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
        <button className="kiosk-task kiosk-task-discover" type="button" aria-label="Discover books" disabled={unavailable} onClick={onDiscover}>
          <span className="kiosk-task-icon"><KioskTileArt kind="discover" /></span>
          <strong>Discover books</strong>
          <span className="kiosk-task-hint">Find your next good read.</span><ArrowUpRight className="tile-arrow" aria-hidden="true" />
        </button>
      </section>

      <section className="kiosk-explore" aria-label="More ways to use the library">
        <form className="kiosk-search" role="search" onSubmit={event => { event.preventDefault(); onSearch(query) }}>
          <label htmlFor="kiosk-home-search">Search the catalog</label>
          <div><input id="kiosk-home-search" value={query} onChange={event => onQuery(event.target.value)} placeholder="Title, author, or topic" /><button className="primary icon-button" disabled={unavailable}>{busy ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <Search aria-hidden="true" />}<span>{busy ? 'Loading...' : 'Search'}</span></button></div>
        </form>
        <div className="kiosk-voice-entry"><AudioLines className="voice-dock-icon" aria-hidden="true" /><div><strong>A little help, just ask.</strong><span>Speak in English or Filipino.</span></div><VoiceControl label="Voice command" disabled={unavailable} confirmBeforeUse onTranscript={onVoiceCommand} /></div>
        <div className="kiosk-quick-links">
          <button disabled={unavailable} onClick={onRegister}><UserRoundPlus aria-hidden="true" />Register</button>
          <button disabled={unavailable} onClick={onAccount}><LibraryActionIcon kind="account" />My account</button>
          <button disabled={unavailable} onClick={onAssistant}><LibraryActionIcon kind="assistant" />Ask LIBRAI</button>
        </div>
      </section>
    </div>
  </div>
}

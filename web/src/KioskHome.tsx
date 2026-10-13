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
}

export default function KioskHome({ query, busy, online, onQuery, onSearch, onBorrow, onReturn, onAccount, onAssistant, onDiscover }: Props) {
  const unavailable = busy || online === false

  return <div className="kiosk-home">
    <section className="kiosk-intro" aria-labelledby="kiosk-intro-title">
      <p className="eyebrow">LIBRAI · Library self service</p>
      <h1 id="kiosk-intro-title">What would you like to do today?</h1>
      <p>Choose an option to begin. Your librarian can help if you need it.</p>
    </section>

    <section className="kiosk-task-grid" aria-label="Borrow or return">
      <button className="kiosk-task" disabled={unavailable} onClick={onBorrow}>
        <span className="kiosk-task-icon" aria-hidden="true"><svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M24 11c-5-3-11-3-17-1v26c6-2 12-2 17 1 5-3 11-3 17-1V10c-6-2-12-2-17 1Z"/><path d="M24 11v26M12 16c2-.3 4-.2 6 .2M12 21c2-.3 4-.2 6 .2M30 16c2-.3 4-.2 6 .2"/></svg></span>
        <strong>Borrow a book</strong>
        <span className="kiosk-task-description">Scan your library ID and the book’s QR code.</span>
        <span className="kiosk-task-link">Start borrowing <span aria-hidden="true">→</span></span>
      </button>
      <button className="kiosk-task" disabled={unavailable} onClick={onReturn}>
        <span className="kiosk-task-icon" aria-hidden="true"><svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9h24v30H14zM20 16h12M20 22h9M14 32H6m5-5-5 5 5 5"/></svg></span>
        <strong>Return a book</strong>
        <span className="kiosk-task-description">Scan the QR code on the borrowed book.</span>
        <span className="kiosk-task-link">Start returning <span aria-hidden="true">→</span></span>
      </button>
    </section>

    <section className="kiosk-explore" aria-label="Explore the library">
      <form className="kiosk-search" role="search" onSubmit={event => { event.preventDefault(); onSearch(query) }}>
        <label htmlFor="kiosk-home-search">Find a book</label>
        <div><input id="kiosk-home-search" value={query} onChange={event => onQuery(event.target.value)} placeholder="Search by title, author, or topic" /><button className="primary" disabled={unavailable}>Search</button></div>
      </form>
      <div className="kiosk-quick-links">
        <button disabled={unavailable} onClick={() => onSearch('')}>Browse catalog</button>
        <button disabled={unavailable} onClick={onAccount}>My account</button>
        <button disabled={unavailable} onClick={onDiscover}>Discover books</button>
        <button disabled={unavailable} onClick={onAssistant}>Ask LIBRAI</button>
      </div>
    </section>
  </div>
}

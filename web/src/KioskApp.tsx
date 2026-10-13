import { useCallback, useEffect, useRef, useState } from 'react'
import { api, bookDetail, books, health, mediaUrl, verifyBook, verifyUser } from './api'
import type { ActiveBorrowing, Book, BookGrant, BorrowReceipt, Page, ReturnReceipt, UserGrant } from './api'
import { QrCapture } from './QrCapture'
import AccountPanel from './AccountPanel'

type View = 'home' | 'search' | 'detail' | 'borrow' | 'return' | 'account' | 'assistant' | 'discover'
const date = (value?: string) => value ? new Date(value).toLocaleString() : '—'

export default function KioskApp() {
  const [view, setView] = useState<View>('home')
  const [online, setOnline] = useState<boolean | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [query, setQuery] = useState('')
  const [catalog, setCatalog] = useState<Page<Book>>({ items: [], total: 0 })
  const [catalogOffset, setCatalogOffset] = useState(0)
  const [selected, setSelected] = useState<Book | null>(null)
  const [user, setUser] = useState<UserGrant | null>(null)
  const [copy, setCopy] = useState<BookGrant | null>(null)
  const [receipt, setReceipt] = useState<BorrowReceipt | ReturnReceipt | null>(null)
  const [activeReturn, setActiveReturn] = useState<ActiveBorrowing | null>(null)
  const [aiQuery, setAiQuery] = useState('')
  const [aiAnswer, setAiAnswer] = useState('')
  const [aiBooks, setAiBooks] = useState<Book[]>([])
  const [aiInteraction, setAiInteraction] = useState<number | null>(null)
  const [feedbackSent, setFeedbackSent] = useState(false)
  const [discoverKind, setDiscoverKind] = useState<'recommended' | 'popular' | 'new'>('recommended')
  const [discoverBooks, setDiscoverBooks] = useState<Book[]>([])
  const lastActivity = useRef(0)

  const endSession = useCallback(() => {
    setUser(null); setCopy(null); setReceipt(null); setActiveReturn(null)
    setAiQuery(''); setAiAnswer(''); setAiBooks([]); setAiInteraction(null); setFeedbackSent(false); setError(''); setView('home')
  }, [])

  useEffect(() => {
    lastActivity.current = Date.now()
    const touch = () => { lastActivity.current = Date.now() }
    window.addEventListener('pointerdown', touch)
    window.addEventListener('keydown', touch)
    const interval = window.setInterval(() => {
      if (Date.now() - lastActivity.current > 90_000) { endSession(); lastActivity.current = Date.now() }
    }, 1000)
    return () => { window.removeEventListener('pointerdown', touch); window.removeEventListener('keydown', touch); window.clearInterval(interval) }
  }, [endSession])

  useEffect(() => {
    let alive = true
    const check = () => { void health().then(value => { if (alive) setOnline(value) }) }
    check()
    const timer = window.setInterval(check, 20_000)
    return () => { alive = false; window.clearInterval(timer) }
  }, [])

  const run = useCallback(async (action: () => Promise<void>) => {
    if (busy) return
    setBusy(true); setError('')
    try { await action(); setOnline(true) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'The action could not be completed.') }
    finally { setBusy(false) }
  }, [busy])

  async function loadBooks(search = query, offset = 0) {
    await run(async () => { setCatalog(await books(search, offset)); setCatalogOffset(offset); setView('search') })
  }

  async function showBook(id: number) {
    await run(async () => { setSelected(await bookDetail(id)); setView('detail') })
  }

  function startBorrow() { setCopy(null); setReceipt(null); setView('borrow'); setError('') }
  function startReturn() { setCopy(null); setActiveReturn(null); setReceipt(null); setView('return'); setError('') }

  async function scanUser(token: string) {
    await run(async () => { setUser(await verifyUser(token)) })
  }

  async function scanBorrowBook(token: string) {
    await run(async () => { setCopy(await verifyBook(token)) })
  }

  async function confirmBorrow() {
    if (!user || !copy) return
    await run(async () => {
      const result = await api<BorrowReceipt>('/borrowings', { method: 'POST', body: JSON.stringify({ user_id: user.id, book_copy_id: copy.book_copy_id, user_verification_token: user.verification_token, book_verification_token: copy.verification_token }) })
      setReceipt(result); setUser(null); setCopy(null)
    })
  }

  async function scanReturnBook(token: string) {
    await run(async () => {
      const checked = await verifyBook(token)
      const active = await api<ActiveBorrowing>(`/borrowings/active/by-copy/${checked.book_copy_id}?book_verification_token=${encodeURIComponent(checked.verification_token)}`)
      setCopy(checked); setActiveReturn(active)
    })
  }

  async function confirmReturn() {
    if (!copy || !activeReturn) return
    await run(async () => {
      const result = await api<ReturnReceipt>('/returns', { method: 'POST', body: JSON.stringify({ borrowing_id: activeReturn.id, book_verification_token: copy.verification_token }) })
      setReceipt(result); setCopy(null); setActiveReturn(null)
    })
  }

  async function askAssistant(event: React.FormEvent) {
    event.preventDefault()
    if (aiQuery.trim().length < 2) return
    await run(async () => {
      const result = await api<{ answer?: string; message?: string; books?: Book[]; interaction_id?: number }>('/ai/search', { method: 'POST', body: JSON.stringify({ query: aiQuery.trim() }) })
      setAiAnswer(result.answer || result.message || 'No answer was returned.')
      setAiBooks(result.books || []); setAiInteraction(result.interaction_id || null); setFeedbackSent(false)
    })
  }

  async function sendFeedback(helpful: boolean) {
    if (!aiInteraction) return
    await run(async () => {
      await api('/ai/feedback', { method: 'POST', body: JSON.stringify({ interaction_id: aiInteraction, helpful, ...(user ? { user_id: user.id, user_verification_token: user.verification_token } : {}) }) })
      setFeedbackSent(true)
    })
  }

  async function discover(kind: 'recommended' | 'popular' | 'new') {
    await run(async () => {
      const result = await api<Book[]>('/ai/recommend', { method: 'POST', body: JSON.stringify({ kind }) })
      setDiscoverBooks(result); setDiscoverKind(kind); setView('discover')
    })
  }

  async function reserveSelected() {
    if (!selected || !user) return
    await run(async () => {
      await api('/reservations', { method: 'POST', body: JSON.stringify({ user_id: user.id, book_id: selected.id, user_verification_token: user.verification_token }) })
      setError('')
      setView('account')
    })
  }

  return <div className="app kiosk" onClick={() => { lastActivity.current = Date.now() }}>
    <header className="topbar"><div className="brand"><span className="brand-mark">L</span><span><strong>LIBRAI</strong><small>Library kiosk</small></span></div><div className="top-actions"><span className={`status ${online ? 'good' : 'bad'}`}>{online === null ? 'Connecting' : online ? 'Library online' : 'Library offline'}</span><button type="button" onClick={endSession}>End session</button></div></header>
    <main className="content">
      {error && <div className="alert error" role="alert">{error}</div>}
      {view === 'home' && <><section className="hero"><p className="eyebrow">Your library, ready to explore</p><h1>Find your next book.</h1><p>Search the catalog, borrow a copy, or return one with your QR code.</p><form className="search-form" onSubmit={event => { event.preventDefault(); void loadBooks(query) }}><input aria-label="Search books" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search title, author, or topic" /><button className="primary" disabled={busy}>Search books</button></form></section><div className="action-grid"><button onClick={() => void loadBooks('')}>Browse catalog<span>Explore available titles →</span></button><button onClick={startBorrow}>Borrow a book<span>Scan your ID and book →</span></button><button onClick={startReturn}>Return a book<span>Scan the book copy →</span></button><button onClick={() => { setView('account'); setError('') }}>My account<span>Loans and due dates →</span></button><button onClick={() => setView('assistant')}>Ask LIBRAI<span>Find a book by topic →</span></button><button onClick={() => void discover('recommended')}>Discover books<span>Recommended and popular →</span></button></div></>}
      {view === 'search' && <><div className="page-heading"><div><p className="eyebrow">Library catalog</p><h1>Find a book</h1><p>{catalog.total} titles found</p></div><button onClick={() => setView('home')}>Home</button></div><form className="search-form" onSubmit={event => { event.preventDefault(); void loadBooks(query) }}><input aria-label="Search books" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search title, author, or topic" /><button className="primary" disabled={busy}>Search</button></form><div className="book-grid">{catalog.items.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}>{(book.cover_url || book.cover_image) ? <img src={mediaUrl(book.cover_url || book.cover_image)} alt="" /> : <div className="cover-placeholder">LIBRAI</div>}<strong>{book.title}</strong><span>{book.author}</span><small>{book.available_copies || 0} available · {book.shelf_location || 'Ask the librarian'}</small></button>)}</div>{!catalog.items.length && <div className="empty">No books found. Try another search.</div>}<div className="pagination"><button disabled={busy || catalogOffset === 0} onClick={() => void loadBooks(query, Math.max(0, catalogOffset - 20))}>Previous</button><span>{catalog.total ? `${catalogOffset + 1}–${Math.min(catalogOffset + 20, catalog.total)} of ${catalog.total}` : '0 results'}</span><button disabled={busy || catalogOffset + 20 >= catalog.total} onClick={() => void loadBooks(query, catalogOffset + 20)}>Next</button></div></>}
      {view === 'detail' && selected && <><button onClick={() => setView('search')}>← Back to results</button><div className="detail"><div className="detail-cover">{(selected.cover_url || selected.cover_image) ? <img src={mediaUrl(selected.cover_url || selected.cover_image)} alt="Book cover" /> : 'LIBRAI'}</div><div><p className="eyebrow">{selected.category || 'Library catalog'}</p><h1>{selected.title}</h1><h2>by {selected.author}</h2><p>{selected.description || 'No description available.'}</p><div className="facts"><span>Available: {selected.available_copies || 0}</span><span>Shelf: {selected.shelf_location || 'Ask the librarian'}</span></div>{(selected.available_copies || 0) > 0 ? <button className="primary large" onClick={startBorrow}>Borrow a copy</button> : user ? <button className="primary large" disabled={busy} onClick={() => void reserveSelected()}>Reserve this title</button> : <button onClick={() => setView('account')}>Scan your ID to reserve</button>}</div></div></>}
      {view === 'borrow' && <><div className="page-heading"><div><p className="eyebrow">Self service</p><h1>Borrow a book</h1></div><button onClick={() => setView('home')}>Home</button></div>{receipt ? <div className="success"><h2>Borrowing complete</h2><p>{receipt.book_title}</p><p>Due: {date((receipt as BorrowReceipt).due_at)}</p><button className="primary" onClick={endSession}>Finish and clear session</button></div> : <div className="flow-grid"><section className="panel"><span className="step">1</span><h2>Scan your library ID</h2>{user ? <p className="verified">Verified: {user.display_name || user.name || user.student_id}</p> : <QrCapture label="your library ID" busy={busy} onToken={token => void scanUser(token)} />}</section><section className="panel"><span className="step">2</span><h2>Scan the book copy</h2>{copy ? <p className="verified">Verified: {copy.title} · {copy.accession_number}</p> : <QrCapture label="the book QR" busy={busy} onToken={token => void scanBorrowBook(token)} />}</section><section className="panel confirm"><span className="step">3</span><h2>Confirm</h2><p>The library server checks availability, limits, and due dates.</p>{copy && !copy.available && <p className="error">This copy is not available.</p>}<button className="primary large" disabled={!user || !copy || !copy.available || busy} onClick={() => void confirmBorrow()}>{busy ? 'Processing…' : 'Confirm borrowing'}</button></section></div>}</>}
      {view === 'return' && <><div className="page-heading"><div><p className="eyebrow">Self service</p><h1>Return a book</h1></div><button onClick={() => setView('home')}>Home</button></div>{receipt ? <div className="success"><h2>Return complete</h2><p>{receipt.book_title}</p><p>Returned: {date((receipt as ReturnReceipt).returned_at)}</p><button className="primary" onClick={endSession}>Finish and clear session</button></div> : <div className="flow-grid"><section className="panel"><span className="step">1</span><h2>Scan the book copy</h2>{copy ? <p className="verified">{copy.title} · {copy.accession_number}</p> : <QrCapture label="the book QR" busy={busy} onToken={token => void scanReturnBook(token)} />}</section><section className="panel"><span className="step">2</span><h2>Review active loan</h2>{activeReturn ? <><p>{activeReturn.book_title}</p><p>Borrower: {activeReturn.user_name}</p><p>Due: {date(activeReturn.due_at)}</p></> : <p className="muted">Scan a borrowed copy to see its loan.</p>}</section><section className="panel confirm"><span className="step">3</span><h2>Confirm return</h2><button className="primary large" disabled={!activeReturn || busy} onClick={() => void confirmReturn()}>{busy ? 'Processing…' : 'Confirm return'}</button></section></div>}</>}
      {view === 'account' && <><div className="page-heading"><div><p className="eyebrow">Private session</p><h1>My account</h1></div><button onClick={endSession}>End session</button></div>{user ? <AccountPanel user={user} /> : <div className="panel"><p>Scan your library ID to see your borrowing history.</p><QrCapture label="your library ID" busy={busy} onToken={token => void scanUser(token)} /></div>}</>}
      {view === 'assistant' && <><div className="page-heading"><div><p className="eyebrow">Book discovery</p><h1>Ask LIBRAI</h1></div><button onClick={() => setView('home')}>Home</button></div><div className="panel"><form onSubmit={event => void askAssistant(event)}><label htmlFor="ai-query">What would you like to read?</label><div className="inline"><input id="ai-query" value={aiQuery} onChange={event => setAiQuery(event.target.value)} placeholder="Books about Philippine history" /><button className="primary" disabled={busy || aiQuery.trim().length < 2}>Ask</button></div></form>{aiAnswer && <div className="answer" role="status">{aiAnswer}</div>}{aiInteraction && !feedbackSent && <div className="inline feedback"><span>Was this helpful?</span><button disabled={busy} onClick={() => void sendFeedback(true)}>Yes</button><button disabled={busy} onClick={() => void sendFeedback(false)}>No</button></div>}{feedbackSent && <p role="status" className="verified">Thank you for your feedback.</p>}</div><div className="book-grid">{aiBooks.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}><div className="cover-placeholder">LIBRAI</div><strong>{book.title}</strong><span>{book.author}</span><small>{book.available_copies || 0} available</small></button>)}</div></>}
      {view === 'discover' && <><div className="page-heading"><div><p className="eyebrow">Book discovery</p><h1>Explore titles</h1></div><button onClick={() => setView('home')}>Home</button></div><div className="inline tabs">{(['recommended', 'popular', 'new'] as const).map(kind => <button key={kind} className={discoverKind === kind ? 'primary' : ''} onClick={() => void discover(kind)} disabled={busy}>{kind === 'new' ? 'New arrivals' : kind === 'popular' ? 'Popular' : 'Recommended'}</button>)}</div><div className="book-grid">{discoverBooks.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}><div className="cover-placeholder">LIBRAI</div><strong>{book.title}</strong><span>{book.author}</span></button>)}</div>{!discoverBooks.length && <div className="empty">No suggestions available right now.</div>}</>}
    </main><footer>LIBRAI · Library services <span>Ask a librarian if you need help.</span></footer>
  </div>
}

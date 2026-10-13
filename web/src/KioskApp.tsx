import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api, bookDetail, books, health, mediaUrl, verifyBook, verifyUser } from './api'
import type { ActiveBorrowing, Book, BookGrant, BorrowReceipt, Page, ReturnReceipt, UserGrant } from './api'
import { QrCapture } from './QrCapture'
import AccountPanel from './AccountPanel'
import KioskHome from './KioskHome'
import { BorrowFlow, ReturnFlow } from './KioskTransaction'
import StartupScreen from './StartupScreen'

type View = 'home' | 'search' | 'detail' | 'borrow' | 'return' | 'account' | 'assistant' | 'discover'
const SESSION_TIMEOUT_MS = 90_000

export default function KioskApp() {
  const [view, setView] = useState<View>('home')
  const [online, setOnline] = useState<boolean | null>(null)
  const [starting, setStarting] = useState(true)
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
  const [secondsLeft, setSecondsLeft] = useState(90)

  const endSession = useCallback(() => {
    setUser(null); setCopy(null); setReceipt(null); setActiveReturn(null)
    setAiQuery(''); setAiAnswer(''); setAiBooks([]); setAiInteraction(null); setFeedbackSent(false); setError(''); setView('home')
    lastActivity.current = Date.now(); setSecondsLeft(90)
  }, [])

  useEffect(() => {
    lastActivity.current = Date.now()
    const touch = () => { lastActivity.current = Date.now(); setSecondsLeft(90) }
    window.addEventListener('pointerdown', touch)
    window.addEventListener('keydown', touch)
    const interval = window.setInterval(() => {
      const remaining = Math.max(0, Math.ceil((SESSION_TIMEOUT_MS - (Date.now() - lastActivity.current)) / 1000))
      setSecondsLeft(remaining)
      if (remaining === 0) endSession()
    }, 1000)
    return () => { window.removeEventListener('pointerdown', touch); window.removeEventListener('keydown', touch); window.clearInterval(interval) }
  }, [endSession])

  useEffect(() => {
    let alive = true
    void Promise.all([health(), new Promise<void>(resolve => window.setTimeout(resolve, 800))])
      .then(([value]) => { if (alive) { setOnline(value); setStarting(false) } })
    const check = () => { void health().then(value => { if (alive) setOnline(value) }) }
    const timer = window.setInterval(check, 20_000)
    return () => { alive = false; window.clearInterval(timer) }
  }, [])

  const run = useCallback(async (action: () => Promise<void>) => {
    if (busy) return
    setBusy(true); setError('')
    try { await action(); setOnline(true) }
    catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The action could not be completed.')
      if (cause instanceof ApiError && cause.status === 0) setOnline(false)
    }
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
  function changeBorrowUser() { setUser(null); setCopy(null); setError('') }
  function changeBorrowBook() { setCopy(null); setError('') }
  function changeReturnBook() { setCopy(null); setActiveReturn(null); setError('') }

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

  const privateSession = !!(user || copy || activeReturn || receipt)

  if (starting) return <StartupScreen />

  return <div className="app kiosk">
    <header className="topbar"><div className="brand"><img className="brand-mark" src="/images/librai-symbol.png" alt="" /><span><strong>LIBRAI</strong><small>Library kiosk</small></span></div><div className="top-actions"><span className={`status ${online ? 'good' : 'bad'}`}>{online === null ? 'Connecting' : online ? 'Library online' : 'Library offline'}</span><button type="button" onClick={endSession}>End session</button></div></header>
    <main className="content">
      {online === false && <div className="connection-banner" role="alert"><div><strong>Library connection lost</strong><span>Borrowing, returns, and catalog updates need the server. Check the tablet connection.</span></div><button onClick={() => void health().then(setOnline)}>Try again</button></div>}
      {privateSession && secondsLeft <= 15 && <div className="session-warning" role="status"><strong>This session will clear in {secondsLeft} seconds.</strong><span>Touch the screen to keep working, or select End session to clear your information now.</span></div>}
      {error && <div className="alert error" role="alert">{error}</div>}
      {view === 'home' && <KioskHome query={query} busy={busy} online={online} onQuery={setQuery} onSearch={search => void loadBooks(search)} onBorrow={startBorrow} onReturn={startReturn} onAccount={() => { setView('account'); setError('') }} onAssistant={() => setView('assistant')} onDiscover={() => void discover('recommended')} />}
      {view === 'search' && <><div className="page-heading"><div><p className="eyebrow">Library catalog</p><h1>Find a book</h1><p>{catalog.total} titles found</p></div><button onClick={() => setView('home')}>Home</button></div><form className="search-form" onSubmit={event => { event.preventDefault(); void loadBooks(query) }}><input aria-label="Search books" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search title, author, or topic" /><button className="primary" disabled={busy}>Search</button></form><div className="book-grid">{catalog.items.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}>{(book.cover_url || book.cover_image) ? <img src={mediaUrl(book.cover_url || book.cover_image)} alt="" /> : <div className="cover-placeholder">LIBRAI</div>}<strong>{book.title}</strong><span>{book.author}</span><small>{book.available_copies || 0} available · {book.shelf_location || 'Ask the librarian'}</small></button>)}</div>{!catalog.items.length && <div className="empty">No books found. Try another search.</div>}<div className="pagination"><button disabled={busy || catalogOffset === 0} onClick={() => void loadBooks(query, Math.max(0, catalogOffset - 20))}>Previous</button><span>{catalog.total ? `${catalogOffset + 1}–${Math.min(catalogOffset + 20, catalog.total)} of ${catalog.total}` : '0 results'}</span><button disabled={busy || catalogOffset + 20 >= catalog.total} onClick={() => void loadBooks(query, catalogOffset + 20)}>Next</button></div></>}
      {view === 'detail' && selected && <><button onClick={() => setView('search')}>← Back to results</button><div className="detail"><div className="detail-cover">{(selected.cover_url || selected.cover_image) ? <img src={mediaUrl(selected.cover_url || selected.cover_image)} alt="Book cover" /> : 'LIBRAI'}</div><div><p className="eyebrow">{selected.category || 'Library catalog'}</p><h1>{selected.title}</h1><h2>by {selected.author}</h2><p>{selected.description || 'No description available.'}</p><div className="facts"><span>Available: {selected.available_copies || 0}</span><span>Shelf: {selected.shelf_location || 'Ask the librarian'}</span></div>{(selected.available_copies || 0) > 0 ? <button className="primary large" onClick={startBorrow}>Borrow a copy</button> : user ? <button className="primary large" disabled={busy} onClick={() => void reserveSelected()}>Reserve this title</button> : <button onClick={() => setView('account')}>Scan your ID to reserve</button>}</div></div></>}
      {view === 'borrow' && <BorrowFlow user={user} copy={copy} receipt={receipt} busy={busy} onUser={token => void scanUser(token)} onBook={token => void scanBorrowBook(token)} onChangeUser={changeBorrowUser} onChangeBook={changeBorrowBook} onConfirm={() => void confirmBorrow()} onFinish={endSession} />}
      {view === 'return' && <ReturnFlow copy={copy} activeReturn={activeReturn} receipt={receipt} busy={busy} onBook={token => void scanReturnBook(token)} onChangeBook={changeReturnBook} onConfirm={() => void confirmReturn()} onFinish={endSession} />}
      {view === 'account' && <><div className="page-heading"><div><p className="eyebrow">Private session</p><h1>My account</h1></div><button onClick={endSession}>End session</button></div>{user ? <AccountPanel user={user} /> : <div className="panel"><p>Scan your library ID to see your borrowing history.</p><QrCapture label="your library ID" busy={busy} onToken={token => void scanUser(token)} /></div>}</>}
      {view === 'assistant' && <><div className="page-heading"><div><p className="eyebrow">Book discovery</p><h1>Ask LIBRAI</h1></div><button onClick={() => setView('home')}>Home</button></div><div className="panel"><form onSubmit={event => void askAssistant(event)}><label htmlFor="ai-query">What would you like to read?</label><div className="inline"><input id="ai-query" value={aiQuery} onChange={event => setAiQuery(event.target.value)} placeholder="Books about Philippine history" /><button className="primary" disabled={busy || aiQuery.trim().length < 2}>Ask</button></div></form>{aiAnswer && <div className="answer" role="status">{aiAnswer}</div>}{aiInteraction && !feedbackSent && <div className="inline feedback"><span>Was this helpful?</span><button disabled={busy} onClick={() => void sendFeedback(true)}>Yes</button><button disabled={busy} onClick={() => void sendFeedback(false)}>No</button></div>}{feedbackSent && <p role="status" className="verified">Thank you for your feedback.</p>}</div><div className="book-grid">{aiBooks.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}><div className="cover-placeholder">LIBRAI</div><strong>{book.title}</strong><span>{book.author}</span><small>{book.available_copies || 0} available</small></button>)}</div></>}
      {view === 'discover' && <><div className="page-heading"><div><p className="eyebrow">Book discovery</p><h1>Explore titles</h1></div><button onClick={() => setView('home')}>Home</button></div><div className="inline tabs">{(['recommended', 'popular', 'new'] as const).map(kind => <button key={kind} className={discoverKind === kind ? 'primary' : ''} onClick={() => void discover(kind)} disabled={busy}>{kind === 'new' ? 'New arrivals' : kind === 'popular' ? 'Popular' : 'Recommended'}</button>)}</div><div className="book-grid">{discoverBooks.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}><div className="cover-placeholder">LIBRAI</div><strong>{book.title}</strong><span>{book.author}</span></button>)}</div>{!discoverBooks.length && <div className="empty">No suggestions available right now.</div>}</>}
    </main><footer>LIBRAI · Library services <span>Ask a librarian if you need help.</span></footer>
  </div>
}

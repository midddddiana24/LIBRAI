import { useCallback, useEffect, useRef, useState } from 'react'
import { LoaderCircle, Volume2, VolumeX } from 'lucide-react'
import { ApiError, api, bookDetail, books, health, mediaUrl, verifyBook, verifyUser } from './api'
import type { ActiveBorrowing, Book, BookGrant, BorrowReceipt, Page, ReturnReceipt, UserGrant } from './api'
import { QrCapture } from './QrCapture'
import AccountPanel from './AccountPanel'
import KioskHome from './KioskHome'
import MemberForm from './MemberForm'
import { BorrowFlow, ReturnFlow } from './KioskTransaction'
import StartupScreen from './StartupScreen'
import KioskChat from './KioskChat'
import type { ChatTurn } from './KioskChat'
import { resolveVoiceCommand } from './voiceCommands'
import useScreenMotion from './useScreenMotion'

type View = 'register' | 'home' | 'search' | 'detail' | 'borrow' | 'return' | 'account' | 'assistant' | 'discover'
type AIContext = { topics: string[]; level: 'beginner' | 'intermediate' | 'advanced' | null; available_only: boolean }
const SESSION_TIMEOUT_MS = 90_000

export default function KioskApp() {
  const [view, setView] = useState<View>('home')
  const [registrationMessage, setRegistrationMessage] = useState('')
  const [online, setOnline] = useState<boolean | null>(null)
  const [starting, setStarting] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [query, setQuery] = useState('')
  const [catalog, setCatalog] = useState<Page<Book>>({ items: [], total: 0 })
  const [catalogOffset, setCatalogOffset] = useState(0)
  const [selected, setSelected] = useState<Book | null>(null)
  const [detailOrigin, setDetailOrigin] = useState<'search' | 'assistant' | 'discover'>('search')
  const [user, setUser] = useState<UserGrant | null>(null)
  const [copy, setCopy] = useState<BookGrant | null>(null)
  const [receipt, setReceipt] = useState<BorrowReceipt | ReturnReceipt | null>(null)
  const [activeReturn, setActiveReturn] = useState<ActiveBorrowing | null>(null)
  const [aiQuery, setAiQuery] = useState('')
  const [aiContext, setAiContext] = useState<AIContext | null>(null)
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([])
  const [chatResetKey, setChatResetKey] = useState(0)
  const chatTurnId = useRef(0)
  const aiGeneration = useRef(0)
  const [voiceNotice, setVoiceNotice] = useState('')
  const [speaking, setSpeaking] = useState(false)
  const [discoverKind, setDiscoverKind] = useState<'recommended' | 'popular' | 'new'>('recommended')
  const [discoverBooks, setDiscoverBooks] = useState<Book[]>([])
  const lastActivity = useRef(0)
  const [secondsLeft, setSecondsLeft] = useState(90)
  const [sessionKey, setSessionKey] = useState(0)
  const screenRef = useRef<HTMLDivElement>(null)
  useScreenMotion(screenRef, `${starting}-${view}-${sessionKey}`)

  const clearAssistant = useCallback(() => {
    aiGeneration.current += 1
    setChatResetKey(key => key + 1)
    window.speechSynthesis?.cancel()
    setSpeaking(false); setAiContext(null); setChatTurns([])
    setAiQuery(''); setDiscoverBooks([])
  }, [])

  const endSession = useCallback(() => {
    clearAssistant()
    setVoiceNotice('')
    setSessionKey(current => current + 1)
    setUser(null); setCopy(null); setReceipt(null); setActiveReturn(null); setRegistrationMessage('')
    setError(''); setView('home')
    lastActivity.current = Date.now(); setSecondsLeft(90)
  }, [clearAssistant])

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
    if (view === 'assistant' || view === 'discover' || view === 'search') setDetailOrigin(view)
    await run(async () => { setSelected(await bookDetail(id)); setView('detail') })
  }

  function startBorrow() { setCopy(null); setReceipt(null); setView('borrow'); setError('') }
  function startReturn() { setCopy(null); setActiveReturn(null); setReceipt(null); setView('return'); setError('') }
  function changeBorrowUser() { clearAssistant(); setUser(null); setCopy(null); setError('') }
  function changeBorrowBook() { setCopy(null); setError('') }
  function changeReturnBook() { setCopy(null); setActiveReturn(null); setError('') }

  async function submitRegistration(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const payload = Object.fromEntries(new FormData(event.currentTarget))
    await run(async () => {
      const result = await api<{ message: string }>('/registrations', { method: 'POST', body: JSON.stringify(payload) })
      setRegistrationMessage(result.message)
    })
  }

  async function scanUser(token: string) {
    const generation = aiGeneration.current
    await run(async () => {
      const checked = await verifyUser(token)
      if (generation !== aiGeneration.current) return
      clearAssistant(); setUser(checked)
    })
  }

  async function scanBorrowBook(token: string) {
    await run(async () => { setCopy(await verifyBook(token)) })
  }

  async function confirmBorrow() {
    if (!user || !copy) return
    await run(async () => {
      const result = await api<BorrowReceipt>('/borrowings', { method: 'POST', body: JSON.stringify({ user_id: user.id, book_copy_id: copy.book_copy_id, user_verification_token: user.verification_token, book_verification_token: copy.verification_token }) })
      setReceipt(result); clearAssistant(); setUser(null); setCopy(null)
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

  async function askAssistant(text: string) {
    const question = text.trim()
    if (busy || online === false || question.length < 2 || question.length > 1000) return
    const generation = aiGeneration.current
    const id = ++chatTurnId.current
    setChatTurns(turns => [...turns.slice(-19), { id, question, answer: '', books: [], status: 'pending' }])
    setAiQuery('')
    await run(async () => {
      try {
        const result = await api<{ context?: AIContext | null; fallback_used?: boolean; answer?: string; message?: string; books?: Book[]; interaction_id?: number }>('/ai/search', { method: 'POST', body: JSON.stringify({ query: question, context: aiContext, ...(user ? { user_id: user.id, user_verification_token: user.verification_token } : {}) }) })
        if (generation !== aiGeneration.current) return
        setAiContext(result.context || null)
        setChatTurns(turns => turns.map(turn => turn.id === id ? { ...turn, answer: result.answer || result.message || 'No answer was returned. Please try again.', books: result.books || [], interactionId: result.interaction_id, fallback: !!result.fallback_used, status: 'done' } : turn))
      } catch (cause) {
        if (generation !== aiGeneration.current) return
        setChatTurns(turns => turns.map(turn => turn.id === id ? { ...turn, answer: 'Message not sent. Check the connection and try again.', status: 'failed' } : turn))
        throw cause
      }
    })
  }

  async function sendFeedback(id: number, helpful: boolean) {
    const turn = chatTurns.find(turn => turn.id === id)
    if (!turn?.interactionId) return
    const generation = aiGeneration.current
    await run(async () => {
      await api('/ai/feedback', { method: 'POST', body: JSON.stringify({ interaction_id: turn.interactionId, helpful, ...(user ? { user_id: user.id, user_verification_token: user.verification_token } : {}) }) })
      if (generation === aiGeneration.current) setChatTurns(turns => turns.map(item => item.id === id ? { ...item, feedback: helpful } : item))
    })
  }

  async function discover(kind: 'recommended' | 'popular' | 'new') {
    const generation = aiGeneration.current
    await run(async () => {
      const result = await api<Book[]>('/ai/recommend', { method: 'POST', body: JSON.stringify({ kind, ...(user ? { user_id: user.id, user_verification_token: user.verification_token } : {}) }) })
      if (generation !== aiGeneration.current) return
      setDiscoverBooks(result); setDiscoverKind(kind); setView('discover')
    })
  }

  function handleVoiceCommand(text: string) {
    const command = resolveVoiceCommand(text)
    if (!command) return
    setError('')
    switch (command.action) {
      case 'home': setView('home'); setVoiceNotice('Home opened.'); break
      case 'borrow': startBorrow(); setVoiceNotice('Borrowing opened. Scan your library ID to continue.'); break
      case 'return': startReturn(); setVoiceNotice('Returns opened. Scan the book QR code to continue.'); break
      case 'account': setView('account'); setVoiceNotice('Account opened. Scan your library ID to continue.'); break
      case 'assistant': setView('assistant'); setVoiceNotice('Assistant opened. Ask a question or use the microphone.'); break
      case 'discover': void discover(command.kind || 'recommended'); setVoiceNotice('Opening book suggestions.'); break
      case 'search': setQuery(command.query); void loadBooks(command.query); setVoiceNotice(command.query ? `Searching for ${command.query}.` : 'Opening the catalog.'); break
      case 'ask': setAiQuery(command.query); setView('assistant'); setVoiceNotice('Your words are ready. Tap Send to send them.'); break
    }
  }

  function readAloud(text: string) {
    if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) { setVoiceNotice('Read aloud is unavailable on this device.'); return }
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = /\b(manghiram|humiram|ibalik|libro|aklat|hanap|pahiram)\b/i.test(text) ? 'fil-PH' : 'en-US'
    utterance.rate = 0.94
    utterance.onstart = () => setSpeaking(true)
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = event => {
      setSpeaking(false)
      if (event.error !== 'canceled' && event.error !== 'interrupted') setVoiceNotice('This device could not read the text aloud. Check its speech settings.')
    }
    try { window.speechSynthesis.speak(utterance); window.speechSynthesis.resume() }
    catch { setSpeaking(false); setVoiceNotice('This device could not read the text aloud. Check its speech settings.') }
  }

  function stopReading() { window.speechSynthesis?.cancel(); setSpeaking(false) }

  async function reserveSelected() {
    if (!selected || !user) return
    await run(async () => {
      await api('/reservations', { method: 'POST', body: JSON.stringify({ user_id: user.id, book_id: selected.id, user_verification_token: user.verification_token }) })
      setError('')
      setView('account')
    })
  }

  const privateSession = !!(user || copy || activeReturn || receipt || chatTurns.length)

  if (starting) return <StartupScreen />

  return <div className="app kiosk" ref={screenRef}>
    <header className="topbar"><div className="brand"><img className="brand-mark" src="/images/librai-symbol-v2.png" alt="" /><span><strong>LIBRAI</strong><small>Library kiosk</small></span></div><div className="top-actions"><span className={`status ${online ? 'good' : 'bad'}`}>{online === null ? 'Connecting' : online ? 'Library online' : 'Library offline'}</span><button type="button" onClick={endSession}>End session</button></div></header>
    {busy && <div className="kiosk-activity" role="status" aria-live="polite"><LoaderCircle className="loading-spinner" aria-hidden="true" /><span>Working with the library…</span></div>}
    <main className="content" aria-busy={busy}>
      {online === false && <div className="connection-banner" role="alert"><div><strong>Library connection lost</strong><span>Borrowing, returns, and catalog updates need the server. Check the tablet connection.</span></div><button onClick={() => void health().then(setOnline)}>Try again</button></div>}
      {privateSession && secondsLeft <= 15 && <div className="session-warning" role="status"><strong>This session will clear in {secondsLeft} seconds.</strong><span>Touch the screen to keep working, or select End session to clear your information now.</span></div>}
      {error && <div className="alert error" role="alert">{error}</div>}
      {voiceNotice && <div className="voice-notice" role="status"><span>{voiceNotice}</span><button type="button" onClick={() => speaking ? stopReading() : readAloud(voiceNotice)}>{speaking ? <VolumeX aria-hidden="true" /> : <Volume2 aria-hidden="true" />}{speaking ? 'Stop reading' : 'Read aloud'}</button></div>}
      {view === 'home' && <KioskHome key={sessionKey} query={query} busy={busy} online={online} onSearch={search => void loadBooks(search)} onBorrow={startBorrow} onReturn={startReturn} onRegister={() => { setRegistrationMessage(''); setView('register'); setError('') }} onAccount={() => { setView('account'); setError('') }} onAssistant={() => setView('assistant')} onDiscover={() => void discover('recommended')} onVoiceCommand={handleVoiceCommand} onHearInstructions={() => readAloud('Welcome to LIBRAI. Tap Voice command, say borrow a book, return a book, or find books, then check the words before running the command.')} />}
      {view === 'search' && <><div className="page-heading"><div><p className="eyebrow">Library catalog</p><h1>Find a book</h1><p>{catalog.total} titles found</p></div><button onClick={() => setView('home')}>Home</button></div><form className="search-form" onSubmit={event => { event.preventDefault(); void loadBooks(query) }}><input aria-label="Search books" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search title, author, or topic" /><button className="primary" disabled={busy}>Search</button></form><div className="book-grid">{catalog.items.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}>{(book.cover_url || book.cover_image) ? <img src={mediaUrl(book.cover_url || book.cover_image)} alt="" /> : <div className="cover-placeholder">LIBRAI</div>}<strong>{book.title}</strong><span>{book.author}</span><small>{book.available_copies || 0} available · {book.shelf_location || 'Ask the librarian'}</small></button>)}</div>{!catalog.items.length && <div className="empty">No books found. Try another search.</div>}<div className="pagination"><button disabled={busy || catalogOffset === 0} onClick={() => void loadBooks(query, Math.max(0, catalogOffset - 20))}>Previous</button><span>{catalog.total ? `${catalogOffset + 1}–${Math.min(catalogOffset + 20, catalog.total)} of ${catalog.total}` : '0 results'}</span><button disabled={busy || catalogOffset + 20 >= catalog.total} onClick={() => void loadBooks(query, catalogOffset + 20)}>Next</button></div></>}
      {view === 'detail' && selected && <><button onClick={() => setView(detailOrigin)}>{detailOrigin === 'assistant' ? 'Back to chat' : 'Back to results'}</button><div className="detail"><div className="detail-cover">{(selected.cover_url || selected.cover_image) ? <img src={mediaUrl(selected.cover_url || selected.cover_image)} alt="Book cover" /> : 'LIBRAI'}</div><div><p className="eyebrow">{selected.category || 'Library catalog'}</p><h1>{selected.title}</h1><h2>by {selected.author}</h2><p>{selected.description || 'No description available.'}</p><div className="facts"><span>Available: {selected.available_copies || 0}</span><span>Shelf: {selected.shelf_location || 'Ask the librarian'}</span></div>{(selected.available_copies || 0) > 0 ? <button className="primary large" onClick={startBorrow}>Borrow a copy</button> : user ? <button className="primary large" disabled={busy} onClick={() => void reserveSelected()}>Reserve this title</button> : <button onClick={() => setView('account')}>Scan your ID to reserve</button>}</div></div></>}
      {view === 'register' && (registrationMessage ? <section className="panel registration-result" role="status"><h1>Registration request received</h1><p>{registrationMessage}</p><button onClick={endSession}>Finish and clear session</button></section> : <MemberForm key={sessionKey} publicRegistration busy={busy} onSubmit={event => void submitRegistration(event)} onCancel={endSession} />)}
      {view === 'borrow' && <BorrowFlow user={user} copy={copy} receipt={receipt} busy={busy} onUser={token => void scanUser(token)} onBook={token => void scanBorrowBook(token)} onChangeUser={changeBorrowUser} onChangeBook={changeBorrowBook} onConfirm={() => void confirmBorrow()} onFinish={endSession} />}
      {view === 'return' && <ReturnFlow copy={copy} activeReturn={activeReturn} receipt={receipt} busy={busy} onBook={token => void scanReturnBook(token)} onChangeBook={changeReturnBook} onConfirm={() => void confirmReturn()} onFinish={endSession} />}
      {view === 'account' && <><div className="page-heading"><div><p className="eyebrow">Private session</p><h1>My account</h1></div><button onClick={() => setView('home')}>Home</button></div>{user ? <AccountPanel user={user} /> : <div className="panel"><p>Scan your library ID to see your borrowing history.</p><QrCapture label="your library ID" busy={busy} onToken={token => void scanUser(token)} /></div>}</>}
      {view === 'assistant' && <><div className="page-heading"><div><h1>Ask LIBRAI</h1><p>Your library chat</p></div><button onClick={() => setView('home')}>Home</button></div><KioskChat turns={chatTurns} query={aiQuery} busy={busy} offline={online === false} personalized={!!user} topic={aiContext ? [aiContext.topics.join(', ') || 'all topics', aiContext.level, aiContext.available_only ? 'available only' : ''].filter(Boolean).join(' / ') : ''} sessionKey={chatResetKey} speaking={speaking} onQuery={setAiQuery} onAsk={text => void askAssistant(text)} onClear={clearAssistant} onBook={id => void showBook(id)} onRead={readAloud} onStop={stopReading} onFeedback={(id, helpful) => void sendFeedback(id, helpful)} /></>}
      {view === 'discover' && <section className="kiosk-discovery"><div className="page-heading"><div><p className="eyebrow">Book discovery</p><h1>Explore titles</h1></div><button onClick={() => setView('home')}>Home</button></div><p>{user ? 'Recommended titles use your borrowing history when available.' : 'Scan your ID in My account for personal recommendations.'}</p><div className="inline tabs">{(['recommended', 'popular', 'new'] as const).map(kind => <button key={kind} className={discoverKind === kind ? 'primary' : ''} onClick={() => void discover(kind)} disabled={busy}>{kind === 'new' ? 'New arrivals' : kind === 'popular' ? 'Popular' : 'Recommended'}</button>)}</div><div className="book-grid">{discoverBooks.map(book => <button className="book-card" key={book.id} onClick={() => void showBook(book.id)}><div className="cover-placeholder">LIBRAI</div><strong>{book.title}</strong><span>{book.author}</span></button>)}</div>{!discoverBooks.length && <div className="empty">No suggestions available right now.</div>}</section>}
    </main><footer>LIBRAI · Library services <span>Ask a librarian if you need help.</span></footer>
  </div>
}

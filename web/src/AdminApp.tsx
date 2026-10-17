import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowDownLeft, ArrowUpRight, BarChart3, BookOpen, Bookmark, Check, ChevronRight, CircleUserRound, ClipboardList, Clock3, LayoutDashboard, LoaderCircle, LogIn, LogOut, Mail, Menu, Plus, Receipt, RefreshCw, Settings2, ShieldCheck, UsersRound, X } from 'lucide-react'
import { ApiError, api, health, mediaUrl, type Book, type Page } from './api'
import ReportsPanel from './ReportsPanel'
import MemberForm from './MemberForm'
import KioskTileArt from './KioskTileArt'
import useScreenMotion from './useScreenMotion'

type Admin = { id: number; name: string; role: string }
type Section = 'dashboard' | 'books' | 'users' | 'borrowings' | 'returns' | 'reservations' | 'fines' | 'reports' | 'audit' | 'email' | 'settings'
type User = { id: number; student_id: string; library_card_number?: string | null; name: string; first_name: string; last_name: string; course: string; year_level: string; email?: string; account_status: string }
type Row = Record<string, unknown>
type Copy = { id: number; accession_number: string; status: string }

const sections: { id: Section; label: string }[] = [
  { id: 'dashboard', label: 'Overview' }, { id: 'books', label: 'Catalog' }, { id: 'users', label: 'Library users' },
  { id: 'borrowings', label: 'Borrowings' }, { id: 'returns', label: 'Returns' }, { id: 'reservations', label: 'Reservations' },
  { id: 'fines', label: 'Fines' }, { id: 'reports', label: 'Reports' }, { id: 'audit', label: 'Audit log' }, { id: 'email', label: 'Email deliveries' }, { id: 'settings', label: 'Settings' },
]
const sectionIcons = { dashboard: LayoutDashboard, books: BookOpen, users: UsersRound, borrowings: ArrowUpRight, returns: ArrowDownLeft, reservations: Bookmark, fines: Receipt, reports: BarChart3, audit: ClipboardList, email: Mail, settings: Settings2 }
const listPath: Partial<Record<Section, string>> = { borrowings: '/borrowings', returns: '/returns', reservations: '/reservations', fines: '/fines', audit: '/audit-logs', email: '/notifications/admin/email-deliveries' }
const metrics = [
  { label: 'Titles in catalog', key: 'total_books', Icon: BookOpen },
  { label: 'Copies available', key: 'available_copies', Icon: Check },
  { label: 'Active loans', key: 'borrowed_copies', Icon: ArrowUpRight },
  { label: 'Overdue loans', key: 'overdue_borrowings', Icon: Clock3 },
  { label: 'Library users', key: 'registered_users', Icon: UsersRound },
  { label: 'Reservations', key: 'active_reservations', Icon: Bookmark },
]

export default function AdminApp() {
  const [admin, setAdmin] = useState<Admin | null>(null)
  const [token, setToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [section, setSection] = useState<Section>('dashboard')
  const [online, setOnline] = useState<boolean | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [dashboard, setDashboard] = useState<Record<string, unknown>>({})
  const [bookPage, setBookPage] = useState<Page<Book>>({ items: [], total: 0 })
  const [userPage, setUserPage] = useState<Page<User>>({ items: [], total: 0 })
  const [rows, setRows] = useState<Row[]>([])
  const [settings, setSettings] = useState<Record<string, string>>({})
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [editingBook, setEditingBook] = useState<Book | null>(null)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [copiesBook, setCopiesBook] = useState<Book | null>(null)
  const [copies, setCopies] = useState<Copy[]>([])
  const [formOpen, setFormOpen] = useState(false)
  const [pendingOnly, setPendingOnly] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
  const screenRef = useRef<HTMLDivElement>(null)
  useScreenMotion(screenRef, `${Boolean(admin)}-${section}`)

  useEffect(() => { void health().then(setOnline) }, [])
  useEffect(() => {
    if (!token) return
    const timer = window.setInterval(() => {
      void api<Admin>('/auth/me', {}, token).then(setAdmin).catch((cause: unknown) => {
        if (cause instanceof ApiError && cause.status === 401) {
          setToken(''); setAdmin(null); setError('Your staff session expired. Please sign in again.')
        } else setOnline(false)
      })
    }, 60_000)
    return () => window.clearInterval(timer)
  }, [token])

  const load = useCallback(async (which: Section, bearer: string, nextOffset = 0, q = '', pending = pendingOnly) => {
    setBusy(true); setError('')
    try {
      if (which === 'dashboard') setDashboard(await api<Record<string, unknown>>('/admin/dashboard', {}, bearer))
      else if (which === 'books') setBookPage(await api<Page<Book>>(`/books?include_archived=true&q=${encodeURIComponent(q)}&offset=${nextOffset}&limit=20`, {}, bearer))
      else if (which === 'users') setUserPage(await api<Page<User>>(`/users?q=${encodeURIComponent(q)}&offset=${nextOffset}&limit=20${pending ? '&status=PENDING' : ''}`, {}, bearer))
      else if (which === 'settings') setSettings(await api<Record<string, string>>('/settings', {}, bearer))
      else if (listPath[which]) {
        const response = await api<Page<Row>>(`${listPath[which]}?offset=${nextOffset}&limit=20`, {}, bearer)
        setRows(response.items)
      }
      setOnline(true)
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Could not load this section.'
      setError(message)
      if (message.toLowerCase().includes('session')) { setAdmin(null); setToken('') }
    } finally { setBusy(false) }
  }, [pendingOnly])

  async function login(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const result = await api<{ access_token: string; user: Admin }>('/auth/login', { method: 'POST', body: JSON.stringify({ username: username.trim(), password }) })
      setToken(result.access_token); setAdmin(result.user); setPassword(''); setSection('dashboard')
      await load('dashboard', result.access_token)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Login failed.') }
    finally { setBusy(false) }
  }

  async function logout() {
    if (token) await api('/auth/logout', { method: 'POST' }, token).catch(() => undefined)
    setToken(''); setAdmin(null); setDashboard({}); setRows([]); setError('')
  }

  function navigate(next: Section) { setNotice(''); setSection(next); setNavOpen(false); setOffset(0); setSearch(''); setFormOpen(false); setPendingOnly(false); void load(next, token, 0, '', false) }

  async function submitBook(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const fields = Object.fromEntries(new FormData(event.currentTarget))
    const payload = { ...fields, initial_copy_count: Number(fields.initial_copy_count || 0) }
    setBusy(true); setError('')
    try {
      await api(`/books${editingBook ? `/${editingBook.id}` : ''}`, { method: editingBook ? 'PUT' : 'POST', body: JSON.stringify(payload) }, token)
      setFormOpen(false); setEditingBook(null); await load('books', token, offset, search)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not save book.') }
    finally { setBusy(false) }
  }

  async function submitUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const payload = Object.fromEntries(new FormData(event.currentTarget))
    const action = ((event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null)?.value
    if (action === 'approve') payload.status = 'ACTIVE'
    if (action === 'reject') payload.status = 'INACTIVE'
    setBusy(true); setError('')
    try {
      await api(`/users${editingUser ? `/${editingUser.id}` : ''}`, { method: editingUser ? 'PUT' : 'POST', body: JSON.stringify(payload) }, token)
      setFormOpen(false); setEditingUser(null); await load('users', token, offset, search)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not save user.') }
    finally { setBusy(false) }
  }

  async function saveSetting(key: string, value: string) {
    setBusy(true); setError('')
    try { await api(`/settings/${encodeURIComponent(key)}`, { method: 'PUT', body: JSON.stringify({ value }) }, token); await load('settings', token) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not save setting.') }
    finally { setBusy(false) }
  }

  async function openCopies(book: Book) {
    setCopiesBook(book); setError('')
    try { setCopies(await api<Copy[]>(`/books/${book.id}/copies`, {}, token)) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load copies.') }
  }

  async function addCopies(quantity: number) {
    if (!copiesBook) return
    setBusy(true); setError('')
    try {
      await api(`/books/${copiesBook.id}/copies`, { method: 'POST', body: JSON.stringify({ quantity }) }, token)
      await openCopies(copiesBook); await load('books', token, offset, search)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not add copies.') }
    finally { setBusy(false) }
  }

  async function downloadQr(path: string) {
    setError('')
    try {
      const result = await api<{ download_url: string }>(path, {}, token)
      const url = mediaUrl(result.download_url)
      if (url) window.open(url, '_blank', 'noopener,noreferrer')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not get QR download.') }
  }

  async function downloadSheet() {
    if (!copiesBook) return
    setError('')
    try {
      const result = await api<{ download_url: string }>(`/books/${copiesBook.id}/copies/qr-sheet`, { method: 'POST' }, token)
      const url = mediaUrl(result.download_url)
      if (url) window.open(url, '_blank', 'noopener,noreferrer')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not create QR sheet.') }
  }

  async function emailQr(user: User) {
    if (!window.confirm(`Email the library ID QR to ${user.email}? Confirm this address belongs to the member.`)) return
    setBusy(true); setError(''); setNotice('')
    try {
      const result = await api<{ message: string }>(`/users/${user.id}/email-qr`, { method: 'POST' }, token)
      setNotice(result.message)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not queue email.') }
    finally { setBusy(false) }
  }

  async function rowAction(row: Row) {
    const id = Number(row.id)
    if (!Number.isInteger(id)) return
    if (section === 'fines' && window.confirm('Mark this fine as paid? Confirm payment was received first.')) {
      await api(`/fines/${id}/pay`, { method: 'POST', body: JSON.stringify({}) }, token)
    } else if (section === 'reservations' && window.confirm('Cancel this reservation?')) {
      await api(`/reservations/${id}`, { method: 'DELETE' }, token)
    } else if (section === 'email') {
      if (row.status === 'pending') {
        if (!window.confirm('Send this email to the listed recipient now?')) return
        const result = await api<{ message: string }>(`/notifications/admin/email-deliveries/${id}/send`, { method: 'POST' }, token)
        setNotice(result.message)
      } else {
        await api(`/notifications/admin/email-deliveries/${id}/retry`, { method: 'POST' }, token)
        setNotice('Email queued for retry. Use Send now, or wait for enabled automatic delivery.')
      }
    } else return
    await load(section, token, offset)
  }

  if (!admin) return <div className="login-page" ref={screenRef}>
    <div className="login-intro">
      <div className="brand"><img className="brand-mark" src="/images/librai-symbol-v2.png" alt="" /><span><strong>LIBRAI</strong><small>Library administration</small></span></div>
      <div className="login-message"><h2>A clear view of your library.</h2><p>Your catalog, readers, and daily circulation. All in one workspace.</p></div>
      <div className="login-illustration" aria-hidden="true"><KioskTileArt kind="discover" /></div>
      <span className="login-intro-foot">Built around the way your library works.</span>
    </div>
    <div className="login-card"><span className="login-symbol"><ShieldCheck aria-hidden="true" /></span><h1>Welcome back.</h1><p>Sign in to your staff workspace.</p>
      {error && <p role="alert" className="alert error">{error}</p>}
      <form onSubmit={event => void login(event)} aria-busy={busy}>
        <label htmlFor="username">Username or email</label><input id="username" autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required />
        <label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required />
        <button className="primary large" disabled={busy}>{busy ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <LogIn aria-hidden="true" />}{busy ? 'Signing in...' : 'Sign in'}</button>
      </form><p className="login-help">Need access? Contact your library administrator.</p>
    </div>
  </div>

  return <div className="app admin" ref={screenRef}>
    <aside className={`sidebar ${navOpen ? 'nav-open' : ''}`}>
      <div className="sidebar-top"><div className="brand"><img className="brand-mark" src="/images/librai-symbol-v2.png" alt="" /><span><strong>LIBRAI</strong><small>Staff workspace</small></span></div>
        <button className="sidebar-toggle" aria-expanded={navOpen} aria-controls="staff-navigation" onClick={() => setNavOpen(!navOpen)}>{navOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}<span>{navOpen ? 'Close menu' : 'Menu'}</span></button>
      </div>
      <nav id="staff-navigation" aria-label="Admin sections">{sections.filter(item => item.id !== 'settings' || admin.role === 'SUPER_ADMIN').map(item => {
        const Icon = sectionIcons[item.id]
        return <button className={section === item.id ? 'active' : ''} aria-current={section === item.id ? 'page' : undefined} key={item.id} onClick={() => navigate(item.id)} disabled={busy}><Icon aria-hidden="true" />{item.label}</button>
      })}</nav>
      <div className="sidebar-bottom"><span><ShieldCheck aria-hidden="true" />Library administration</span><button className="logout" onClick={() => void logout()}><LogOut aria-hidden="true" />Sign out</button></div>
    </aside>
    <div className="admin-main"><header className="admin-header"><div><span>Workspace</span><ChevronRight aria-hidden="true" /><strong>{sections.find(item => item.id === section)?.label}</strong></div><div><span className={`status ${online ? 'good' : 'bad'}`}>{online ? 'Server connected' : 'Connection problem'}</span><span className="staff-identity"><CircleUserRound aria-hidden="true" />{admin.name}</span></div></header>
      {busy && <div className="admin-activity" role="status" aria-live="polite"><LoaderCircle className="loading-spinner" aria-hidden="true" />Updating library information...</div>}
      <main className="admin-content" aria-busy={busy}>{notice && <div className="alert" role="status">{notice}</div>}{error && <div className="alert error" role="alert">{error}</div>}
        {section === 'dashboard' && <>
          <div className="page-heading"><div><h1>Library dashboard</h1><p>Everything you need to keep the library moving.</p></div><button className="icon-button" disabled={busy} onClick={() => void load(section, token)}><RefreshCw aria-hidden="true" />Refresh</button></div>
          <div className="metric-grid">{metrics.map(({label, key, Icon}) => <div className={`metric metric-${key}`} key={key}><span className="metric-icon"><Icon aria-hidden="true" /></span><strong>{String(dashboard[key] ?? '—')}</strong><span>{label}</span></div>)}</div>
          <div className="dashboard-workspace">
            <section className="panel workspace-panel"><div className="workspace-panel-heading"><span className="panel-icon"><ArrowUpRight aria-hidden="true" /></span><div><h2>Circulation today</h2><p>Current activity from your library.</p></div></div>
              <div className="today-totals"><div><strong>{String(dashboard.transactions_today ?? '—')}</strong><span>Borrowings</span></div><div><strong>{String(dashboard.renewals_today ?? '—')}</strong><span>Renewals</span></div></div>
              <button className="workspace-link" onClick={() => navigate('borrowings')}>View borrowing records<ChevronRight aria-hidden="true" /></button>
            </section>
            <section className="panel workspace-panel"><div className="workspace-panel-heading"><span className="panel-icon"><ClipboardList aria-hidden="true" /></span><div><h2>Keep things moving</h2><p>Your everyday library tasks.</p></div></div>
              <div className="dashboard-shortcuts"><button onClick={() => navigate('books')}><BookOpen aria-hidden="true" /><span><strong>Manage catalog</strong><small>Books, copies, and QR codes</small></span><ChevronRight aria-hidden="true" /></button><button onClick={() => navigate('users')}><UsersRound aria-hidden="true" /><span><strong>Manage readers</strong><small>Library IDs and user records</small></span><ChevronRight aria-hidden="true" /></button><button onClick={() => navigate('reports')}><BarChart3 aria-hidden="true" /><span><strong>Open reports</strong><small>Review and export library activity</small></span><ChevronRight aria-hidden="true" /></button></div>
            </section>
          </div>
        </>}
    {(section === 'books' || section === 'users') && <><div className="page-heading"><div><p className="eyebrow">Management</p><h1>{section === 'books' ? 'Catalog' : 'Library users'}</h1><p>{section === 'books' ? bookPage.total : userPage.total} records</p></div><button className="primary icon-button" onClick={() => { setEditingBook(null); setEditingUser(null); setFormOpen(true) }}><Plus aria-hidden="true" />Add {section === 'books' ? 'book' : 'user'}</button></div><form className="search-form" onSubmit={event => { event.preventDefault(); setOffset(0); void load(section, token, 0, search) }}><input aria-label="Search records" placeholder="Search records" value={search} onChange={event => setSearch(event.target.value)} /><button>Search</button></form>{formOpen && section === 'books' && <form className="panel form-grid" onSubmit={event => void submitBook(event)}><h2>{editingBook ? 'Edit book' : 'Add book'}</h2>{[['isbn', 'ISBN'], ['title', 'Title'], ['author', 'Author'], ['category', 'Category'], ['shelf_location', 'Shelf location'], ['publisher', 'Publisher']].map(([name, label]) => <label key={name}>{label}<input name={name} defaultValue={String(editingBook?.[name as keyof Book] || '')} required={['isbn', 'title', 'author', 'category', 'shelf_location'].includes(name)} /></label>)}{!editingBook && <label>Initial copies<input name="initial_copy_count" type="number" min="0" max="100" defaultValue="1" /></label>}<div className="inline"><button className="primary" disabled={busy}>Save book</button><button type="button" onClick={() => setFormOpen(false)}>Cancel</button></div></form>}{formOpen && section === 'users' && <MemberForm key={editingUser?.id || 'new-user'} user={editingUser} busy={busy} onSubmit={event => void submitUser(event)} onCancel={() => setFormOpen(false)} />}{section === 'users' && <div className="registration-filters"><button disabled={busy} aria-pressed={!pendingOnly} onClick={() => { setPendingOnly(false); setOffset(0); void load('users', token, 0, search, false) }}>All users</button><button disabled={busy} aria-pressed={pendingOnly} onClick={() => { setPendingOnly(true); setOffset(0); void load('users', token, 0, search, true) }}>Pending registrations</button></div>}{section === 'books' && copiesBook && <div className="panel"><div className="page-heading"><h2>Copies: {copiesBook.title}</h2><button onClick={() => setCopiesBook(null)}>Close</button></div><div className="inline"><button onClick={() => void addCopies(1)} disabled={busy}>Add copy</button><button onClick={() => void downloadSheet()} disabled={!copies.length}>Download QR sheet</button></div><div className="list">{copies.map(copy => <div key={copy.id}><span><strong>{copy.accession_number}</strong> ? {copy.status}</span><button onClick={() => void downloadQr(`/book-copies/${copy.id}/qr`)}>Download QR</button></div>)}</div></div>}<div className="table-wrap"><table><thead><tr>{section === 'books' ? <><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th><th></th></> : <><th>Name</th><th>Student ID</th><th>Course</th><th>Status</th><th></th></>}</tr></thead><tbody>{section === 'books' ? bookPage.items.map(book => <tr key={book.id}><td>{book.title}</td><td>{book.author}</td><td>{book.isbn}</td><td>{book.available_copies ?? 0}</td><td><button onClick={() => { setEditingBook(book); setFormOpen(true) }}>Edit</button> <button onClick={() => void openCopies(book)}>Copies & QR</button></td></tr>) : userPage.items.map(user => <tr key={user.id}><td>{user.name}</td><td>{user.student_id}{user.library_card_number && <small className="library-card-label">Library: {user.library_card_number}</small>}</td><td>{user.course}</td><td>{user.account_status}</td><td><button onClick={() => { setEditingUser(user); setFormOpen(true) }}>{user.account_status === 'pending' ? 'Review request' : 'Edit'}</button> {user.account_status !== 'pending' && <button onClick={() => void downloadQr(`/users/${user.id}/qr`)}>QR</button>} {user.account_status === 'active' && user.email && <button disabled={busy} onClick={() => void emailQr(user)}>Email QR</button>}</td></tr>)}</tbody></table></div><div className="pagination"><button disabled={busy || offset === 0} onClick={() => { const next = Math.max(0, offset - 20); setOffset(next); void load(section, token, next, search) }}>Previous</button><span>{offset + 1}–{Math.min(offset + 20, section === 'books' ? bookPage.total : userPage.total)}</span><button disabled={busy || offset + 20 >= (section === 'books' ? bookPage.total : userPage.total)} onClick={() => { const next = offset + 20; setOffset(next); void load(section, token, next, search) }}>Next</button></div></>}
    {listPath[section] && <>{section === 'email' && <p className="alert">Pending emails can be sent individually with Send now. Automatic delivery must be enabled by the server operator. Sent means the provider accepted the email; check the inbox or spam folder.</p>}<div className="page-heading"><div><p className="eyebrow">Records</p><h1>{sections.find(item => item.id === section)?.label}</h1></div><button disabled={busy} onClick={() => void load(section, token, offset)}>Refresh</button></div><div className="table-wrap"><table><thead><tr>{Object.keys(rows[0] || {}).slice(0, 7).map(key => <th key={key}>{key.replaceAll('_', ' ')}</th>)}{['fines', 'reservations', 'email'].includes(section) && <th>Action</th>}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{Object.values(row).slice(0, 7).map((value, column) => <td key={column}>{typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}</td>)}{['fines', 'reservations', 'email'].includes(section) && <td><button disabled={busy || (section === 'email' ? !['pending', 'failed'].includes(String(row.status)) : section === 'fines' ? row.status !== 'unpaid' : !['active', 'ready'].includes(String(row.status)))} onClick={() => void rowAction(row).catch(cause => setError(cause instanceof Error ? cause.message : 'Action failed.'))}>{section === 'email' ? (row.status === 'pending' ? 'Send now' : 'Retry') : section === 'fines' ? 'Mark paid' : 'Cancel'}</button></td>}</tr>)}</tbody></table>{!rows.length && <div className="empty">No records found.</div>}</div><div className="pagination"><button disabled={busy || offset === 0} onClick={() => { const next = Math.max(0, offset - 20); setOffset(next); void load(section, token, next) }}>Previous</button><span>Page {Math.floor(offset / 20) + 1}</span><button disabled={busy || rows.length < 20} onClick={() => { const next = offset + 20; setOffset(next); void load(section, token, next) }}>Next</button></div></>}
    {section === 'settings' && <><div className="page-heading"><div><p className="eyebrow">Super admin</p><h1>Library policies</h1></div></div><div className="settings-list">{Object.entries(settings).map(([key, value]) => <form className="panel" key={key} onSubmit={event => { event.preventDefault(); const field = event.currentTarget.elements.namedItem('value') as HTMLInputElement; void saveSetting(key, field.value) }}><label>{key.replaceAll('_', ' ').toLowerCase()}<input name="value" defaultValue={value} /></label><button disabled={busy}>Save</button></form>)}</div></>}
    {section === 'reports' && <ReportsPanel token={token} />}
  </main></div></div>
}

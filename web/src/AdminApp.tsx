import { useCallback, useEffect, useState } from 'react'
import { ArrowDownLeft, ArrowUpRight, BarChart3, BookOpen, Bookmark, ClipboardList, LayoutDashboard, LoaderCircle, Mail, Receipt, Settings2, UsersRound } from 'lucide-react'
import { ApiError, api, health, mediaUrl, type Book, type Page } from './api'
import ReportsPanel from './ReportsPanel'

type Admin = { id: number; name: string; role: string }
type Section = 'dashboard' | 'books' | 'users' | 'borrowings' | 'returns' | 'reservations' | 'fines' | 'reports' | 'audit' | 'email' | 'settings'
type User = { id: number; student_id: string; name: string; first_name: string; last_name: string; course: string; year_level: string; email?: string; account_status: string }
type Row = Record<string, unknown>
type Copy = { id: number; accession_number: string; status: string }

const sections: { id: Section; label: string }[] = [
  { id: 'dashboard', label: 'Overview' }, { id: 'books', label: 'Catalog' }, { id: 'users', label: 'Library users' },
  { id: 'borrowings', label: 'Borrowings' }, { id: 'returns', label: 'Returns' }, { id: 'reservations', label: 'Reservations' },
  { id: 'fines', label: 'Fines' }, { id: 'reports', label: 'Reports' }, { id: 'audit', label: 'Audit log' }, { id: 'email', label: 'Email deliveries' }, { id: 'settings', label: 'Settings' },
]
const sectionIcons = { dashboard: LayoutDashboard, books: BookOpen, users: UsersRound, borrowings: ArrowUpRight, returns: ArrowDownLeft, reservations: Bookmark, fines: Receipt, reports: BarChart3, audit: ClipboardList, email: Mail, settings: Settings2 }
const listPath: Partial<Record<Section, string>> = { borrowings: '/borrowings', returns: '/returns', reservations: '/reservations', fines: '/fines', audit: '/audit-logs', email: '/notifications/admin/email-deliveries' }

export default function AdminApp() {
  const [admin, setAdmin] = useState<Admin | null>(null)
  const [token, setToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [section, setSection] = useState<Section>('dashboard')
  const [online, setOnline] = useState<boolean | null>(null)
  const [error, setError] = useState('')
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

  const load = useCallback(async (which: Section, bearer: string, nextOffset = 0, q = '') => {
    setBusy(true); setError('')
    try {
      if (which === 'dashboard') setDashboard(await api<Record<string, unknown>>('/admin/dashboard', {}, bearer))
      else if (which === 'books') setBookPage(await api<Page<Book>>(`/books?include_archived=true&q=${encodeURIComponent(q)}&offset=${nextOffset}&limit=20`, {}, bearer))
      else if (which === 'users') setUserPage(await api<Page<User>>(`/users?q=${encodeURIComponent(q)}&offset=${nextOffset}&limit=20`, {}, bearer))
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
  }, [])

  async function login(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const result = await api<{ access_token: string; user: Admin }>('/auth/login', { method: 'POST', body: JSON.stringify({ username: username.trim(), password }) })
      setToken(result.access_token); setAdmin(result.user); setPassword('')
      await load('dashboard', result.access_token)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Login failed.') }
    finally { setBusy(false) }
  }

  async function logout() {
    if (token) await api('/auth/logout', { method: 'POST' }, token).catch(() => undefined)
    setToken(''); setAdmin(null); setDashboard({}); setRows([]); setError('')
  }

  function navigate(next: Section) { setSection(next); setOffset(0); setSearch(''); setFormOpen(false); void load(next, token) }

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

  async function rowAction(row: Row) {
    const id = Number(row.id)
    if (!Number.isInteger(id)) return
    if (section === 'fines' && window.confirm('Mark this fine as paid? Confirm payment was received first.')) {
      await api(`/fines/${id}/pay`, { method: 'POST', body: JSON.stringify({}) }, token)
    } else if (section === 'reservations' && window.confirm('Cancel this reservation?')) {
      await api(`/reservations/${id}`, { method: 'DELETE' }, token)
    } else return
    await load(section, token, offset)
  }

  if (!admin) return <div className="login-page"><div className="login-intro"><div className="brand"><img className="brand-mark" src="/images/librai-symbol.png" alt="" /><span><strong>LIBRAI</strong><small>Library administration</small></span></div><div><p className="eyebrow">Staff workspace</p><h2>Keep the library moving.</h2><p>Manage the catalog, readers, and daily circulation in one place.</p></div><span className="login-intro-foot">LIBRAI · Library operations</span></div><div className="login-card"><p className="eyebrow">Staff sign in</p><h1>Welcome back.</h1><p>Enter your library staff credentials.</p>{error && <p role="alert" className="alert error">{error}</p>}<form onSubmit={event => void login(event)} aria-busy={busy}><label htmlFor="username">Username or email</label><input id="username" autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required /><label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required /><button className="primary large" disabled={busy}>{busy && <LoaderCircle className="loading-spinner" aria-hidden="true" />}{busy ? 'Signing in…' : 'Sign in'}</button></form></div></div>

  return <div className="app admin"><aside className="sidebar"><div className="brand"><img className="brand-mark" src="/images/librai-symbol.png" alt="" /><span><strong>LIBRAI</strong><small>Administration</small></span></div><p className="sidebar-label">Workspace</p><nav aria-label="Admin sections">{sections.filter(item => item.id !== 'settings' || admin.role === 'SUPER_ADMIN').map(item => { const Icon = sectionIcons[item.id]; return <button className={section === item.id ? 'active' : ''} aria-current={section === item.id ? 'page' : undefined} key={item.id} onClick={() => navigate(item.id)} disabled={busy}><Icon aria-hidden="true" />{item.label}</button> })}</nav><button className="logout" onClick={() => void logout()}>Sign out</button></aside><div className="admin-main"><header className="admin-header"><div><strong>{sections.find(item => item.id === section)?.label}</strong><span>Library operations</span></div><div><span className={`status ${online ? 'good' : 'bad'}`}>{online ? 'Server connected' : 'Connection problem'}</span><span>{admin.name}</span></div></header>{busy && <div className="admin-activity" role="status" aria-live="polite"><LoaderCircle className="loading-spinner" aria-hidden="true" /> Updating library information…</div>}<main className="admin-content" aria-busy={busy}>{error && <div className="alert error" role="alert">{error}</div>}
    {section === 'dashboard' && <><div className="page-heading"><div><p className="eyebrow">Overview</p><h1>Library dashboard</h1></div><button onClick={() => void load(section, token)}>Refresh</button></div><div className="metric-grid">{[['Titles', 'total_books'], ['Copies available', 'available_copies'], ['Active loans', 'borrowed_copies'], ['Overdue', 'overdue_borrowings'], ['Library users', 'registered_users'], ['Reservations', 'active_reservations']].map(([label, key]) => <div className="metric" key={key}><span>{label}</span><strong>{String(dashboard[key] ?? '—')}</strong></div>)}</div><div className="panel"><h2>Today</h2><p>{String(dashboard.transactions_today ?? 0)} borrowings · {String(dashboard.renewals_today ?? 0)} renewals</p></div></>}
    {(section === 'books' || section === 'users') && <><div className="page-heading"><div><p className="eyebrow">Management</p><h1>{section === 'books' ? 'Catalog' : 'Library users'}</h1><p>{section === 'books' ? bookPage.total : userPage.total} records</p></div><button className="primary" onClick={() => { setEditingBook(null); setEditingUser(null); setFormOpen(true) }}>Add {section === 'books' ? 'book' : 'user'}</button></div><form className="search-form" onSubmit={event => { event.preventDefault(); setOffset(0); void load(section, token, 0, search) }}><input aria-label="Search records" placeholder="Search records" value={search} onChange={event => setSearch(event.target.value)} /><button>Search</button></form>{formOpen && section === 'books' && <form className="panel form-grid" onSubmit={event => void submitBook(event)}><h2>{editingBook ? 'Edit book' : 'Add book'}</h2>{[['isbn', 'ISBN'], ['title', 'Title'], ['author', 'Author'], ['category', 'Category'], ['shelf_location', 'Shelf location'], ['publisher', 'Publisher']].map(([name, label]) => <label key={name}>{label}<input name={name} defaultValue={String(editingBook?.[name as keyof Book] || '')} required={['isbn', 'title', 'author', 'category', 'shelf_location'].includes(name)} /></label>)}{!editingBook && <label>Initial copies<input name="initial_copy_count" type="number" min="0" max="100" defaultValue="1" /></label>}<div className="inline"><button className="primary" disabled={busy}>Save book</button><button type="button" onClick={() => setFormOpen(false)}>Cancel</button></div></form>}{formOpen && section === 'users' && <form className="panel form-grid" onSubmit={event => void submitUser(event)}><h2>{editingUser ? 'Edit user' : 'Register user'}</h2>{[['student_id', 'Student ID'], ['first_name', 'First name'], ['last_name', 'Last name'], ['course', 'Course'], ['year_level', 'Year level'], ['email', 'Email']].filter(([name]) => !editingUser || name !== 'student_id').map(([name, label]) => <label key={name}>{label}<input name={name} defaultValue={String(editingUser?.[name as keyof User] || '')} required={!['email'].includes(name)} /></label>)}<label>Status<select name="status" defaultValue={editingUser?.account_status.toUpperCase() || 'ACTIVE'}><option value="ACTIVE">Active</option><option value="INACTIVE">Inactive</option><option value="SUSPENDED">Suspended</option></select></label><div className="inline"><button className="primary" disabled={busy}>Save user</button><button type="button" onClick={() => setFormOpen(false)}>Cancel</button></div></form>}{section === 'books' && copiesBook && <div className="panel"><div className="page-heading"><h2>Copies: {copiesBook.title}</h2><button onClick={() => setCopiesBook(null)}>Close</button></div><div className="inline"><button onClick={() => void addCopies(1)} disabled={busy}>Add copy</button><button onClick={() => void downloadSheet()} disabled={!copies.length}>Download QR sheet</button></div><div className="list">{copies.map(copy => <div key={copy.id}><span><strong>{copy.accession_number}</strong> ? {copy.status}</span><button onClick={() => void downloadQr(`/book-copies/${copy.id}/qr`)}>Download QR</button></div>)}</div></div>}<div className="table-wrap"><table><thead><tr>{section === 'books' ? <><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th><th></th></> : <><th>Name</th><th>Student ID</th><th>Course</th><th>Status</th><th></th></>}</tr></thead><tbody>{section === 'books' ? bookPage.items.map(book => <tr key={book.id}><td>{book.title}</td><td>{book.author}</td><td>{book.isbn}</td><td>{book.available_copies ?? 0}</td><td><button onClick={() => { setEditingBook(book); setFormOpen(true) }}>Edit</button> <button onClick={() => void openCopies(book)}>Copies & QR</button></td></tr>) : userPage.items.map(user => <tr key={user.id}><td>{user.name}</td><td>{user.student_id}</td><td>{user.course}</td><td>{user.account_status}</td><td><button onClick={() => { setEditingUser(user); setFormOpen(true) }}>Edit</button> <button onClick={() => void downloadQr(`/users/${user.id}/qr`)}>QR</button></td></tr>)}</tbody></table></div><div className="pagination"><button disabled={busy || offset === 0} onClick={() => { const next = Math.max(0, offset - 20); setOffset(next); void load(section, token, next, search) }}>Previous</button><span>{offset + 1}–{Math.min(offset + 20, section === 'books' ? bookPage.total : userPage.total)}</span><button disabled={busy || offset + 20 >= (section === 'books' ? bookPage.total : userPage.total)} onClick={() => { const next = offset + 20; setOffset(next); void load(section, token, next, search) }}>Next</button></div></>}
    {listPath[section] && <><div className="page-heading"><div><p className="eyebrow">Records</p><h1>{sections.find(item => item.id === section)?.label}</h1></div><button disabled={busy} onClick={() => void load(section, token, offset)}>Refresh</button></div><div className="table-wrap"><table><thead><tr>{Object.keys(rows[0] || {}).slice(0, 7).map(key => <th key={key}>{key.replaceAll('_', ' ')}</th>)}{['fines', 'reservations'].includes(section) && <th>Action</th>}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{Object.values(row).slice(0, 7).map((value, column) => <td key={column}>{typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}</td>)}{['fines', 'reservations'].includes(section) && <td><button disabled={busy || (section === 'fines' ? row.status !== 'unpaid' : !['active', 'ready'].includes(String(row.status)))} onClick={() => void rowAction(row).catch(cause => setError(cause instanceof Error ? cause.message : 'Action failed.'))}>{section === 'fines' ? 'Mark paid' : 'Cancel'}</button></td>}</tr>)}</tbody></table>{!rows.length && <div className="empty">No records found.</div>}</div><div className="pagination"><button disabled={busy || offset === 0} onClick={() => { const next = Math.max(0, offset - 20); setOffset(next); void load(section, token, next) }}>Previous</button><span>Page {Math.floor(offset / 20) + 1}</span><button disabled={busy || rows.length < 20} onClick={() => { const next = offset + 20; setOffset(next); void load(section, token, next) }}>Next</button></div></>}
    {section === 'settings' && <><div className="page-heading"><div><p className="eyebrow">Super admin</p><h1>Library policies</h1></div></div><div className="settings-list">{Object.entries(settings).map(([key, value]) => <form className="panel" key={key} onSubmit={event => { event.preventDefault(); const field = event.currentTarget.elements.namedItem('value') as HTMLInputElement; void saveSetting(key, field.value) }}><label>{key.replaceAll('_', ' ').toLowerCase()}<input name="value" defaultValue={value} /></label><button disabled={busy}>Save</button></form>)}</div></>}
    {section === 'reports' && <ReportsPanel token={token} />}
  </main></div></div>
}

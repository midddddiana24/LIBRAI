import UtilityMenu from './UtilityMenu'
import GuidedHelp from './GuidedHelp'
import AppInfo from './AppInfo'
import { AdminConfirmation, AdminPagination, AdminTable, StatusBadge, type Confirmation, type AdminColumn } from './AdminUx'
import { adminValue } from './adminValue'
import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowDownLeft, ArrowUpRight, BarChart3, BookOpen, Bookmark, Check, ChevronRight, CircleUserRound, ClipboardList, Clock3, LayoutDashboard, LoaderCircle, LogIn, LogOut, Mail, Menu, Plus, Receipt, RefreshCw, Settings2, ShieldCheck, UsersRound, X } from 'lucide-react'
import { ApiError, api, health, downloadFile, type Book, type Page } from './api'
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
const recordColumns: Partial<Record<Section, AdminColumn[]>> = {
  borrowings: [['transaction_id', 'Loan'], ['user_name', 'Member'], ['student_id', 'Student ID'], ['book_title', 'Book'], ['due_at', 'Due date'], ['status', 'Status']].map(([key, label]) => ({ key, label, ...(key === 'status' ? { render: (row: Row) => <StatusBadge value={['active', 'overdue'].includes(String(row.status)) && new Date(String(row.due_at)).getTime() < Date.now() ? 'overdue' : row.status} /> } : {}) })),
  returns: [['transaction_id', 'Return'], ['user_name', 'Member'], ['student_id', 'Student ID'], ['book', 'Book'], ['returned_at', 'Returned'], ['status', 'Status']].map(([key, label]) => ({ key, label })),
  reservations: [['id', 'Reservation'], ['user_name', 'Member'], ['student_id', 'Student ID'], ['book_title', 'Book'], ['reserved_at', 'Reserved'], ['status', 'Status']].map(([key, label]) => ({ key, label })),
  fines: [['id', 'Fine'], ['user_id', 'Member ID'], ['book_title', 'Book'], ['amount', 'Amount'], ['reason', 'Reason'], ['status', 'Status'], ['assessed_at', 'Assessed']].map(([key, label]) => ({ key, label })),
  email: [['id', 'Email'], ['recipient', 'Recipient'], ['subject', 'Subject'], ['status', 'Status'], ['error', 'Delivery detail'], ['created_at', 'Queued'], ['sent_at', 'Sent']].map(([key, label]) => ({ key, label })),
  audit: [['id', 'Record'], ['action', 'Action'], ['actor_type', 'Actor type'], ['actor_id', 'Actor ID'], ['entity_type', 'Record type'], ['entity_id', 'Record ID'], ['created_at', 'Time'], ['details', 'Details']].map(([key, label]) => ({ key, label })),
}
const recordStatuses: Partial<Record<Section, string[]>> = { borrowings: ['active', 'overdue', 'returned'], fines: ['unpaid', 'paid', 'waived'], email: ['pending', 'failed', 'sent'] }

export default function AdminApp() {
  const [admin, setAdmin] = useState<Admin | null>(null)
  const [token, setToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [section, setSection] = useState<Section>('dashboard')
  const [online, setOnline] = useState<boolean | null>(null)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [dashboard, setDashboard] = useState<Record<string, unknown>>({})
  const [bookPage, setBookPage] = useState<Page<Book>>({ items: [], total: 0 })
  const [userPage, setUserPage] = useState<Page<User>>({ items: [], total: 0 })
  const [rows, setRows] = useState<Row[]>([])
  const [rowTotal, setRowTotal] = useState(0)
  const [recordFilter, setRecordFilter] = useState('')
  const [pendingCount, setPendingCount] = useState<number | null>(null)
  const [confirmation, setConfirmation] = useState<Confirmation | null>(null)
  const confirmationAnswer = useRef<((answer: boolean) => void) | null>(null)
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

  const load = useCallback(async (which: Section, bearer: string, nextOffset = 0, q = '', pending = pendingOnly, filter = recordFilter) => {
    setBusy(true); setError('')
    try {
      if (which === 'dashboard') {
        const [summary, pendingUsers] = await Promise.all([api<Record<string, unknown>>('/admin/dashboard', {}, bearer), api<Page<User>>('/users?status=PENDING&limit=1', {}, bearer)])
        setDashboard(summary); setPendingCount(pendingUsers.total)
      }
      else if (which === 'books') setBookPage(await api<Page<Book>>(`/books?include_archived=true&q=${encodeURIComponent(q)}&offset=${nextOffset}&limit=20`, {}, bearer))
      else if (which === 'users') setUserPage(await api<Page<User>>(`/users?q=${encodeURIComponent(q)}&offset=${nextOffset}&limit=20${pending ? '&status=PENDING' : ''}`, {}, bearer))
      else if (which === 'settings') setSettings(await api<Record<string, string>>('/settings', {}, bearer))
      else if (listPath[which]) {
        const query = filter ? filter === 'overdue' && which === 'borrowings' ? '&overdue=true' : `&status=${encodeURIComponent(filter)}` : ''
        let response = await api<Page<Row>>(`${listPath[which]}?offset=${nextOffset}&limit=20${query}`, {}, bearer)
        if (nextOffset > 0 && !response.items.length && response.total > 0) {
          const lastOffset = Math.floor((response.total - 1) / 20) * 20
          response = await api<Page<Row>>(`${listPath[which]}?offset=${lastOffset}&limit=20${query}`, {}, bearer)
          setOffset(lastOffset)
        } else if (!response.total) setOffset(0)
        setRows(response.items); setRowTotal(response.total)
      }
      setOnline(true)
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Could not load this section.'
      setError(message)
      if (message.toLowerCase().includes('session')) { setAdmin(null); setToken('') }
    } finally { setBusy(false) }
  }, [pendingOnly, recordFilter])

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

  function navigate(next: Section, filter = '') { setNotice(''); setFieldErrors({}); setRows([]); setRowTotal(0); setSection(next); setNavOpen(false); setOffset(0); setSearch(''); setFormOpen(false); setCopiesBook(null); setPendingOnly(filter === 'pending'); setRecordFilter(filter === 'pending' ? '' : filter); void load(next, token, 0, '', filter === 'pending', filter === 'pending' ? '' : filter) }

  function askConfirmation(request: Confirmation): Promise<boolean> {
    return new Promise(resolve => { confirmationAnswer.current = resolve; setConfirmation(request) })
  }

  function answerConfirmation(answer: boolean) {
    confirmationAnswer.current?.(answer); confirmationAnswer.current = null; setConfirmation(null)
  }

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
    setBusy(true); setError(''); setFieldErrors({})
    try {
      await api(`/users${editingUser ? `/${editingUser.id}` : ''}`, { method: editingUser ? 'PUT' : 'POST', body: JSON.stringify(payload) }, token)
      setFormOpen(false); setEditingUser(null); await load('users', token, offset, search)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not save user.'); if (cause instanceof ApiError) setFieldErrors(cause.fields) }
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
      await downloadFile(result.download_url, 'LIBRAI-' + path.split('/')[1] + '-' + path.split('/')[2] + '-QR.png')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not get QR download.') }
  }

  async function downloadSheet() {
    if (!copiesBook) return
    setError('')
    try {
      const result = await api<{ download_url: string }>(`/books/${copiesBook.id}/copies/qr-sheet`, { method: 'POST' }, token)
      await downloadFile(result.download_url, `LIBRAI-book-${copiesBook.id}-QR-sheet.pdf`)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not create QR sheet.') }
  }

  async function emailQr(user: User) {
    if (!await askConfirmation({ title: 'Email this member’s library QR?', description: 'Confirm this address belongs to this member. This queues an email and may deliver automatically when the server enables delivery.', details: [['Member', user.name], ['Student ID', user.student_id], ['Recipient', user.email || 'No email address']], action: 'Queue QR email' })) return
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
    const request: Confirmation | null = section === 'fines' ? { title: 'Mark this fine as paid?', description: 'Confirm you received payment before recording it. This updates the member’s fine balance.', details: [['Fine', `#${id}`], ['Member', String(row.user_name || `User #${row.user_id}`)], ['Book', String(row.book_title || '—')], ['Amount', adminValue(row.amount, 'amount')]], action: 'Confirm payment received' }
      : section === 'reservations' ? { title: 'Cancel this reservation?', description: 'The member will lose this reservation and its place in the queue.', details: [['Reservation', `#${id}`], ['Member', String(row.user_name || `User #${row.user_id}`)], ['Student ID', String(row.student_id || '—')], ['Book', String(row.book_title || '—')]], action: 'Cancel reservation' }
      : section === 'email' ? { title: row.status === 'pending' ? 'Send this email now?' : 'Queue this email for retry?', description: row.status === 'pending' ? 'This requests delivery to the address below. Confirm the recipient and subject.' : 'This resets the failed email to pending. Enabled automatic delivery may send it.', details: [['Email record', `#${id}`], ['Recipient', String(row.recipient || '—')], ['Subject', String(row.subject || '—')]], action: row.status === 'pending' ? 'Send email now' : 'Queue retry' } : null
    if (!request || !await askConfirmation(request)) return
    setBusy(true); setError(''); setNotice('')
    try {
      if (section === 'fines') { await api(`/fines/${id}/pay`, { method: 'POST', body: JSON.stringify({}) }, token); setNotice(`Fine #${id} marked paid.`) }
      else if (section === 'reservations') { await api(`/reservations/${id}`, { method: 'DELETE' }, token); setNotice(`Reservation #${id} cancelled.`) }
      else { const result = await api<{ message: string }>(`/notifications/admin/email-deliveries/${id}/${row.status === 'pending' ? 'send' : 'retry'}`, { method: 'POST' }, token); setNotice(result.message) }
      await load(section, token, offset)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Action failed.') }
    finally { setBusy(false) }
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
    <div className="admin-main"><header className="admin-header"><div><span>Workspace</span><ChevronRight aria-hidden="true" /><strong>{sections.find(item => item.id === section)?.label}</strong></div><div><span className={`status ${online ? 'good' : 'bad'}`}>{online ? 'Server connected' : 'Connection problem'}</span><UtilityMenu><AppInfo online={online} /><GuidedHelp admin tasks={formOpen ? [] : sections.filter(item => item.id !== 'settings' || admin.role === 'SUPER_ADMIN')} onTask={id => navigate(id as Section)} screen={section} phase={formOpen ? 'form' : 'list'} /></UtilityMenu><span className="staff-identity"><CircleUserRound aria-hidden="true" />{admin.name}</span></div></header>
      {busy && <div className="admin-activity" role="status" aria-live="polite"><LoaderCircle className="loading-spinner" aria-hidden="true" />Updating library information...</div>}
      <main data-help-content className="admin-content" aria-busy={busy}>{notice && <div className="alert" role="status">{notice}</div>}{error && <div className="alert error" role="alert">{error}</div>}
        {section === 'dashboard' && <>
          <div className="page-heading"><div><h1>Library dashboard</h1><p>Everything you need to keep the library moving.</p></div><button className="icon-button" disabled={busy} onClick={() => void load(section, token)}><RefreshCw aria-hidden="true" />Refresh</button></div>
          <section className="admin-attention" aria-labelledby="attention-title"><h2 id="attention-title">Needs attention</h2><p>Open a focused list to review the next action.</p><div className="admin-attention-links"><button disabled={busy} onClick={() => navigate('users', 'pending')}><strong>{pendingCount ?? '—'}</strong><span>Pending registrations<small>Review member details and approve access</small></span><ChevronRight aria-hidden="true" /></button><button disabled={busy} onClick={() => navigate('borrowings', 'overdue')}><strong>{String(dashboard.overdue_borrowings ?? '—')}</strong><span>Overdue loans<small>Review loans past their due date</small></span><ChevronRight aria-hidden="true" /></button><button disabled={busy} onClick={() => navigate('email', 'failed')}><strong>{String(dashboard.failed_email_deliveries ?? '—')}</strong><span>Failed emails<small>Check delivery details before retrying</small></span><ChevronRight aria-hidden="true" /></button></div></section>
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
    {(section === 'books' || section === 'users') && <>
      <div className="page-heading"><div><p className="eyebrow">Management</p><h1>{section === 'books' ? 'Catalog' : 'Library users'}</h1><p>{section === 'books' ? bookPage.total : userPage.total} records</p></div><button className="primary icon-button" disabled={busy} onClick={() => { setEditingBook(null); setEditingUser(null); setFieldErrors({}); setFormOpen(true) }}><Plus aria-hidden="true" />Add {section === 'books' ? 'book' : 'user'}</button></div>
      <form className="search-form" onSubmit={event => { event.preventDefault(); setOffset(0); void load(section, token, 0, search) }}><input aria-label="Search records" placeholder="Search all records" value={search} onChange={event => setSearch(event.target.value)} /><button disabled={busy}>Search</button></form>
      {formOpen && section === 'books' && <form className="panel form-grid" onSubmit={event => void submitBook(event)}><h2>{editingBook ? 'Edit book' : 'Add book'}</h2>{[['isbn', 'ISBN'], ['title', 'Title'], ['author', 'Author'], ['category', 'Category'], ['shelf_location', 'Shelf location'], ['publisher', 'Publisher']].map(([name, label]) => <label key={name}>{label}<input name={name} defaultValue={String(editingBook?.[name as keyof Book] || '')} required={['isbn', 'title', 'author', 'category', 'shelf_location'].includes(name)} /></label>)}{!editingBook && <label>Initial copies<input name="initial_copy_count" type="number" min="0" max="100" defaultValue="1" /></label>}<div className="inline"><button className="primary" disabled={busy}>Save book</button><button type="button" onClick={() => setFormOpen(false)}>Cancel</button></div></form>}
      {formOpen && section === 'users' && <MemberForm key={editingUser?.id || 'new-user'} user={editingUser} fieldErrors={fieldErrors} busy={busy} onSubmit={event => void submitUser(event)} onCancel={() => setFormOpen(false)} />}
      {section === 'users' && <div className="registration-filters"><button disabled={busy} aria-pressed={!pendingOnly} onClick={() => { setPendingOnly(false); setOffset(0); void load('users', token, 0, search, false) }}>All users</button><button disabled={busy} aria-pressed={pendingOnly} onClick={() => { setPendingOnly(true); setOffset(0); void load('users', token, 0, search, true) }}>Pending registrations</button></div>}
      {section === 'books' && copiesBook && <div className="panel"><div className="page-heading"><h2>Copies: {copiesBook.title}</h2><button onClick={() => setCopiesBook(null)}>Close</button></div><div className="inline"><button onClick={() => void addCopies(1)} disabled={busy}>Add copy</button><button onClick={() => void downloadSheet()} disabled={!copies.length}>Download QR sheet</button></div><div className="list">{copies.map(copy => <div key={copy.id}><span><strong>{copy.accession_number}</strong> · {copy.status}</span><button onClick={() => void downloadQr(`/book-copies/${copy.id}/qr`)}>Download QR</button></div>)}</div></div>}
      <AdminTable key={section} rows={section === 'books' ? bookPage.items : userPage.items} columns={section === 'books' ? [{ key: 'title', label: 'Title' }, { key: 'author', label: 'Author' }, { key: 'isbn', label: 'ISBN' }, { key: 'available_copies', label: 'Available' }] : [{ key: 'name', label: 'Name' }, { key: 'student_id', label: 'Student ID', render: row => <>{String(row.student_id)}{Boolean(row.library_card_number) && <small className="library-card-label">Library: {String(row.library_card_number)}</small>}</> }, { key: 'course', label: 'Course' }, { key: 'account_status', label: 'Status' }]} actions={row => {
        if (section === 'books') { const book = row as Book; return <><button disabled={busy} aria-label={`Edit ${book.title}`} onClick={() => { setEditingBook(book); setFormOpen(true) }}>Edit</button><button disabled={busy} aria-label={`Copies and QR for ${book.title}`} onClick={() => void openCopies(book)}>Copies & QR</button></> }
        const user = row as User
        return <><button disabled={busy} aria-label={`${user.account_status === 'pending' ? 'Review request' : 'Edit'} for ${user.name}`} onClick={() => { setEditingUser(user); setFieldErrors({}); setFormOpen(true) }}>{user.account_status === 'pending' ? 'Review request' : 'Edit'}</button>{user.account_status !== 'pending' && <button disabled={busy} aria-label={`QR for ${user.name}`} onClick={() => void downloadQr(`/users/${user.id}/qr`)}>QR</button>}{user.account_status === 'active' && user.email && <button disabled={busy} aria-label={`Email QR to ${user.name}`} onClick={() => void emailQr(user)}>Email QR</button>}</>
      }} />
      <AdminPagination offset={offset} total={section === 'books' ? bookPage.total : userPage.total} busy={busy} onPage={next => { setOffset(next); void load(section, token, next, search) }} />
    </>}
    {listPath[section] && <>
      {section === 'email' && <p className="alert">Pending emails can be sent individually with Send now. Automatic delivery must be enabled by the server operator. Sent means the provider accepted the email; check the inbox or spam folder.</p>}
      <div className="page-heading"><div><p className="eyebrow">Records</p><h1>{sections.find(item => item.id === section)?.label}</h1><p>{rowTotal} records{recordFilter ? ` · ${recordFilter}` : ''}</p></div><button disabled={busy} onClick={() => void load(section, token, offset)}>Refresh</button></div>
      {recordStatuses[section] && <label className="admin-record-filter">Status across all records<select aria-label="Filter records by status" disabled={busy} value={recordFilter} onChange={event => { const filter = event.target.value; setRecordFilter(filter); setOffset(0); void load(section, token, 0, '', false, filter) }}><option value="">All statuses</option>{recordStatuses[section]?.map(status => <option key={status} value={status}>{status === 'overdue' ? 'Overdue by due date' : status.charAt(0).toUpperCase() + status.slice(1)}</option>)}</select></label>}
      <AdminTable key={`${section}-${recordFilter}`} rows={rows} columns={recordColumns[section] || []} searchable actions={['fines', 'reservations', 'email'].includes(section) ? row => <button disabled={busy || (section === 'email' ? !['pending', 'failed'].includes(String(row.status)) : section === 'fines' ? row.status !== 'unpaid' : !['active', 'ready'].includes(String(row.status)))} aria-label={`${section === 'email' ? row.status === 'pending' ? 'Send now' : 'Retry' : section === 'fines' ? 'Mark paid' : 'Cancel'} ${section === 'email' ? `email #${row.id} to ${row.recipient}` : `record #${row.id}`}`} onClick={() => void rowAction(row)}>{section === 'email' ? row.status === 'pending' ? 'Send now' : row.status === 'failed' ? 'Retry' : 'Sent' : section === 'fines' ? row.status === 'unpaid' ? 'Mark paid' : String(row.status) : ['active', 'ready'].includes(String(row.status)) ? 'Cancel' : String(row.status)}</button> : undefined} />
      <AdminPagination offset={offset} total={rowTotal} busy={busy} onPage={next => { setOffset(next); void load(section, token, next) }} />
    </>}
    {section === 'settings' && <><div className="page-heading"><div><p className="eyebrow">Super admin</p><h1>Library policies</h1></div></div><div className="settings-list">{Object.entries(settings).map(([key, value]) => <form className="panel" key={key} onSubmit={event => { event.preventDefault(); const field = event.currentTarget.elements.namedItem('value') as HTMLInputElement; void saveSetting(key, field.value) }}><label>{key.replaceAll('_', ' ').toLowerCase()}<input name="value" defaultValue={value} /></label><button disabled={busy}>Save</button></form>)}</div></>}
    {section === 'reports' && <ReportsPanel token={token} />}
  </main></div><AdminConfirmation request={confirmation} onAnswer={answerConfirmation} /></div>
}

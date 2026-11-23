import { useEffect, useId, useState } from 'react'
import { api, type Page, type UserGrant } from './api'
import './account-panel.css'

type Loan = { id: number; book_title: string; due_at: string; status: string; can_renew?: boolean; renewal_count?: number; renewal_unavailable_reason?: string }
type Reservation = { id: number; book_title: string; status: string; position?: number }
type Notification = { id: number; message: string; is_read: boolean; created_at: string }
type Fine = { id: number; book_title?: string; amount_cents: number; status: string }
type Tab = 'active' | 'history' | 'reservations' | 'fines' | 'notifications'
const tabs: Tab[] = ['active', 'history', 'reservations', 'fines', 'notifications']
const size = 10

export default function AccountPanel({ user, language = 'en' }: { user: UserGrant; language?: 'en' | 'fil' }) {
  const t = (en: string, fil: string) => language === 'fil' ? fil : en
  const labels: Record<Tab, string> = { active: t('Active loans', 'Kasalukuyang hiram'), history: t('History', 'Kasaysayan'), reservations: t('Reservations', 'Mga reserbasyon'), fines: t('Fines', 'Mga multa'), notifications: t('Notifications', 'Mga abiso') }
  const id = useId()
  const [tab, setTab] = useState<Tab>('active')
  const [offset, setOffset] = useState(0)
  const [revision, setRevision] = useState(0)
  const [loans, setLoans] = useState<Loan[]>([])
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [fines, setFines] = useState<Fine[]>([])
  const [total, setTotal] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let current = true
    const params = `user_id=${user.id}&verification_token=${encodeURIComponent(user.verification_token)}`
    async function load() {
      setLoading(true); setError(''); setTotal(null)
      try {
        // Open statuses are fetched separately, so old returned loans cannot hide a current loan.
        if (tab === 'active') {
          async function openLoans(status: string) {
            const items: Loan[] = []
            let count = 0
            do {
              const page = await api<Page<Loan>>(`/borrowings?${params}&status=${status}&offset=${items.length}&limit=100`)
              if (!current) return []
              count = page.total
              if (!page.items.length && items.length < count) throw new Error(language === 'fil' ? 'Hindi kumpleto ang listahan. I-refresh ang account.' : 'The loan list is incomplete. Refresh the account.')
              items.push(...page.items)
            } while (items.length < count)
            return items
          }
          const results = await Promise.all([openLoans('active'), openLoans('overdue')])
          if (current) { const items = results.flat().sort((a, b) => a.due_at.localeCompare(b.due_at)); setLoans(items.slice(offset, offset + size)); setTotal(items.length) }
        } else if (tab === 'notifications') {
          const items = await api<Notification[]>(`/notifications?${params}`)
          if (current) { setNotifications(items.slice(offset, offset + size)); setTotal(items.length) }
        } else {
          const path = tab === 'history' ? 'borrowings' : tab
          const result = await api<Page<Loan | Reservation | Fine>>(`/${path}?${params}&offset=${offset}&limit=${size}`)
          if (current) {
            if (tab === 'history') setLoans(result.items as Loan[])
            else if (tab === 'reservations') setReservations(result.items as Reservation[])
            else setFines(result.items as Fine[])
            setTotal(result.total)
          }
        }
      } catch (cause) { if (current) setError(cause instanceof Error ? cause.message : language === 'fil' ? 'Hindi ma-load ang account.' : 'Could not load account.') }
      finally { if (current) setLoading(false) }
    }
    void load()
    return () => { current = false }
  }, [user.id, user.verification_token, tab, offset, revision, language])

  async function act(action: () => Promise<unknown>) {
    if (busy || loading) return
    setBusy(true); setError('')
    try { await action(); setRevision(value => value + 1) }
    catch (cause) { setError(cause instanceof Error ? cause.message : t('The action could not be completed.', 'Hindi makumpleto ang aksyon.')) }
    finally { setBusy(false) }
  }
  function choose(next: Tab) { setTab(next); setOffset(0) }
  const date = (value: string) => new Date(value).toLocaleDateString(language === 'fil' ? 'fil-PH' : 'en-PH')
  const status = (value: string) => ({ active: t('Active', 'Aktibo'), overdue: t('Overdue', 'Lampas sa takdang araw'), returned: t('Returned', 'Naibalik'), lost: t('Lost', 'Nawala'), ready: t('Ready', 'Handa na'), cancelled: t('Cancelled', 'Kinansela'), fulfilled: t('Fulfilled', 'Nakumpleto'), expired: t('Expired', 'Nag-expire'), paid: t('Paid', 'Bayad'), unpaid: t('Unpaid', 'Hindi pa bayad'), waived: t('Waived', 'Pinawalang-bisa') }[value.toLowerCase()] || value)
  return <div className="account-sections account-workspace">
    <div className="panel account-identity"><div><h2>{user.display_name || user.name || user.student_id}</h2><p>Student ID: {user.student_id}</p></div><button disabled={busy || loading} onClick={() => setRevision(value => value + 1)}>{t('Refresh account', 'I-refresh ang account')}</button></div>
    <div className="account-tabs" role="tablist" aria-label={t('Account sections', 'Mga bahagi ng account')}>
      {tabs.map((item, index) => <button key={item} role="tab" id={`${id}-${item}`} aria-controls={`${id}-panel`} aria-selected={tab === item} tabIndex={tab === item ? 0 : -1} onClick={() => choose(item)} onKeyDown={event => {
        const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : null
        if (next !== null) { event.preventDefault(); choose(tabs[next]); document.getElementById(`${id}-${tabs[next]}`)?.focus() }
      }}>{labels[item]}</button>)}
    </div>
    {error && <p className="alert error" role="alert">{error}</p>}
    <section className="panel account-tab-panel" role="tabpanel" id={`${id}-panel`} aria-labelledby={`${id}-${tab}`} aria-busy={loading}>
      <h2>{labels[tab]}</h2>
      {tab === 'history' && <p className="muted">{t('All borrowing records, including current loans.', 'Lahat ng tala ng paghiram, kasama ang kasalukuyang hiram.')}</p>}
      {loading ? <p role="status">{t('Loading account…', 'Nilo-load ang account…')}</p> : total !== null && <>
        <p className="account-total" role="status">{total === 0 ? t('0 records', '0 tala') : t(`Showing ${offset + 1}–${Math.min(offset + size, total)} of ${total} records`, `Ipinapakita ang ${offset + 1}–${Math.min(offset + size, total)} sa ${total} tala`)}</p>
        {total === 0 ? <p className="muted">{t('No records in this section.', 'Walang tala sa bahaging ito.')}</p> : <div className="list">
          {(tab === 'active' || tab === 'history') && loans.map(loan => <div key={loan.id}><span><strong>{loan.book_title}</strong><small>{status(loan.status)} · {t('Due', 'Takdang araw')} {date(loan.due_at)} · {t(`Renewed ${loan.renewal_count || 0} times`, `Na-renew nang ${loan.renewal_count || 0} beses`)}</small>{tab === 'active' && !loan.can_renew && <small className="account-renewal-reason">{loan.renewal_unavailable_reason || t('Renewal is unavailable. The server did not provide a reason; please ask library staff.', 'Hindi magagamit ang renewal. Walang ibinigay na dahilan ang server; magtanong sa kawani ng aklatan.')}</small>}</span>{loan.can_renew && <button disabled={busy || loading} onClick={() => void act(() => api(`/borrowings/${loan.id}/renew`, { method: 'POST', body: JSON.stringify({ user_id: user.id, user_verification_token: user.verification_token }) }))}>{t('Renew', 'I-renew')}</button>}</div>)}
          {tab === 'reservations' && reservations.map(item => <div key={item.id}><span><strong>{item.book_title}</strong><small>{status(item.status)}{item.position ? ` · ${t('Queue position', 'Puwesto sa pila')} ${item.position}` : ''}</small></span>{['active', 'ready'].includes(item.status) && <button disabled={busy} onClick={() => void act(() => api(`/reservations/${item.id}?verification_token=${encodeURIComponent(user.verification_token)}`, { method: 'DELETE' }))}>{t('Cancel', 'Kanselahin')}</button>}</div>)}
          {tab === 'fines' && fines.map(item => <div key={item.id}><strong>{item.book_title || `${t('Fine', 'Multa')} #${item.id}`}</strong><span>₱{(item.amount_cents / 100).toFixed(2)} · {status(item.status)}</span></div>)}
          {tab === 'notifications' && notifications.map(item => <div key={item.id}><span>{item.message}<small>{date(item.created_at)} · {item.is_read ? t('Read', 'Nabasa na') : t('Unread', 'Hindi pa nababasa')}</small></span>{!item.is_read && <button disabled={busy} onClick={() => void act(() => api(`/notifications/${item.id}/read`, { method: 'POST', body: JSON.stringify({ verification_token: user.verification_token }) }))}>{t('Mark read', 'Markahang nabasa')}</button>}</div>)}
        </div>}
        {total > size && <nav className="account-pagination" aria-label={t('Account pages', 'Mga pahina ng account')}><button disabled={busy || offset === 0} onClick={() => setOffset(value => Math.max(0, value - size))}>{t('Previous', 'Nakaraan')}</button><span>{t('Page', 'Pahina')} {Math.floor(offset / size) + 1} / {Math.ceil(total / size)}</span><button disabled={busy || offset + size >= total} onClick={() => setOffset(value => value + size)}>{t('Next', 'Susunod')}</button></nav>}
      </>}
    </section>
  </div>
}

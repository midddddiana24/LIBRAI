import { useCallback, useEffect, useState } from 'react'
import { api, type Page, type UserGrant } from './api'

type Loan = { id: number; book_title: string; due_at: string; status: string; can_renew?: boolean; renewal_count?: number }
type Reservation = { id: number; book_title: string; status: string; position?: number }
type Notification = { id: number; message: string; is_read: boolean; created_at: string }
type Fine = { id: number; book_title?: string; amount_cents: number; status: string }
const date = (value: string) => new Date(value).toLocaleDateString()

export default function AccountPanel({ user }: { user: UserGrant }) {
  const [loans, setLoans] = useState<Loan[]>([])
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [fines, setFines] = useState<Fine[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    const params = `user_id=${user.id}&verification_token=${encodeURIComponent(user.verification_token)}`
    const [loanResult, reservationResult, notificationResult, fineResult] = await Promise.all([
      api<Page<Loan>>(`/borrowings?${params}&limit=50`),
      api<Page<Reservation>>(`/reservations?${params}&limit=50`),
      api<Notification[]>(`/notifications?${params}`),
      api<Page<Fine>>(`/fines?${params}&limit=50`),
    ])
    setLoans(loanResult.items); setReservations(reservationResult.items)
    setNotifications(notificationResult); setFines(fineResult.items)
  }, [user])

  useEffect(() => {
    const timer = window.setTimeout(() => { void refresh().catch(cause => setError(cause instanceof Error ? cause.message : 'Could not load account.')) }, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  async function act(action: () => Promise<unknown>) {
    if (busy) return
    setBusy(true); setError('')
    try { await action(); await refresh() }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'The action could not be completed.') }
    finally { setBusy(false) }
  }

  return <div className="account-sections"><div className="panel"><h2>{user.display_name || user.name || user.student_id}</h2><p>Student ID: {user.student_id}</p><button disabled={busy} onClick={() => void act(async () => undefined)}>Refresh account</button></div>{error && <p className="alert error" role="alert">{error}</p>}
    <section className="panel"><h2>My loans</h2>{loans.length ? <div className="list">{loans.map(loan => <div key={loan.id}><span><strong>{loan.book_title}</strong><small>{loan.status} · Due {date(loan.due_at)} · Renewed {loan.renewal_count || 0} times</small></span>{loan.can_renew && <button disabled={busy} onClick={() => void act(() => api(`/borrowings/${loan.id}/renew`, { method: 'POST', body: JSON.stringify({ user_id: user.id, user_verification_token: user.verification_token }) }))}>Renew</button>}</div>)}</div> : <p className="muted">No loans yet.</p>}</section>
    <section className="panel"><h2>Reservations</h2>{reservations.length ? <div className="list">{reservations.map(reservation => <div key={reservation.id}><span><strong>{reservation.book_title}</strong><small>{reservation.status}{reservation.position ? ` · Queue position ${reservation.position}` : ''}</small></span>{['active', 'ready'].includes(reservation.status) && <button disabled={busy} onClick={() => void act(() => api(`/reservations/${reservation.id}?verification_token=${encodeURIComponent(user.verification_token)}`, { method: 'DELETE' }))}>Cancel</button>}</div>)}</div> : <p className="muted">No reservations.</p>}</section>
    <section className="panel"><h2>Fines</h2>{fines.length ? <div className="list">{fines.map(fine => <div key={fine.id}><strong>{fine.book_title || `Fine #${fine.id}`}</strong><span>₱{(fine.amount_cents / 100).toFixed(2)} · {fine.status}</span></div>)}</div> : <p className="muted">No fines.</p>}</section>
    <section className="panel"><h2>Notifications</h2>{notifications.length ? <div className="list">{notifications.map(notification => <div key={notification.id}><span>{notification.message}<small>{date(notification.created_at)}</small></span>{!notification.is_read && <button disabled={busy} onClick={() => void act(() => api(`/notifications/${notification.id}/read`, { method: 'POST', body: JSON.stringify({ verification_token: user.verification_token }) }))}>Mark read</button>}</div>)}</div> : <p className="muted">No notifications.</p>}</section>
  </div>
}

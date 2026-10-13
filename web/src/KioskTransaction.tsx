import type { ActiveBorrowing, BookGrant, BorrowReceipt, ReturnReceipt, UserGrant } from './api'
import { QrCapture } from './QrCapture'

const date = (value?: string) => value ? new Date(value).toLocaleString() : '—'

function Progress({ labels, current }: { labels: string[]; current: number }) {
  return <ol className="transaction-progress" aria-label="Transaction progress">{labels.map((label, index) => <li key={label} className={index === current ? 'current' : index < current ? 'done' : ''} aria-current={index === current ? 'step' : undefined}><span>{index < current ? '✓' : index + 1}</span>{label}</li>)}</ol>
}

function TransactionShell({ title, intro, step, labels, onCancel, children }: { title: string; intro: string; step: number; labels: string[]; onCancel: () => void; children: React.ReactNode }) {
  return <div className="transaction-page">
    <div className="page-heading"><div><p className="eyebrow">Self service</p><h1>{title}</h1><p>{intro}</p></div><button onClick={onCancel}>Cancel and clear</button></div>
    <Progress labels={labels} current={step} />
    <section className="transaction-card">{children}</section>
  </div>
}

type BorrowProps = {
  user: UserGrant | null
  copy: BookGrant | null
  receipt: BorrowReceipt | ReturnReceipt | null
  busy: boolean
  onUser: (token: string) => void
  onBook: (token: string) => void
  onChangeUser: () => void
  onChangeBook: () => void
  onConfirm: () => void
  onFinish: () => void
}

export function BorrowFlow({ user, copy, receipt, busy, onUser, onBook, onChangeUser, onChangeBook, onConfirm, onFinish }: BorrowProps) {
  const step = receipt ? 3 : !user ? 0 : !copy ? 1 : 2
  return <TransactionShell title="Borrow a book" intro="Follow the steps to check out one copy." step={step} labels={['Library ID', 'Book QR', 'Review', 'Done']} onCancel={onFinish}>
    {receipt ? <div className="transaction-result" role="status"><span className="result-symbol" aria-hidden="true">✓</span><h2>Borrowing complete</h2><p>{receipt.book_title}</p><div className="receipt-detail"><span>Due date</span><strong>{date((receipt as BorrowReceipt).due_at)}</strong></div><button className="primary large" onClick={onFinish}>Finish and clear session</button></div>
      : !user ? <><p className="step-kicker">Step 1 of 3</p><h2>Scan your library ID</h2><p className="muted">Hold the QR code on your library ID in front of the tablet camera.</p><QrCapture key="user-scan" label="your library ID" busy={busy} onToken={onUser} /></>
        : !copy ? <><p className="step-kicker">Step 2 of 3</p><h2>Scan the book copy</h2><p className="verified">Library ID verified: {user.display_name || user.name || user.student_id}</p><QrCapture key="book-scan" label="the book QR" busy={busy} onToken={onBook} /><button className="text-button" onClick={onChangeUser}>Use a different library ID</button></>
          : <><p className="step-kicker">Step 3 of 3</p><h2>Review your borrowing</h2><div className="review-list"><div><span>Library user</span><strong>{user.display_name || user.name || user.student_id}</strong></div><div><span>Book</span><strong>{copy.title}</strong></div><div><span>Copy</span><strong>{copy.accession_number}</strong></div></div><p className="muted">The library server checks availability and assigns the due date after confirmation.</p>{!copy.available && <p className="alert error">This copy is unavailable. Scan another copy.</p>}<div className="transaction-buttons"><button onClick={onChangeBook}>Scan another book</button><button className="primary large" disabled={!copy.available || busy} onClick={onConfirm}>{busy ? 'Processing…' : 'Confirm borrowing'}</button></div></>}
  </TransactionShell>
}

type ReturnProps = {
  copy: BookGrant | null
  activeReturn: ActiveBorrowing | null
  receipt: BorrowReceipt | ReturnReceipt | null
  busy: boolean
  onBook: (token: string) => void
  onChangeBook: () => void
  onConfirm: () => void
  onFinish: () => void
}

export function ReturnFlow({ copy, activeReturn, receipt, busy, onBook, onChangeBook, onConfirm, onFinish }: ReturnProps) {
  const step = receipt ? 2 : !copy || !activeReturn ? 0 : 1
  return <TransactionShell title="Return a book" intro="Scan the copy and check its loan before returning it." step={step} labels={['Book QR', 'Review', 'Done']} onCancel={onFinish}>
    {receipt ? <div className="transaction-result" role="status"><span className="result-symbol" aria-hidden="true">✓</span><h2>Return complete</h2><p>{receipt.book_title}</p><div className="receipt-detail"><span>Returned</span><strong>{date((receipt as ReturnReceipt).returned_at)}</strong></div><button className="primary large" onClick={onFinish}>Finish and clear session</button></div>
      : !copy || !activeReturn ? <><p className="step-kicker">Step 1 of 2</p><h2>Scan the book copy</h2><p className="muted">Hold the QR code on the borrowed book in front of the tablet camera.</p><QrCapture label="the book QR" busy={busy} onToken={onBook} /></>
        : <><p className="step-kicker">Step 2 of 2</p><h2>Review this return</h2><div className="review-list"><div><span>Book</span><strong>{activeReturn.book_title}</strong></div><div><span>Borrower</span><strong>{activeReturn.user_name}</strong></div><div><span>Due date</span><strong>{date(activeReturn.due_at)}</strong></div></div><p className="muted">Any overdue charge is calculated by the library server.</p><div className="transaction-buttons"><button onClick={onChangeBook}>Scan another book</button><button className="primary large" disabled={busy} onClick={onConfirm}>{busy ? 'Processing…' : 'Confirm return'}</button></div></>}
  </TransactionShell>
}

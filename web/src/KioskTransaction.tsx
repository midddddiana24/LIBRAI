import type { ActiveBorrowing, BookGrant, BorrowReceipt, ReturnReceipt, UserGrant } from './api'
import { QrCapture } from './QrCapture'
import { ArrowLeft, Check, LoaderCircle, ShieldCheck } from 'lucide-react'
import { BorrowScanArt } from './BorrowScanArt'
import './borrow-screen.css'

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

function BorrowStepSummary({ number, title, detail, kind, complete = false, onChange, busy }: {
  number: number; title: string; detail: string; kind: 'id' | 'book' | 'confirm'; complete?: boolean; onChange?: () => void; busy: boolean
}) {
  return <section className={`borrow-step-summary${complete ? ' is-complete' : ''}`}>
    <span className="borrow-step-number" aria-label={complete ? `Step ${number} complete` : `Step ${number}`}>{complete ? <Check aria-hidden="true" /> : number}</span>
    <div><h2>{title}</h2><p>{detail}</p></div>
    {onChange ? <button type="button" className="borrow-change" aria-label={`Change ${kind === 'id' ? 'library ID' : 'book'}`} onClick={onChange} disabled={busy}>Change</button> : <BorrowScanArt kind={kind} />}
  </section>
}

export function BorrowFlow({ user, copy, receipt, busy, onUser, onBook, onChangeUser, onChangeBook, onConfirm, onFinish }: BorrowProps) {
  const step = receipt ? 3 : !user ? 0 : !copy ? 1 : 2
  const userName = user?.display_name || user?.name || user?.student_id || ''
  return <div className="transaction-page borrow-page">
    <div className="page-heading"><div><h1>Borrow a book</h1><p>Scan your library ID, then your book.</p></div></div>
    <Progress labels={['Library ID', 'Book QR', 'Confirm']} current={step} />
    <div className="borrow-stages">
      {receipt ? <section className="borrow-stage borrow-receipt" role="status">
        <BorrowScanArt kind="confirm" />
        <div><p className="borrow-complete"><Check aria-hidden="true" /> All done</p><h2>Borrowing complete</h2><p>{receipt.book_title}</p><div className="receipt-detail"><span>Due date</span><strong>{date((receipt as BorrowReceipt).due_at)}</strong></div><button className="primary large" onClick={onFinish}>Finish and clear session</button></div>
      </section> : <>
        {user ? <BorrowStepSummary number={1} title="Library ID verified" detail={userName} kind="id" complete onChange={onChangeUser} busy={busy} /> : <section className="borrow-stage" aria-labelledby="borrow-id-heading">
          <BorrowScanArt kind="id" />
          <div className="borrow-stage-controls"><h2 id="borrow-id-heading" tabIndex={-1}>Scan your library ID</h2><QrCapture key="user-scan" label="your library ID" busy={busy} onToken={onUser} presentation="borrow" /></div>
        </section>}
        {!user ? <BorrowStepSummary number={2} title="Scan a book" detail="Scan your library ID first." kind="book" busy={busy} />
          : !copy ? <section className="borrow-stage" aria-labelledby="borrow-book-heading">
            <BorrowScanArt kind="book" />
            <div className="borrow-stage-controls"><h2 id="borrow-book-heading" tabIndex={-1}>Scan a book</h2><QrCapture key="book-scan" label="the book" busy={busy} onToken={onBook} presentation="borrow" /></div>
          </section> : <BorrowStepSummary number={2} title="Book scanned" detail={copy.title} kind="book" complete onChange={onChangeBook} busy={busy} />}
        {!user || !copy ? <BorrowStepSummary number={3} title="Confirm and borrow" detail={user ? 'Scan a book first.' : 'Scan your library ID and a book first.'} kind="confirm" busy={busy} /> : <section className="borrow-stage borrow-review" aria-labelledby="borrow-review-heading">
          <BorrowScanArt kind="confirm" />
          <div><h2 id="borrow-review-heading" tabIndex={-1}>Review your borrowing</h2><div className="review-list"><div><span>Library user</span><strong>{userName}</strong></div><div><span>Book</span><strong>{copy.title}</strong></div><div><span>Copy</span><strong>{copy.accession_number}</strong></div></div><p className="muted">The library server checks availability and assigns the due date after confirmation.</p>{!copy.available && <p role="alert" className="alert error">This copy is unavailable. Scan another copy.</p>}<button className="primary large icon-button" disabled={!copy.available || busy} onClick={onConfirm}>{busy && <LoaderCircle className="loading-spinner" aria-hidden="true" />}{busy ? 'Processing…' : 'Confirm borrowing'}</button></div>
        </section>}
      </>}
    </div>
    <div className="borrow-footer"><button type="button" className="icon-button" onClick={onFinish} disabled={busy}><ArrowLeft aria-hidden="true" />Home</button><p><ShieldCheck aria-hidden="true" />Your session clears when you finish.</p></div>
  </div>
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

import type { ActiveBorrowing, BookGrant, BorrowReceipt, ReturnReceipt, UserGrant } from './api'
import { QrCapture } from './QrCapture'
import { ArrowLeft, Check, LoaderCircle, ShieldCheck } from 'lucide-react'
import { BorrowScanArt } from './BorrowScanArt'
import './borrow-screen.css'
import { useKioskLanguage } from './kioskLanguage'

const date = (value?: string) => value ? new Date(value).toLocaleString() : '—'

function Progress({ labels, current }: { labels: string[]; current: number }) {
  const { t } = useKioskLanguage()
  return <ol className="transaction-progress" aria-label={t('Transaction progress', 'Progreso ng transaksyon')}>{labels.map((label, index) => <li key={label} className={index === current ? 'current' : index < current ? 'done' : ''} aria-current={index === current ? 'step' : undefined}><span>{index < current ? '✓' : index + 1}</span>{label}</li>)}</ol>
}

function TransactionShell({ title, intro, step, labels, onCancel, children }: { title: string; intro: string; step: number; labels: string[]; onCancel: () => void; children: React.ReactNode }) {
  const { t } = useKioskLanguage()
  return <div className="transaction-page">
    <div className="page-heading"><div><p className="eyebrow">{t('Self service', 'Sariling serbisyo')}</p><h1>{title}</h1><p>{intro}</p></div><button onClick={onCancel}>{t('Cancel and clear', 'Kanselahin at burahin')}</button></div>
    <Progress labels={labels} current={step} />
    <section className="transaction-card">{children}</section>
  </div>
}

type BorrowProps = {
  user: UserGrant | null
  copy: BookGrant | null
  receipt: BorrowReceipt | ReturnReceipt | null
  busy: boolean
  error?: string
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
  const { t } = useKioskLanguage()
  return <section className={`borrow-step-summary${complete ? ' is-complete' : ''}`}>
    <span className="borrow-step-number" aria-label={complete ? `Step ${number} complete` : `Step ${number}`}>{complete ? <Check aria-hidden="true" /> : number}</span>
    <div><h2>{title}</h2><p>{detail}</p></div>
    {onChange ? <button type="button" className="borrow-change" aria-label={`Change ${kind === 'id' ? 'library ID' : 'book'}`} onClick={onChange} disabled={busy}>{t('Change', 'Palitan')}</button> : <BorrowScanArt kind={kind} />}
  </section>
}

export function BorrowFlow({ user, copy, receipt, busy, error = '', onUser, onBook, onChangeUser, onChangeBook, onConfirm, onFinish }: BorrowProps) {
  const { t } = useKioskLanguage()
  const step = receipt ? 3 : !user ? 0 : !copy ? 1 : 2
  const userName = user?.display_name || user?.name || user?.student_id || ''
  return <div className="transaction-page borrow-page">
    <div className="page-heading"><div><h1>{t('Borrow a book', 'Humiram ng libro')}</h1><p>{t('Scan your library ID, then your book.', 'I-scan ang library ID, pagkatapos ang libro.')}</p></div></div>
    <Progress labels={[t('Library ID', 'Library ID'), t('Book QR', 'QR ng libro'), t('Confirm', 'Kumpirmahin')]} current={step} />
    <div className="borrow-stages">
      {receipt ? <section className="borrow-stage borrow-receipt" role="status">
        <BorrowScanArt kind="confirm" />
        <div><p className="borrow-complete"><Check aria-hidden="true" /> {t('All done', 'Tapos na')}</p><h2>{t('Borrowing complete', 'Kumpleto na ang paghiram')}</h2><p>{receipt.book_title}</p><div className="receipt-detail"><span>{t('Due date', 'Takdang petsa')}</span><strong>{date((receipt as BorrowReceipt).due_at)}</strong></div><button data-help-borrow-finish className="primary large" onClick={onFinish}>{t('Finish and clear session', 'Tapusin at burahin ang session')}</button></div>
      </section> : <>
        {user ? <BorrowStepSummary number={1} title={t('Library ID verified', 'Na-verify ang library ID')} detail={userName} kind="id" complete onChange={onChangeUser} busy={busy} /> : <section className="borrow-stage" aria-labelledby="borrow-id-heading">
          <BorrowScanArt kind="id" />
          <div className="borrow-stage-controls"><h2 id="borrow-id-heading" tabIndex={-1}>{t('Scan your library ID', 'I-scan ang iyong library ID')}</h2><QrCapture key="user-scan" label="your library ID" busy={busy} error={error} onToken={onUser} presentation="borrow" /></div>
        </section>}
        {!user ? <BorrowStepSummary number={2} title={t('Scan a book', 'I-scan ang libro')} detail={t('Scan your library ID first.', 'I-scan muna ang iyong library ID.')} kind="book" busy={busy} />
          : !copy ? <section className="borrow-stage" aria-labelledby="borrow-book-heading">
            <BorrowScanArt kind="book" />
            <div className="borrow-stage-controls"><h2 id="borrow-book-heading" tabIndex={-1}>{t('Scan a book', 'I-scan ang libro')}</h2><QrCapture key="book-scan" label="the book" busy={busy} error={error} onToken={onBook} presentation="borrow" /></div>
          </section> : <BorrowStepSummary number={2} title={t('Book scanned', 'Na-scan ang libro')} detail={copy.title} kind="book" complete onChange={onChangeBook} busy={busy} />}
        {!user || !copy ? <BorrowStepSummary number={3} title={t('Confirm and borrow', 'Kumpirmahin at humiram')} detail={user ? t('Scan a book first.', 'I-scan muna ang libro.') : t('Scan your library ID and a book first.', 'I-scan muna ang library ID at libro.')} kind="confirm" busy={busy} /> : <section className="borrow-stage borrow-review" aria-labelledby="borrow-review-heading">
          <BorrowScanArt kind="confirm" />
          <div><h2 id="borrow-review-heading" tabIndex={-1}>{t('Review your borrowing', 'Suriin ang paghiram')}</h2><div className="review-list"><div><span>{t('Library user', 'Miyembro')}</span><strong>{userName}</strong></div><div><span>{t('Book', 'Libro')}</span><strong>{copy.title}</strong></div><div><span>{t('Copy', 'Kopya')}</span><strong>{copy.accession_number}</strong></div></div><p className="muted">{t('The library server checks availability and assigns the due date after confirmation.', 'Susuriin ng library server ang availability at itatakda ang petsa ng pagsauli pagkatapos magkumpirma.')}</p>{!copy.available && <p role="alert" className="alert error">{t('This copy is unavailable. Scan another copy.', 'Hindi available ang kopyang ito. I-scan ang ibang kopya.')}</p>}{error && <p role="alert" className="error">{error}</p>}<button data-help-borrow-confirm className="primary large icon-button" disabled={!copy.available || busy} onClick={onConfirm}>{busy && <LoaderCircle className="loading-spinner" aria-hidden="true" />}{busy ? t('Processing…', 'Pinoproseso…') : t('Confirm borrowing', 'Kumpirmahin ang paghiram')}</button></div>
        </section>}
      </>}
    </div>
    <div className="borrow-footer"><button type="button" className="icon-button" onClick={onFinish} disabled={busy}><ArrowLeft aria-hidden="true" />{t('Home', 'Home')}</button><p><ShieldCheck aria-hidden="true" />{t('Your session clears when you finish.', 'Mabubura ang session kapag natapos mo ito.')}</p></div>
  </div>
}

type ReturnProps = {
  copy: BookGrant | null
  activeReturn: ActiveBorrowing | null
  receipt: BorrowReceipt | ReturnReceipt | null
  busy: boolean
  error?: string
  onBook: (token: string) => void
  onChangeBook: () => void
  onConfirm: () => void
  onFinish: () => void
}

export function ReturnFlow({ copy, activeReturn, receipt, busy, error = '', onBook, onChangeBook, onConfirm, onFinish }: ReturnProps) {
  const { t } = useKioskLanguage()
  const step = receipt ? 2 : !copy || !activeReturn ? 0 : 1
  return <TransactionShell title={t('Return a book', 'Magsauli ng libro')} intro={t('Scan the copy and check its loan before returning it.', 'I-scan ang kopya at suriin ang paghiram bago magsauli.')} step={step} labels={[t('Book QR', 'QR ng libro'), t('Review', 'Suriin'), t('Done', 'Tapos')]} onCancel={onFinish}>
    {receipt ? <div className="transaction-result" role="status"><span className="result-symbol" aria-hidden="true">✓</span><h2>{t('Return complete', 'Kumpleto na ang pagsauli')}</h2><p>{receipt.book_title}</p><div className="receipt-detail"><span>{t('Returned', 'Naisauli')}</span><strong>{date((receipt as ReturnReceipt).returned_at)}</strong></div><button data-help-return-finish className="primary large" onClick={onFinish}>{t('Finish and clear session', 'Tapusin at burahin ang session')}</button></div>
      : !copy || !activeReturn ? <><p className="step-kicker">{t('Step 1 of 2', 'Hakbang 1 sa 2')}</p><h2>{t('Scan the book copy', 'I-scan ang kopya ng libro')}</h2><p className="muted">{t('Hold the QR code on the borrowed book in front of the tablet camera.', 'Itapat sa camera ng tablet ang QR ng hiniram na libro.')}</p><QrCapture label="the book QR" busy={busy} error={error} onToken={onBook} /></>
        : <><p className="step-kicker">{t('Step 2 of 2', 'Hakbang 2 sa 2')}</p><h2>{t('Review this return', 'Suriin ang pagsauli')}</h2><div className="review-list"><div><span>{t('Book', 'Libro')}</span><strong>{activeReturn.book_title}</strong></div><div><span>{t('Borrower', 'Humiram')}</span><strong>{activeReturn.user_name}</strong></div><div><span>{t('Due date', 'Takdang petsa')}</span><strong>{date(activeReturn.due_at)}</strong></div></div><p className="muted">{t('Any overdue charge is calculated by the library server.', 'Kakalkulahin ng library server ang anumang multa sa pagkaantala.')}</p>{error && <p role="alert" className="error">{error}</p>}<div className="transaction-buttons"><button onClick={onChangeBook}>{t('Scan another book', 'I-scan ang ibang libro')}</button><button data-help-return-confirm className="primary large" disabled={busy} onClick={onConfirm}>{busy ? t('Processing…', 'Pinoproseso…') : t('Confirm return', 'Kumpirmahin ang pagsauli')}</button></div></>}
  </TransactionShell>
}

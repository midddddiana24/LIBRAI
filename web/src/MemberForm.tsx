import { useState } from 'react'
import IdScanPanel from './IdScanPanel'
import './member-registration.css'

type Member = { student_id: string; library_card_number?: string | null; first_name: string; last_name: string; course: string; year_level: string; email?: string | null; account_status: string }
type Props = { user?: Member | null; publicRegistration?: boolean; busy: boolean; onSubmit: (event: React.FormEvent<HTMLFormElement>) => void; onCancel: () => void }

export default function MemberForm({ user, publicRegistration = false, busy, onSubmit, onCancel }: Props) {
  const [fields, setFields] = useState({ student_id: user?.student_id || '', library_card_number: user?.library_card_number || '', first_name: user?.first_name || '', last_name: user?.last_name || '', course: user?.course || '', year_level: user?.year_level || '', email: user?.email || '' })
  const [scanned, setScanned] = useState(false)
  const [checked, setChecked] = useState(false)
  const [scanWarning, setScanWarning] = useState('')
  const entries = [['student_id', 'Campus student ID'], ['library_card_number', 'Library card number (optional)'], ['first_name', 'First name / middle initial'], ['last_name', 'Last name / suffix'], ['course', 'Course'], ['year_level', 'Current year level'], ['email', 'Email (optional)']] as const
  return <form className="panel form-grid member-form" onSubmit={onSubmit}>
    <h2>{publicRegistration ? 'Request a library account' : user ? 'Review library user' : 'Register user'}</h2>
    {user && <p className="member-form-intro">Campus student ID: <strong>{user.student_id}</strong></p>}
    {publicRegistration && <p className="member-form-intro">Scan your ID or type your details. Library staff must review and approve your request before you can borrow.</p>}
    <IdScanPanel disabled={busy} onApply={draft => {
      if (user && draft.student_id && draft.student_id !== user.student_id) { setScanWarning('The scanned campus number does not match this member. No scanned details were applied.'); return }
      setScanWarning(''); setFields(current => ({ ...current, ...draft, ...(user ? { student_id: current.student_id } : {}) })); setScanned(true); setChecked(false)
    }} />
    {scanWarning && <p className="member-form-intro error" role="alert">{scanWarning}</p>}
    {entries.filter(([name]) => !user || name !== 'student_id').map(([name, label]) => <label key={name}>{label}<input name={name} value={fields[name]} maxLength={name === 'course' ? 150 : name === 'email' ? 255 : name === 'year_level' ? 30 : name.endsWith('name') ? 100 : 80} type={name === 'email' ? 'email' : 'text'} required={!['email', 'library_card_number'].includes(name)} disabled={busy} autoComplete="off" onChange={e => setFields(current => ({ ...current, [name]: e.target.value }))} /></label>)}
    {!publicRegistration && <label>Status<select name="status" defaultValue={user?.account_status.toUpperCase() || 'ACTIVE'} disabled={busy}>{user?.account_status === 'pending' && <option value="PENDING">Pending staff approval</option>}<option value="ACTIVE">Active</option><option value="INACTIVE">Inactive</option><option value="SUSPENDED">Suspended</option></select></label>}
    {scanned && <label className="member-review"><input type="checkbox" checked={checked} onChange={e => setChecked(e.target.checked)} required />I checked the scanned names and numbers against the card.</label>}
    {publicRegistration && <label className="member-review"><input type="checkbox" required />These are my details, and I am submitting them for library staff review.</label>}
    <div className="inline member-form-buttons">
      {user?.account_status === 'pending' ? <><button className="primary" name="registration_action" value="approve" disabled={busy || (scanned && !checked)}>Approve registration</button><button name="registration_action" value="reject" formNoValidate disabled={busy}>Reject request</button></> : <button className="primary" disabled={busy || (scanned && !checked)}>{busy ? 'Submitting...' : publicRegistration ? 'Submit for staff approval' : 'Save user'}</button>}
      <button type="button" disabled={busy} onClick={onCancel}>Cancel</button>
    </div>
  </form>
}

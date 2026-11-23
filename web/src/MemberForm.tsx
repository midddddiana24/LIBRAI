import { useId, useState } from 'react'
import IdScanPanel from './IdScanPanel'
import './member-registration.css'
import './member-form-sections.css'

type Member = { student_id: string; library_card_number?: string | null; first_name: string; last_name: string; course: string; year_level: string; email?: string | null; account_status: string }
type Props = { user?: Member | null; publicRegistration?: boolean; busy: boolean; language?: 'en' | 'fil'; fieldErrors?: Record<string, string>; onSubmit: (event: React.FormEvent<HTMLFormElement>) => void; onCancel: () => void }
type Field = 'student_id' | 'library_card_number' | 'first_name' | 'last_name' | 'course' | 'year_level' | 'email'
const emptyErrors: Record<string, string> = {}

export default function MemberForm({ user, publicRegistration = false, busy, language = 'en', fieldErrors = emptyErrors, onSubmit, onCancel }: Props) {
  const t = (en: string, fil: string) => language === 'fil' ? fil : en
  const id = useId()
  const [fields, setFields] = useState({ student_id: user?.student_id || '', library_card_number: user?.library_card_number || '', first_name: user?.first_name || '', last_name: user?.last_name || '', course: user?.course || '', year_level: user?.year_level || '', email: user?.email || '' })
  const [scanned, setScanned] = useState(false)
  const [checked, setChecked] = useState(false)
  const [scanWarning, setScanWarning] = useState('')
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({})
  const [dismissedErrors, setDismissedErrors] = useState<Record<string, string>>({})
  const labels: Record<Field, string> = {
    student_id: t('Campus student ID', 'Student ID sa paaralan'), library_card_number: t('Library card number (optional)', 'Numero ng library card (opsyonal)'),
    first_name: t('First name / middle initial', 'Pangalan / gitnang inisyal'), last_name: t('Last name / suffix', 'Apelyido / hulapi'),
    course: t('Course', 'Kurso'), year_level: t('Current year level', 'Kasalukuyang taon sa pag-aaral'), email: t('Email (optional)', 'Email (opsyonal)'),
  }
  function validate(input: HTMLInputElement) {
    const message = input.validity.valueMissing || (input.required && !input.value.trim()) ? t('Please complete this field.', 'Pakikumpleto ang bahaging ito.') : input.validity.typeMismatch ? t('Enter a valid email address or leave this field blank.', 'Maglagay ng wastong email address o iwan itong blangko.') : input.validationMessage
    setLocalErrors(current => ({ ...current, [input.name]: message }))
    return message
  }
  function renderField(name: Field) {
    if (user && name === 'student_id') return null
    const error = localErrors[name] || (dismissedErrors[name] !== fieldErrors[name] ? fieldErrors[name] : '')
    const description = [name === 'email' ? `${id}-email-help` : '', error ? `${id}-${name}-error` : ''].filter(Boolean).join(' ') || undefined
    return <div className="member-field" key={name}>
      <label htmlFor={`${id}-${name}`}>{labels[name]}</label>
      <input id={`${id}-${name}`} name={name} value={fields[name]} maxLength={name === 'course' ? 150 : name === 'email' ? 255 : name === 'year_level' ? 30 : name.endsWith('name') ? 100 : 80} type={name === 'email' ? 'email' : 'text'} required={!['email', 'library_card_number'].includes(name)} disabled={busy} autoComplete="off" aria-invalid={Boolean(error)} aria-describedby={description} onBlur={event => validate(event.currentTarget)} onInvalid={event => validate(event.currentTarget)} onChange={event => {
        setFields(current => ({ ...current, [name]: event.target.value }))
        setLocalErrors(current => ({ ...current, [name]: '' }))
        setDismissedErrors(current => ({ ...current, [name]: fieldErrors[name] }))
      }} />
      {name === 'email' && <p className="member-field-help" id={`${id}-email-help`}>{t('Optional. Add an email address if you want staff to send your library QR by email after approval. Without one, ask staff for your QR.', 'Opsyonal. Maglagay ng email kung nais mong ipadala ng kawani ang library QR pagkatapos maaprubahan. Kung wala, hingin ang QR sa kawani.')}</p>}
      {error && <p className="member-field-error" id={`${id}-${name}-error`} role="alert">{error}</p>}
    </div>
  }
  return <form className="panel form-grid member-form" onSubmit={event => {
    setDismissedErrors({})
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null
    if (!submitter?.formNoValidate) {
      const invalid = [...event.currentTarget.querySelectorAll<HTMLInputElement>('.member-field input')].filter(input => validate(input))
      if (invalid.length) { event.preventDefault(); invalid[0].focus(); return }
    }
    onSubmit(event)
  }}>
    <h2>{publicRegistration ? t('Request a library account', 'Humiling ng library account') : user ? t('Review library user', 'Suriin ang gumagamit ng aklatan') : t('Register user', 'Magrehistro ng gumagamit')}</h2>
    {user && <p className="member-form-intro">{t('Campus student ID', 'Student ID sa paaralan')}: <strong>{user.student_id}</strong></p>}
    {publicRegistration && <p className="member-form-intro">{t('Scan your ID or type your details. Library staff must review and approve your request before you can borrow.', 'I-scan ang ID o ilagay ang iyong impormasyon. Kailangang suriin at aprubahan ng kawani ang iyong kahilingan bago ka makahiram.')}</p>}
    <fieldset className="member-section"><legend>{t('1. ID & identity', '1. ID at pagkakakilanlan')}</legend>
      <IdScanPanel disabled={busy} onApply={draft => {
        if (user && draft.student_id && draft.student_id !== user.student_id) { setScanWarning(t('The scanned campus number does not match this member. No scanned details were applied.', 'Hindi tugma sa miyembrong ito ang na-scan na numero. Walang inilapat na na-scan na impormasyon.')); return }
        setScanWarning(''); setFields(current => ({ ...current, ...draft, ...(user ? { student_id: current.student_id } : {}) })); setScanned(true); setChecked(false); setLocalErrors({}); setDismissedErrors({ ...fieldErrors })
      }} />
      {scanWarning && <p className="member-form-intro error" role="alert">{scanWarning}</p>}
      {(['student_id', 'library_card_number', 'first_name', 'last_name'] as Field[]).map(renderField)}
    </fieldset>
    <fieldset className="member-section"><legend>{t('2. Academic details', '2. Impormasyon sa pag-aaral')}</legend>{(['course', 'year_level'] as Field[]).map(renderField)}</fieldset>
    <fieldset className="member-section"><legend>{t('3. Contact', '3. Pakikipag-ugnayan')}</legend>{renderField('email')}</fieldset>
    <fieldset className="member-section member-review-section"><legend>{t('4. Review & submit', '4. Suriin at isumite')}</legend>
      <p className="member-form-intro">{t('Check your ID, names, course, year level and contact details before submitting.', 'Suriin ang ID, pangalan, kurso, taon at impormasyon sa pakikipag-ugnayan bago isumite.')}</p>
      {!publicRegistration && <label>{t('Status', 'Katayuan')}<select name="status" defaultValue={user?.account_status.toUpperCase() || 'ACTIVE'} disabled={busy}>{user?.account_status === 'pending' && <option value="PENDING">{t('Pending staff approval', 'Naghihintay ng pag-apruba')}</option>}<option value="ACTIVE">{t('Active', 'Aktibo')}</option><option value="INACTIVE">{t('Inactive', 'Hindi aktibo')}</option><option value="SUSPENDED">{t('Suspended', 'Suspendido')}</option></select></label>}
      {scanned && <label className="member-review"><input type="checkbox" checked={checked} onChange={event => setChecked(event.target.checked)} required disabled={busy} />{t('I checked the scanned names and numbers against the card.', 'Sinuri ko ang mga na-scan na pangalan at numero ayon sa card.')}</label>}
      {publicRegistration && <label className="member-review"><input type="checkbox" required disabled={busy} />{t('These are my details, and I am submitting them for library staff review.', 'Ito ang aking impormasyon, at isinusumite ko ito para sa pagsusuri ng kawani ng aklatan.')}</label>}
    </fieldset>
    <div className="inline member-form-buttons">
      {user?.account_status === 'pending' ? <><button className="primary" name="registration_action" value="approve" disabled={busy || (scanned && !checked)}>{t('Approve registration', 'Aprubahan ang pagpaparehistro')}</button><button name="registration_action" value="reject" formNoValidate disabled={busy}>{t('Reject request', 'Tanggihan ang kahilingan')}</button></> : <button className="primary" disabled={busy || (scanned && !checked)}>{busy ? t('Submitting...', 'Isinusumite...') : publicRegistration ? t('Submit for staff approval', 'Isumite para sa pag-apruba') : t('Save user', 'I-save ang gumagamit')}</button>}
      <button type="button" disabled={busy} onClick={onCancel}>{t('Cancel', 'Kanselahin')}</button>
    </div>
  </form>
}

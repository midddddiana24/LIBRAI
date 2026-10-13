import { useState } from 'react'
import { api, mediaUrl } from './api'

const types = [
  ['daily_borrowing', 'Daily borrowing'], ['weekly_borrowing', 'Weekly borrowing'],
  ['monthly_borrowing', 'Monthly borrowing'], ['overdue', 'Overdue loans'],
  ['inventory', 'Inventory'], ['most_borrowed', 'Most borrowed'],
  ['popular_categories', 'Popular categories'], ['user_activity', 'User activity'],
  ['unpaid_fines', 'Unpaid fines'],
] as const

type Preview = { headers: string[]; items: unknown[][]; total: number }

export default function ReportsPanel({ token }: { token: string }) {
  const [type, setType] = useState<string>('daily_borrowing')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [format, setFormat] = useState('pdf')
  const [preview, setPreview] = useState<Preview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function run(exportFile: boolean) {
    setBusy(true); setError('')
    try {
      if (exportFile) {
        const result = await api<{ download_url: string }>('/reports/export', { method: 'POST', body: JSON.stringify({ report_type: type, start_date: start || null, end_date: end || null, format }) }, token)
        const url = mediaUrl(result.download_url)
        if (url) window.open(url, '_blank', 'noopener,noreferrer')
      } else {
        const params = new URLSearchParams({ report_type: type })
        if (start) params.set('start_date', start)
        if (end) params.set('end_date', end)
        setPreview(await api<Preview>(`/reports?${params}`, {}, token))
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not generate report.') }
    finally { setBusy(false) }
  }

  return <><div className="page-heading"><div><p className="eyebrow">Analytics</p><h1>Reports</h1></div></div><div className="panel report-controls"><label>Report<select value={type} onChange={event => setType(event.target.value)}>{types.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>From<input type="date" value={start} onChange={event => setStart(event.target.value)} /></label><label>To<input type="date" value={end} onChange={event => setEnd(event.target.value)} /></label><label>Export format<select value={format} onChange={event => setFormat(event.target.value)}><option value="pdf">PDF</option><option value="csv">CSV</option><option value="xlsx">Excel</option></select></label><div className="inline"><button disabled={busy} onClick={() => void run(false)}>Preview</button><button className="primary" disabled={busy} onClick={() => void run(true)}>Export report</button></div></div>{error && <p role="alert" className="error">{error}</p>}{preview && <><p>{preview.total} rows · first 100 shown</p><div className="table-wrap"><table><thead><tr>{preview.headers.map(header => <th key={header}>{header}</th>)}</tr></thead><tbody>{preview.items.map((row, index) => <tr key={index}>{row.map((value, column) => <td key={column}>{String(value ?? '—')}</td>)}</tr>)}</tbody></table></div></>}</>
}

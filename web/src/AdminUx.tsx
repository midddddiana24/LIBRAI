import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { adminValue } from './adminValue'
import './admin-ux.css'

export type AdminRow = Record<string, unknown>
export type AdminColumn = { key: string; label: string; render?: (row: AdminRow) => ReactNode }
export type Confirmation = { title: string; description: string; details: [string, string][]; action: string }

export function AdminConfirmation({ request, onAnswer }: { request: Confirmation | null; onAnswer: (answer: boolean) => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    if (!request) return
    const previous = document.activeElement as HTMLElement | null
    const dialog = ref.current
    dialog?.showModal()
    return () => { dialog?.close(); previous?.focus() }
  }, [request])
  if (!request) return null
  return <dialog ref={ref} className="admin-confirmation" aria-labelledby="admin-confirm-title" aria-describedby="admin-confirm-description" onCancel={event => { event.preventDefault(); onAnswer(false) }}>
    <h2 id="admin-confirm-title">{request.title}</h2>
    <p id="admin-confirm-description">{request.description}</p>
    <dl>{request.details.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    <div className="admin-confirm-actions"><button autoFocus onClick={() => onAnswer(false)}>Cancel</button><button className="primary" onClick={() => onAnswer(true)}>{request.action}</button></div>
  </dialog>
}

export function StatusBadge({ value }: { value: unknown }) {
  const status = String(value || 'unknown').toLowerCase()
  return <span className={`admin-status admin-status-${status.replace(/[^a-z]/g, '')}`}>{status.replaceAll('_', ' ')}</span>
}

export function AdminTable({ rows, columns, actions, searchable = false }: { rows: AdminRow[]; columns: AdminColumn[]; actions?: (row: AdminRow) => ReactNode; searchable?: boolean }) {
  const [sort, setSort] = useState('')
  const [query, setQuery] = useState('')
  const visible = useMemo(() => {
    const filtered = rows.filter(row => !query || columns.some(column => adminValue(row[column.key], column.key).toLowerCase().includes(query.toLowerCase())))
    if (!sort) return filtered
    const [key, direction] = sort.split(':')
    return [...filtered].sort((a, b) => {
      const first = a[key], second = b[key]
      const comparison = typeof first === 'number' && typeof second === 'number' ? first - second : String(first ?? '').localeCompare(String(second ?? ''), undefined, { numeric: true, sensitivity: 'base' })
      return direction === 'desc' ? -comparison : comparison
    })
  }, [rows, columns, query, sort])
  return <>
    <div className="admin-table-tools">{searchable && <label>Find on this page<input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Name, title, or record number" /></label>}<label>Sort this page<select aria-label="Sort this page" value={sort} onChange={event => setSort(event.target.value)}><option value="">Default order</option>{columns.flatMap(column => [<option key={`${column.key}:asc`} value={`${column.key}:asc`}>{column.label} ↑</option>, <option key={`${column.key}:desc`} value={`${column.key}:desc`}>{column.label} ↓</option>])}</select></label></div>
    <div className="table-wrap admin-record-table" tabIndex={0} role="region" aria-label="Records table, scroll horizontally for all columns"><table><thead><tr>{columns.map(column => <th scope="col" key={column.key}>{column.label}</th>)}{actions && <th scope="col">Actions</th>}</tr></thead><tbody>{visible.map((row, index) => <tr key={String(row.id ?? index)}>{columns.map(column => <td data-label={column.label} key={column.key}>{column.render ? column.render(row) : ['status', 'account_status'].includes(column.key) ? <StatusBadge value={row[column.key]} /> : adminValue(row[column.key], column.key)}</td>)}{actions && <td data-label="Actions"><div className="admin-row-actions">{actions(row)}</div></td>}</tr>)}</tbody></table>{!visible.length && <p className="empty">{query ? 'No matching records on this page. Clear the page search or try another page.' : 'No records found.'}</p>}</div>
  </>
}

export function AdminPagination({ offset, total, busy, onPage }: { offset: number; total: number; busy: boolean; onPage: (offset: number) => void }) {
  return <nav className="pagination" aria-label="Record pages"><button disabled={busy || offset === 0} onClick={() => onPage(Math.max(0, offset - 20))}>Previous</button><span role="status">{total ? `${offset + 1}–${Math.min(offset + 20, total)} of ${total}` : '0 records'}</span><button disabled={busy || offset + 20 >= total} onClick={() => onPage(offset + 20)}>Next</button></nav>
}

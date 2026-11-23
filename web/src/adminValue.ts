export function adminValue(value: unknown, key = ''): string {
  if (value == null || value === '') return '—'
  if (key === 'amount') return `PHP ${Number(value).toFixed(2)}`
  if (key.endsWith('_at')) {
    const date = new Date(String(value))
    if (!Number.isNaN(date.getTime())) return date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
  }
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}

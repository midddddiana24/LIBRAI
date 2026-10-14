export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '')
const API_ORIGIN = new URL(API_BASE).origin

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

function messageFrom(body: unknown, status: number): string {
  if (body && typeof body === 'object') {
    const value = body as Record<string, unknown>
    const detail = value.detail || value.message || (value.error as Record<string, unknown> | undefined)?.message
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((item) => typeof item === 'object' && item ? String((item as Record<string, unknown>).msg || item) : String(item)).join('; ')
  }
  if (status === 401) return 'Your session or QR verification expired. Please start again.'
  if (status === 409) return 'This action conflicts with the current library record. Please refresh and try again.'
  if (status === 429) return 'Too many attempts. Please wait a moment.'
  return `The library server returned ${status}.`
}

export async function api<T>(path: string, options: RequestInit = {}, token?: string, timeoutMs = 12000): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
      signal: controller.signal,
      cache: 'no-store',
    })
    const body: unknown = await response.json().catch(() => null)
    if (!response.ok) throw new ApiError(messageFrom(body, response.status), response.status)
    return body as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') throw new ApiError('The request timed out. Check the connection and try again.', 0)
    throw new ApiError('Cannot reach the library server. Check the tablet connection.', 0)
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function health(): Promise<boolean> {
  try {
    const response = await fetch(`${API_ORIGIN}/health`, { signal: AbortSignal.timeout(4000), cache: 'no-store' })
    return response.ok
  } catch { return false }
}

export function mediaUrl(path?: string | null): string | undefined {
  if (!path) return undefined
  if (/^https?:\/\//.test(path)) return path
  if (path.startsWith('/')) return `${API_ORIGIN}${path}`
  return `${API_BASE}/${path}`
}

export type Page<T> = { items: T[]; total: number }
export type Book = {
  id: number; title: string; author: string; isbn?: string; category?: string;
  description?: string; shelf_location?: string; cover_url?: string; cover_image?: string;
  available_copies?: number; total_copies?: number; publication_year?: number;
}
export type UserGrant = {
  id: number; student_id: string; name?: string; display_name?: string;
  account_status?: string; can_borrow?: boolean; verification_token: string;
}
export type BookGrant = {
  id: number; book_copy_id: number; book_id: number; title: string; author: string;
  accession_number: string; available: boolean; verification_token: string;
}
export type BorrowReceipt = { id: number; transaction_id: string; book_title: string; borrowed_at: string; due_at: string; status: string }
export type ReturnReceipt = { id: number; transaction_id: string; book_title: string; returned_at: string; return_status: string }
export type ActiveBorrowing = { id: number; book_title: string; user_name: string; student_id: string; due_at: string }

export const books = (query = '', offset = 0) => api<Page<Book>>(`/search/books?q=${encodeURIComponent(query)}&offset=${offset}&limit=20`)
export const bookDetail = (id: number) => api<Book>(`/books/${id}`)
export const verifyUser = (token: string) => api<UserGrant>('/qr/verify-user', { method: 'POST', body: JSON.stringify({ token }) })
export const verifyBook = (token: string) => api<BookGrant>('/qr/verify-book', { method: 'POST', body: JSON.stringify({ token }) })

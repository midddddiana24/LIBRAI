import { lazy, Suspense } from 'react'

const KioskApp = lazy(() => import('./KioskApp'))
const AdminApp = lazy(() => import('./AdminApp'))

export default function App() {
  return <Suspense fallback={<div className="empty">Opening LIBRAI…</div>}>
    {window.location.pathname.startsWith('/admin') ? <AdminApp /> : <KioskApp />}
  </Suspense>
}

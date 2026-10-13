import { lazy, Suspense } from 'react'
import StartupScreen from './StartupScreen'

const KioskApp = lazy(() => import('./KioskApp'))
const AdminApp = lazy(() => import('./AdminApp'))

export default function App() {
  return <Suspense fallback={<StartupScreen />}>
    {window.location.pathname.startsWith('/admin') ? <AdminApp /> : <KioskApp />}
  </Suspense>
}

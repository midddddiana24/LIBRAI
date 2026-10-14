import { lazy, Suspense } from 'react'
import StartupScreen from './StartupScreen'

const KioskApp = lazy(() => import('./KioskApp'))
const AdminApp = lazy(() => import('./AdminApp'))

export default function App() {
  const adminRoute = window.location.pathname.startsWith('/admin')
  return <Suspense fallback={<StartupScreen mode={adminRoute ? 'admin' : 'kiosk'} />}>
    {adminRoute ? <AdminApp /> : <KioskApp />}
  </Suspense>
}

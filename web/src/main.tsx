import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './kiosk-reference.css'
import './voice.css'
import './library-refresh.css'
import './kiosk-tile-menu.css'
import '@fontsource-variable/outfit'
import '@fontsource-variable/source-sans-3/wght.css'
import '../../tokens.css'
import './library-modern.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

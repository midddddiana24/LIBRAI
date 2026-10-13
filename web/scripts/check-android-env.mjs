const url = process.env.VITE_API_BASE_URL

if (!url || !url.startsWith('https://') || !url.endsWith('/api/v1')) {
  console.error('Set VITE_API_BASE_URL to your reachable HTTPS FastAPI URL ending in /api/v1 before building the Android app.')
  process.exit(1)
}

console.log(`Building kiosk for API origin: ${new URL(url).origin}`)

import { createReadStream } from 'node:fs'
import { stat } from 'node:fs/promises'
import { createServer } from 'node:http'
import { dirname, extname, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), 'dist')
const port = Number(process.env.PORT || 10000)
const types = new Map([
  ['.css', 'text/css; charset=utf-8'],
  ['.html', 'text/html; charset=utf-8'],
  ['.ico', 'image/x-icon'],
  ['.jpg', 'image/jpeg'],
  ['.jpeg', 'image/jpeg'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.png', 'image/png'],
  ['.svg', 'image/svg+xml'],
  ['.txt', 'text/plain; charset=utf-8'],
  ['.webp', 'image/webp'],
  ['.woff', 'font/woff'],
  ['.woff2', 'font/woff2'],
])

createServer(async (request, response) => {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    response.writeHead(405, { Allow: 'GET, HEAD' }).end()
    return
  }

  let pathname
  try {
    pathname = decodeURIComponent(new URL(request.url || '/', 'http://localhost').pathname)
  } catch {
    response.writeHead(400).end()
    return
  }

  // The React admin route is handled by the same index.html as the kiosk.
  const route = pathname === '/' || /^\/admin(?:\/.*)?$/.test(pathname)
    ? '/index.html'
    : pathname
  const file = resolve(root, `.${route}`)
  if (!file.startsWith(`${root}${sep}`)) {
    response.writeHead(403).end()
    return
  }

  try {
    const info = await stat(file)
    if (!info.isFile()) throw new Error('Not a file')
    response.writeHead(200, {
      'Content-Type': types.get(extname(file)) || 'application/octet-stream',
      'Content-Length': info.size,
      'Cache-Control': route === '/index.html' ? 'no-cache' : route.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'public, max-age=3600',
      'X-Content-Type-Options': 'nosniff',
    })
    if (request.method === 'HEAD') response.end()
    else createReadStream(file).pipe(response)
  } catch {
    response.writeHead(404).end()
  }
}).listen(port, '0.0.0.0', () => {
  process.stdout.write(`LIBRAI web listening on ${port}\n`)
})

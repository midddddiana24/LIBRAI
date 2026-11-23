import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { helpSteps } from './helpSteps'
import { useKioskLanguage } from './kioskLanguage'
import './guided-help.css'

type Props = { screen: string; phase?: string; tasks?: { id: string; label: string }[]; onTask?: (id: string) => void; admin?: boolean }
type Box = { left: number; top: number; width: number; height: number }
type Layout = { targets: Box[]; left: number; top: number; width: number; maxHeight: number; docked: boolean; viewportHeight: number }
const focusable = 'button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href],[tabindex="0"]'
const overlaps = (a: Box, b: Box) => a.left < b.left + b.width + 10 && a.left + a.width + 10 > b.left && a.top < b.top + b.height + 10 && a.top + a.height + 10 > b.top

export default function GuidedHelp({ screen, phase = '', tasks = [], onTask, admin = false }: Props) {
 const kiosk = useKioskLanguage()
 const [open, setOpen] = useState(false), [picker, setPicker] = useState(true), [language, setLanguage] = useState('en')
 const [compact, setCompact] = useState<boolean | null>(null)
 const [cursor, setCursor] = useState({ key: '', index: 0 })
 const [layout, setLayout] = useState<Layout>({ targets: [], left: 12, top: 12, width: 390, maxHeight: 500, docked: false, viewportHeight: 700 })
 const button = useRef<HTMLButtonElement>(null), panel = useRef<HTMLDivElement>(null), docked = useRef(false)
 const maskId = useId()
 const key = screen + ':' + phase, steps = helpSteps(screen, phase), index = cursor.key === key ? Math.min(cursor.index, steps.length - 1) : 0, step = steps[index]
 const fil = language === 'fil', minimized = compact ?? layout.viewportHeight < 380
 const close = () => { setOpen(false); window.speechSynthesis?.cancel(); button.current?.focus() }
 const progress = screen === 'borrow' ? { current: phase === 'receipt' ? 3 : phase === 'review' ? 2 : phase === 'book' ? 1 : 0, en: ['Library ID', 'Book QR', 'Review', 'Receipt'], fil: ['Library ID', 'QR ng libro', 'Suriin', 'Resibo'] }
  : screen === 'return' ? { current: phase === 'receipt' ? 2 : phase === 'review' ? 1 : 0, en: ['Book QR', 'Review', 'Receipt'], fil: ['QR ng libro', 'Suriin', 'Resibo'] } : null

 // Reserve scroll space for a fallback dock. Keep it docked for this tip so
 // scrolling does not alternate between floating and docked layouts.
 useLayoutEffect(() => {
  if (!open) return
  docked.current = false
  let frame = 0
  const targets = () => picker ? [] : [step.target, step.related].filter(Boolean).flatMap(selector => Array.from(document.querySelectorAll<HTMLElement>(selector!)).slice(0, 1))
  const update = () => {
   const viewport = window.visualViewport
   const left = viewport?.offsetLeft || 0, top = viewport?.offsetTop || 0, width = viewport?.width || innerWidth, height = viewport?.height || innerHeight
   const panelWidth = Math.max(0, Math.min(390, width - 24)), maxHeight = Math.max(64, height - 24)
   const boxes = targets().filter(el => el.getClientRects().length).map(el => {
    const r = el.getBoundingClientRect(); return { left: r.left - 5, top: r.top - 5, width: r.width + 10, height: r.height + 10 }
   })
   const end = document.querySelector<HTMLElement>('[data-help-end]')?.getBoundingClientRect()
   const obstacles = [...boxes, ...(end ? [end] : [])]
   const measuredHeight = Math.min(panel.current?.getBoundingClientRect().height || 360, maxHeight)
   const fits = (point: { left: number; top: number }) => point.left >= left + 12 && point.top >= top + 12 && point.left + panelWidth <= left + width - 12 && point.top + measuredHeight <= top + height - 12 && !obstacles.some(box => overlaps({ ...point, width: panelWidth, height: measuredHeight }, box))
   const target = boxes[0]
   const right = left + width - panelWidth - 12, bottom = top + height - measuredHeight - 12
   const candidates = target ? [
    { left: right, top: target.top + target.height + 16 },
    { left: right, top: target.top - measuredHeight - 16 },
    { left: target.left + target.width + 16, top: Math.max(top + 12, Math.min(target.top, bottom)) },
    { left: target.left - panelWidth - 16, top: Math.max(top + 12, Math.min(target.top, bottom)) },
    { left: right, top: top + 12 }, { left: left + 12, top: top + 12 }, { left: right, top: bottom }, { left: left + 12, top: bottom },
   ] : [{ left: right, top: bottom }]
   const placement = !docked.current && candidates.find(fits)
   if (!picker && !placement) docked.current = true
   const dockHeight = Math.min(measuredHeight, Math.max(64, height * .44))
   const next = { targets: boxes, left: placement ? placement.left : right, top: placement ? placement.top : picker ? top + 12 : top + height - dockHeight - 12, width: panelWidth, maxHeight: docked.current ? Math.max(64, height * .44) : maxHeight, docked: docked.current, viewportHeight: height }
   document.documentElement.style.setProperty('--help-reserved-space', docked.current ? (dockHeight + 24) + 'px' : '0px')
   setLayout(previous => JSON.stringify(previous) === JSON.stringify(next) ? previous : next)
   if (target) {
    const availableBottom = docked.current ? next.top - 16 : top + height - 12
    const adjustment = target.top + target.height > availableBottom ? target.top + target.height - availableBottom : target.top < top + 12 ? target.top - top - 12 : 0
    if (Math.abs(adjustment) > 1 && target.height < availableBottom - top - 12) window.scrollBy({ top: adjustment, behavior: 'instant' })
   }
  }
  const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(update) }
  const observer = new ResizeObserver(schedule)
  if (panel.current) observer.observe(panel.current)
  targets().forEach(target => observer.observe(target))
  const mutation = new MutationObserver(schedule)
  mutation.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-modal', 'data-help-scanning'] })
  targets()[0]?.scrollIntoView({ block: 'nearest', behavior: 'instant' })
  update()
  window.addEventListener('resize', schedule); window.addEventListener('scroll', schedule, true)
  viewportListeners('addEventListener', schedule)
  return () => {
   cancelAnimationFrame(frame); observer.disconnect(); mutation.disconnect()
   window.removeEventListener('resize', schedule); window.removeEventListener('scroll', schedule, true)
   viewportListeners('removeEventListener', schedule)
   document.documentElement.style.removeProperty('--help-reserved-space')
  }
 }, [open, picker, key, index, step.target, step.related, minimized])

 useEffect(() => {
  if (!open) return
  panel.current?.focus({ preventScroll: true })
  const keyboard = (event: KeyboardEvent) => {
   if (document.querySelector('[aria-modal="true"], dialog[open], [data-help-scanning="true"]')) return
   if (event.key === 'Escape') { event.preventDefault(); close() }
   if (event.key === 'Tab') {
    const targets = picker ? [] : [step.target, step.related].filter(Boolean).flatMap(selector => Array.from(document.querySelectorAll<HTMLElement>(selector!)).slice(0, 1))
    const end = document.querySelector<HTMLElement>('[data-help-end]')
    const nodes = [...Array.from(panel.current?.querySelectorAll<HTMLElement>(focusable) || []), ...targets.flatMap(target => [...(target.matches(focusable) ? [target] : []), ...Array.from(target.querySelectorAll<HTMLElement>(focusable))]), ...(end ? [end] : [])].filter((el, i, all) => all.indexOf(el) === i && el.getClientRects().length)
    const current = nodes.indexOf(document.activeElement as HTMLElement), next = event.shiftKey ? (current <= 0 ? nodes.length - 1 : current - 1) : (current + 1) % nodes.length
    if (nodes.length) { event.preventDefault(); nodes[next].focus() }
   }
  }
  document.addEventListener('keydown', keyboard, true)
  return () => { document.removeEventListener('keydown', keyboard, true); window.speechSynthesis?.cancel() }
 }, [open, picker, key, index, step.target, step.related])

 return <><button ref={button} type="button" className="help-launch" aria-expanded={open} onClick={() => { setPicker(true); setCompact(null); setLanguage(admin ? language : kiosk.language); setOpen(true) }}>{!admin && kiosk.language === 'fil' ? 'Tulong' : 'Help'}</button>{open && createPortal(<div className="help-layer" data-docked={layout.docked}>
  <svg className="help-shade" width="100%" height="100%" aria-hidden="true"><defs><mask id={maskId}><rect width="100%" height="100%" fill="white" />{!picker && layout.targets.map((box, i) => <rect key={i} x={box.left} y={box.top} width={box.width} height={box.height} rx="8" fill="black" />)}</mask></defs><rect width="100%" height="100%" mask={'url(#' + maskId + ')'} /></svg>
  {!picker && layout.targets.map((box, i) => <div key={i} className="help-highlight" style={box} />)}
  <div ref={panel} className={'help-panel' + (minimized ? ' is-minimized' : '')} role="dialog" aria-label={fil ? 'Gabay sa LIBRAI' : 'LIBRAI guided help'} tabIndex={-1} style={{ left: layout.left, top: layout.top, width: layout.width, maxHeight: layout.maxHeight }}>
   <div className="help-toolbar"><strong>{fil ? 'Gabay sa LIBRAI' : 'LIBRAI help'}</strong><button type="button" onClick={() => setCompact(!minimized)}>{minimized ? (fil ? 'Ipakita' : 'Show tip') : (fil ? 'Paliitin' : 'Minimize')}</button><button type="button" onClick={close}>{fil ? 'Isara ang gabay' : 'Exit help'}</button></div>
   {!minimized && <><label>{fil ? 'Wika ng gabay' : 'Help language'} <select value={language} onChange={e => { window.speechSynthesis?.cancel(); setLanguage(e.target.value) }}><option value="en">English</option><option value="fil">Filipino</option></select></label>
    {picker ? <><h2>{fil ? 'Ano ang kailangan mo?' : 'What would you like help with?'}</h2><button type="button" onClick={() => { setCursor({ key, index: 0 }); setPicker(false) }}>{fil ? 'Gabayan ako sa screen na ito' : 'Guide this screen'}</button><div className="help-task-list">{tasks.map(task => <button type="button" key={task.id} onClick={() => { onTask?.(task.id); setCursor({ key: '', index: 0 }); setPicker(false) }}>{task.label}</button>)}</div><p>{admin ? (fil ? 'Pumili ng seksyon gamit ang navigation, pagkatapos buksan ang Help.' : 'For another task, use the section navigation, then open Help.') : (fil ? 'Pumili ng serbisyo sa Home. Susundan ng gabay ang iyong progreso.' : 'Choose a service on Home. Help follows your successful progress.')}</p></> : <>
     {progress ? <><h2>{fil ? 'Hakbang' : 'Step'} {progress.current + 1} / {progress.en.length}: {(fil ? progress.fil : progress.en)[progress.current]}</h2><ol className="help-progress" aria-label={fil ? 'Progreso ng gawain' : 'Task progress'}>{(fil ? progress.fil : progress.en).map((label, i) => <li key={label} aria-current={i === progress.current ? 'step' : undefined} className={i < progress.current ? 'is-complete' : ''}><span aria-hidden="true">{i < progress.current ? '✓' : i + 1}</span>{label}</li>)}</ol></> : <h2>{fil ? 'Gabay' : 'Guide'}{steps.length > 1 ? ' ' + (index + 1) + ' / ' + steps.length : ''}</h2>}
     <p aria-live="polite">{fil ? step.fil : step.en}</p>{!layout.targets.length && <p role="status">{fil ? 'Hindi available ang control. Sundin ang instruction o pumili ng ibang gabay.' : 'This control is not available. Read the instruction or choose another guide.'}</p>}{step.wait && <p className="help-wait">{fil ? 'Ikaw ang gumawa ng action. Susunod ang gabay kapag nagtagumpay ito.' : 'Complete the action yourself. Help follows successful progress.'}</p>}
     <div className="help-actions"><button type="button" disabled={index === 0} onClick={() => setCursor({ key, index: index - 1 })}>{fil ? 'Bumalik' : 'Back'}</button><button type="button" disabled={!!step.wait} onClick={() => index === steps.length - 1 ? close() : setCursor({ key, index: index + 1 })}>{index === steps.length - 1 ? (fil ? 'Tapos' : 'Done') : (fil ? 'Susunod' : 'Next')}</button><button type="button" onClick={() => setPicker(true)}>{fil ? 'Pumili ng gabay' : 'Choose a task'}</button></div>
     {'speechSynthesis' in window && <button type="button" onClick={() => { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(fil ? step.fil : step.en); u.lang = fil ? 'fil-PH' : 'en-PH'; speechSynthesis.speak(u) }}>{fil ? 'Basahin nang malakas' : 'Read aloud'}</button>}
    </>}
   </>}
  </div>
 </div>, document.body)}</>
}

function viewportListeners(method: 'addEventListener' | 'removeEventListener', handler: () => void) {
 window.visualViewport?.[method]('resize', handler)
 window.visualViewport?.[method]('scroll', handler)
}


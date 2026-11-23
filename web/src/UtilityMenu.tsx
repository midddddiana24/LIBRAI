import { useEffect, useRef, type ReactNode } from 'react'

/** Persistent children keep Help sessions and native dialogs alive when closed. */
export default function UtilityMenu({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDetailsElement>(null)
  useEffect(() => {
    const close = (event: PointerEvent | KeyboardEvent) => {
      const menu = ref.current
      if (!menu?.open || document.querySelector('dialog[open], .help-panel')) return
      if (event instanceof KeyboardEvent) {
        if (event.key !== 'Escape' || event.defaultPrevented) return
        menu.open = false
        menu.querySelector('summary')?.focus()
      } else if (!menu.contains(event.target as Node)) menu.open = false
    }
    document.addEventListener('pointerdown', close)
    document.addEventListener('keydown', close)
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', close) }
  }, [])
  return <details className="utility-menu" ref={ref}><summary aria-label="Library options">Options</summary><div className="utility-menu-panel">{children}</div></details>
}

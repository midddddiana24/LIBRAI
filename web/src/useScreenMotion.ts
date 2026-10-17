import type { RefObject } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'

gsap.registerPlugin(useGSAP)

// Scope entry motion to the current view; data refreshes do not replay it.
export default function useScreenMotion(scope: RefObject<HTMLDivElement | null>, screen: string) {
  useGSAP(() => {
    const media = gsap.matchMedia()
    media.add('(prefers-reduced-motion: no-preference)', () => {
      const targets = scope.current?.querySelectorAll('.kiosk-intro, .kiosk-task, .page-heading, .metric, .workspace-panel, .login-card')
      if (targets?.length) gsap.fromTo(targets, { opacity: .45, y: 8 }, {
        opacity: 1, y: 0, duration: .32, stagger: .025, ease: 'power2.out', clearProps: 'opacity,transform',
      })
    })
    return () => media.revert()
  }, { scope, dependencies: [screen], revertOnUpdate: true })
}

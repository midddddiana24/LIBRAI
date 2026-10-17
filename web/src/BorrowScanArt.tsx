// Decorative drawings only: real QR values stay inside the scanner controls.
export function BorrowScanArt({ kind }: { kind: 'id' | 'book' | 'confirm' }) {
  return <svg className={`borrow-art borrow-art-${kind}`} viewBox="0 0 320 260" fill="none" aria-hidden="true">
    <g stroke="var(--color-accent)" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M26 62V32a8 8 0 0 1 8-8h34M252 24h34a8 8 0 0 1 8 8v30M294 198v30a8 8 0 0 1-8 8h-34M68 236H34a8 8 0 0 1-8-8v-30" />
    </g>
    {kind === 'id' ? <>
      <ellipse cx="160" cy="214" rx="98" ry="9" fill="var(--color-soft)" />
      <g transform="rotate(-7 160 137)" stroke="var(--color-ink)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
        <rect x="51" y="82" width="218" height="126" rx="14" fill="var(--color-paper)" />
        <rect x="66" y="99" width="70" height="90" rx="8" fill="var(--color-book-peach)" stroke="none" />
        <circle cx="101" cy="128" r="14" fill="var(--color-paper)" />
        <path d="M78 174v-4a23 23 0 0 1 46 0v4Z" fill="var(--color-paper)" />
        <path d="M155 111h91M155 126h91M155 141h54" stroke="var(--color-rule)" strokeWidth="5" />
        <path d="M156 160v25m8-25v25m10-25v25m7-25v25m12-25v25m7-25v25m11-25v25m12-25v25m7-25v25m10-25v25" />
      </g>
      <path d="m246 66 10-13m-25 6 2-15m22 34 16-3" stroke="var(--color-book-peach)" strokeWidth="5" strokeLinecap="round" />
    </> : kind === 'book' ? <g transform="rotate(12 160 135)" stroke="var(--color-ink)" strokeWidth="4" strokeLinejoin="round">
      <path d="M103 61h112v146H108a13 13 0 0 1-13-13V74a13 13 0 0 1 8-13Z" fill="var(--color-book-blue)" />
      <path d="M108 184h107v23H108a11.5 11.5 0 0 1 0-23Z" fill="var(--color-paper)" />
      <path d="M113 64v115" /><rect x="135" y="97" width="59" height="59" rx="3" fill="var(--color-paper)" />
      <path d="M144 106h13v13h-13Zm28 0h13v13h-13Zm-28 28h13v13h-13Zm28 0h5v5h8v8h-13Z" fill="var(--color-ink)" stroke="none" />
    </g> : <g stroke="var(--color-ink)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M181 208h-68a12 12 0 0 1-12-12V66a12 12 0 0 1 12-12h92a12 12 0 0 1 12 12v93" fill="var(--color-paper)" />
      <path d="M124 86h70m-70 24h70m-70 24h40" stroke="var(--color-rule)" />
      <circle cx="214" cy="189" r="35" fill="var(--color-blue-soft)" /><path d="m198 189 11 11 22-24" stroke="var(--color-accent)" />
    </g>}
  </svg>
}

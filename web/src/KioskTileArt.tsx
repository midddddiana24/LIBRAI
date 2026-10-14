type Kind = 'borrow' | 'return' | 'find' | 'discover'

// Original small illustrations stay crisp on tablets and can take the card's colors.
export default function KioskTileArt({ kind }: { kind: Kind }) {
  return <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    {kind === 'borrow' && <>
      <path d="M25 83h69v11H25z" fill="var(--tile-accent)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M32 71h59v12H32z" fill="var(--tile-paper)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M23 57h65v14H23z" fill="var(--tile-pop)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M33 42h57v15H33z" fill="var(--tile-paper)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M79 25h23v25H79z" fill="var(--tile-accent)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M84 33h13m-13 6h9M29 63h13m48 24H75" stroke="var(--tile-ink)" strokeWidth="2.5" strokeLinecap="round" />
      <path d="m54 28 2 5 5 2-5 2-2 5-2-5-5-2 5-2 2-5Z" fill="var(--tile-pop)" stroke="var(--tile-ink)" strokeWidth="2" />
    </>}
    {kind === 'return' && <>
      <path d="M25 79h70v14H25z" fill="var(--tile-accent)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M31 79V47c9-2 18-1 29 4 11-5 20-6 29-4v32c-10-2-19-1-29 4-10-5-19-6-29-4Z" fill="var(--tile-paper)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M60 51v32M39 56c5-.2 9 .3 14 2m14 0c5-2 9-2.2 14-2" stroke="var(--tile-ink)" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M87 31C77 23 62 24 53 32c-4 3-6 8-7 13m0 0-8-6m8 6 8-7" stroke="var(--tile-ink)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="m92 38 1.5 4 4 1.5-4 1.5-1.5 4-1.5-4-4-1.5 4-1.5 1.5-4Z" fill="var(--tile-pop)" stroke="var(--tile-ink)" strokeWidth="2" />
    </>}
    {kind === 'find' && <>
      <path d="M29 26h51v14H29z" fill="var(--tile-pop)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M35 40h55v13H35z" fill="var(--tile-paper)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M24 53h56v14H24z" fill="var(--tile-accent)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <circle cx="67" cy="65" r="21" fill="var(--tile-paper)" stroke="var(--tile-ink)" strokeWidth="4" />
      <path d="m52 81-18 19" stroke="var(--tile-ink)" strokeWidth="9" strokeLinecap="round" />
      <path d="m50 86-13 13" stroke="var(--tile-accent)" strokeWidth="5" strokeLinecap="round" />
      <path d="M59 58c3-3 7-4 11-3" stroke="var(--tile-ink)" strokeWidth="2.5" strokeLinecap="round" />
    </>}
    {kind === 'discover' && <>
      <circle cx="60" cy="62" r="39" fill="var(--tile-accent)" stroke="var(--tile-ink)" strokeWidth="3" />
      <path d="M30 58c10-3 20-2 30 4 10-6 20-7 30-4v28c-11-3-21-2-30 4-9-6-19-7-30-4V58Z" fill="var(--tile-paper)" stroke="var(--tile-ink)" strokeWidth="3" strokeLinejoin="round" />
      <path d="M60 62v28M37 66c6-1 11 0 16 2m14 0c5-2 10-3 16-2" stroke="var(--tile-ink)" strokeWidth="2.5" strokeLinecap="round" />
      <path d="m61 29 3 8 8 3-8 3-3 8-3-8-8-3 8-3 3-8Zm24 5 1.5 4 4 1.5-4 1.5-1.5 4-1.5-4-4-1.5 4-1.5 1.5-4Z" fill="var(--tile-pop)" stroke="var(--tile-ink)" strokeWidth="2" strokeLinejoin="round" />
    </>}
  </svg>
}

type Kind = 'borrow' | 'return' | 'find' | 'discover'

// A shared book-spine and scan-card language keeps the four services recognizable.
export default function KioskTileArt({ kind }: { kind: Kind }) {
  return <svg viewBox="0 0 160 140" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <ellipse cx="80" cy="72" rx="58" ry="55" fill="var(--tile-accent)" opacity=".16" />
    <g stroke="var(--tile-ink)" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
      {kind === 'borrow' && <>
        <path d="M39 30h57v81H39c-7 0-11-5-11-11V42c0-7 4-12 11-12Z" fill="var(--tile-paper)" />
        <path d="M47 23h55v86H47c-7 0-11-4-11-10V35c0-7 4-12 11-12Z" fill="var(--tile-accent)" />
        <path d="M47 23v86M58 43h32v22H58z" fill="var(--tile-paper)" />
        <path d="m87 82 39 7-7 34-39-7 7-34Z" fill="var(--tile-paper)" />
        <path d="m91 94-2 11m8-10-2 11m8-10-2 11m8-10-2 11m8-10-2 11M117 59l8-5m-11-5 3-8" />
      </>}
      {kind === 'return' && <>
        <path d="M28 91h102v29H28z" fill="var(--tile-accent)" />
        <path d="m28 91 14-16h74l14 16H28Z" fill="var(--tile-paper)" />
        <path d="m65 39 41 13-19 54-42-13 20-54Z" fill="var(--tile-accent)" />
        <path d="m72 52 22 7-7 19-22-7 7-19Z" fill="var(--tile-paper)" />
        <path d="M39 29c-10 1-17 10-15 22m0 0-7-5m7 5 5-7" />
        <path d="M22 121h116" />
      </>}
      {kind === 'find' && <>
        <path d="M84 36h19v75H84z" fill="var(--tile-paper)" />
        <path d="m108 51 16-2 7 61-16 2-7-61Z" fill="var(--tile-accent)" />
        <path d="M64 61h17v50H64z" fill="var(--tile-pop)" />
        <circle cx="58" cy="60" r="29" fill="var(--tile-accent)" />
        <circle cx="58" cy="60" r="21" fill="var(--tile-paper)" />
        <path d="m37 83-19 25" strokeWidth="13" />
        <path d="m36 85-17 22" stroke="var(--tile-accent)" strokeWidth="6" />
        <path d="M48 49c3-4 8-5 12-4M58 117h79M90 47h7" />
      </>}
      {kind === 'discover' && <>
        <path d="M29 62c16-4 34-1 51 9 17-10 35-13 51-9v51c-18-4-34-1-51 8-17-9-33-12-51-8V62Z" fill="var(--tile-accent)" />
        <path d="M34 54c16-1 31 3 46 13 15-10 30-14 46-13v50c-16-1-31 3-46 13-15-10-30-14-46-13V54Z" fill="var(--tile-paper)" />
        <path d="M80 67v50M44 70c9 1 16 4 24 9m24 0c8-5 15-8 24-9M44 83c9 1 16 4 24 9m24 0c8-5 15-8 24-9" />
        <path d="m80 18 5 12 12 5-12 5-5 12-5-12-12-5 12-5 5-12Z" fill="var(--tile-pop)" strokeWidth="2.5" />
        <path d="m116 31 5-7M42 38l-5-7" />
      </>}
    </g>
  </svg>
}

type Kind = 'borrow' | 'return' | 'catalog' | 'account' | 'discover' | 'assistant'

export default function LibraryActionIcon({ kind, className = '' }: { kind: Kind; className?: string }) {
  const book = <><path d="M31.5 16.5c-5.2-3.1-11-3.7-17.5-2v31c6.5-1.7 12.3-1.1 17.5 2 5.2-3.1 11-3.7 17.5-2v-31c-6.5-1.7-12.3-1.1-17.5 2Z" /><path d="M31.5 16.5v31" /><path d="M18.5 23c3.2-.5 6.1-.2 8.8.8M36 23.8c2.7-1 5.6-1.3 8.8-.8" /></>
  const detail = {
    borrow: <><path d="M39 35h13m-5-5 5 5-5 5" /><path d="M17 51h28" /></>,
    return: <><path d="M51 32H38m5-5-5 5 5 5" /><path d="M17 51h28" /></>,
    catalog: <><path d="M16 47h31M19 42V16h10v26m5 0V21h10v21" /><path d="M22 22h4m-4 6h4m11 0h4" /></>,
    account: <><circle cx="32" cy="24" r="7" /><path d="M18 47c1.2-7.5 6.1-11 14-11s12.8 3.5 14 11H18Z" /></>,
    discover: <><path d="m32 11 3.3 9.7L45 24l-9.7 3.3L32 37l-3.3-9.7L19 24l9.7-3.3L32 11Zm15 25 1.5 4.5L53 42l-4.5 1.5L47 48l-1.5-4.5L41 42l4.5-1.5L47 36Z" /><path d="M17 42h16m-16 6h12" /></>,
    assistant: <><path d="M16 18h32v23H31l-9 7v-7h-6V18Z" /><path d="M24 29h16m-16 6h10" /></>,
  }[kind]

  return <svg className={className} viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {(kind === 'borrow' || kind === 'return') && book}
    {detail}
  </svg>
}

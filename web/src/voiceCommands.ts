export type VoiceCommand =
  | { action: 'home' | 'borrow' | 'return' | 'account' | 'assistant' | 'discover'; kind?: 'recommended' | 'popular' | 'new' }
  | { action: 'search'; query: string }
  | { action: 'ask'; query: string }

export function resolveVoiceCommand(text: string): VoiceCommand | null {
  const command = text.trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.!?]+$/, '')
  if (!command) return null
  if (/\b(go home|home page|return home|back home|main menu|go to home|take me home|home)\b/.test(command) || /^(?:punta sa )?(?:home|unang pahina)$/.test(command)) return { action: 'home' }
  if (/\b(show available books|show me books i can borrow|available books|books on shelf|what books can i borrow|books available|what can i borrow|browse catalog|show all books)\b/.test(command) || /^(?:search books|find books|catalog|books|book|hanap ng libro|hanap ng aklat)$/.test(command) || /^(?:ipakita|tingnan) (?:ang )?(?:mga )?libro$/.test(command)) return { action: 'search', query: '' }
  if (/\b(return|give back|bring back)\b.*\b(book|books|one|it)\b/.test(command) || /^(?:please )?(?:return|returns)$/.test(command) || /\b(start return|i want to return|can i return)\b/.test(command) || /\b(?:ibalik|isauli|magsauli|magbalik|balik)\b(?:.*\b(?:libro|aklat|book)\b)?/.test(command)) return { action: 'return' }
  if (/\b(borrow|barrow|burrow|take out|get)\b.*\b(book|books|something|one)\b/.test(command) || /^(?:please )?(?:borrow|borro|boro|barrow|burrow)$/.test(command) || /\b(start borrowing|i want to borrow|i need to borrow|can i borrow)\b/.test(command) || /\b(?:manghiram|humiram|maghiram|hiram|pahiram)\b(?:.*\b(?:libro|aklat|book)\b)?/.test(command)) return { action: 'borrow' }
  if (/\b(my account|open account|show account|my loans|my borrowed books|library account|account)\b/.test(command) || /\b(?:aking account|account ko|mga hiniram ko)\b/.test(command)) return { action: 'account' }
  if (/\b(popular books|most popular books|trending books)\b/.test(command)) return { action: 'discover', kind: 'popular' }
  if (/\b(new books|new arrivals|latest books|recent books)\b/.test(command)) return { action: 'discover', kind: 'new' }
  if (/\b(recommended books|recommendations|books for me|recommend a book|recommend something)\b/.test(command)) return { action: 'discover', kind: 'recommended' }
  if (/\b(ask librai|open assistant|talk to assistant)\b/.test(command)) return { action: 'assistant' }
  const filipinoSearch = command.match(/^(?:hanap|hanapin|maghanap|maghanap ng|hanap ng)\s+(?:ng\s+)?(?:libro|aklat|book)?\s*(?:tungkol sa|na tungkol sa|ni|ng)?\s*(.+)$/)
  if (filipinoSearch?.[1]) return { action: 'search', query: filipinoSearch[1].trim() }
  const search = command.match(/^(?:please )?(?:search(?: for)?|find|look for|show me)\s+(?:some\s+)?(?:books?\s+(?:about|on|by)\s+)?(.+)$/)
  if (search?.[1]) return { action: 'search', query: search[1] }
  return { action: 'ask', query: text.trim() }
}

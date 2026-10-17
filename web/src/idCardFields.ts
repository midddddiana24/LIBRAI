export type CardKind = 'campus' | 'library'
export type IdDraft = Partial<Record<'student_id' | 'library_card_number' | 'first_name' | 'last_name' | 'course', string>>

function splitName(value: string): Pick<IdDraft, 'first_name' | 'last_name'> {
  const name = value.replace(/^NAME\s*:?\s*/i, '').replace(/\s+/g, ' ').trim()
  if (!/^[\p{L}\p{M} .,'’-]+$/u.test(name) || name.split(/\s+/).length < 2) return {}
  if (/UNIVERSITY|CAMPUS|INFORMATION|TECHNOLOGY|SCHOOL|COLLEGE|SIGNATURE|PRESIDENT|IMPORTANT|ADDRESS|EMERGENCY/i.test(name)) return {}
  const suffix = /^(JR\.?|SR\.?|II|III|IV)$/i
  if (name.includes(',')) {
    const parts = name.split(',').map(p => p.trim()).filter(Boolean)
    const last = parts.shift()!
    const ending = parts[0] && suffix.test(parts[0]) ? parts.shift() : ''
    return parts.length ? { first_name: parts.join(' '), last_name: [last, ending].filter(Boolean).join(' ') } : {}
  }
  const words = name.split(' ')
  const ending = suffix.test(words.at(-1)!) ? words.pop() : ''
  let last = words.pop()!
  while (words.length > 1 && /^(DE|DEL|DELA|LOS|LAS|VAN|VON|SAN|SANTA)$/i.test(words.at(-1)!)) last = `${words.pop()} ${last}`
  return words.length ? { first_name: words.join(' '), last_name: [last, ending].filter(Boolean).join(' ') } : {}
}

// Return only registration fields. Never infer identity, enrollment, or contact data.
export function parseIdCard(text: string, kind: CardKind): IdDraft {
  const lines = text.normalize('NFKC').split(/\r?\n/).map(s => s.replace(/\s+/g, ' ').trim()).filter(Boolean)
  const draft: IdDraft = {}
  const numberPattern = /\b\d{2}\s*-\s*\d{3,8}\b/g
  if (kind === 'campus') {
    const candidates = lines.flatMap((line, index) => /^(?:(?:STUDENT\s*(?:ID|NO\.?|NUMBER))\s*:?\s*)?\d{2}\s*-\s*\d{3,8}$/i.test(line) ? [{ value: line.match(numberPattern)![0].replace(/\s/g, ''), index }] : [])
    if (new Set(candidates.map(c => c.value)).size === 1) {
      draft.student_id = candidates[0].value
      for (const line of lines.slice(candidates[0].index + 1, candidates[0].index + 3)) {
        const name = splitName(line)
        if (name.first_name) { Object.assign(draft, name); break }
      }
    }
    const course = lines.find(line => /^(?:BS|BA|BACHELOR OF SCIENCE|BACHELOR OF ARTS)\s+[\p{L}]/iu.test(line) || /^BS[A-Z]{2,5}$/i.test(line))
    if (course && course.length <= 150) draft.course = course
  } else {
    const match = lines.join('\n').match(/BORROWER['’]?S?\s+CARD\s+(?:NO\.?|NUMBER)\s*:?\s*(\d{2}\s*-\s*\d{3,8})\b/i)
    if (match) draft.library_card_number = match[1].replace(/\s/g, '')
    const index = lines.findIndex(line => /^NAME(?:\s|:|$)/i.test(line))
    if (match && index >= 0) {
      const value = lines[index].replace(/^NAME\s*:?\s*/i, '') || lines[index + 1] || ''
      Object.assign(draft, splitName(value))
    }
  }
  return draft
}

export type CardKind = 'campus' | 'library'
export type IdDraft = Partial<Record<'student_id' | 'library_card_number' | 'first_name' | 'last_name' | 'course', string>>

function normalized(text: string): string {
  return text.normalize('NFKC').replace(/[\u2010-\u2015\u2212]/g, '-').replace(/[\u2018\u2019]/g, "'")
}

export function cardScanHint(text: string, kind: CardKind): string | null {
  const value = normalized(text)
  if (/STUDENT\s+INFORMATION|IN\s+CASE\s+OF\s+EMERGENCY|EMERGENCY\s+CONTACT|RENEWAL\s+CHART|BIRTHDAY/i.test(value)) return 'This looks like the back of a card. Photograph the front with the name and card number.'
  const library = /BORROWER\s*'?S?\s*CARD/i.test(value)
  if (kind === 'campus' && library) return "This looks like a library card. Choose Library borrower's card front, then select the photo again."
  if (kind === 'library' && !library && /STUDENT\s*(?:ID|NUMBER)|\bCAMPUS\b|\bBS\s+INFORMATION/i.test(value)) return 'This looks like a campus ID. Choose Campus ID front, then select the photo again.'
  return null
}

function splitName(value: string): Pick<IdDraft, 'first_name' | 'last_name'> {
  const name = value.replace(/^NAME\s*:?\s*/i, '').replace(/\s+/g, ' ').trim()
  if (!/^[\p{L}\p{M} .,'-]+$/u.test(name) || name.split(/\s+/).length < 2) return {}
  if (/UNIVERSITY|CAMPUS|INFORMATION|TECHNOLOGY|SCHOOL|COLLEGE|SIGNATURE|PRESIDENT|IMPORTANT|ADDRESS|EMERGENCY/i.test(name) || /^(?:BS|BA|BACHELOR)\b/i.test(name)) return {}
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

// Extract only printed registration fields; never repair digits or infer enrollment.
export function parseIdCard(text: string, kind: CardKind): IdDraft {
  if (cardScanHint(text, kind)) return {}
  const lines = normalized(text).split(/\r?\n/).map(s => s.replace(/\s+/g, ' ').replace(/^[|\s]+|[|\s]+$/g, '')).filter(Boolean)
  const draft: IdDraft = {}
  if (kind === 'campus') {
    const candidates = lines.flatMap((line, index) => {
      const match = line.match(/^(?:(?:STUDENT\s*(?:ID|NO\.?|NUMBER)|ID\s*(?:NO\.?|NUMBER)?)[\s:#.-]*)?(\d{2}\s*-\s*\d{3,8})(?![\p{L}\d])(.*)$/iu)
      if (!match || (match[2].trim() && !splitName(match[2].replace(/^[|:; ]+/, '')).first_name)) return []
      return [{ value: match[1].replace(/\s/g, ''), index, name: match[2].replace(/^[|:; ]+/, '').trim() }]
    })
    if (new Set(candidates.map(c => c.value)).size === 1) {
      const candidate = candidates[0]
      draft.student_id = candidate.value
      for (const line of [candidate.name, ...lines.slice(candidate.index + 1, candidate.index + 4)]) {
        const name = splitName(line)
        if (name.first_name) { Object.assign(draft, name); break }
      }
    }
    const courses = lines.map(line => line.replace(/^COURSE\s*:?\s*/i, '').replace(/^B\.S\.\s*/i, 'BS '))
    const course = courses.find(line => /^(?:BS|BA|BACHELOR OF SCIENCE|BACHELOR OF ARTS)\s+[\p{L}]/iu.test(line) || /^BS[A-Z]{2,5}$/i.test(line))
    if (course && course.length <= 150) draft.course = course
  } else {
    const match = lines.join('\n').match(/BORROWER\s*'?S?\s*CARD\s*(?:NO\.?|NUMBER|#)\s*[:#.]?\s*(\d{2}\s*-\s*\d{3,8})\b/i)
    if (match) draft.library_card_number = match[1].replace(/\s/g, '')
    const index = lines.findIndex(line => /^NAME(?:\s|:|$)/i.test(line))
    if (match && index >= 0) {
      const value = lines[index].replace(/^NAME\s*:?\s*/i, '') || lines[index + 1] || ''
      Object.assign(draft, splitName(value))
    }
  }
  return draft
}

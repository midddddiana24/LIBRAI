import assert from 'node:assert/strict'
import test from 'node:test'
import { cardScanHint, parseIdCard } from './idCardFields.ts'

test('campus front fills only student number, name, and printed course', () => {
  assert.deepEqual(parseIdCard('SAMPLE STATE UNIVERSITY\n25-1234\nJUAN P. DELA CRUZ JR.\nBS Information Technology', 'campus'), {
    student_id: '25-1234', first_name: 'JUAN P.', last_name: 'DELA CRUZ JR.', course: 'BS Information Technology',
  })
})
test('library number is separate and surname-first names preserve suffix and initial', () => {
  assert.deepEqual(parseIdCard("BORROWER'S CARD\nBorrower's Card No. 25-9876\nNAME DELA CRUZ, JR., JUAN, P.\nADDRESS Sample town", 'library'), {
    library_card_number: '25-9876', first_name: 'JUAN P.', last_name: 'DELA CRUZ JR.',
  })
})
test('backs, emergency contacts, document numbers, and renewal years do not become registration fields', () => {
  const back = 'STUDENT INFORMATION\nBirthday January 1, 2001\nIn case of EMERGENCY\nName Emergency Person\nTel No. 09000000000\n2026-2027 IV-C\nDocument No. SCHOOL-LRC-01'
  assert.deepEqual(parseIdCard(back, 'campus'), {})
  assert.deepEqual(parseIdCard(back, 'library'), {})
})
test('ambiguous student numbers require manual input', () => {
  assert.deepEqual(parseIdCard('25-1234\nJUAN CRUZ\n25-5678', 'campus'), {})
})

test('campus OCR accepts a labeled number, Unicode dash and a name on the same line', () => {
  assert.deepEqual(parseIdCard('STUDENT ID: 25\u20131234 | JUAN P. DELA CRUZ JR.\nCourse: B.S. Information Technology', 'campus'), {
    student_id: '25-1234', first_name: 'JUAN P.', last_name: 'DELA CRUZ JR.', course: 'BS Information Technology',
  })
})

test('library OCR accepts curly apostrophes and wrapped number/name labels', () => {
  assert.deepEqual(parseIdCard('BORROWER\u2019S CARD\nBorrower\u2019s Card No.\n25 - 9876\nNAME:\nDELA CRUZ, JR., JUAN, P.', 'library'), {
    library_card_number: '25-9876', first_name: 'JUAN P.', last_name: 'DELA CRUZ JR.',
  })
})

test('wrong card and back photos produce guidance without filling fields', () => {
  const library = "BORROWER'S CARD\nBorrower's Card No. 25-9876\nNAME JUAN CRUZ"
  assert.deepEqual(parseIdCard(library, 'campus'), {})
  assert.match(cardScanHint(library, 'campus'), /Choose Library/)
  const campus = 'STUDENT ID 25-1234\nJUAN CRUZ\nBS Information Technology'
  assert.deepEqual(parseIdCard(campus, 'library'), {})
  assert.match(cardScanHint(campus, 'library'), /Choose Campus/)
  assert.match(cardScanHint('STUDENT INFORMATION\nBirthday January 1', 'campus'), /back of a card/)
})

test('OCR does not guess unreadable digits or use document and academic year numbers', () => {
  assert.deepEqual(parseIdCard('STUDENT ID 25-I234\nJUAN CRUZ', 'campus'), {})
  assert.deepEqual(parseIdCard('Document No. 25-1234\n2026-2027\nJUAN CRUZ', 'campus'), {})
})

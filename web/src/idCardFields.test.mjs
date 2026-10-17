import assert from 'node:assert/strict'
import test from 'node:test'
import { parseIdCard } from './idCardFields.ts'

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

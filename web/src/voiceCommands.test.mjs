import assert from 'node:assert/strict'
import test from 'node:test'
import { resolveVoiceCommand } from './voiceCommands.ts'

test('voice commands open the intended safe kiosk flow', () => {
  assert.deepEqual(resolveVoiceCommand('Borrow a book'), { action: 'borrow' })
  assert.deepEqual(resolveVoiceCommand('Return this book'), { action: 'return' })
  assert.deepEqual(resolveVoiceCommand('Show my account'), { action: 'account' })
  assert.deepEqual(resolveVoiceCommand('Go home'), { action: 'home' })
  assert.deepEqual(resolveVoiceCommand('borrow'), { action: 'borrow' })
  assert.deepEqual(resolveVoiceCommand('Boro'), { action: 'borrow' })
  assert.deepEqual(resolveVoiceCommand('return'), { action: 'return' })
  assert.deepEqual(resolveVoiceCommand('Manghiram ng libro'), { action: 'borrow' })
  assert.deepEqual(resolveVoiceCommand('Ibalik ang libro'), { action: 'return' })
  assert.deepEqual(resolveVoiceCommand('Pahiram ng libro'), { action: 'borrow' })
  assert.deepEqual(resolveVoiceCommand('Account ko'), { action: 'account' })
})

test('catalog requests do not accidentally start borrowing', () => {
  assert.deepEqual(resolveVoiceCommand('Show me books I can borrow'), { action: 'search', query: '' })
  assert.deepEqual(resolveVoiceCommand('Find books about Philippine history'), { action: 'search', query: 'philippine history' })
  assert.deepEqual(resolveVoiceCommand('Hanap ng libro tungkol sa kasaysayan'), { action: 'search', query: 'kasaysayan' })
  assert.deepEqual(resolveVoiceCommand('Hanap ng libro'), { action: 'search', query: '' })
  assert.deepEqual(resolveVoiceCommand('Search for books about astronomy'), { action: 'search', query: 'astronomy' })
})

test('questions require a separate Ask tap', () => {
  assert.deepEqual(resolveVoiceCommand('Can you suggest a mystery book?'), { action: 'ask', query: 'Can you suggest a mystery book?' })
  assert.equal(resolveVoiceCommand('  '), null)
})


test('English, Filipino and mixed policy questions stay in the assistant', () => {
  for (const phrase of ['How many books can I borrow?', 'Ilang libro ang puwedeng hiramin?', 'Magkano ang multa?', 'Show easier ones', 'Only available books', 'Can I renew my libro?']) {
    assert.deepEqual(resolveVoiceCommand(phrase), { action: 'ask', query: phrase })
  }
  assert.deepEqual(resolveVoiceCommand('Find books about borrowing laws'), { action: 'search', query: 'borrowing laws' })
})

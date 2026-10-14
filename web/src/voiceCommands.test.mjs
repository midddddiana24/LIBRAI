import assert from 'node:assert/strict'
import test from 'node:test'
import { resolveVoiceCommand } from './voiceCommands.ts'

test('voice commands open the intended safe kiosk flow', () => {
  assert.deepEqual(resolveVoiceCommand('Borrow a book'), { action: 'borrow' })
  assert.deepEqual(resolveVoiceCommand('Return this book'), { action: 'return' })
  assert.deepEqual(resolveVoiceCommand('Show my account'), { action: 'account' })
  assert.deepEqual(resolveVoiceCommand('Go home'), { action: 'home' })
})

test('catalog requests do not accidentally start borrowing', () => {
  assert.deepEqual(resolveVoiceCommand('Show me books I can borrow'), { action: 'search', query: '' })
  assert.deepEqual(resolveVoiceCommand('Find books about Philippine history'), { action: 'search', query: 'philippine history' })
})

test('questions require a separate Ask tap', () => {
  assert.deepEqual(resolveVoiceCommand('Can you suggest a mystery book?'), { action: 'ask', query: 'Can you suggest a mystery book?' })
  assert.equal(resolveVoiceCommand('  '), null)
})

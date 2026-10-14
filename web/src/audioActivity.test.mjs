import assert from 'node:assert/strict'
import test from 'node:test'
import { hasAudibleAudio } from './audioActivity.ts'

test('silence and recorder noise do not reach the transcriber', () => {
  assert.equal(hasAudibleAudio(new Float32Array(16000), 16000), false)
  assert.equal(hasAudibleAudio(Float32Array.from({ length: 16000 }, () => 0.001), 16000), false)
})

test('a brief spoken word can pass the audio activity check', () => {
  const samples = new Float32Array(16000)
  for (let index = 2000; index < 6000; index++) samples[index] = Math.sin(index * 0.3) * 0.025
  assert.equal(hasAudibleAudio(samples, 16000), true)
})

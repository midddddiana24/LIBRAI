// A silent recording can make a generative transcriber invent words. Check the
// decoded microphone signal before uploading it. This is a coarse silence
// check, not a speech classifier: a user still reviews the final transcript.
export function hasAudibleAudio(samples: Float32Array, sampleRate: number): boolean {
  if (!samples.length || !Number.isFinite(sampleRate) || sampleRate <= 0) return false
  const frameSize = Math.max(1, Math.floor(sampleRate * 0.02))
  let activeFrames = 0
  for (let offset = 0; offset < samples.length; offset += frameSize) {
    const end = Math.min(offset + frameSize, samples.length)
    let power = 0
    for (let index = offset; index < end; index++) power += samples[index] * samples[index]
    const rms = Math.sqrt(power / (end - offset))
    if (rms >= 0.006) activeFrames++
  }
  return activeFrames * 0.02 >= 0.1
}

export async function recordingHasAudibleAudio(blob: Blob): Promise<boolean | null> {
  if (typeof AudioContext === 'undefined') return null
  const context = new AudioContext()
  try {
    const decoded = await context.decodeAudioData(await blob.arrayBuffer())
    for (let channel = 0; channel < decoded.numberOfChannels; channel++) {
      if (hasAudibleAudio(decoded.getChannelData(channel), decoded.sampleRate)) return true
    }
    return false
  } catch {
    // The recorder's format may work for transcription even if this browser
    // cannot decode it. Keep the review step available in that case.
    return null
  } finally {
    await context.close().catch(() => undefined)
  }
}

import { useEffect, useRef, useState } from 'react'
import { LoaderCircle, Mic, Square } from 'lucide-react'
import { api } from './api'

const MAX_RECORDING_MS = 12_000
const MAX_AUDIO_BYTES = 4 * 1024 * 1024

type Props = { label: string; disabled?: boolean; onTranscript: (text: string) => void }

function recordingType(): string {
  for (const type of ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']) {
    if (MediaRecorder.isTypeSupported(type)) return type
  }
  return ''
}

export default function VoiceControl({ label, disabled = false, onTranscript }: Props) {
  const [status, setStatus] = useState<'idle' | 'listening' | 'transcribing'>('idle')
  const [message, setMessage] = useState('')
  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<number | null>(null)
  const mountedRef = useRef(true)
  const onTranscriptRef = useRef(onTranscript)

  useEffect(() => { onTranscriptRef.current = onTranscript }, [onTranscript])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (timerRef.current !== null) window.clearTimeout(timerRef.current)
      recorderRef.current?.stop()
      streamRef.current?.getTracks().forEach(track => track.stop())
    }
  }, [])

  function stop() {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current)
    timerRef.current = null
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
  }

  async function start() {
    setMessage('')
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setMessage('Microphone recording is unavailable in this browser. Use a supported HTTPS browser or the Android app.')
      return
    }
    let stream: MediaStream | null = null
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (!mountedRef.current) { stream.getTracks().forEach(track => track.stop()); return }
      streamRef.current = stream
      const mimeType = recordingType()
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      recorderRef.current = recorder
      const chunks: BlobPart[] = []
      let failed = false
      recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data) }
      recorder.onerror = () => {
        failed = true
        stream?.getTracks().forEach(track => track.stop())
        streamRef.current = null
        if (mountedRef.current) { setStatus('idle'); setMessage('Recording failed. Please try again.') }
      }
      recorder.onstop = () => {
        stream?.getTracks().forEach(track => track.stop())
        streamRef.current = null
        recorderRef.current = null
        if (!mountedRef.current) return
        if (failed) return
        const recordedType = recorder.mimeType.split(';')[0] || 'audio/webm'
        const type = recordedType === 'audio/mp4' ? 'audio/m4a' : recordedType
        const blob = new Blob(chunks, { type })
        if (!blob.size) { setStatus('idle'); setMessage('No audio was recorded. Please try again.'); return }
        if (blob.size > MAX_AUDIO_BYTES) { setStatus('idle'); setMessage('Recording is too large. Please try a shorter command.'); return }
        setStatus('transcribing')
        const form = new FormData()
        form.append('audio', blob, type === 'audio/m4a' ? 'speech.m4a' : type === 'audio/ogg' ? 'speech.ogg' : 'speech.webm')
        void api<{ text: string }>('/speech/transcribe', { method: 'POST', body: form }, undefined, 45_000)
          .then(result => {
            if (!mountedRef.current) return
            const text = result.text.trim()
            setMessage(text ? `Heard: “${text}”` : 'No words were detected. Please try again.')
            if (text) onTranscriptRef.current(text)
          })
          .catch(error => { if (mountedRef.current) setMessage(error instanceof Error ? error.message : 'Speech transcription failed.') })
          .finally(() => { if (mountedRef.current) setStatus('idle') })
      }
      recorder.start()
      setStatus('listening')
      timerRef.current = window.setTimeout(stop, MAX_RECORDING_MS)
    } catch (error) {
      stream?.getTracks().forEach(track => track.stop())
      streamRef.current = null
      setStatus('idle')
      setMessage(error instanceof DOMException && error.name === 'NotAllowedError'
        ? 'Microphone access was denied. Allow it in your browser or Android settings, then try again.'
        : 'Could not start the microphone. Check that another app is not using it.')
    }
  }

  return <div className="voice-control">
    <button type="button" className={status === 'listening' ? 'voice-button listening' : 'voice-button'} disabled={disabled || status === 'transcribing'} onClick={status === 'listening' ? stop : () => void start()}>
      {status === 'listening' ? <Square aria-hidden="true" /> : status === 'transcribing' ? <LoaderCircle className="loading-spinner" aria-hidden="true" /> : <Mic aria-hidden="true" />}
      <span>{status === 'listening' ? 'Stop recording' : status === 'transcribing' ? 'Transcribing…' : label}</span>
    </button>
    <span className="voice-message" role="status" aria-live="polite">{message || (status === 'listening' ? 'Listening. Speak now, then tap Stop.' : '')}</span>
  </div>
}

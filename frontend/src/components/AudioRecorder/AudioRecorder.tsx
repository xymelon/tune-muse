/**
 * AudioRecorder component: browser-side recording interface.
 * Provides one-click start/stop recording, real-time waveform visualization, recording timing, and microphone permission processing.
 * Support keyboard operation (spacebar start/stop) to meet accessibility requirements.
 */

import { useState, useRef, useCallback, useEffect } from 'react'

/** Recording state enum */
type RecordingState = 'idle' | 'recording' | 'processing'

interface AudioRecorderProps {
  /** Callback after recording completes, receives AudioBuffer (for feature extraction) and Blob (backup) */
  onRecordingComplete: (audioBuffer: AudioBuffer, blob: Blob) => void
  /** Error callback */
  onError: (message: string) => void
  /** Whether currently processing (controlled by parent component) */
  isProcessing?: boolean
}

export default function AudioRecorder({
  onRecordingComplete,
  onError,
  isProcessing = false,
}: AudioRecorderProps) {
  const [state, setState] = useState<RecordingState>(isProcessing ? 'processing' : 'idle')
  const [duration, setDuration] = useState(0)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationRef = useRef<number | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)

  // Sync external processing state
  useEffect(() => {
    if (isProcessing) setState('processing')
  }, [isProcessing])

  /**
   * Draw real-time waveform to canvas.
   * Uses Web Audio API AnalyserNode to get time-domain data.
   */
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current
    const analyser = analyserRef.current
    if (!canvas || !analyser) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    analyser.getByteTimeDomainData(dataArray)

    ctx.fillStyle = '#F9FAFB'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.lineWidth = 2
    ctx.strokeStyle = '#4F46E5'
    ctx.beginPath()

    const sliceWidth = canvas.width / bufferLength
    let x = 0

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0
      const y = (v * canvas.height) / 2

      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
      x += sliceWidth
    }

    ctx.lineTo(canvas.width, canvas.height / 2)
    ctx.stroke()

    animationRef.current = requestAnimationFrame(drawWaveform)
  }, [])

  /**
   * Start recording: request microphone permission, create MediaRecorder, start waveform visualization and timer.
   */
  const startRecording = useCallback(async () => {
    try {
      // Check browser support
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        onError(
          'Your browser does not support microphone access. Please use the file upload option instead.',
        )
        return
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      // Set up audio analyzer for waveform visualization
      const audioContext = new AudioContext()
      audioContextRef.current = audioContext
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      source.connect(analyser)
      analyserRef.current = analyser

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })

        try {
          // Decode recording to AudioBuffer for feature extraction
          const arrayBuffer = await blob.arrayBuffer()
          const decodeContext = new AudioContext()
          const audioBuffer = await decodeContext.decodeAudioData(arrayBuffer)
          onRecordingComplete(audioBuffer, blob)
        } catch {
          onError('Failed to process the recording. Please try again.')
        }
      }

      mediaRecorder.start()
      setState('recording')
      setDuration(0)

      // Start timer
      timerRef.current = window.setInterval(() => {
        setDuration((d) => d + 1)
      }, 1000)

      // Start waveform visualization
      drawWaveform()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        onError(
          'Microphone access was denied. Please allow microphone access in your browser settings, or use the file upload option.',
        )
      } else {
        onError('Failed to access microphone. Please check your device settings.')
      }
    }
  }, [onRecordingComplete, onError, drawWaveform])

  /**
   * Stop recording: stop MediaRecorder, clean up timer and waveform animation.
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }

    // Stop microphone stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    // Clean up timer and animation
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    setState('processing')
  }, [])

  /**
   * Toggle recording state: start when idle, stop when recording.
   */
  const toggleRecording = useCallback(() => {
    if (state === 'idle') {
      startRecording()
    } else if (state === 'recording') {
      stopRecording()
    }
  }, [state, startRecording, stopRecording])

  // Keyboard shortcut: Space key toggles recording
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && e.target === document.body) {
        e.preventDefault()
        toggleRecording()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggleRecording])

  // Clean up resources on component unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop())
      if (audioContextRef.current) audioContextRef.current.close()
    }
  }, [])

  /**
   * Format seconds to MM:SS display format.
   */
  const formatDuration = (seconds: number): string => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 'var(--space-6)',
      }}
    >
      {/* Waveform visualization area */}
      <canvas
        ref={canvasRef}
        width={400}
        height={100}
        style={{
          width: '100%',
          maxWidth: 400,
          height: 100,
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--color-surface)',
          border: `1px solid var(--color-border)`,
        }}
        aria-label="Audio waveform visualization"
      />

      {/* Recording duration display */}
      {state === 'recording' && (
        <div
          style={{
            fontSize: 'var(--font-size-2xl)',
            fontWeight: 'var(--font-weight-semibold)',
            fontVariantNumeric: 'tabular-nums',
          }}
          aria-live="polite"
        >
          {formatDuration(duration)}
        </div>
      )}

      {/* Record button */}
      <button
        onClick={toggleRecording}
        disabled={state === 'processing'}
        aria-label={
          state === 'idle'
            ? 'Start recording'
            : state === 'recording'
              ? 'Stop recording'
              : 'Processing...'
        }
        style={{
          width: 80,
          height: 80,
          borderRadius: 'var(--radius-full)',
          border: 'none',
          cursor: state === 'processing' ? 'not-allowed' : 'pointer',
          backgroundColor:
            state === 'recording' ? 'var(--color-error)' : 'var(--color-primary)',
          color: 'var(--color-text-on-primary)',
          fontSize: 'var(--font-size-sm)',
          fontWeight: 'var(--font-weight-semibold)',
          fontFamily: 'var(--font-family)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background-color 0.2s, transform 0.1s',
          opacity: state === 'processing' ? 0.6 : 1,
          boxShadow: 'var(--shadow-md)',
        }}
      >
        {state === 'idle' && 'REC'}
        {state === 'recording' && 'STOP'}
        {state === 'processing' && '...'}
      </button>

      {/* Hint text */}
      <p
        style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          textAlign: 'center',
        }}
      >
        {state === 'idle' && 'Tap to start recording. Sing for 10–60 seconds.'}
        {state === 'recording' && 'Sing now! Tap again to stop.'}
        {state === 'processing' && 'Analyzing your voice...'}
      </p>
    </div>
  )
}

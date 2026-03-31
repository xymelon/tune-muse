/**
 * Home page: entry point for recording or uploading audio.
 * Supports switching between recording and upload modes.
 * After recording, extracts audio features, submits analysis, and navigates to results page.
 */

import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import AudioRecorder from '../components/AudioRecorder/AudioRecorder'
import AudioUploader from '../components/AudioUploader/AudioUploader'
import type { AnalyzeResponse, AudioFeatures } from '../types'
import { submitFeatures } from '../services/api'

type InputMode = 'record' | 'upload'

export default function HomePage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<InputMode>('record')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Post-recording processing flow:
   * 1. Extract audio features (Meyda.js + pitchfinder)
   * 2. Quality check
   * 3. Submit to backend for analysis
   * 4. Navigate to results page
   */
  const handleRecordingComplete = useCallback(
    async (audioBuffer: AudioBuffer, _blob: Blob) => {
      setIsProcessing(true)
      setError(null)

      try {
        // Dynamically import audio analysis module (code splitting, reduce initial load)
        const { analyzeAudio } = await import('../services/audioAnalyzer')
        const { checkQuality } = await import('../services/qualityChecker')

        // Extract audio features
        const features: AudioFeatures = analyzeAudio(audioBuffer)

        // Quality check
        const quality = checkQuality(features)
        if (!quality.passed) {
          setError(quality.issues[0])
          setIsProcessing(false)
          return
        }

        // Submit to backend
        const result: AnalyzeResponse = await submitFeatures({
          source_type: 'recording',
          duration_seconds: audioBuffer.duration,
          features,
        })

        // Store in sessionStorage for the results page
        sessionStorage.setItem(`analysis_${result.session_id}`, JSON.stringify(result))

        // Navigate to results page
        navigate(`/analysis/${result.session_id}`)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Analysis failed. Please try again.'
        setError(message)
        setIsProcessing(false)
      }
    },
    [navigate],
  )

  const handleError = useCallback((message: string) => {
    setError(message)
    setIsProcessing(false)
  }, [])

  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: 'var(--space-6)' }}>
      {/* Brand header */}
      <header style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
        <h1
          style={{
            fontSize: 'var(--font-size-4xl)',
            fontWeight: 'var(--font-weight-bold)',
            marginBottom: 'var(--space-3)',
            color: 'var(--color-text)',
          }}
        >
          TuneMuse
        </h1>
        <p
          style={{
            fontSize: 'var(--font-size-lg)',
            color: 'var(--color-text-secondary)',
            maxWidth: 500,
            margin: '0 auto',
          }}
        >
          Sing a few bars and discover song styles that match your voice.
        </p>
      </header>

      {/* Mode toggle tabs */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: 'var(--space-2)',
          marginBottom: 'var(--space-6)',
        }}
      >
        {(['record', 'upload'] as InputMode[]).map((m) => (
          <button
            key={m}
            onClick={() => {
              setMode(m)
              setError(null)
            }}
            style={{
              padding: 'var(--space-2) var(--space-5)',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-family)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 'var(--font-weight-medium)',
              backgroundColor: mode === m ? 'var(--color-primary)' : 'var(--color-surface-dark)',
              color: mode === m ? 'var(--color-text-on-primary)' : 'var(--color-text-secondary)',
              transition: 'background-color 0.2s',
            }}
          >
            {m === 'record' ? 'Record' : 'Upload'}
          </button>
        ))}
      </div>

      {/* Main content area */}
      <section
        style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-8)',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        {mode === 'record' ? (
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            onError={handleError}
            isProcessing={isProcessing}
          />
        ) : (
          <AudioUploader
            onUploadComplete={(result: AnalyzeResponse) => {
              sessionStorage.setItem(`analysis_${result.session_id}`, JSON.stringify(result))
              navigate(`/analysis/${result.session_id}`)
            }}
            onError={handleError}
            isProcessing={isProcessing}
          />
        )}
      </section>

      {/* Error message */}
      {error && (
        <div
          role="alert"
          style={{
            marginTop: 'var(--space-4)',
            padding: 'var(--space-4)',
            backgroundColor: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: 'var(--radius-md)',
            color: '#991B1B',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {error}
        </div>
      )}
    </main>
  )
}

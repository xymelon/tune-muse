/**
 * Analysis results page: displays Vocal profile and Song recommendations.
 * Gets analysis result data from sessionStorage, or fetches from API.
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import VocalProfile from '../components/VocalProfile/VocalProfile'
import Recommendations from '../components/Recommendations/Recommendations'
import type { AnalyzeResponse } from '../types'
import { getSessionDetail } from '../services/api'

export default function AnalysisPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      navigate('/')
      return
    }

    // Prioritize sessionStorage (for just-completed analysis scenario)
    const cached = sessionStorage.getItem(`analysis_${sessionId}`)
    if (cached) {
      try {
        setData(JSON.parse(cached))
        setLoading(false)
        return
      } catch {
        // Cache corrupted, fetch from API
      }
    }

    // Fetch from API
    getSessionDetail(sessionId)
      .then((result) => {
        setData(result)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load analysis results.')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [sessionId, navigate])

  if (loading) {
    return (
      <main
        style={{
          maxWidth: 900,
          margin: '0 auto',
          padding: 'var(--space-6)',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            padding: 'var(--space-12)',
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--font-size-lg)',
          }}
        >
          Loading analysis results...
        </div>
      </main>
    )
  }

  if (error || !data) {
    return (
      <main style={{ maxWidth: 900, margin: '0 auto', padding: 'var(--space-6)' }}>
        <div
          role="alert"
          style={{
            padding: 'var(--space-6)',
            backgroundColor: '#FEF2F2',
            borderRadius: 'var(--radius-md)',
            color: '#991B1B',
            textAlign: 'center',
          }}
        >
          <p style={{ marginBottom: 'var(--space-4)' }}>{error || 'No analysis data found.'}</p>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: 'var(--space-2) var(--space-5)',
              backgroundColor: 'var(--color-primary)',
              color: 'var(--color-text-on-primary)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              fontFamily: 'var(--font-family)',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            Back to Home
          </button>
        </div>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 'var(--space-6)' }}>
      {/* Page header */}
      <header style={{ marginBottom: 'var(--space-6)' }}>
        <h1
          style={{
            fontSize: 'var(--font-size-2xl)',
            fontWeight: 'var(--font-weight-bold)',
            marginBottom: 'var(--space-2)',
          }}
        >
          Your Vocal Analysis
        </h1>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          Here's what we found in your singing voice.
        </p>
      </header>

      {/* Vocal profile */}
      <section style={{ marginBottom: 'var(--space-8)' }}>
        <VocalProfile profile={data.vocal_profile} />
      </section>

      {/* Song recommendations */}
      <section style={{ marginBottom: 'var(--space-8)' }}>
        <Recommendations recommendations={data.recommendations} />
      </section>

      {/* Action buttons */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-4)' }}>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: 'var(--space-3) var(--space-6)',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-text-on-primary)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer',
            fontFamily: 'var(--font-family)',
            fontSize: 'var(--font-size-base)',
            fontWeight: 'var(--font-weight-medium)',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          Record Again
        </button>
      </div>
    </main>
  )
}

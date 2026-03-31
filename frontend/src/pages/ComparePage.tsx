/**
 * Comparison page: Compare the Vocal profiles of two analysis sessions side by side to track vocal development.
 */

import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import type { SessionDetailResponse } from '../types'
import { getSessionDetail } from '../services/api'

/**
 * Comparison indicator: shows the direction and magnitude of change between two values.
 */
function Delta({ label, a, b, unit = '', higherIsBetter = true }: {
  label: string; a: number; b: number; unit?: string; higherIsBetter?: boolean
}) {
  const diff = b - a
  const threshold = 0.03
  let arrow = '='
  let color = 'var(--color-text-secondary)'
  if (Math.abs(diff) > threshold) {
    const isPositive = higherIsBetter ? diff > 0 : diff < 0
    arrow = diff > 0 ? '↑' : '↓'
    color = isPositive ? 'var(--color-success)' : 'var(--color-warning)'
  }

  const fmt = (v: number) => unit === '%' ? `${Math.round(v * 100)}%` : v.toFixed(2)

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 'var(--font-size-sm)' }}>
      <span style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
      <div style={{ display: 'flex', gap: 'var(--space-3)', fontVariantNumeric: 'tabular-nums' }}>
        <span>{fmt(a)}</span>
        <span style={{ color, fontWeight: 'var(--font-weight-semibold)', minWidth: 24, textAlign: 'center' }}>{arrow}</span>
        <span>{fmt(b)}</span>
      </div>
    </div>
  )
}

export default function ComparePage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [sessionA, setSessionA] = useState<SessionDetailResponse | null>(null)
  const [sessionB, setSessionB] = useState<SessionDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const idA = params.get('a')
  const idB = params.get('b')

  useEffect(() => {
    if (!idA || !idB) {
      setError('Two session IDs required for comparison.')
      setLoading(false)
      return
    }

    Promise.all([getSessionDetail(idA), getSessionDetail(idB)])
      .then(([a, b]) => { setSessionA(a); setSessionB(b) })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load sessions.'))
      .finally(() => setLoading(false))
  }, [idA, idB])

  if (loading) {
    return (
      <main style={{ maxWidth: 1024, margin: '0 auto', padding: 'var(--space-6)', textAlign: 'center' }}>
        <p style={{ color: 'var(--color-text-secondary)', padding: 'var(--space-12)' }}>Loading comparison...</p>
      </main>
    )
  }

  if (error || !sessionA || !sessionB) {
    return (
      <main style={{ maxWidth: 1024, margin: '0 auto', padding: 'var(--space-6)' }}>
        <div role="alert" style={{ padding: 'var(--space-6)', backgroundColor: '#FEF2F2', borderRadius: 'var(--radius-md)', color: '#991B1B', textAlign: 'center' }}>
          <p>{error || 'Could not load comparison data.'}</p>
          <button onClick={() => navigate('/history')} style={{ marginTop: 'var(--space-3)', padding: 'var(--space-2) var(--space-5)', backgroundColor: 'var(--color-primary)', color: 'var(--color-text-on-primary)', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-family)' }}>
            Back to History
          </button>
        </div>
      </main>
    )
  }

  const pA = sessionA.vocal_profile
  const pB = sessionB.vocal_profile
  const dateA = new Date(sessionA.created_at).toLocaleDateString()
  const dateB = new Date(sessionB.created_at).toLocaleDateString()

  return (
    <main style={{ maxWidth: 1024, margin: '0 auto', padding: 'var(--space-6)' }}>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', marginBottom: 'var(--space-5)' }}>
        Compare Sessions
      </h1>

      {/* Date header */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-6)', textAlign: 'center' }}>
        <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--color-surface-dark)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)' }}>{dateA}</div>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>Session A</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', fontSize: 'var(--font-size-xl)', color: 'var(--color-text-secondary)' }}>→</div>
        <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--color-surface-dark)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)' }}>{dateB}</div>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>Session B</div>
        </div>
      </div>

      {/* Pitch comparison */}
      <section style={{ backgroundColor: 'white', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', marginBottom: 'var(--space-4)', border: '1px solid var(--color-border)' }}>
        <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)' }}>Pitch Range</h2>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', marginBottom: 'var(--space-3)' }}>
          <div>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-primary)' }}>{pA.pitch.range_low} – {pA.pitch.range_high}</div>
          </div>
          <div style={{ color: 'var(--color-text-secondary)' }}>→</div>
          <div>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-primary)' }}>{pB.pitch.range_low} – {pB.pitch.range_high}</div>
          </div>
        </div>
        <Delta label="Pitch Stability" a={pA.pitch.stability} b={pB.pitch.stability} unit="%" />
      </section>

      {/* Rhythm comparison */}
      <section style={{ backgroundColor: 'white', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', marginBottom: 'var(--space-4)', border: '1px solid var(--color-border)' }}>
        <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)' }}>Rhythm</h2>
        <Delta label="Regularity" a={pA.rhythm.regularity} b={pB.rhythm.regularity} unit="%" />
      </section>

      {/* Mood comparison */}
      <section style={{ backgroundColor: 'white', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', marginBottom: 'var(--space-4)', border: '1px solid var(--color-border)' }}>
        <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)' }}>
          Mood: {pA.mood.label} → {pB.mood.label}
        </h2>
        <Delta label="Positivity" a={pA.mood.valence} b={pB.mood.valence} unit="%" />
        <Delta label="Energy" a={pA.mood.energy} b={pB.mood.energy} unit="%" />
        <Delta label="Tension" a={pA.mood.tension} b={pB.mood.tension} unit="%" higherIsBetter={false} />
      </section>

      {/* Timbre comparison */}
      <section style={{ backgroundColor: 'white', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', marginBottom: 'var(--space-4)', border: '1px solid var(--color-border)' }}>
        <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)' }}>
          Timbre: {pA.timbre.label} → {pB.timbre.label}
        </h2>
        <Delta label="Warmth" a={pA.timbre.warmth} b={pB.timbre.warmth} unit="%" />
        <Delta label="Brightness" a={pA.timbre.brightness} b={pB.timbre.brightness} unit="%" />
        <Delta label="Breathiness" a={pA.timbre.breathiness} b={pB.timbre.breathiness} unit="%" />
      </section>

      {/* Expression comparison */}
      <section style={{ backgroundColor: 'white', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', marginBottom: 'var(--space-6)', border: '1px solid var(--color-border)' }}>
        <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)' }}>Expression</h2>
        <Delta label="Vibrato" a={pA.expression.vibrato} b={pB.expression.vibrato} unit="%" />
        <Delta label="Dynamic Range" a={pA.expression.dynamic_range} b={pB.expression.dynamic_range} unit="%" />
      </section>

      <div style={{ textAlign: 'center' }}>
        <button onClick={() => navigate('/history')} style={{ padding: 'var(--space-3) var(--space-6)', backgroundColor: 'var(--color-primary)', color: 'var(--color-text-on-primary)', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-family)', fontWeight: 'var(--font-weight-medium)' }}>
          Back to History
        </button>
      </div>
    </main>
  )
}

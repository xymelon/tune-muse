/**
 * History page: displays user's analysis session list with pagination and comparison selection.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import type { SessionSummary } from '../types'
import { getSessionHistory } from '../services/api'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const limit = 20

  const token = localStorage.getItem('tunemuse_token')

  const fetchSessions = useCallback(async (pageOffset: number) => {
    setLoading(true)
    try {
      const data = await getSessionHistory(limit, pageOffset)
      if (pageOffset === 0) {
        setSessions(data.sessions)
      } else {
        setSessions((prev) => [...prev, ...data.sessions])
      }
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (token) fetchSessions(0)
    else setLoading(false)
  }, [token, fetchSessions])

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else if (next.size < 2) {
        next.add(id)
      }
      return next
    })
  }

  const handleCompare = () => {
    const ids = Array.from(selected)
    if (ids.length === 2) {
      navigate(`/compare?a=${ids[0]}&b=${ids[1]}`)
    }
  }

  if (!token) {
    return (
      <main style={{ maxWidth: 800, margin: '0 auto', padding: 'var(--space-6)', textAlign: 'center' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', marginBottom: 'var(--space-4)' }}>
          Analysis History
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-4)' }}>
          Please log in to view your analysis history.
        </p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: 'var(--space-6)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', margin: 0 }}>
          Analysis History
        </h1>
        <button
          onClick={handleCompare}
          disabled={selected.size !== 2}
          style={{
            padding: 'var(--space-2) var(--space-5)',
            backgroundColor: selected.size === 2 ? 'var(--color-primary)' : 'var(--color-surface-dark)',
            color: selected.size === 2 ? 'var(--color-text-on-primary)' : 'var(--color-text-secondary)',
            border: 'none', borderRadius: 'var(--radius-md)', cursor: selected.size === 2 ? 'pointer' : 'not-allowed',
            fontFamily: 'var(--font-family)', fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)',
          }}
        >
          Compare ({selected.size}/2)
        </button>
      </div>

      {error && (
        <div role="alert" style={{ padding: 'var(--space-4)', backgroundColor: '#FEF2F2', borderRadius: 'var(--radius-md)', color: '#991B1B', marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-sm)' }}>
          {error}
        </div>
      )}

      {!loading && sessions.length === 0 && (
        <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-secondary)' }}>
          <p>No analysis history yet. Record or upload audio to get started!</p>
          <button
            onClick={() => navigate('/')}
            style={{ marginTop: 'var(--space-4)', padding: 'var(--space-2) var(--space-5)', backgroundColor: 'var(--color-primary)', color: 'var(--color-text-on-primary)', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-family)' }}
          >
            Start Analysis
          </button>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {sessions.map((s) => (
          <div
            key={s.id}
            style={{
              display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
              backgroundColor: selected.has(s.id) ? '#EEF2FF' : 'white',
              border: `1px solid ${selected.has(s.id) ? 'var(--color-primary)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-md)', padding: 'var(--space-4)',
              cursor: 'pointer', transition: 'all 0.15s',
            }}
            onClick={() => toggleSelect(s.id)}
          >
            <input
              type="checkbox"
              checked={selected.has(s.id)}
              onChange={() => toggleSelect(s.id)}
              style={{ width: 18, height: 18, accentColor: 'var(--color-primary)' }}
              aria-label={`Select session from ${s.created_at}`}
            />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)' }}>
                  {s.source_type === 'recording' ? '🎤' : '📁'}{' '}
                  {new Date(s.created_at).toLocaleDateString()} {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {s.recommendation_count} recommendations
                </span>
              </div>
              {s.vocal_profile_summary && (
                <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-1)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  <span>{s.vocal_profile_summary.pitch_range}</span>
                  <span>{s.vocal_profile_summary.mood_label}</span>
                  <span>{s.vocal_profile_summary.timbre_label}</span>
                </div>
              )}
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); navigate(`/analysis/${s.id}`) }}
              style={{ padding: 'var(--space-1) var(--space-3)', fontSize: 'var(--font-size-xs)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'white', cursor: 'pointer', fontFamily: 'var(--font-family)', color: 'var(--color-text-secondary)' }}
            >
              View
            </button>
          </div>
        ))}
      </div>

      {sessions.length < total && (
        <div style={{ textAlign: 'center', marginTop: 'var(--space-5)' }}>
          <button
            onClick={() => { const next = offset + limit; setOffset(next); fetchSessions(next) }}
            disabled={loading}
            style={{ padding: 'var(--space-2) var(--space-5)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', background: 'white', cursor: 'pointer', fontFamily: 'var(--font-family)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}
          >
            {loading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
    </main>
  )
}

/**
 * Login/Register modal component.
 */

import { useState } from 'react'
import type { AuthResponse } from '../../types'
import { login, register } from '../../services/api'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (auth: AuthResponse) => void
}

export default function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      let result: AuthResponse
      if (mode === 'login') {
        result = await login(email, password)
      } else {
        result = await register({ email, password, display_name: displayName || undefined })
      }
      onSuccess(result)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        backgroundColor: 'rgba(0,0,0,0.4)',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      onKeyDown={(e) => { if (e.key === 'Escape') onClose() }}
    >
      <div
        style={{
          backgroundColor: 'white', borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)', width: '100%', maxWidth: 400,
          boxShadow: 'var(--shadow-lg)',
        }}
        role="dialog"
        aria-label={mode === 'login' ? 'Login' : 'Register'}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-5)' }}>
          <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', margin: 0 }}>
            {mode === 'login' ? 'Login' : 'Create Account'}
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 'var(--font-size-xl)', cursor: 'pointer', color: 'var(--color-text-secondary)' }} aria-label="Close">
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <input
            type="email" placeholder="Email" required value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', fontFamily: 'var(--font-family)', fontSize: 'var(--font-size-base)' }}
          />
          <input
            type="password" placeholder="Password" required value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', fontFamily: 'var(--font-family)', fontSize: 'var(--font-size-base)' }}
          />
          {mode === 'register' && (
            <input
              type="text" placeholder="Display Name (optional)" value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              style={{ padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', fontFamily: 'var(--font-family)', fontSize: 'var(--font-size-base)' }}
            />
          )}

          {error && (
            <p style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-sm)', margin: 0 }}>{error}</p>
          )}

          <button
            type="submit" disabled={loading}
            style={{
              padding: 'var(--space-3)', backgroundColor: 'var(--color-primary)',
              color: 'var(--color-text-on-primary)', border: 'none', borderRadius: 'var(--radius-md)',
              cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-family)',
              fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-medium)',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? '...' : mode === 'login' ? 'Login' : 'Register'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 'var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null) }}
            style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', fontFamily: 'var(--font-family)', fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)' }}
          >
            {mode === 'login' ? 'Register' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  )
}

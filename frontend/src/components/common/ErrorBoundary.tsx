/**
 * ErrorBoundary component: captures JavaScript errors of subcomponents and displays a friendly error interface.
 * Prevent the entire application from having a white screen due to a single component error.
 */

import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          style={{
            maxWidth: 500,
            margin: '80px auto',
            padding: 'var(--space-8)',
            textAlign: 'center',
            fontFamily: 'var(--font-family)',
          }}
        >
          <h2
            style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: 'var(--font-weight-bold)',
              marginBottom: 'var(--space-3)',
              color: 'var(--color-text)',
            }}
          >
            Something went wrong
          </h2>
          <p
            style={{
              color: 'var(--color-text-secondary)',
              marginBottom: 'var(--space-5)',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            An unexpected error occurred. Please refresh the page and try again.
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false })
              window.location.href = '/'
            }}
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
            }}
          >
            Back to Home
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

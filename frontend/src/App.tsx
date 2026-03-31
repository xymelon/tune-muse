import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import ErrorBoundary from './components/common/ErrorBoundary'
import './tokens/design-tokens.css'

/**
 * TuneMuse application root component.
 * Configures page routing with React Router v7, supports code splitting and lazy loading.
 */

// Lazy-load page components to reduce initial bundle size
const HomePage = lazy(() => import('./pages/HomePage'))
const AnalysisPage = lazy(() => import('./pages/AnalysisPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const ComparePage = lazy(() => import('./pages/ComparePage'))

/**
 * Global loading placeholder component, displayed while page components are loading.
 */
function LoadingFallback() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        fontFamily: 'var(--font-family)',
        color: 'var(--color-text-secondary)',
      }}
    >
      Loading...
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
      <div
        style={{
          minHeight: '100vh',
          fontFamily: 'var(--font-family)',
          color: 'var(--color-text)',
          backgroundColor: 'var(--color-surface)',
        }}
      >
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analysis/:sessionId" element={<AnalysisPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/compare" element={<ComparePage />} />
          </Routes>
        </Suspense>
      </div>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App

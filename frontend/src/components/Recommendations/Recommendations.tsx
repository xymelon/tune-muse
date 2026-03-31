/**
 * Recommendations component: Displays a list of personalized song direction recommendation cards.
 * Each card includes: Genre/Style, Tempo Range, Vocal Difficulty, Mood Alignment,
 * Explanations, confidence labels and Reference songs.
 * Responsive layout: 1 column for mobile, 2 columns for desktop.
 */

import type { Recommendation } from '../../types'

interface RecommendationsProps {
  /** Recommended result list (3-8 items) */
  recommendations: Recommendation[]
}

/**
 * Returns the corresponding label text and color based on confidence.
 */
function getConfidenceBadge(confidence: Recommendation['confidence']): {
  text: string
  color: string
  bg: string
} {
  switch (confidence) {
    case 'high':
      return { text: 'High Match', color: '#065F46', bg: '#D1FAE5' }
    case 'medium':
      return { text: 'Good Match', color: '#92400E', bg: '#FEF3C7' }
    case 'exploratory':
      return { text: 'Worth Exploring', color: '#1E40AF', bg: '#DBEAFE' }
  }
}

/**
 * Vocal difficulty star rating component.
 *
 * @param level - difficulty level 1-5
 */
function DifficultyStars({ level }: { level: number }) {
  return (
    <span
      aria-label={`Vocal difficulty: ${level} out of 5`}
      style={{ letterSpacing: 2 }}
    >
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          style={{
            color: i < level ? 'var(--color-warning)' : 'var(--color-border)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          ★
        </span>
      ))}
    </span>
  )
}

/**
 * Single recommendation card component.
 */
function RecommendationCard({ rec }: { rec: Recommendation }) {
  const badge = getConfidenceBadge(rec.confidence)

  return (
    <div
      style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-5)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
      }}
    >
      {/* Header row: genre + confidence badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3
            style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 'var(--font-weight-semibold)',
              margin: 0,
            }}
          >
            {rec.genre}
          </h3>
          {rec.sub_style && (
            <span
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
              }}
            >
              {rec.sub_style}
            </span>
          )}
        </div>
        <span
          style={{
            fontSize: 'var(--font-size-xs)',
            fontWeight: 'var(--font-weight-medium)',
            color: badge.color,
            backgroundColor: badge.bg,
            padding: '2px 8px',
            borderRadius: 'var(--radius-full)',
            whiteSpace: 'nowrap',
          }}
        >
          {badge.text}
        </span>
      </div>

      {/* Metadata row: BPM + difficulty */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--space-4)',
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
        }}
      >
        <span>
          {rec.tempo_range.low}–{rec.tempo_range.high} BPM
        </span>
        <DifficultyStars level={rec.vocal_difficulty} />
      </div>

      {/* Mood alignment */}
      <div
        style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          fontStyle: 'italic',
        }}
      >
        {rec.mood_alignment}
      </div>

      {/* Match explanation */}
      <p
        style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text)',
          lineHeight: 1.6,
          margin: 0,
        }}
      >
        {rec.match_explanation}
      </p>

      {/* Reference songs */}
      {rec.reference_songs && rec.reference_songs.length > 0 && (
        <details
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
          }}
        >
          <summary
            style={{
              cursor: 'pointer',
              fontWeight: 'var(--font-weight-medium)',
              marginBottom: 'var(--space-1)',
            }}
          >
            Reference songs ({rec.reference_songs.length})
          </summary>
          <ul style={{ margin: 0, paddingLeft: 'var(--space-4)' }}>
            {rec.reference_songs.map((song, i) => (
              <li key={i}>{song}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

export default function Recommendations({ recommendations }: RecommendationsProps) {
  if (recommendations.length === 0) {
    return (
      <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center' }}>
        No recommendations available.
      </p>
    )
  }

  return (
    <div>
      <h2
        style={{
          fontSize: 'var(--font-size-xl)',
          fontWeight: 'var(--font-weight-bold)',
          marginBottom: 'var(--space-2)',
        }}
      >
        Song Directions For You
      </h2>
      <p
        style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          marginBottom: 'var(--space-5)',
        }}
      >
        {recommendations.length} recommendations based on your vocal profile
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        {recommendations.map((rec) => (
          <RecommendationCard key={rec.rank} rec={rec} />
        ))}
      </div>
    </div>
  )
}

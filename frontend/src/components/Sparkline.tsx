interface SparklineProps {
  values: number[]
  label: string
  className?: string
}

const WIDTH = 100
const HEIGHT = 28
const PADDING = 2

/**
 * Micro-graphique d'évolution en SVG pur (aucune dépendance). Affiche une
 * ligne normalisée entre la valeur minimale et maximale de la série. Renvoie
 * ``null`` s'il n'y a pas au moins deux points (pas d'évolution à montrer).
 */
export function Sparkline({ values, label, className }: SparklineProps) {
  if (values.length < 2) {
    return null
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const points = values
    .map((value, index) => {
      const x = PADDING + (index * (WIDTH - 2 * PADDING)) / (values.length - 1)
      const y = HEIGHT - PADDING - ((value - min) / span) * (HEIGHT - 2 * PADDING)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')

  return (
    <svg
      role="img"
      aria-label={label}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="none"
      className={className}
      data-testid="sparkline"
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

import type { Trend } from '../dynamics'

type Props = { points: (number | undefined)[]; trend: Trend; breaks?: number[] }

const W = 84, H = 36, PAD = 5

/** A tiny line of weekly values; the last point is larger, a dashed tick marks a new month. */
export function Spark({ points, trend, breaks = [] }: Props) {
  const known = points.map((v, i) => ({ v, i })).filter((p): p is { v: number; i: number } => p.v != null)
  if (!known.length) return null
  const min = Math.min(...known.map((p) => p.v))
  const max = Math.max(...known.map((p) => p.v))
  const span = max - min || 1
  const step = points.length > 1 ? (W - 2 * PAD) / (points.length - 1) : 0
  const x = (i: number) => PAD + i * step
  const y = (v: number) => H - PAD - ((v - min) / span) * (H - 2 * PAD)
  const last = known[known.length - 1].i
  return (
    <svg className="spark" width={W} height={H} viewBox={`0 0 ${W} ${H}`} aria-hidden="true">
      {breaks.map((b) => (
        <line key={b} className="month-break" x1={x(b) - step / 2} x2={x(b) - step / 2} y1={2} y2={H - 2}>
          <title>Новый месяц</title>
        </line>
      ))}
      <polyline className={`spark-line ${trend}`} points={known.map((p) => `${x(p.i)},${y(p.v)}`).join(' ')} />
      {known.map((p) => (
        <circle key={p.i} className={`spark-dot ${trend}`} cx={x(p.i)} cy={y(p.v)} r={p.i === last ? 3.5 : 2} />
      ))}
    </svg>
  )
}

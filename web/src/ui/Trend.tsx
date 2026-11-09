import type { Payload } from '../data'
import { zone } from '../eval'
import { fmt, fmtDay, weekdaysOf, weekNo } from '../format'
import { METRIC } from '../metrics'

type Props = { payload: Payload; entity: string; metric: string; peerKeys: string[]; onClose: () => void }

const W = 760, H = 220, PAD = { l: 44, r: 16, t: 16, b: 34 }

/** One employee's metric over the 4 weeks, with the group average and the norm. */
export function Trend({ payload, entity, metric, peerKeys, onClose }: Props) {
  const m = METRIC[metric]
  const daily = m.granularity === 'day'
  const byPeriod = payload.values[metric] ?? {}
  const group = payload.entities[entity]?.group
  const groupKey = group ? `g:${group}` : entity
  const points: { x: number; day: string; week: string; v?: number; avg?: number; zone: string }[] = []
  payload.weeks.forEach((week) => {
    for (const day of [...new Set([...weekdaysOf(week), ...(payload.days[week] ?? [])])].sort()) {
      const period = daily ? day : week
      const v = byPeriod[period]?.[entity]
      const avg = byPeriod[period]?.[groupKey]
      const peers = peerKeys.map((k) => byPeriod[period]?.[k]).filter((x): x is number => x != null)
      const absolute = daily ? byPeriod[`${week}~${day}`]?.[entity] : v
      points.push({ x: points.length, day, week, v, avg, zone: zone({ value: v, absolute, peers, norm: payload.norms[metric], duck: payload.duckThreshold }).zone })
    }
  })
  const target = payload.norms[metric]?.target
  const vals = points.flatMap((p) => [p.v, p.avg]).filter((x): x is number => x != null)
  const max = Math.max(...vals, target ?? 0) * 1.1 || 1
  const n = Math.max(points.length - 1, 1)
  const X = (i: number) => PAD.l + (i / n) * (W - PAD.l - PAD.r)
  const Y = (v: number) => H - PAD.b - (v / max) * (H - PAD.t - PAD.b)
  const path = (key: 'v' | 'avg') => points.filter((p) => p[key] != null)
    .map((p, i) => `${i ? 'L' : 'M'}${X(p.x).toFixed(1)},${Y(p[key]!).toFixed(1)}`).join(' ')
  const weekStarts = payload.weeks.map((w) => ({ w, i: points.findIndex((p) => p.week === w) })).filter((s) => s.i >= 0)
  const name = payload.entities[entity]?.label ?? entity
  const gridVals = [0, max / 2, max].map((v) => Math.round(v * 100) / 100)

  return (
    <section className="panel trend" aria-label={`Динамика: ${name}, ${m.label}`}>
      <div className="trend-head">
        <div>
          <h2>{name}</h2>
          <p className="muted">{m.label} за 4 недели{daily ? '' : ' (значение недели)'} · пунктир — {target != null ? `цель ${fmt(metric, target)}` : 'среднее группы'}</p>
        </div>
        <button type="button" className="close" onClick={onClose}>Закрыть</button>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`График: ${m.label}`}>
        {gridVals.map((g) => (
          <g key={g}>
            <line className="grid" x1={PAD.l} x2={W - PAD.r} y1={Y(g)} y2={Y(g)} />
            <text className="axis" x={PAD.l - 8} y={Y(g) + 4} textAnchor="end">{fmt(metric, g)}</text>
          </g>
        ))}
        {weekStarts.map(({ w, i }) => (
          <text key={w} className="axis" x={X(i)} y={H - 10}>{`${weekNo(w)} нед.`}</text>
        ))}
        {target != null && <line className="norm" x1={PAD.l} x2={W - PAD.r} y1={Y(target)} y2={Y(target)} />}
        {groupKey !== entity && <path className="peer" d={path('avg')} />}
        <path className="line" d={path('v')} />
        {points.filter((p) => p.v != null).map((p) => (
          <circle key={p.day} className={`dot z-${p.zone}`} cx={X(p.x)} cy={Y(p.v!)} r={4.5}>
            <title>{`${fmtDay(p.day)}: ${fmt(metric, p.v)}`}</title>
          </circle>
        ))}
      </svg>
    </section>
  )
}

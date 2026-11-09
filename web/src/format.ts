import { METRIC } from './metrics'

export function fmt(metric: string, v: number | undefined): string {
  if (v == null || Number.isNaN(v)) return '—'
  const unit = METRIC[metric]?.unit ?? (metric.startsWith('runrate') ? 'pct' : 'num')
  if (unit === 'pct') return `${Math.round(v * 100)}%`
  if (unit === 'score') return `${Math.round(v)}`
  return v.toFixed(1).replace('.', ',')
}

export function fmtDay(iso: string, opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('ru-RU', opts).replace('.', '')
}

export function weekNo(week: string): string {
  return String(Number(week.split('.')[1]))
}

/** Monday..Friday of an ISO week `YYYY.WW` as `YYYY-MM-DD`. */
export function weekdaysOf(week: string): string[] {
  const [y, w] = week.split('.').map(Number)
  const jan4 = new Date(Date.UTC(y, 0, 4))
  const monday = new Date(jan4)
  monday.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() + 6) % 7) + (w - 1) * 7)
  return Array.from({ length: 5 }, (_, i) => {
    const d = new Date(monday)
    d.setUTCDate(monday.getUTCDate() + i)
    return d.toISOString().slice(0, 10)
  })
}

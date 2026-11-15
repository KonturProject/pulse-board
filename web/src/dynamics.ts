import type { Payload } from './data'
import { weekdaysOf } from './format'
import { METRIC } from './metrics'
import { rankGroups } from './rating'
import { cellZone, type Sel } from './view'

export type Trend = 'up' | 'down' | 'flat' | 'none'
export type Change = { points: (number | undefined)[]; now?: number; prev?: number; diff?: number; trend: Trend }

const FLAT = 0.03 // a change under 3% of the current value is noise

/** Noise (< 3% of the value) or a change that would show as zero on screen. */
function isFlat(metric: string, now: number, diff: number): boolean {
  const a = Math.abs(diff)
  const unit = METRIC[metric]?.unit ?? 'num'
  const shown = unit === 'pct' ? Math.round(a * 100) : unit === 'score' ? Math.round(a) : Math.round(a * 10)
  return a < FLAT * Math.abs(now) || shown === 0
}

/** The last day with data in the current (last) week of the window. */
export function lastDay(p: Payload): string | null {
  const days = p.days[p.weeks[p.weeks.length - 1]] ?? []
  return days.length ? days[days.length - 1] : null
}

/**
 * Weekly points over the window and the change of the last week. Daily metrics compare the current
 * week to date with the previous week up to the same weekday; weekly metrics compare week with week.
 */
export function change(p: Payload, metric: string, entity: string): Change {
  const byPeriod = p.values[metric] ?? {}
  const points = p.weeks.map((w) => byPeriod[w]?.[entity])
  const lastW = p.weeks[p.weeks.length - 1]
  const prevW = p.weeks[p.weeks.length - 2]
  const now = byPeriod[lastW]?.[entity]
  let prev: number | undefined
  // this metric's own last day (another report may be a day ahead), else the window's last day
  const d = (p.days[lastW] ?? []).filter((x) => byPeriod[`${lastW}~${x}`]).pop() ?? lastDay(p)
  if (prevW && (METRIC[metric]?.granularity ?? 'day') === 'day' && d) {
    const i = (new Date(`${d}T00:00:00`).getDay() + 6) % 7
    const same = weekdaysOf(prevW)[Math.min(i, 4)]
    // the latest day of last week up to the same weekday that this metric has (holidays skip back)
    const k = (p.days[prevW] ?? []).filter((x) => x <= same && byPeriod[`${prevW}~${x}`]).pop()
    prev = k ? byPeriod[`${prevW}~${k}`]?.[entity] : undefined
  } else if (prevW) {
    prev = byPeriod[prevW]?.[entity]
  }
  if (now == null || prev == null) return { points, now, prev, trend: 'none' }
  const diff = now - prev
  const trend: Trend = isFlat(metric, now, diff) ? 'flat' : diff > 0 ? 'up' : 'down'
  return { points, now, prev, diff, trend }
}

export type Summary = {
  place?: number; dPlace?: number; good: number; dGood: number; bad: number; dBad: number
  /** False when there was nothing to compare with last week (short history) — deltas are then not shown. */
  hasPrev: boolean
}

function weeksSel(p: Payload): [Sel, Sel | null] {
  const n = p.weeks.length
  return [{ week: p.weeks[n - 1], day: null }, n > 1 ? { week: p.weeks[n - 2], day: null } : null]
}

/** Place in the leaders' rating and counts of strong / failing metrics, with their change since last week. */
export function groupSummary(p: Payload, group: string): Summary {
  const [cur, prev] = weeksSel(p)
  const now = rankGroups(p, cur)
  const i = now.findIndex((r) => r.group === group)
  const row = now[i]
  const before = prev ? rankGroups(p, prev) : null
  const j = before ? before.findIndex((r) => r.group === group) : -1
  const was = j >= 0 && before![j].cells.some((c) => c.value != null) ? before![j] : null
  return {
    place: i + 1,
    dPlace: was ? j - i : undefined,
    good: row.good, dGood: was ? row.good - was.good : 0,
    bad: row.bad, dBad: was ? row.bad - was.bad : 0,
    hasPrev: Boolean(was),
  }
}

/** Strong / failing metrics of a manager this week and the change since last week. */
export function employeeSummary(p: Payload, emp: string, peers: string[], metrics: string[]): Summary {
  const [cur, prev] = weeksSel(p)
  const count = (sel: Sel) => {
    let good = 0, bad = 0
    for (const m of metrics) {
      const z = cellZone(p, m, emp, sel, peers).zone
      if (z === 'good') good += 1
      if (z === 'bad') bad += 1
    }
    return { good, bad }
  }
  const now = count(cur)
  const had = prev ? metrics.some((m) => p.values[m]?.[prev.week]?.[emp] != null) : false
  const was = had && prev ? count(prev) : null
  return {
    good: now.good, dGood: was ? now.good - was.good : 0, bad: now.bad, dBad: was ? now.bad - was.bad : 0,
    hasPrev: Boolean(was),
  }
}

/** Indices of weeks whose data month (their last data day, else Friday) differs from the previous week's —
 * where the month-to-date run-rate restarts. */
export function monthBreaks(weeks: string[], days: Record<string, string[]>): number[] {
  const month = (w: string) => (days[w]?.[days[w].length - 1] ?? weekdaysOf(w)[4]).slice(0, 7)
  return weeks.flatMap((w, i) => (i > 0 && month(w) !== month(weeks[i - 1]) ? [i] : []))
}

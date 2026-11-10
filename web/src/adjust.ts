import type { Payload } from './data'
import { weekdaysOf } from './format'
import type { Sel } from './view'

const CUMULATIVE = new Set(['runrate_money', 'runrate_pcs']) // month-to-date: the week shows its last day

type Parts = Record<string, [number, number]>

function ratio(parts: Parts | undefined, keep: (k: string) => boolean): [number, number] {
  let n = 0, d = 0
  for (const [k, [a, b]] of Object.entries(parts ?? {})) {
    if (keep(k)) { n += a; d += b }
  }
  return [n, d]
}

/**
 * The payload as if `hidden` employees of `group` were not there: the group's own values are rebuilt
 * from the remaining people's (num, den) parts. Other groups and the direction stay as published.
 */
export function withoutEmployees(p: Payload, group: string, hidden: Set<string>): Payload {
  if (!hidden.size || !p.parts) return p
  const g = `g:${group}`
  const prefix = `e:${group}:`
  const keep = (k: string) => k.startsWith(prefix) && !hidden.has(k)
  const values: Payload['values'] = { ...p.values }
  for (const [metric, byPeriod] of Object.entries(p.parts)) {
    const mv = { ...(values[metric] ?? {}) }
    const set = (period: string, [n, d]: [number, number]) => {
      const cell = { ...(mv[period] ?? {}) }
      if (d) cell[g] = Math.round((n / d) * 1e4) / 1e4
      else delete cell[g]
      mv[period] = cell
    }
    for (const [period, parts] of Object.entries(byPeriod)) set(period, ratio(parts, keep))
    for (const week of p.weeks) {
      const days = weekdaysOf(week).filter((d) => byPeriod[d])
      let n = 0, d = 0
      for (const day of days) {
        const [a, b] = ratio(byPeriod[day], keep)
        if (CUMULATIVE.has(metric)) { n = a; d = b } else { n += a; d += b }
        set(`${week}~${day}`, [n, d])
      }
      if (days.length) set(week, [n, d])
    }
    values[metric] = mv
  }
  return { ...p, values }
}

/** Members of `group` with no plan in the daily funnel on the selected day (or any day of the week). */
export function noPlan(p: Payload, group: string, sel: Sel): string[] {
  if (!p.staff) return []
  const days = sel.day ? [sel.day] : weekdaysOf(sel.week)
  const present = new Set(days.flatMap((d) => p.staff?.[d] ?? []))
  return Object.entries(p.entities)
    .filter(([k, e]) => k.startsWith('e:') && e.group === group && !present.has(k))
    .sort((a, b) => a[1].label.localeCompare(b[1].label, 'ru'))
    .map(([k]) => k)
}

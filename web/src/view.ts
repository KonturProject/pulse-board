import type { Payload } from './data'
import { zone, type Zone } from './eval'
import { METRIC, SOURCE_OF } from './metrics'

/** Selected period: a week, and a day of it (null = the whole week). */
export type Sel = { week: string; day: string | null }

export const GROUP_KEYS = ['g:СР1', 'g:СР2', 'g:СР3', 'g:СР5', 'g:СР6', 'g:СР9']

export function cellValue(p: Payload, metric: string, entity: string, sel: Sel) {
  const byPeriod = p.values[metric] ?? {}
  const daily = (METRIC[metric]?.granularity ?? 'day') === 'day'
  if (sel.day && daily) {
    return {
      value: byPeriod[sel.day]?.[entity],
      absolute: byPeriod[`${sel.week}~${sel.day}`]?.[entity],
      weekOnly: false,
    }
  }
  const v = byPeriod[sel.week]?.[entity]
  return { value: v, absolute: v, weekOnly: Boolean(sel.day) && !daily }
}

export function cellZone(p: Payload, metric: string, entity: string, sel: Sel, peerKeys: string[]): { zone: Zone; best: boolean } {
  const { value, absolute } = cellValue(p, metric, entity, sel)
  const peers = peerKeys.includes(entity)
    ? peerKeys.map((k) => cellValue(p, metric, k, sel).value).filter((v): v is number => v != null)
    : []
  return zone({ value, absolute, peers, norm: p.norms[metric], duck: p.duckThreshold })
}

export function isStale(p: Payload, metric: string): boolean {
  return p.sources.some((s) => s.id === SOURCE_OF[metric] && s.stale)
}

export function employeesOf(p: Payload, group: string): string[] {
  return Object.entries(p.entities)
    .filter(([k, e]) => k.startsWith('e:') && e.group === group)
    .sort((a, b) => a[1].label.localeCompare(b[1].label, 'ru'))
    .map(([k]) => k)
}

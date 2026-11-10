import type { Payload } from './data'
import type { Zone } from './eval'
import { cellValue, cellZone, GROUP_KEYS, type Sel } from './view'

/** Run-rate (the end result) and the quality metrics that drive it — no funnel volumes like «взятые». */
export const RATING_METRICS = [
  'runrate_money', 'quality_invoices', 'long_presentations', 'ns1_attempts', 'attempts_300',
  'oz_attempts', 'oz_speed_30', 'ak_pay_term_primary', 'ak_pay_term_ns',
]

export type RatingRow = {
  group: string
  good: number
  risk: number
  bad: number
  /** Average of value / reference (the target, or the groups' mean without one). */
  score: number
  cells: { id: string; value: number | undefined; zone: Zone }[]
}

function mean(xs: number[]) {
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : NaN
}

/** Groups ordered: most strong metrics, then fewest failures, then highest score. */
export function rankGroups(p: Payload, sel: Sel): RatingRow[] {
  const metrics = RATING_METRICS.filter((id) => p.values[id])
  const rows = GROUP_KEYS.map((key) => {
    const row: RatingRow = { group: key.slice(2), good: 0, risk: 0, bad: 0, score: 0, cells: [] }
    const ratios: number[] = []
    for (const id of metrics) {
      const { value } = cellValue(p, id, key, sel)
      const { zone } = cellZone(p, id, key, sel, GROUP_KEYS)
      row.cells.push({ id, value, zone })
      if (zone !== 'none') row[zone] += 1
      const peers = GROUP_KEYS.map((k) => cellValue(p, id, k, sel).value).filter((v): v is number => v != null)
      const ref = p.norms[id]?.target ?? mean(peers)
      if (value != null && ref) ratios.push(value / ref)
    }
    row.score = ratios.length ? mean(ratios) : 0
    return row
  })
  return rows.sort((a, b) => b.good - a.good || a.bad - b.bad || b.score - a.score)
}

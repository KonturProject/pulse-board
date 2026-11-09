import type { Payload } from '../data'
import { fmt } from '../format'
import { METRIC, METRICS } from '../metrics'
import { cellValue, cellZone, GROUP_KEYS, type Sel } from '../view'
import { Ring } from './Ring'

const BAR_METRICS = ['quality_invoices', 'long_presentations', 'oz_speed_30', 'oz_attempts', 'attempts_300']

function plural(n: number, one: string, few: string, many: string) {
  const m10 = n % 10, m100 = n % 100
  if (m10 === 1 && m100 !== 11) return one
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few
  return many
}

type Props = { payload: Payload; sel: Sel; group: string; large?: boolean }

export function GroupCard({ payload, sel, group, large }: Props) {
  const key = `g:${group}`
  const label = payload.entities[key]?.label ?? group
  const counts = { good: 0, risk: 0, bad: 0 }
  for (const m of METRICS) {
    const z = cellZone(payload, m.id, key, sel, GROUP_KEYS).zone
    if (z !== 'none') counts[z] += 1
  }
  const rr = cellValue(payload, 'runrate_money', key, sel).value
  const bars = BAR_METRICS.filter((id) => payload.values[id]).map((id) => {
    const { value } = cellValue(payload, id, key, sel)
    const peers = GROUP_KEYS.map((k) => cellValue(payload, id, k, sel).value).filter((v): v is number => v != null)
    const target = payload.norms[id]?.target
    const max = Math.max(...peers, target ?? 0, value ?? 0) * 1.12 || 1
    return { id, value, target, max, zone: cellZone(payload, id, key, sel, GROUP_KEYS).zone }
  })
  const Tag = large ? 'section' : 'a'
  return (
    <Tag className={`gcard${large ? ' gcard-lg' : ''}`} {...(large ? {} : { href: `#/g/${group}` })}>
      <header>
        <h3>{label}{!large && <span aria-hidden="true"> ›</span>}</h3>
        <p className="tags">
          {counts.good > 0 && <span className="tag z-good">{counts.good} {plural(counts.good, 'сильный', 'сильных', 'сильных')}</span>}
          {counts.risk > 0 && <span className="tag z-risk">{counts.risk} в риске</span>}
          {counts.bad > 0 && <span className="tag z-bad">{counts.bad} {plural(counts.bad, 'провал', 'провала', 'провалов')}</span>}
        </p>
      </header>
      <div className="gcard-body">
        <Ring value={rr} size="sm" label="ран-рейт" tiers={payload.norms.runrate_money?.tiers} />
        <ul className="bars">
          {bars.map((b) => (
            <li key={b.id}>
              <span className="b-name">{METRIC[b.id].short}</span>
              <span className="b-track">
                {b.value != null && <i className={`b-fill z-${b.zone}`} style={{ width: `${(b.value / b.max) * 100}%` }} />}
                {b.target != null && <i className="b-norm" style={{ left: `${(b.target / b.max) * 100}%` }} title={`цель ${fmt(b.id, b.target)}`} />}
              </span>
              <b>{fmt(b.id, b.value)}</b>
            </li>
          ))}
        </ul>
      </div>
    </Tag>
  )
}

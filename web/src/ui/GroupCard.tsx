import { useState } from 'react'
import type { Payload } from '../data'
import type { Zone } from '../eval'
import { fmt } from '../format'
import { MAIN_METRICS, METRIC } from '../metrics'
import { cellValue, cellZone, GROUP_KEYS, type Sel } from '../view'
import { Ring } from './Ring'

const BAR_METRICS = ['quality_invoices', 'long_presentations', 'oz_speed_30', 'oz_attempts', 'attempts_300']

function plural(n: number, one: string, few: string, many: string) {
  const m10 = n % 10, m100 = n % 100
  if (m10 === 1 && m100 !== 11) return one
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few
  return many
}

const ZONE_TITLE = { good: 'Сильные показатели', risk: 'Показатели в зоне риска', bad: 'Провалы' }

type Props = { payload: Payload; sel: Sel; group: string; large?: boolean }

export function GroupCard({ payload, sel, group, large }: Props) {
  const key = `g:${group}`
  const label = payload.entities[key]?.label ?? group
  const [open, setOpen] = useState<Exclude<Zone, 'none'> | null>(null)
  const byZone: Record<Exclude<Zone, 'none'>, string[]> = { good: [], risk: [], bad: [] }
  for (const m of MAIN_METRICS) {
    const z = cellZone(payload, m.id, key, sel, GROUP_KEYS).zone
    if (z !== 'none') byZone[z].push(m.id)
  }
  const tag = (z: Exclude<Zone, 'none'>, text: string) =>
    byZone[z].length > 0 && (
      <button type="button" className={`tag z-${z}${open === z ? ' open' : ''}`} aria-expanded={open === z}
        onClick={() => setOpen(open === z ? null : z)}>{text}</button>
    )
  const rr = cellValue(payload, 'runrate_money', key, sel).value
  const bars = BAR_METRICS.filter((id) => payload.values[id]).map((id) => {
    const { value } = cellValue(payload, id, key, sel)
    const peers = GROUP_KEYS.map((k) => cellValue(payload, id, k, sel).value).filter((v): v is number => v != null)
    const target = payload.norms[id]?.target
    const max = Math.max(...peers, target ?? 0, value ?? 0) * 1.12 || 1
    return { id, value, target, max, zone: cellZone(payload, id, key, sel, GROUP_KEYS).zone }
  })
  const n = (z: Exclude<Zone, 'none'>) => byZone[z].length
  return (
    <section className={`gcard${large ? ' gcard-lg' : ''}`}>
      <header>
        <h3>{large ? label : <a href={`#/g/${group}`}>{label}<span aria-hidden="true"> ›</span></a>}</h3>
        <p className="tags">
          {tag('good', `${n('good')} ${plural(n('good'), 'сильный', 'сильных', 'сильных')}`)}
          {tag('risk', `${n('risk')} в риске`)}
          {tag('bad', `${n('bad')} ${plural(n('bad'), 'провал', 'провала', 'провалов')}`)}
        </p>
        {open && (
          <ul className={`zone-list z-${open}`} aria-label={ZONE_TITLE[open]}>
            {byZone[open].map((id) => {
              const target = payload.norms[id]?.target
              return (
                <li key={id}>
                  <span>{METRIC[id].label}</span>
                  <b>{fmt(id, cellValue(payload, id, key, sel).value)}</b>
                  <small>{target != null ? `цель ${fmt(id, target)}` : 'от среднего'}</small>
                </li>
              )
            })}
          </ul>
        )}
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
    </section>
  )
}

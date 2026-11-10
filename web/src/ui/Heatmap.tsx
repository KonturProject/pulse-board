import type { Payload } from '../data'
import { fmt } from '../format'
import { MAIN_METRICS, type MetricDef } from '../metrics'
import { cellValue, cellZone, isStale, type Sel } from '../view'

export type Row = { key: string; label: string; href?: string; kind: 'group' | 'branch' | 'dir' | 'emp' }

type Props = {
  payload: Payload
  sel: Sel
  rows: Row[]
  peerKeys: string[]
  caption: string
  metrics?: MetricDef[]
  onCell?: (entity: string, metric: string) => void
  active?: { entity: string; metric: string } | null
}

function normText(p: Payload, m: MetricDef): string {
  const n = p.norms[m.id]
  if (n?.target == null) return 'от среднего'
  return `цель ${fmt(m.id, n.target)}`
}

export function Heatmap({ payload, sel, rows, peerKeys, caption, metrics = MAIN_METRICS, onCell, active }: Props) {
  const shown = metrics.filter((m) => payload.values[m.id])
  return (
    <div className="heat-wrap">
      <table className="heat" aria-label={caption}>
        <thead>
          <tr>
            <th scope="col" className="heat-corner">{rows[0]?.kind === 'emp' ? 'Сотрудник' : 'Группа'}</th>
            {shown.map((m) => (
              <th scope="col" key={m.id} data-testid={`head-${m.id}`} title={m.label}>
                <span className="h-name">{m.short}{isStale(payload, m.id) && <span className="stale" title="Отчёт устарел"> ⚠</span>}</span>
                <span className="h-norm">{normText(payload, m)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} className={`row-${r.kind}`}>
              <th scope="row">{r.href ? <a href={r.href}>{r.label}<span aria-hidden="true"> ›</span></a> : r.label}</th>
              {shown.map((m) => {
                const { value, weekOnly } = cellValue(payload, m.id, r.key, sel)
                const z = cellZone(payload, m.id, r.key, sel, peerKeys)
                const isActive = active?.entity === r.key && active.metric === m.id
                const cls = `cell z-${z.zone}${z.best ? ' best' : ''}${isActive ? ' active' : ''}`
                const content = <>{fmt(m.id, value)}{weekOnly && value != null && <small> нед.</small>}</>
                return (
                  <td key={m.id} className={cls} data-testid={`cell-${r.key}-${m.id}`}>
                    {onCell && value != null
                      ? <button type="button" onClick={() => onCell(r.key, m.id)} aria-label={`${r.label}, ${m.label}: ${fmt(m.id, value)}`}>{content}</button>
                      : content}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Legend() {
  return (
    <ul className="legend" aria-label="Обозначения">
      <li><i className="sw z-good" />Норматив выполнен</li>
      <li><i className="sw z-risk" />Ниже норматива — зона риска</li>
      <li><i className="sw z-bad" />Гадкий утёнок: заметно хуже соседей</li>
      <li><i className="sw best" />Эталон — лучшая группа</li>
    </ul>
  )
}

import { useMemo } from 'react'
import { withoutEmployees } from '../adjust'
import type { Payload } from '../data'
import { change, employeeSummary, groupSummary, lastDay, monthBreaks, type Summary } from '../dynamics'
import { fmt, fmtDay, weekNo } from '../format'
import { loadHidden } from '../hidden'
import { MAIN_METRICS, METRIC, type MetricDef } from '../metrics'
import { Header } from '../ui/Header'
import { Spark } from '../ui/Spark'
import { employeesOf, GROUP_KEYS, type Sel } from '../view'

type Props = { payload: Payload; sel: Sel; onSel: (s: Sel) => void; group: string | null }

function signed(n: number) {
  return n > 0 ? `+${n}` : n < 0 ? `−${-n}` : '0'
}

function diffText(metric: string, diff: number | undefined, trend: string) {
  if (trend === 'none' || diff == null) return '—'
  if (trend === 'flat') return '='
  const arrow = diff > 0 ? '▲ +' : '▼ −'
  const a = Math.abs(diff)
  return METRIC[metric]?.unit === 'pct' ? `${arrow}${Math.round(a * 100)} п.п.` : `${arrow}${fmt(metric, a)}`
}

function SummaryCell({ s }: { s: Summary }) {
  const tone = (d: number, goodWhenUp: boolean) => (d === 0 ? 't-flat' : (d > 0) === goodWhenUp ? 't-up' : 't-down')
  return (
    <td className="dyn-sum">
      {s.place != null && (
        <span className="dyn-place">
          {s.place} место{' '}
          {s.hasPrev && s.dPlace != null && (
            <span className={`tag ${tone(s.dPlace, true)}`}>{s.dPlace > 0 ? `▲${s.dPlace}` : s.dPlace < 0 ? `▼${-s.dPlace}` : '='}</span>
          )}
        </span>
      )}
      {s.hasPrev ? (
        <>
          <span className={`tag ${tone(s.dGood, true)}`}>сильных {signed(s.dGood)}</span>
          <span className={`tag ${tone(s.dBad, false)}`}>провалов {signed(s.dBad)}</span>
        </>
      ) : <span className="tag t-flat">нет прошлой недели для сравнения</span>}
    </td>
  )
}

export function Dynamics({ payload, sel, onSel, group }: Props) {
  const shown = useMemo(
    () => GROUP_KEYS.reduce((p, k) => withoutEmployees(p, k.slice(2), loadHidden(k.slice(2))), payload),
    [payload],
  )
  const metrics: MetricDef[] = MAIN_METRICS.filter((m) => shown.values[m.id] && (!group || !m.groupOnly))
  const breaks = monthBreaks(shown.weeks, shown.days)
  const last = shown.weeks[shown.weeks.length - 1]
  const prev = shown.weeks[shown.weeks.length - 2]
  const day = lastDay(shown)
  const allPeople = GROUP_KEYS.flatMap((k) => employeesOf(shown, k.slice(2)))

  const rows = group
    ? (() => {
        const hidden = loadHidden(group)
        return employeesOf(shown, group).filter((k) => !hidden.has(k)).map((k) => ({
          key: k, label: shown.entities[k].label, href: null as string | null,
          summary: employeeSummary(shown, k, allPeople, metrics.map((m) => m.id)),
        }))
      })()
    : GROUP_KEYS.map((k) => ({
        key: k, label: shown.entities[k]?.label ?? k, href: `#/dynamics/${k.slice(2)}`,
        summary: groupSummary(shown, k.slice(2)),
      })).sort((a, b) => (a.summary.place ?? 99) - (b.summary.place ?? 99))

  const groupLabel = group ? shown.entities[`g:${group}`]?.label ?? group : null
  return (
    <>
      <Header payload={payload} sel={sel} onSel={onSel} title={groupLabel ? `Динамика · ${groupLabel}` : 'Динамика'} back />
      <main className="page">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>{group ? 'Динамика менеджеров' : 'Динамика групп'}</h2>
              <p className="muted dyn-note">
                Недели {weekNo(shown.weeks[0])} → {weekNo(last)}. Прирост — {weekNo(last)} неделя
                {day ? ` по ${fmtDay(day, { weekday: 'short', day: 'numeric' })}` : ''} против того же отрезка
                {prev ? ` ${weekNo(prev)} недели` : ''}. Пунктир на графике — начало нового месяца.
              </p>
            </div>
            {group && <a className="view-btn" href={`#/g/${group}`}>Экран группы ›</a>}
          </div>
          <div className="heat-wrap">
            <table className="heat dyn" aria-label={group ? 'Динамика менеджеров' : 'Динамика групп'}>
              <thead>
                <tr>
                  <th scope="col" className="heat-corner">{group ? 'Менеджер' : 'Группа'}</th>
                  <th scope="col">Итог недели</th>
                  {metrics.map((m) => (
                    <th scope="col" key={m.id} title={m.label}><span className="h-name">{m.short}</span></th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.key}>
                    <th scope="row">{r.href ? <a href={r.href}>{r.label}<span aria-hidden="true"> ›</span></a> : r.label}</th>
                    <SummaryCell s={r.summary} />
                    {metrics.map((m) => {
                      const c = change(shown, m.id, r.key)
                      return (
                        <td key={m.id} className={`dyn-cell dyn-${c.trend}`} data-testid={`dyn-${r.key}-${m.id}`}>
                          <Spark points={c.points} trend={c.trend} breaks={m.id.startsWith('runrate') ? breaks : []} />
                          <span className="dyn-diff">{diffText(m.id, c.diff, c.trend)}</span>
                          <span className="dyn-now">{c.now != null ? `сейчас ${fmt(m.id, c.now)}` : ''}</span>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!rows.length && <p className="muted">Нет менеджеров для показа — проверьте фильтр на экране группы.</p>}
        </section>
      </main>
    </>
  )
}

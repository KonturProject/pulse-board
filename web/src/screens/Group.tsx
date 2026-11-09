import { useState } from 'react'
import type { Payload } from '../data'
import { METRICS } from '../metrics'
import { GroupCard } from '../ui/GroupCard'
import { Header } from '../ui/Header'
import { Heatmap, Legend, type Row } from '../ui/Heatmap'
import { Trend } from '../ui/Trend'
import { employeesOf, GROUP_KEYS, type Sel } from '../view'

type Props = { payload: Payload; sel: Sel; onSel: (s: Sel) => void; group: string }

export function Group({ payload, sel, onSel, group }: Props) {
  const [active, setActive] = useState<{ entity: string; metric: string } | null>(null)
  const label = payload.entities[`g:${group}`]?.label ?? group
  const rows: Row[] = employeesOf(payload, group).map((k) => ({ key: k, label: payload.entities[k].label, kind: 'emp' }))
  const allEmployees = GROUP_KEYS.flatMap((g) => employeesOf(payload, g.slice(2)))
  const metrics = METRICS.filter((m) => !m.groupOnly)
  return (
    <>
      <Header payload={payload} sel={sel} onSel={onSel} title={label} back />
      <main className="page">
        <nav className="group-nav" aria-label="Группы">
          {GROUP_KEYS.map((k) => (
            <a key={k} href={`#/g/${k.slice(2)}`} aria-current={k === `g:${group}` ? 'page' : undefined}>
              {payload.entities[k]?.label ?? k}
            </a>
          ))}
        </nav>
        <GroupCard payload={payload} sel={sel} group={group} large />
        <section className="panel">
          <div className="panel-head">
            <h2>Сотрудники группы</h2>
            <Legend />
          </div>
          {rows.length ? (
            <Heatmap payload={payload} sel={sel} rows={rows} peerKeys={allEmployees} metrics={metrics}
              caption={`Сотрудники группы ${label}`} active={active}
              onCell={(entity, metric) => setActive({ entity, metric })} />
          ) : <p className="muted">По сотрудникам этой группы пока нет данных.</p>}
          <p className="muted note">Сотрудники сравниваются со всеми сотрудниками направления. Нажмите на ячейку — откроется динамика за 4 недели.</p>
        </section>
        {active && (
          <Trend payload={payload} entity={active.entity} metric={active.metric} peerKeys={allEmployees} onClose={() => setActive(null)} />
        )}
      </main>
    </>
  )
}

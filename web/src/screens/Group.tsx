import { useMemo, useState } from 'react'
import { noPlan, withoutEmployees } from '../adjust'
import type { Payload } from '../data'
import { MAIN_METRICS } from '../metrics'
import { GroupCard } from '../ui/GroupCard'
import { Header } from '../ui/Header'
import { Heatmap, Legend, type Row } from '../ui/Heatmap'
import { Trend } from '../ui/Trend'
import { employeesOf, GROUP_KEYS, type Sel } from '../view'

type Props = { payload: Payload; sel: Sel; onSel: (s: Sel) => void; group: string }

const storageKey = (group: string) => `npsr-hidden:${group}`

function loadHidden(group: string): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(storageKey(group)) ?? '[]') as string[])
  } catch {
    return new Set()
  }
}

function saveHidden(group: string, hidden: Set<string>) {
  try {
    localStorage.setItem(storageKey(group), JSON.stringify([...hidden]))
  } catch {
    /* private mode: the filter lives only in this tab */
  }
}

export function Group({ payload, sel, onSel, group }: Props) {
  const [active, setActive] = useState<{ entity: string; metric: string } | null>(null)
  const [hidden, setHidden] = useState<Set<string>>(() => loadHidden(group))
  const update = (next: Set<string>) => {
    setHidden(next)
    saveHidden(group, next)
  }
  const label = payload.entities[`g:${group}`]?.label ?? group
  const members = employeesOf(payload, group)
  const shown = useMemo(() => withoutEmployees(payload, group, hidden), [payload, group, hidden])
  const rows: Row[] = members.filter((k) => !hidden.has(k)).map((k) => ({ key: k, label: payload.entities[k].label, kind: 'emp' }))
  const allEmployees = GROUP_KEYS.flatMap((g) => employeesOf(payload, g.slice(2)))
  const metrics = MAIN_METRICS.filter((m) => !m.groupOnly)
  const absent = noPlan(payload, group, sel)
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
        <GroupCard payload={shown} sel={sel} group={group} large />
        <section className="panel">
          <div className="panel-head">
            <h2>Сотрудники группы</h2>
            <Legend />
          </div>

          <div className="people">
            <div className="people-actions">
              <button type="button" className="chip" disabled={!absent.length}
                onClick={() => update(new Set([...hidden, ...absent]))}>
                Скрыть тех, у кого нет плана в дневной воронке
              </button>
              <button type="button" className="chip" disabled={!hidden.size} onClick={() => update(new Set())}>
                Показать всех
              </button>
              <span className="muted">
                Показаны {members.length - hidden.size} из {members.length}
                {hidden.size > 0 && ' — цифры группы пересчитаны без скрытых'}
              </span>
            </div>
            <details>
              <summary>Выбрать сотрудников вручную</summary>
              <ul className="people-list">
                {members.map((k) => (
                  <li key={k}>
                    <label>
                      <input type="checkbox" checked={!hidden.has(k)} onChange={(e) => {
                        const next = new Set(hidden)
                        if (e.target.checked) next.delete(k)
                        else next.add(k)
                        update(next)
                      }} />
                      {payload.entities[k].label}
                    </label>
                    {absent.includes(k) && <small className="muted"> нет плана</small>}
                  </li>
                ))}
              </ul>
            </details>
          </div>

          {rows.length ? (
            <Heatmap payload={shown} sel={sel} rows={rows} peerKeys={allEmployees} metrics={metrics}
              caption={`Сотрудники группы ${label}`} active={active}
              onCell={(entity, metric) => setActive({ entity, metric })} />
          ) : <p className="muted">Нет сотрудников для показа — верните кого-нибудь в списке выше.</p>}
          <p className="muted note">Сотрудники сравниваются со всеми сотрудниками направления. Нажмите на ячейку — откроется динамика за 4 недели.</p>
        </section>
        {active && !hidden.has(active.entity) && (
          <Trend payload={shown} entity={active.entity} metric={active.metric} peerKeys={allEmployees} onClose={() => setActive(null)} />
        )}
      </main>
    </>
  )
}

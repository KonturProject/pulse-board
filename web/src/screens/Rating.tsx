import type { Payload } from '../data'
import { fmt } from '../format'
import { METRIC } from '../metrics'
import { rankGroups } from '../rating'
import { Header } from '../ui/Header'
import { Legend } from '../ui/Heatmap'
import { Ring } from '../ui/Ring'
import type { Sel } from '../view'

type Props = { payload: Payload; sel: Sel; onSel: (s: Sel) => void }

export function Rating({ payload, sel, onSel }: Props) {
  const rows = rankGroups(payload, sel)
  const tiers = payload.norms.runrate_money?.tiers
  return (
    <>
      <Header payload={payload} sel={sel} onSel={onSel} title="Рейтинг руководителей" back />
      <main className="page">
        <section className="panel rating">
          <div className="panel-head">
            <div>
              <h2>Качество работы групп</h2>
              <p className="muted">
                Место — по числу сильных показателей, при равенстве — по меньшему числу провалов. Учитываются
                ран-рейт и качественные показатели; объёмы воронки (взятые, завершённые) — нет.
              </p>
            </div>
            <Legend />
          </div>
          <ol className="ladder" aria-label="Рейтинг руководителей групп">
            {rows.map((r, i) => {
              const label = payload.entities[`g:${r.group}`]?.label ?? r.group
              const rr = r.cells.find((c) => c.id === 'runrate_money')
              return (
                <li key={r.group} className={`rung place-${i + 1}`}>
                  <span className="place">{i + 1}</span>
                  <Ring value={rr?.value} size="sm" label="ран-рейт" tiers={tiers} />
                  <div className="rung-name">
                    <a href={`#/g/${r.group}`}>{label}</a>
                    <span className="tags">
                      <span className="tag z-good">{r.good} сильн.</span>
                      <span className="tag z-risk">{r.risk} в риске</span>
                      <span className="tag z-bad">{r.bad} провал.</span>
                    </span>
                  </div>
                  <div className="rung-cells">
                    {r.cells.filter((c) => c.id !== 'runrate_money').map((c) => (
                      <span key={c.id} className={`cell z-${c.zone}`} title={METRIC[c.id]?.label}>
                        <small>{METRIC[c.id]?.short ?? c.id}</small>
                        <b>{fmt(c.id, c.value)}</b>
                      </span>
                    ))}
                  </div>
                </li>
              )
            })}
          </ol>
        </section>
      </main>
    </>
  )
}

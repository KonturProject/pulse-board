import { useState } from 'react'
import type { Payload } from '../data'
import { fmt } from '../format'
import { LEAD_METRICS, METRIC } from '../metrics'
import { GroupCard } from '../ui/GroupCard'
import { Header } from '../ui/Header'
import { Heatmap, Legend, type Row } from '../ui/Heatmap'
import { Ring } from '../ui/Ring'
import { cellValue, cellZone, GROUP_KEYS, type Sel } from '../view'

const KPIS = ['quality_invoices', 'oz_speed_30', 'attempts_300']

type Props = { payload: Payload; sel: Sel; onSel: (s: Sel) => void }

export function Main({ payload, sel, onSel }: Props) {
  const rows: Row[] = [
    ...GROUP_KEYS.map((k) => ({ key: k, label: payload.entities[k]?.label ?? k, href: `#/g/${k.slice(2)}`, kind: 'group' as const })),
    { key: 'dir', label: 'Направление', kind: 'dir' },
  ]
  const tiers = payload.norms.runrate_money?.tiers
  const [lead, setLead] = useState(false)
  return (
    <>
      <Header payload={payload} sel={sel} onSel={onSel} title="Пульс направления" />
      <main className="page">
        <section className="hero" aria-label="Главное">
          <div className="hero-run">
            <Ring value={cellValue(payload, 'runrate_money', 'dir', sel).value} size="lg" label="Ран-рейт направления, деньги" tiers={tiers} dark />
            <Ring value={cellValue(payload, 'runrate_pcs', 'dir', sel).value} size="sm" label="штуки" tiers={tiers} dark />
          </div>
          {KPIS.filter((id) => payload.values[id]).map((id) => {
            const { value, weekOnly } = cellValue(payload, id, 'dir', sel)
            const target = payload.norms[id]?.target
            const z = cellZone(payload, id, 'dir', sel, []).zone
            return (
              <div className={`kpi z-${z}`} key={id}>
                <span className="kpi-name">{METRIC[id].label}</span>
                <b>{fmt(id, value)}{weekOnly && <small> за неделю</small>}</b>
                {target != null && <span className="kpi-norm">цель {fmt(id, target)}</span>}
              </div>
            )
          })}
        </section>

        <nav className="views" aria-label="Разделы">
          <a className="view-btn" href="#/rating">Рейтинг руководителей</a>
          <button type="button" className={`view-btn${lead ? ' on' : ''}`} aria-expanded={lead} onClick={() => setLead(!lead)}>
            Данные для ДПП, координатора и РФ
          </button>
        </nav>

        {lead && (
          <section className="panel lead-panel">
            <div className="panel-head">
              <h2>Данные для ДПП, координатора и РФ</h2>
              <p className="muted">Показатели для руководства направлением — группам смотреть не обязательно.</p>
            </div>
            <Heatmap payload={payload} sel={sel} rows={rows} peerKeys={GROUP_KEYS} metrics={LEAD_METRICS} caption="Данные для руководства" />
          </section>
        )}

        <section className="panel">
          <div className="panel-head">
            <h2>Группы по показателям</h2>
            <Legend />
          </div>
          <Heatmap payload={payload} sel={sel} rows={rows} peerKeys={GROUP_KEYS} caption="Группы по показателям" />
        </section>

        <section aria-label="Карточки групп" className="cards">
          {GROUP_KEYS.map((k) => <GroupCard key={k} payload={payload} sel={sel} group={k.slice(2)} />)}
        </section>
      </main>
    </>
  )
}

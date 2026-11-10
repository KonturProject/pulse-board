import type { Payload } from '../src/data'

const G = ['СР1', 'СР2', 'СР3', 'СР5', 'СР6', 'СР9'] as const
const LABEL: Record<string, string> = { СР1: 'СР1 ГБ', СР2: 'СР2 Фин', СР3: 'СР3 ГБ', СР5: 'СР5 ГБ УД', СР6: 'СР6 Право', СР9: 'СР9 ГБА' }
const DAYS = ['2026-11-02', '2026-11-03', '2026-11-05', '2026-11-06']

function groupValues(base: number[], extra: Record<string, number> = {}) {
  const v: Record<string, number> = { ...extra }
  G.forEach((g, i) => { if (base[i] != null && !Number.isNaN(base[i])) v[`g:${g}`] = base[i] })
  return v
}

/** Small but complete payload: 6 groups, 2 employees in СР2, СР9 without attempts_300. */
export function fixture(): Payload {
  const q = groupValues([3.9, 3.1, 4.4, 2.6, 4.1, 3.5], { dir: 3.6, 'e:СР2:Иванова Анна': 2.0, 'e:СР2:Петров Иван': 4.5 })
  const rr = groupValues([1.8, 0.9, 1.52, 0.98, 2.18, 1.5], { dir: 1.395, 'e:СР2:Иванова Анна': 0.7, 'e:СР2:Петров Иван': 1.1 })
  const a300 = groupValues([3.5, 3.1, 3.8, 3.1, 3.06, NaN], { dir: 3.41 })
  const values: Payload['values'] = {
    quality_invoices: {}, runrate_money: {}, runrate_pcs: {}, attempts_300: { '2026.45': a300, '2026.44': a300 },
    oz_speed_30: {},
    ns1_attempts: { '2026.45': groupValues([3.8, 4.6, 4.4, 5.4, 3.9, 3.0], { dir: 4.4, 'e:СР2:Иванова Анна': 3.2, 'e:СР2:Петров Иван': 5.6 }) },
  }
  for (const d of DAYS) {
    values.quality_invoices[d] = q
    values.quality_invoices[`2026.45~${d}`] = q
    values.runrate_money[d] = rr
    values.runrate_pcs[d] = rr
    values.oz_speed_30[d] = groupValues([0.79, 0.91, 0.78, 0.89, 0.61, 0.87], { dir: 0.8 })
  }
  values.quality_invoices['2026.45'] = q
  values.runrate_money['2026.45'] = rr
  values.runrate_pcs['2026.45'] = rr
  values.oz_speed_30['2026.45'] = values.oz_speed_30['2026-11-06']
  const entities: Payload['entities'] = { dir: { label: 'Направление' } }
  for (const g of G) entities[`g:${g}`] = { label: LABEL[g] }
  entities['e:СР2:Иванова Анна'] = { label: 'Иванова Анна', group: 'СР2' }
  entities['e:СР2:Петров Иван'] = { label: 'Петров Иван', group: 'СР2' }
  return {
    schemaVersion: 1,
    generatedAt: '2026-11-09T07:40:00',
    dataDate: '2026-11-06',
    weeks: ['2026.42', '2026.43', '2026.44', '2026.45'],
    days: { '2026.42': [], '2026.43': [], '2026.44': [], '2026.45': DAYS },
    sources: [{ id: 'oper', dataDate: '2026-11-06', collectedAt: '2026-11-09T07:40:00', stale: false },
      { id: 'funnel', dataDate: '2026-11-05', collectedAt: '2026-11-09T07:40:00', stale: true }],
    norms: { quality_invoices: { target: 4 }, runrate_money: { target: 1, tiers: [1, 1.2, 1.4] }, attempts_300: { target: 3.8 }, oz_speed_30: { target: 0.95 } },
    duckThreshold: 0.15,
    entities,
    values,
  }
}

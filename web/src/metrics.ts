export type Unit = 'pct' | 'num' | 'score'

export type MetricDef = {
  id: string
  label: string
  short: string
  unit: Unit
  granularity: 'day' | 'week'
  /** No per-employee values exist for this metric (pivot or group-only data). */
  groupOnly?: boolean
}

/** Column order of the heatmaps. */
export const METRICS: MetricDef[] = [
  { id: 'runrate_money', label: 'Ран-рейт, деньги', short: 'Ран-рейт ₽', unit: 'pct', granularity: 'day' },
  { id: 'quality_invoices', label: 'Качественные счета на человека', short: 'Кач. счета', unit: 'num', granularity: 'day' },
  { id: 'long_presentations', label: 'Длинные презентации на человека', short: 'Длинные през.', unit: 'num', granularity: 'day' },
  { id: 'taken', label: 'Взятые, % плана', short: 'Взятые', unit: 'pct', granularity: 'day' },
  { id: 'ns1_attempts', label: 'Попытки в НС1', short: 'Попытки НС1', unit: 'num', granularity: 'week' },
  { id: 'attempts_300', label: 'Попытки в 300+', short: 'Попытки 300+', unit: 'num', granularity: 'week', groupOnly: true },
  { id: 'oz_attempts', label: 'Попытки в ОЗ', short: 'Попытки ОЗ', unit: 'num', granularity: 'day' },
  { id: 'oz_speed_30', label: 'ОЗ взяты за 30 минут', short: 'ОЗ ≤ 30 мин', unit: 'pct', granularity: 'day' },
  { id: 'ak_rg_feedback', label: 'АК: обратная связь руководителя', short: 'АК: ОС РГ', unit: 'score', granularity: 'week', groupOnly: true },
  { id: 'ak_robot_coverage', label: 'АК: охват оценкой робота', short: 'АК: охват', unit: 'pct', granularity: 'week', groupOnly: true },
  { id: 'ak_pay_term_primary', label: 'АК: срок оплаты, первичка', short: 'Срок опл. перв.', unit: 'pct', granularity: 'week' },
  { id: 'ak_pay_term_ns', label: 'АК: срок оплаты, НС', short: 'Срок опл. НС', unit: 'pct', granularity: 'week' },
  { id: 'orders_extra_seats', label: 'Счета на доп. места на человека', short: 'Доп. места', unit: 'num', granularity: 'week', groupOnly: true },
  { id: 'orders_schools', label: 'Счета на школы на человека', short: 'Школы', unit: 'num', granularity: 'week', groupOnly: true },
  { id: 'orders_periodicals', label: 'Счета на периодику на человека', short: 'Периодика', unit: 'num', granularity: 'week', groupOnly: true },
]

export const METRIC = Object.fromEntries(METRICS.map((m) => [m.id, m])) as Record<string, MetricDef>

/** Which report each metric comes from — to flag stale data. */
export const SOURCE_OF: Record<string, string> = {
  runrate_money: 'oper', runrate_pcs: 'oper', quality_invoices: 'funnel', long_presentations: 'funnel',
  taken: 'funnel', completed: 'funnel', ns1_attempts: 'gkg', attempts_300: 'attempts300', oz_attempts: 'oz_attempts',
  oz_speed_30: 'oz_speed', ak_rg_feedback: 'ak', ak_robot_coverage: 'ak', ak_pay_term_primary: 'ak',
  ak_pay_term_ns: 'ak', orders_extra_seats: 'orders', orders_schools: 'orders', orders_periodicals: 'orders',
}

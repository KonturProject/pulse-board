import type { Payload } from '../data'
import { fmtDay, weekNo } from '../format'
import type { Sel } from '../view'

type Props = { payload: Payload; sel: Sel; onSel: (s: Sel) => void; title: string; back?: boolean }

export function Header({ payload, sel, onSel, title, back }: Props) {
  const days = payload.days[sel.week] ?? []
  const updated = new Date(payload.generatedAt).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
  return (
    <header className="top">
      <div className="top-row">
        <div className="brand">
          {back ? <a className="back" href="#/" aria-label="Ко всем группам">‹</a> : <span className="logo" aria-hidden="true">П</span>}
          <div>
            <h1>{title}</h1>
            <p className="muted">
              {payload.dataDate ? `Данные по ${fmtDay(payload.dataDate, { day: 'numeric', month: 'long' })}` : 'Нет данных'} · обновлено {updated}
            </p>
          </div>
        </div>
        <nav className="chips" aria-label="Неделя">
          {payload.weeks.map((w) => (
            <button key={w} type="button" className={`chip${w === sel.week ? ' on' : ''}`} aria-pressed={w === sel.week}
              onClick={() => onSel({ week: w, day: null })}>
              {w === sel.week ? `${weekNo(w)} неделя` : weekNo(w)}
            </button>
          ))}
        </nav>
      </div>
      <nav className="chips days" aria-label="День">
        <button type="button" className={`chip${sel.day == null ? ' on' : ''}`} aria-pressed={sel.day == null}
          onClick={() => onSel({ ...sel, day: null })}>Вся неделя</button>
        {days.map((d) => (
          <button key={d} type="button" className={`chip${d === sel.day ? ' on' : ''}`} aria-pressed={d === sel.day}
            onClick={() => onSel({ ...sel, day: d })}>
            {fmtDay(d, { weekday: 'short', day: 'numeric' })}
          </button>
        ))}
      </nav>
    </header>
  )
}

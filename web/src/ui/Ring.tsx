import { runrateTier, TIER_LABEL } from '../eval'
import { fmt } from '../format'

type Props = { value: number | undefined; size: 'lg' | 'sm'; label: string; tiers?: number[]; dark?: boolean }

/** Run-rate ring: a full circle is 140% («отличный кайф»), ticks at 100 and 120. */
export function Ring({ value, size, label, tiers = [1, 1.2, 1.4], dark }: Props) {
  const d = size === 'lg' ? 150 : 84
  const stroke = size === 'lg' ? 14 : 9
  const r = (d - stroke) / 2
  const c = 2 * Math.PI * r
  const share = value == null ? 0 : Math.min(value / tiers[2], 1)
  const tier = value == null ? null : runrateTier(value, tiers)
  const tick = (t: number) => {
    const a = (t / tiers[2]) * 2 * Math.PI - Math.PI / 2
    return { x1: d / 2 + (r - stroke / 2 - 2) * Math.cos(a), y1: d / 2 + (r - stroke / 2 - 2) * Math.sin(a),
      x2: d / 2 + (r + stroke / 2 + 2) * Math.cos(a), y2: d / 2 + (r + stroke / 2 + 2) * Math.sin(a) }
  }
  return (
    <figure className={`ring ring-${size} ${dark ? 'ring-dark' : ''} tier-${tier ?? 'none'}`} aria-label={`${label}: ${fmt('runrate_money', value)}`}>
      <svg width={d} height={d} viewBox={`0 0 ${d} ${d}`} aria-hidden="true">
        <circle cx={d / 2} cy={d / 2} r={r} className="ring-track" strokeWidth={stroke} fill="none" />
        <circle cx={d / 2} cy={d / 2} r={r} className="ring-fill" strokeWidth={stroke} fill="none" strokeLinecap="round"
          strokeDasharray={`${c * share} ${c}`} transform={`rotate(-90 ${d / 2} ${d / 2})`} />
        {[tiers[0], tiers[1]].map((t) => <line key={t} {...tick(t)} className="ring-tick" />)}
      </svg>
      <div className="ring-center">
        <b>{fmt('runrate_money', value)}</b>
        {size === 'lg' && tier && <span>{TIER_LABEL[tier]}</span>}
      </div>
      <figcaption>{label}</figcaption>
    </figure>
  )
}

export type Zone = 'good' | 'risk' | 'bad' | 'none'
export type Norm = { floor?: number; target?: number; tiers?: number[] }

/**
 * Two layers (spec §5): an absolute norm marks a risk zone (checked on the week-to-date value), a value
 * far below the peers' mean is an ugly duckling — so a cold day where everybody dipped is not red.
 */
export function zone(args: {
  value: number | undefined
  absolute: number | undefined
  peers: number[]
  norm?: Norm
  duck: number
}): { zone: Zone; best: boolean } {
  const { value, peers, norm, duck } = args
  if (value == null) return { zone: 'none', best: false }
  const absolute = args.absolute ?? value
  const mean = peers.length ? peers.reduce((a, b) => a + b, 0) / peers.length : value
  const best = peers.length > 1 && value >= Math.max(...peers)
  if ((peers.length > 1 && value < mean * (1 - duck)) || (norm?.floor != null && absolute < norm.floor)) {
    return { zone: 'bad', best: false }
  }
  const belowNorm = norm?.target != null ? absolute < norm.target : value < mean
  return { zone: belowNorm ? 'risk' : 'good', best }
}

export type Tier = 'below' | 'ok' | 'super' | 'top'

export const TIER_LABEL: Record<Tier, string> = {
  below: 'ниже плана', ok: 'круто', super: 'супер', top: 'отличный кайф',
}

export function runrateTier(v: number, tiers: number[] = [1.0, 1.2, 1.4]): Tier {
  if (v >= tiers[2]) return 'top'
  if (v >= tiers[1]) return 'super'
  if (v >= tiers[0]) return 'ok'
  return 'below'
}

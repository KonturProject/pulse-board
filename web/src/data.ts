import { decryptJson, type Envelope } from './crypto'
import type { Norm } from './eval'

export type Entity = { label: string; branch?: string; group?: string }

export type Payload = {
  schemaVersion: 1
  generatedAt: string
  dataDate: string | null
  weeks: string[]
  days: Record<string, string[]>
  sources: { id: string; dataDate: string | null; collectedAt: string; stale: boolean }[]
  norms: Record<string, Norm>
  duckThreshold: number
  entities: Record<string, Entity>
  /** metric -> period (`YYYY-MM-DD`, `YYYY.WW`, `YYYY.WW~YYYY-MM-DD`) -> entity key -> value */
  values: Record<string, Record<string, Record<string, number>>>
  /** metric -> period -> employee key -> [num, den]: lets a group be recomputed without some people */
  parts?: Record<string, Record<string, Record<string, [number, number]>>>
  /** day -> employee keys with a plan in the daily funnel that day */
  staff?: Record<string, string[]>
}

const STORAGE_KEY = 'npsr-phrase'

/** Phrase from `#/?k=…` (then stored and removed from the address bar) or from storage. */
export function readPhrase(): string | null {
  const m = location.hash.match(/[?&]k=([^&]+)/)
  if (m) {
    const phrase = decodeURIComponent(m[1])
    savePhrase(phrase)
    const rest = location.hash.replace(/[?&]k=[^&]+/, '').replace(/\?$/, '')
    history.replaceState(null, '', `${location.pathname}${location.search}${rest || '#/'}`)
    return phrase
  }
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

export function savePhrase(phrase: string | null): void {
  try {
    if (phrase) localStorage.setItem(STORAGE_KEY, phrase)
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* private mode: the phrase lives only in this tab */
  }
}

export async function loadDashboard(phrase: string): Promise<Payload> {
  const vres = await fetch(`data/version.json?t=${Date.now()}`, { cache: 'no-store' })
  if (!vres.ok) throw new Error('Данные ещё не опубликованы')
  const { rev } = (await vres.json()) as { rev: string }
  const res = await fetch(`data/dashboard.enc.json?v=${rev}`)
  if (!res.ok) throw new Error('Не удалось загрузить данные')
  return (await decryptJson((await res.json()) as Envelope, phrase)) as Payload
}

import { GROUP_KEYS } from './view'

/** `#/g/<key>` → group key (СР1…) if it is one of the six groups; anything else → null. */
export function groupFromHash(hash: string): string | null {
  let path = hash.replace(/^#/, '').split('?')[0]
  try {
    path = decodeURIComponent(path)
  } catch {
    return null
  }
  const m = path.match(/^\/g\/(.+)$/)
  return m && GROUP_KEYS.includes(`g:${m[1]}`) ? m[1] : null
}

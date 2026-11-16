/** People hidden on a group screen — kept per viewer in the browser and shared by every screen. */

const storageKey = (group: string) => `npsr-hidden:${group}`

export function loadHidden(group: string): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(storageKey(group)) ?? '[]') as string[])
  } catch {
    return new Set()
  }
}

export function saveHidden(group: string, hidden: Set<string>): void {
  try {
    localStorage.setItem(storageKey(group), JSON.stringify([...hidden]))
  } catch {
    /* private mode: the filter lives only in this tab */
  }
}

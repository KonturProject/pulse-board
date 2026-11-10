import { useCallback, useEffect, useState } from 'react'
import { AccessScreen } from './access'
import { DecryptError } from './crypto'
import { loadDashboard, readPhrase, savePhrase, type Payload } from './data'
import { groupFromHash } from './route'
import { Group } from './screens/Group'
import { Main } from './screens/Main'
import { Rating } from './screens/Rating'
import type { Sel } from './view'

function defaultSel(p: Payload): Sel {
  const week = p.weeks[p.weeks.length - 1]
  const days = p.days[week] ?? []
  const day = p.dataDate && days.includes(p.dataDate) ? p.dataDate : days[days.length - 1] ?? null
  return { week, day }
}

export default function App() {
  const [payload, setPayload] = useState<Payload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(true)
  const [sel, setSel] = useState<Sel | null>(null)
  const [, setTick] = useState(0)

  const open = useCallback(async (phrase: string | null) => {
    if (!phrase) { setBusy(false); return }
    setBusy(true)
    try {
      const p = await loadDashboard(phrase)
      savePhrase(phrase)
      setPayload(p)
      setSel(defaultSel(p))
      setError(null)
    } catch (e) {
      if (e instanceof DecryptError) {
        savePhrase(null) // only a wrong code is forgotten; a network hiccup must not cost the RG their link
        setError('Код не подходит. Проверьте ссылку или попросите новую.')
      } else if (e instanceof TypeError) {
        setError('Нет связи с сайтом. Проверьте интернет и обновите страницу.')
      } else {
        setError(`${(e as Error).message}. Обновите страницу через минуту.`)
      }
    } finally {
      setBusy(false)
    }
  }, [])

  useEffect(() => { open(readPhrase()) }, [open])
  useEffect(() => {
    const onHash = () => {
      if (/[?&]k=/.test(location.hash)) open(readPhrase()) // a fresh link pasted into an open tab
      setTick((t) => t + 1)
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [open])

  if (!payload || !sel) {
    if (busy && !error) return <main className="access"><p className="muted">Загружаю данные…</p></main>
    return <AccessScreen error={error} busy={busy} onSubmit={open} />
  }
  if (location.hash.startsWith('#/rating')) return <Rating payload={payload} sel={sel} onSel={setSel} />
  const group = groupFromHash(location.hash)
  if (!group && location.hash.startsWith('#/g/')) history.replaceState(null, '', '#/') // unknown group → main
  return group
    ? <Group key={group} payload={payload} sel={sel} onSel={setSel} group={group} />
    : <Main payload={payload} sel={sel} onSel={setSel} />
}

import { useState } from 'react'

type Props = { error: string | null; onSubmit: (phrase: string) => void; busy: boolean }

export function AccessScreen({ error, onSubmit, busy }: Props) {
  const [value, setValue] = useState('')
  return (
    <main className="access">
      <form className="access-card" onSubmit={(e) => { e.preventDefault(); if (value.trim()) onSubmit(value.trim()) }}>
        <span className="logo" aria-hidden="true">П</span>
        <h1>Пульс направления</h1>
        <p className="muted">Откройте ссылку, которую прислал руководитель направления, или введите код доступа из неё.</p>
        <label htmlFor="code">Код доступа</label>
        <input id="code" autoComplete="off" spellCheck={false} value={value} onChange={(e) => setValue(e.target.value)}
          placeholder="например, arbuz-volk-luna-sad-42" aria-invalid={Boolean(error)} aria-describedby={error ? 'code-error' : undefined} />
        {error && <p className="access-error" id="code-error" role="alert">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>{busy ? 'Открываю…' : 'Открыть дашборд'}</button>
      </form>
    </main>
  )
}

import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { Dynamics } from '../src/screens/Dynamics'
import { Main } from '../src/screens/Main'
import { fixture } from './fixture'

const sel = { week: '2026.45', day: '2026-11-06' }
const names = (label: RegExp) =>
  within(screen.getByRole('table', { name: label })).getAllByRole('rowheader').map((t) => t.textContent)

describe('Dynamics screen', () => {
  afterEach(() => {
    cleanup()
    localStorage.clear()
  })

  it('lists the six groups with a dash where a metric is missing', () => {
    render(<Dynamics payload={fixture()} sel={sel} onSel={() => {}} group={null} />)
    expect(names(/Динамика групп/)).toHaveLength(6)
    const cell = screen.getByTestId('dyn-g:СР9-attempts_300')
    expect(cell.textContent).toContain('—')
    expect(cell.className).toContain('dyn-none')
  })

  it('drills a group down to its managers', () => {
    render(<Dynamics payload={fixture()} sel={sel} onSel={() => {}} group={null} />)
    const table = screen.getByRole('table', { name: /Динамика групп/ })
    expect(within(table).getByRole('link', { name: /СР2 Фин/ }).getAttribute('href')).toBe('#/dynamics/СР2')
  })

  it('shows managers of the group without the people hidden on the group screen', () => {
    const { unmount } = render(<Dynamics payload={fixture()} sel={sel} onSel={() => {}} group="СР2" />)
    expect(names(/Динамика менеджеров/)).toEqual(['Иванова Анна', 'Петров Иван'])
    unmount()
    localStorage.setItem('npsr-hidden:СР2', JSON.stringify(['e:СР2:Иванова Анна']))
    render(<Dynamics payload={fixture()} sel={sel} onSel={() => {}} group="СР2" />)
    expect(names(/Динамика менеджеров/)).toEqual(['Петров Иван'])
  })

  it('is reachable from the main screen', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    expect(screen.getByRole('link', { name: 'Динамика' }).getAttribute('href')).toBe('#/dynamics')
  })
})

describe('Dynamics with hidden people', () => {
  afterEach(() => {
    cleanup()
    localStorage.clear()
  })

  it('recomputes the group without people hidden on the group screen', () => {
    localStorage.setItem('npsr-hidden:СР2', JSON.stringify(['e:СР2:Иванова Анна']))
    render(<Dynamics payload={fixture()} sel={sel} onSel={() => {}} group={null} />)
    expect(screen.getByTestId('dyn-g:СР2-quality_invoices').textContent).toContain('сейчас 4,5')
  })
})

import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { groupFromHash } from '../src/route'
import { Group } from '../src/screens/Group'
import { fixture } from './fixture'

const sel = { week: '2026.45', day: '2026-11-06' }

describe('Group screen', () => {
  afterEach(cleanup)

  it('lists only the employees of the group', () => {
    render(<Group payload={fixture()} sel={sel} onSel={() => {}} group="СР2" />)
    const table = screen.getByRole('table', { name: /Сотрудники/ })
    const names = within(table).getAllByRole('rowheader').map((th) => th.textContent)
    expect(names).toEqual(['Иванова Анна', 'Петров Иван'])
  })

  it('opens the employee trend from a cell, with the 4 weeks on the axis', () => {
    render(<Group payload={fixture()} sel={sel} onSel={() => {}} group="СР2" />)
    fireEvent.click(screen.getByRole('button', { name: /Иванова Анна, Качественные счета/ }))
    const trend = screen.getByRole('region', { name: /Динамика/ })
    expect(trend.textContent).toContain('Иванова Анна')
    for (const w of ['42', '43', '44', '45']) expect(within(trend).getByText(`${w} нед.`)).toBeTruthy()
  })

  it('links to every group', () => {
    render(<Group payload={fixture()} sel={sel} onSel={() => {}} group="СР2" />)
    const nav = screen.getByRole('navigation', { name: 'Группы' })
    expect(within(nav).getByRole('link', { name: 'СР3 ГБ' }).getAttribute('href')).toBe('#/g/СР3')
    expect(within(nav).getByRole('link', { name: 'СР2 Фин' }).getAttribute('aria-current')).toBe('page')
  })
})

describe('groupFromHash', () => {
  it('accepts known groups, encoded or not, and rejects the rest', () => {
    expect(groupFromHash('#/g/СР1')).toBe('СР1')
    expect(groupFromHash('#/g/%D0%A1%D0%A05')).toBe('СР5')
    expect(groupFromHash('#/g/СР4')).toBeNull()
    expect(groupFromHash('#/')).toBeNull()
  })
})

import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { noPlan, withoutEmployees } from '../src/adjust'
import { Group } from '../src/screens/Group'
import { fixture } from './fixture'

const sel = { week: '2026.45', day: '2026-11-06' }

describe('withoutEmployees', () => {
  it('recomputes the group from the people left — day, week and week-to-date', () => {
    const p = withoutEmployees(fixture(), 'СР2', new Set(['e:СР2:Иванова Анна']))
    const q = p.values.quality_invoices
    expect(q['2026-11-06']['g:СР2']).toBe(4.5)
    expect(q['2026.45']['g:СР2']).toBe(4.5)
    expect(q['2026.45~2026-11-06']['g:СР2']).toBe(4.5)
    expect(q['2026-11-06']['g:СР1']).toBe(3.9) // other groups untouched
  })

  it('changes nothing when nobody is hidden', () => {
    const f = fixture()
    expect(withoutEmployees(f, 'СР2', new Set())).toBe(f)
  })
})

describe('noPlan', () => {
  it('finds the group members without a plan in the daily funnel', () => {
    expect(noPlan(fixture(), 'СР2', sel)).toEqual(['e:СР2:Иванова Анна'])
  })
})

describe('Group filter', () => {
  afterEach(() => {
    cleanup()
    localStorage.clear()
  })

  const names = () => within(screen.getByRole('table', { name: /Сотрудники/ })).getAllByRole('rowheader').map((t) => t.textContent)

  it('hides people without a plan with one button', () => {
    render(<Group payload={fixture()} sel={sel} onSel={() => {}} group="СР2" />)
    fireEvent.click(screen.getByRole('button', { name: 'Скрыть тех, у кого нет плана в дневной воронке' }))
    expect(names()).toEqual(['Петров Иван'])
  })

  it('hides a person by unticking them and brings everyone back', () => {
    render(<Group payload={fixture()} sel={sel} onSel={() => {}} group="СР2" />)
    fireEvent.click(screen.getByRole('checkbox', { name: 'Петров Иван' }))
    expect(names()).toEqual(['Иванова Анна'])
    fireEvent.click(screen.getByRole('button', { name: 'Показать всех' }))
    expect(names()).toEqual(['Иванова Анна', 'Петров Иван'])
  })
})

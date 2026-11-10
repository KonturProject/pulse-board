import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { GroupCard } from '../src/ui/GroupCard'
import { fixture } from './fixture'

const sel = { week: '2026.45', day: '2026-11-06' }

describe('GroupCard zone buttons', () => {
  afterEach(cleanup)

  it('lists the metrics of the clicked zone and hides them on a second click', () => {
    render(<GroupCard payload={fixture()} sel={sel} group="СР5" />)
    const bad = screen.getByRole('button', { name: /провал/ })
    fireEvent.click(bad)
    const list = screen.getByRole('list', { name: /Провалы/ })
    expect(within(list).getByText('Качественные счета на человека')).toBeTruthy()
    expect(within(list).queryByText('ОЗ взяты за 30 минут')).toBeNull() // 89% is above the groups' mean
    fireEvent.click(bad)
    expect(screen.queryByRole('list', { name: /Провалы/ })).toBeNull()
  })

  it('opens the strong metrics from the green button', () => {
    render(<GroupCard payload={fixture()} sel={sel} group="СР3" />)
    fireEvent.click(screen.getByRole('button', { name: /сильн/ }))
    expect(within(screen.getByRole('list', { name: /Сильные/ })).getByText('Качественные счета на человека')).toBeTruthy()
  })

  it('keeps the group link on the title', () => {
    render(<GroupCard payload={fixture()} sel={sel} group="СР5" />)
    expect(screen.getByRole('link', { name: /СР5 ГБ УД/ }).getAttribute('href')).toBe('#/g/СР5')
  })
})

import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { Main } from '../src/screens/Main'
import { fixture } from './fixture'

const sel = { week: '2026.45', day: '2026-11-06' }

describe('Main screen', () => {
  afterEach(() => {
    cleanup()
    history.replaceState(null, '', '/')
  })

  it('shows 6 groups and the direction in the heatmap', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    const rows = within(screen.getByRole('table', { name: 'Группы по показателям' })).getAllByRole('row')
    expect(rows).toHaveLength(1 + 7)
  })

  it('renders a missing value as a dash without a zone', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    const cell = screen.getByTestId('cell-g:СР9-attempts_300')
    expect(cell.textContent).toContain('—')
    expect(cell.className).not.toMatch(/z-(good|risk|bad)/)
  })

  it('colours an ugly duckling red and the best group as reference', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    expect(screen.getByTestId('cell-g:СР5-quality_invoices').className).toMatch(/z-bad/)
    expect(screen.getByTestId('cell-g:СР3-quality_invoices').className).toMatch(/best/)
  })

  it('opens a group from its row', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    const table = screen.getByRole('table', { name: 'Группы по показателям' })
    expect(within(table).getByRole('link', { name: /СР1 ГБ/ }).getAttribute('href')).toBe('#/g/СР1')
  })

  it('marks metrics from a stale report', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    expect(screen.getByTestId('head-quality_invoices').textContent).toContain('⚠')
  })

  it('keeps leadership-only and dropped metrics off the main heatmap', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    const table = screen.getByRole('table', { name: 'Группы по показателям' })
    expect(within(table).queryByTestId('head-ak_rg_feedback')).toBeNull()
    expect(screen.queryByTestId('head-ak_robot_coverage')).toBeNull()
  })

  it('shows leadership data behind its button', () => {
    render(<Main payload={fixture()} sel={sel} onSel={() => {}} />)
    expect(screen.queryByRole('table', { name: 'Данные для руководства' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Данные для ДПП, координатора и РФ' }))
    const t = screen.getByRole('table', { name: 'Данные для руководства' })
    expect(within(t).getByTestId('head-ak_rg_feedback')).toBeTruthy()
    expect(within(t).queryByTestId('head-ak_robot_coverage')).toBeNull()
  })
})

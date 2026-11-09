import { cleanup, render, screen, within } from '@testing-library/react'
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
})

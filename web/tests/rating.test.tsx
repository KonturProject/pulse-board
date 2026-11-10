import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { rankGroups, RATING_METRICS } from '../src/rating'
import { Rating } from '../src/screens/Rating'
import { fixture } from './fixture'

function payload() {
  const p = fixture()
  const g = (vals: number[]) => Object.fromEntries(['СР1', 'СР2', 'СР3', 'СР5', 'СР6', 'СР9'].map((k, i) => [`g:${k}`, vals[i]]))
  p.values = {
    quality_invoices: { '2026.45': g([4.5, 4.2, 2.0, 4.1, 4.4, 4.6]) },
    runrate_money: { '2026.45': g([1.5, 1.5, 1.6, 0.9, 1.2, 1.3]) },
    taken: { '2026.45': g([0.1, 0.1, 9, 9, 9, 9]) }, // funnel metric: must not count
  }
  p.norms = { quality_invoices: { target: 4 }, runrate_money: { target: 1, tiers: [1, 1.2, 1.4] } }
  return p
}
const week = { week: '2026.45', day: null }

describe('rankGroups', () => {
  it('ranks by strong metrics, then fewer failures, then closeness to the target', () => {
    expect(rankGroups(payload(), week).map((r) => r.group)).toEqual(['СР1', 'СР2', 'СР9', 'СР6', 'СР3', 'СР5'])
  })

  it('counts run-rate and quality metrics but never the funnel', () => {
    expect(RATING_METRICS).toContain('runrate_money')
    expect(RATING_METRICS).not.toContain('taken')
    const top = rankGroups(payload(), week)[0]
    expect(top.good).toBe(2)
    expect(top.cells.map((c) => c.id)).not.toContain('taken')
  })
})

describe('Rating screen', () => {
  afterEach(cleanup)

  it('shows the ladder with places and run-rate first', () => {
    render(<Rating payload={payload()} sel={week} onSel={() => {}} />)
    const rows = within(screen.getByRole('list', { name: 'Рейтинг руководителей групп' })).getAllByRole('listitem')
    expect(rows).toHaveLength(6)
    expect(rows[0].textContent).toMatch(/^1.*СР1 ГБ/)
    expect(rows[5].textContent).toMatch(/^6.*СР5 ГБ УД/)
    expect(within(rows[0]).getByRole('link', { name: /СР1 ГБ/ }).getAttribute('href')).toBe('#/g/СР1')
  })
})

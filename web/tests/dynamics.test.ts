import { describe, expect, it } from 'vitest'
import type { Payload } from '../src/data'
import { change, groupSummary, lastDay } from '../src/dynamics'
import { fixture } from './fixture'

const g = (o: Record<string, number>) => Object.fromEntries(Object.entries(o).map(([k, v]) => [`g:${k}`, v]))

/** Four weeks; the current one (45) runs Mon, Tue, Thu (Wed is a holiday). */
export function dynPayload(currentDays = ['2026-11-02', '2026-11-03', '2026-11-05']): Payload {
  const p = fixture()
  p.weeks = ['2026.42', '2026.43', '2026.44', '2026.45']
  p.days = {
    '2026.42': ['2026-10-12', '2026-10-13', '2026-10-14', '2026-10-15', '2026-10-16'],
    '2026.43': ['2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23'],
    '2026.44': ['2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30'],
    '2026.45': currentDays,
  }
  p.norms = { quality_invoices: { target: 4 } }
  p.values = {
    quality_invoices: {
      '2026.42': g({ СР1: 3.0 }),
      '2026.43': g({ СР1: 3.5 }),
      '2026.44': g({ СР1: 3.6, СР2: 4.5, СР3: 4.2, СР5: 3.6 }),
      '2026.45': g({ СР1: 4.0, СР2: 4.0, СР3: 3.0, СР5: 4.0 }),
      '2026.44~2026-10-26': g({ СР1: 2.8 }),
      '2026.44~2026-10-29': g({ СР1: 3.2, СР2: 3.95, СР3: 3.6 }),
    },
    ns1_attempts: { '2026.44': g({ СР1: 4.2 }), '2026.45': g({ СР1: 4.6 }) },
  }
  return p
}

describe('change', () => {
  it('gives the 4 weekly points and compares the current week with the same span of the last one', () => {
    expect(lastDay(dynPayload())).toBe('2026-11-05')
    expect(change(dynPayload(), 'quality_invoices', 'g:СР1')).toMatchObject({
      points: [3.0, 3.5, 3.6, 4.0], now: 4.0, prev: 3.2, trend: 'up',
    })
  })

  it('treats a change under 3% as flat and a fall as down', () => {
    expect(change(dynPayload(), 'quality_invoices', 'g:СР2').trend).toBe('flat')
    expect(change(dynPayload(), 'quality_invoices', 'g:СР3').trend).toBe('down')
  })

  it('compares weekly metrics week with week', () => {
    expect(change(dynPayload(), 'ns1_attempts', 'g:СР1')).toMatchObject({ prev: 4.2, now: 4.6, trend: 'up' })
  })

  it('handles a short history without a previous value', () => {
    expect(change(dynPayload(), 'quality_invoices', 'g:СР5')).toMatchObject({
      points: [undefined, undefined, 3.6, 4.0], prev: undefined, trend: 'none',
    })
  })

  it('compares Monday with Monday when only Monday is in', () => {
    expect(change(dynPayload(['2026-11-02']), 'quality_invoices', 'g:СР1').prev).toBe(2.8)
  })
})

describe('groupSummary', () => {
  it('shows the place and how it moved since last week', () => {
    expect(groupSummary(dynPayload(), 'СР1')).toMatchObject({ place: 1, dPlace: 2 })
  })
})

// --- final review fixes ---
import { monthBreaks as mb } from '../src/dynamics'

describe('review fixes', () => {
  it('uses the metric own last day when another report is a day ahead', () => {
    const p = dynPayload(['2026-11-02', '2026-11-03', '2026-11-05', '2026-11-06']) // union has Fri
    p.values.quality_invoices['2026.45~2026-11-05'] = { 'g:СР1': 4.0 } // this metric only through Thu
    expect(change(p, 'quality_invoices', 'g:СР1').prev).toBe(3.2) // Thu vs Thu, not vs Fri
  })

  it('falls back to the latest earlier day when last week had a holiday on that weekday', () => {
    const p = dynPayload()
    p.values.quality_invoices['2026.45~2026-11-05'] = { 'g:СР1': 4.0 }
    delete p.values.quality_invoices['2026.44~2026-10-29']
    p.values.quality_invoices['2026.44~2026-10-28'] = { 'g:СР1': 3.1 }
    expect(change(p, 'quality_invoices', 'g:СР1').prev).toBe(3.1)
  })

  it('shows no change, not a fall, when both weeks are zero', () => {
    const p = dynPayload()
    p.values.quality_invoices['2026.45']['g:СР6'] = 0
    p.values.quality_invoices['2026.45~2026-11-05'] = { ...p.values.quality_invoices['2026.45~2026-11-05'], 'g:СР6': 0 }
    p.values.quality_invoices['2026.44~2026-10-29']['g:СР6'] = 0
    expect(change(p, 'quality_invoices', 'g:СР6').trend).toBe('flat')
  })

  it('treats a change that rounds to zero on screen as flat', () => {
    const p = dynPayload()
    p.values.oz_speed_30 = { '2026.44': { 'g:СР1': 0.10 }, '2026.45': { 'g:СР1': 0.104 },
      '2026.44~2026-10-29': { 'g:СР1': 0.10 }, '2026.45~2026-11-05': { 'g:СР1': 0.104 } }
    expect(change(p, 'oz_speed_30', 'g:СР1').trend).toBe('flat')
  })

  it('gives no week-over-week change in the summary when the group had no data last week', () => {
    const p = dynPayload()
    p.values.ns1_attempts['2026.45']['g:СР6'] = 9
    p.values.quality_invoices['2026.45']['g:СР6'] = 5
    expect(groupSummary(p, 'СР6')).toMatchObject({ hasPrev: false, dPlace: undefined, dGood: 0, dBad: 0 })
  })

  it('puts the month marker where the data month changes, not by the calendar Friday', () => {
    expect(mb(['2026.13', '2026.14', '2026.15'], { '2026.13': ['2026-03-27'], '2026.14': ['2026-03-31'], '2026.15': ['2026-04-06'] })).toEqual([2])
  })
})

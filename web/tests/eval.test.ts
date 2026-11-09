import { describe, expect, it } from 'vitest'
import { runrateTier, zone } from '../src/eval'
import { fmt } from '../src/format'

const peers = [3.9, 3.1, 4.4, 2.6, 4.1, 3.5]

describe('zone', () => {
  it('marks a value far below the peers as an ugly duckling', () => {
    expect(zone({ value: 2.6, absolute: 2.6, peers, norm: { target: 4 }, duck: 0.15 })).toEqual({ zone: 'bad', best: false })
  })
  it('marks a value below the norm but close to peers as risk', () => {
    expect(zone({ value: 3.1, absolute: 3.1, peers, norm: { target: 4 }, duck: 0.15 })).toEqual({ zone: 'risk', best: false })
  })
  it('marks the best value as good and best', () => {
    expect(zone({ value: 4.4, absolute: 4.4, peers, norm: { target: 4 }, duck: 0.15 })).toEqual({ zone: 'good', best: true })
  })
  it('treats a value below the floor as bad', () => {
    expect(zone({ value: 1.3, absolute: 1.1, peers: [1.3, 1.4], norm: { floor: 1.2, target: 1.5 }, duck: 0.15 }).zone).toBe('bad')
  })
  it('gives none without a value', () => {
    expect(zone({ value: undefined, absolute: undefined, peers, duck: 0.15 }).zone).toBe('none')
  })
  it('does not punish everybody on a cold day', () => {
    expect(zone({ value: 2.0, absolute: 3.8, peers: [2.0, 2.1, 1.9, 2.0, 2.2, 2.0], norm: { target: 4 }, duck: 0.15 }).zone).toBe('risk')
  })
  it('without a norm compares with the peer mean', () => {
    expect(zone({ value: 0.9, absolute: 0.9, peers: [0.9, 1.1, 1.0], duck: 0.15 }).zone).toBe('risk')
    expect(zone({ value: 1.1, absolute: 1.1, peers: [0.9, 1.1, 1.0], duck: 0.15 })).toEqual({ zone: 'good', best: true })
  })
})

describe('runrateTier', () => {
  it('uses 100 / 120 / 140 steps', () => {
    expect(runrateTier(0.999)).toBe('below')
    expect(runrateTier(1.0)).toBe('ok')
    expect(runrateTier(1.2)).toBe('super')
    expect(runrateTier(1.4)).toBe('top')
  })
})

describe('fmt', () => {
  it('formats by metric unit', () => {
    expect(fmt('runrate_money', 1.3951)).toBe('140%')
    expect(fmt('quality_invoices', 3.4643)).toBe('3,5')
    expect(fmt('ak_rg_feedback', 65.67)).toBe('66')
    expect(fmt('quality_invoices', undefined)).toBe('—')
  })
})

describe('weekdaysOf', () => {
  it('gives Monday..Friday of an ISO week', async () => {
    const { weekdaysOf } = await import('../src/format')
    expect(weekdaysOf('2026.45')).toEqual(['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06'])
    expect(weekdaysOf('2026.01')[0]).toBe('2025-12-29')
  })
})

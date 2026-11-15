import { cleanup, render } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { monthBreaks } from '../src/dynamics'
import { Spark } from '../src/ui/Spark'

describe('monthBreaks', () => {
  it('marks the week whose Friday falls into a new month', () => {
    expect(monthBreaks(['2026.42', '2026.43', '2026.44', '2026.45'])).toEqual([3])
    expect(monthBreaks(['2026.41', '2026.42'])).toEqual([])
  })
})

describe('Spark', () => {
  afterEach(cleanup)

  it('draws a dot per known week and the month break', () => {
    const { container } = render(<Spark points={[1, 2, undefined, 3]} trend="up" breaks={[3]} />)
    expect(container.querySelectorAll('circle')).toHaveLength(3)
    expect(container.querySelectorAll('line.month-break')).toHaveLength(1)
    expect(container.querySelector('polyline')?.getAttribute('class')).toContain('up')
  })

  it('draws nothing but a dash when there are no points', () => {
    const { container } = render(<Spark points={[undefined, undefined]} trend="none" />)
    expect(container.querySelector('svg')).toBeNull()
  })
})

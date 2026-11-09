import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../src/App'

describe('App access', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it('keeps the stored code when the network fails', async () => {
    localStorage.setItem('npsr-phrase', 'good-phrase')
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch') }))
    render(<App />)
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByRole('alert').textContent).toMatch(/Нет связи/)
    expect(localStorage.getItem('npsr-phrase')).toBe('good-phrase')
  })
})

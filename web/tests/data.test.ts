import { afterEach, describe, expect, it, vi } from 'vitest'
import { DecryptError, encryptJson, newSalt } from '../src/crypto'
import { loadDashboard, readPhrase } from '../src/data'

describe('readPhrase', () => {
  afterEach(() => {
    localStorage.clear()
    history.replaceState(null, '', '/')
  })

  it('takes the phrase from the link, stores it and removes it from the address', () => {
    history.replaceState(null, '', '/#/?k=abc-def')
    expect(readPhrase()).toBe('abc-def')
    expect(location.hash).not.toContain('k=')
    expect(readPhrase()).toBe('abc-def') // now from storage
  })

  it('returns null without a phrase', () => {
    expect(readPhrase()).toBeNull()
  })
})

describe('loadDashboard', () => {
  afterEach(() => vi.unstubAllGlobals())

  async function stubFetch(phrase: string) {
    const env = await encryptJson({ schemaVersion: 1, weeks: ['2026.45'] }, phrase, { salt: newSalt() })
    vi.stubGlobal('fetch', vi.fn(async (url: string) => ({
      ok: true,
      json: async () => (url.includes('version.json') ? { rev: 'r1' } : env),
    })))
  }

  it('decrypts the payload with the right phrase', async () => {
    await stubFetch('good-phrase')
    const p = await loadDashboard('good-phrase')
    expect(p.weeks).toEqual(['2026.45'])
  })

  it('throws DecryptError with a wrong phrase', async () => {
    await stubFetch('good-phrase')
    await expect(loadDashboard('bad-phrase')).rejects.toBeInstanceOf(DecryptError)
  })
})

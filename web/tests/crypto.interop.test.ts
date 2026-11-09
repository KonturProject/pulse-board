// @vitest-environment node
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { decryptJson, encryptJson, newSalt, type Envelope } from '../src/crypto'

const fixture = (name: string) => fileURLToPath(new URL(`./fixtures/${name}`, import.meta.url))

describe('encryption interop with the Python admin', () => {
  it('decrypts an envelope produced by Python', async () => {
    const data = JSON.parse(readFileSync(fixture('envelope.json'), 'utf-8')) as {
      phrase: string
      env: Envelope
      plain: unknown
    }
    expect(await decryptJson(data.env, data.phrase)).toEqual(data.plain)
  })

  it('writes an envelope for Python to decrypt', async () => {
    const plain = { hello: 'из браузера', n: [3] }
    const phrase = 'sova-reka-dom-les-07'
    const env = await encryptJson(plain, phrase, { salt: newSalt() })
    mkdirSync(fixture('generated'), { recursive: true })
    writeFileSync(fixture('generated/envelope_ts.json'), JSON.stringify({ phrase, env, plain }))
    expect(await decryptJson(env, phrase)).toEqual(plain)
  })
})

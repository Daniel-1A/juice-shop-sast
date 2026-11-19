/*
 * Copyright (c) 2026 Carlos Daniel Martinez.
 * SPDX-License-Identifier: MIT
 */
const test = require('node:test')
const assert = require('node:assert/strict')
const { demoCalculator } = require('../../routes/demoCalculator.js')

function call (expression) {
  const response = {
    statusCode: 200,
    status (code) { this.statusCode = code; return this },
    json (body) { this.body = body; return this }
  }
  demoCalculator({ query: { expression } }, response)
  return response
}

test('suma dos números sin ejecutar código', () => {
  assert.deepEqual(call('1 + 2').body, { result: 3 })
})

test('resta números negativos y decimales', () => {
  assert.deepEqual(call('-2.5 - 3').body, { result: -5.5 })
})

for (const expression of ['Math.max(1,2)', '1; Math.max(1,2)', '1/0', 'Infinity', '', undefined, ['1+2'], '1'.repeat(101)]) {
  test(`rechaza una expresión fuera de la gramática: ${String(expression).slice(0, 30)}`, () => {
    assert.equal(call(expression).statusCode, 400)
  })
}

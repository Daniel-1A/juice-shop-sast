/* Muestra estática del laboratorio SAST; no se registra en el servidor. */
'use strict'

function demoCalculator (req, res) {
  const expression = req.query.expression
  if (typeof expression !== 'string' || expression.length > 100) {
    return res.status(400).json({ error: 'Expresión no válida' })
  }

  const match = /^(-?\d+(?:\.\d+)?)\s*([+-])\s*(-?\d+(?:\.\d+)?)$/.exec(expression.trim())
  if (!match) {
    return res.status(400).json({ error: 'Solo se permite sumar o restar dos números' })
  }

  const left = Number(match[1])
  const right = Number(match[3])
  const result = match[2] === '+' ? left + right : left - right
  if (!Number.isFinite(result)) {
    return res.status(400).json({ error: 'Resultado fuera de rango' })
  }
  return res.json({ result })
}

module.exports = { demoCalculator }

/* Muestra estática del laboratorio SAST; no se registra en el servidor. */
'use strict'

function demoCalculator (req, res) {
  // Vulnerabilidad intencional: entrada de la petición ejecutada como JavaScript.
  res.json({ result: eval(req.query.expression) }) // eslint-disable-line no-eval
}

module.exports = { demoCalculator }

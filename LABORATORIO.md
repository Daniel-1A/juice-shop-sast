# Laboratorio SAST con Bearer CLI

Aplicación: OWASP Juice Shop. Este repositorio académico conserva vulnerabilidades intencionales.
Fuente: https://github.com/juice-shop/juice-shop
Commit de origen: `399fba76194305a312693eee44f4df64bdf0c3ce`.
Se retiraron el historial Git y los workflows originales y se inició `main` desde cero.

## Análisis local (Ubuntu / WSL)

Bearer CLI 2.1.2. No se necesita instalar ni ejecutar Juice Shop para SAST.

```bash
cd /mnt/c/Users/danie/Downloads/Github/juice-shop-sast
export PATH="$HOME/.local/bin:$PATH"
mkdir -p reports
bearer version
bearer scan --help
bearer scan . --skip-path test,frontend/src/test,cypress,node_modules,reports --exit-code 0
bearer scan . --skip-path test,frontend/src/test,cypress,node_modules,reports --format html --output reports/bearer-local.html --exit-code 0
bearer scan . --skip-path test,frontend/src/test,cypress,node_modules,reports --format sarif --output reports/bearer-local.sarif --exit-code 0
bearer scan . --skip-path test,frontend/src/test,cypress,node_modules,reports --severity critical,high --format json --output reports/bearer-high-critical.json --exit-code 0
```

Los reportes se guardan localmente en `reports/`, carpeta ignorada por Git. El código no se ejecuta.
`--exit-code 0` permite publicar resultados aunque existan hallazgos; no significa que el código sea seguro.

## Pipeline

Archivo: `.github/workflows/sast-bearer.yml`. Todas sus líneas incluyen un comentario explicativo.
Se ejecuta en push a main, pull_request hacia main y workflow_dispatch.
Permisos: contents: read y security-events: write.
Analiza `.` con el mismo alcance y versión que el análisis local. No usa `diff: true`.
Genera SARIF y HTML. El primero se publica en Security > Code scanning; ambos se descargan
desde el artefacto `bearer-reports` de Actions. Las cargas usan `if: always()`.
Una carga fallida o un reporte ausente siguen produciendo un fallo visible del workflow.

## Demostración realizada

PR: https://github.com/Daniel-1A/juice-shop-sast/pull/1

La rama `demo-vulnerabilidad` conserva el commit vulnerable y el commit de corrección.
En `routes/demoCalculator.js`, el primer commit usa `eval(req.query.expression)` en la línea 6.
Bearer lo detectó localmente como `javascript_lang_eval_user_input`, critical, CWE-95.
El análisis completo del PR detectó 398 hallazgos: los 397 de main más esta vulnerabilidad.
La alerta se puede consultar en https://github.com/Daniel-1A/juice-shop-sast/security/code-scanning/398.

La corrección elimina `eval` y solo permite sumar o restar dos números, validando tipo,
longitud, gramática y resultado finito. El nuevo análisis local de la muestra no reporta hallazgos.
El handler es una muestra estática: no está registrado en el servidor ni crea un reto de Juice Shop.

```powershell
node --test test/sast/demo-calculator.test.cjs
```

Resultado de las pruebas: antes, 2 aprobadas y 8 fallidas; después, 10 aprobadas y 0 fallidas.
Los reportes de ambos escaneos y pruebas están en `reports/` y se entregan por separado.
La suite completa de Juice Shop y su lint se intentaron, pero no se ejecutaron por falta de
`eslint` y Angular CLI (`ng`): no se instalaron las dependencias de ejecución de la aplicación.
El flujo SAST no necesita esas dependencias.

La línea base local y la de CI coinciden en las 397 combinaciones de regla, archivo y línea.
El filtro `critical,high` produce 43 hallazgos. Se mantienen los ejemplos de `data/static/codefixes`.
El PR se deja abierto para conservar la demostración; no se integra ni se despliega la muestra vulnerable.

## Fuentes

- https://docs.bearer.com/guides/configure-scan/
- https://docs.bearer.com/guides/github-action/
- https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github

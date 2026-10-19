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

## Demostración

La rama `demo-vulnerabilidad` añadirá un handler de laboratorio en `routes/demoCalculator.js`.
El primer commit evaluará una expresión de la petición con `eval` para observar el hallazgo SAST.
La corrección sustituirá esa evaluación por operaciones numéricas de una gramática limitada.
El handler se usa como muestra estática: no se registra en el servidor ni crea un reto de Juice Shop.
La evidencia del PR debe conservar ambos commits y el estado de la alerta antes y después.

## Fuentes

- https://docs.bearer.com/guides/configure-scan/
- https://docs.bearer.com/guides/github-action/
- https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github

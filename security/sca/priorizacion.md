# Priorización de los avisos SCA corregidos

Datos de CVSS del reporte Grype inicial. EPSS consultado el 26 de noviembre de 2026, expresado como probabilidad a 30 días. KEV corresponde al catálogo CISA 2026.11.25. La alcanzabilidad se describe a partir de las rutas de dependencia y la revisión estática del fork.

| Aviso | CVSS | EPSS | KEV | Alcanzabilidad razonada | Decisión que se aplicó |
|---|---:|---:|---|---|---|
| CVE-2015-9235 | No informado | 8,367 % | Sin entrada | Verificación de tokens en rutas del backend | Prioridad alta por estar en autenticación y tener parche. R01. |
| CVE-2019-10744 | 9,1 (3.1) | 5,006 % | Sin entrada | Dependencia transitiva del sanitizador. Ruta vulnerable específica sin demostrar | Actualizar el sanitizador y verificar el inventario. R02. |
| CVE-2023-46233 | 9,1 (3.1) | 0,646 % | Sin entrada | Presente bajo pdfkit. Uso de la operación afectada sin demostrar | Aplicar versión corregida disponible y emitir VEX. R03. |
| CVE-2026-71851 | 9,0 (3.1) | 0,550 % | Sin entrada | Mismo componente en pdfkit. Ruta concreta sin demostrar | Corregir con la actualización de CryptoJS. R04. |
| CVE-2026-59873 | 9,2 (4.0) | 0,644 % | Sin entrada | Transitiva de sqlite3. Uso de la ruta afectada en HTTP sin demostrar | Aplicar override y validar el build. R05. |

Fuentes: [run inicial](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/43664666668), [FIRST EPSS](https://www.first.org/epss/data), [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) y [registro de remediación](../remediacion.md).

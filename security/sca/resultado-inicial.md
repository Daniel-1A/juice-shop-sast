# Resultado inicial de SCA

La [primera ejecución de DevSecOps](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/43664666668) generó un SBOM CycloneDX con **1 178 componentes**. El inventario incluye Express 4.22.3 del backend y Angular Core 22.2.6 del frontend. El artefacto `reporte-sca` conserva `sbom.cdx.json`, `grype.sarif` y `grype.json`.

Grype 0.118.0 registró nueve coincidencias críticas en el reporte completo. Seis tenían versión corregida registrada y activaron el umbral. El job de Docker quedó omitido por esa dependencia. El control de licencias se ejecutó y emitió avisos para 26 componentes sin licencia declarada.

| Paquete | Versiones detectadas | Coincidencias críticas con parche |
|---|---|---:|
| `jsonwebtoken` | 0.1.0 y 0.4.0 | 2 |
| `lodash` | 2.4.2 | 1 |
| `crypto-js` | 3.3.0 | 2 |
| `tar` | 6.2.1 | 1 |

Las coincidencias representan pares de aviso y versión detectada. Para decidir una corrección, se debe identificar la ruta de dependencia, verificar si se usa en tiempo de ejecución y ejecutar pruebas de regresión. El inventario de esta fase se genera a partir de npm antes de construir la imagen.

## Correcciones para integrar el avance

Se actualizaron jsonwebtoken a 8.5.1 y express-jwt a 6.1.2 con algoritmos explicitos. Se resolvieron crypto-js 4.2.0 bajo pdfkit, sanitize-html 1.27.5, compatible con lodash corregido y tar 7.5.19 bajo sqlite3 mediante actualizaciones y overrides npm. La verificacion del backend ejecuta 414 pruebas correctas y omite cinco. Los retos que esperaban tokens sin firma ahora comprueban su rechazo.

La verificacion posterior incluye 546 pruebas de API correctas y seis omitidas por la suite. Una prueba confirma que el mismo token valido deja de autorizar acceso al eliminar la cuenta. El middleware deniega explicitamente las rutas cerradas y usa RS256 para autenticar.

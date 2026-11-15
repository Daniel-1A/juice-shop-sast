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

# Registro de remediación y evidencia

Se verificó el historial ya integrado. La unidad de remediación SCA es el aviso distinto. Las dos versiones afectadas por el mismo aviso JWT se cuentan una vez. Los dos avisos de CryptoJS se corrigen con una actualización y conservan sus IDs independientes.

| ID | Hallazgo | Antes | Después en CI | PR |
|---|---|---|---|---|
| R01 | CVE-2015-9235 · JWT | `jsonwebtoken` 0.1.0 y 0.4.0 | `8.5.1` y algoritmo RS256 explícito en el middleware. Ausente en el reporte posterior. | [#2](https://github.com/Daniel-1A/juice-shop-sast/pull/2), `0830475`, `e859086` |
| R02 | CVE-2019-10744 · lodash | `lodash` 2.4.2 | Actualización de `sanitize-html`. El SBOM posterior resuelve `lodash` 4.18.1 y el aviso desaparece. | [#2](https://github.com/Daniel-1A/juice-shop-sast/pull/2), `3dacd8a` |
| R03 | CVE-2023-46233 · CryptoJS | `crypto-js` 3.3.0 | `4.2.0` bajo `pdfkit`. Desaparece el aviso. | [#2](https://github.com/Daniel-1A/juice-shop-sast/pull/2), `0830475` |
| R04 | CVE-2026-71851 · CryptoJS | `crypto-js` 3.3.0 | `4.2.0` bajo `pdfkit`. Desaparece este segundo aviso. | [#2](https://github.com/Daniel-1A/juice-shop-sast/pull/2), `0830475` |
| R05 | CVE-2026-59873 · tar | `tar` 6.2.1 | Override `7.5.19` bajo `sqlite3`. Desaparece el aviso. | [#2](https://github.com/Daniel-1A/juice-shop-sast/pull/2), `0830475` |
| R06 | CKV_DOCKER_7 · imagen base sin fijar | Checkov detectó el tag implícito de la base original. | El Dockerfile de despliegue fija los digests. Checkov dio 41 aprobaciones, cero fallos y cero omisiones. | [#18](https://github.com/Daniel-1A/juice-shop-sast/pull/18), `b6e74b9` |
| R07 | CKV_DOCKER_2 · ausencia de healthcheck | El Dockerfile original carecía del control. | Healthcheck HTTP en el Dockerfile endurecido. Checkov aprobó y el build verificó el arranque. | [#18](https://github.com/Daniel-1A/juice-shop-sast/pull/18), `b6e74b9` |

Evidencia Grype/SBOM: [antes, run 43664666668](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/43664666668), [CI aprobada del PR #2](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/44415276779) y [después, run 45846349943](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/45846349943). Los ZIP de SCA se compararon con los SHA-256 publicados. El primero contiene 1 178 componentes y el segundo 1 221. Las coincidencias críticas con corrección disponible pasaron de seis a cero. El reporte posterior conserva críticas sin parche en `decompress` y `marsdb`.

Evidencia de infraestructura: [comparación local documentada](iac/resultado-fase-5.md), [diff integrado del PR #18](https://github.com/Daniel-1A/juice-shop-sast/pull/18/files) y artefacto `reporte-iac-contenedor` del run posterior. El Dockerfile usado para estos controles es el de `infra/`.

El cierre aplica al aviso y a la versión comparada. Las pruebas de revocación de cuentas y rechazo de tokens inválidos complementan R01. Los hallazgos de [SAST](sast/hallazgos-iniciales.md) y [ZAP](dast/hallazgos.md) conservan el estado descrito en esos registros.

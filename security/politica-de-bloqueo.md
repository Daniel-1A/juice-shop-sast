# Política de bloqueo del pipeline

**Principio:** Gitleaks y el gate SAST se enfocan en cambios nuevos del PR. SCA evalúa el inventario completo resuelto en esa ejecución, incluida la deuda heredada. Los reportes se guardan en GitHub Actions y los SARIF se envían a Code Scanning. La integración con DefectDojo se incorpora en la entrega final.

Ningún gate usa `continue-on-error` ni `|| true`. Los pasos de reporte usan `if: always()` solo para publicar resultados *después* de que el gate falló.

## Umbrales por herramienta

| Etapa | Herramienta | BLOQUEA el PR | Solo AVISA | Justificación |
|---|---|---|---|---|
| Secretos | gitleaks 8.30.1 | Cualquier secreto en los commits nuevos del PR | — | Un secreto filtrado no se puede "des-publicar"; debe rotarse siempre |
| SAST | Semgrep 1.182.1 | Hallazgos **nuevos** (respecto a la rama base) de severidad `ERROR` | `WARNING` e `INFO`; hallazgos ya existentes en `main` | Severidad ERROR = inyección, ejecución de código, credenciales. Bloquear la deuda heredada haría fallar todos los PR |
| SCA - vulnerabilidades | Grype (anchore/scan-action v7.4.2) | CVE `CRITICAL` **con corrección disponible** que no esté en `.grype.yaml` | `HIGH` o menor; CVE sin parche | Cubre también las dependencias heredadas con parche disponible |
| SCA - licencias | `check-licenses.py` | SBOM vacío o con una licencia denegada por la política del curso (GPL, AGPL o SSPL, con soporte para alternativas SPDX simples) | Componentes sin licencia declarada | Un inventario vacío invalida el análisis y las licencias denegadas se revisan antes de integrar |
| IaC - Dockerfile | Checkov 3.4.7 | Cualquier check fallido o error de parsing en `infra/Dockerfile`; reporte sin recursos también falla | Ninguno; sin checks omitidos | Se analiza el despliegue del equipo; los directorios de retos no forman parte del gate |
| IaC - despliegue | `infra/check-compose.py` sobre Compose normalizado | Usuario distinto de 65532:65532, puertos fuera de localhost, privilegios/capabilities, namespaces del host, montajes/dispositivos, falta de límites o healthcheck; JSON inválido/vacío | Ninguno | Control explícito porque Checkov no tiene cobertura nativa de Compose |
| Contenedor | Trivy 0.76.2 | CVE CRITICAL con corrección disponible en la imagen del build; errores de escaneo también fallan | HIGH o menor; CVE sin corrección, conservadas en reporte completo | Misma imagen que supera el smoke test; sin excepciones de Trivy |
| DAST | ZAP baseline | *Fase 6* (reglas en `.zap/rules.tsv`) | *Fase 6* | — |

## Checks obligatorios en `main`
Configurar en *Settings → Rules → Rulesets* (o *Branches → Branch protection*) cuando el equipo haya comprobado la primera ejecución:

- Requerir pull request con **1 aprobación** de otro integrante.
- Requerir que pasen: `secretos (gitleaks)`, `sast (semgrep)`, `sca (syft + grype)`, `build (docker)` e `iac (checkov + trivy)` (añadir este último después de verificar su primera ejecución).
- Requerir rama actualizada antes de fusionar.
- Bloquear force-push y borrado de `main`.

## Proceso de excepciones
1. La excepción se registra en la tabla de abajo **y** en la configuración de la herramienta (`.grype.yaml`, `# nosemgrep: <regla>` con comentario, o `.gitleaksignore`).
2. Toda excepción tiene justificación, responsable y fecha de revisión (máximo la entrega final).
3. Si el componente resulta no afectado, documenten en `security/vex/` la evidencia técnica. Una vulnerabilidad intencional que sí afecta al laboratorio se registra como riesgo aceptado, con responsable y fecha de revisión.
4. La excepción la aprueba el otro integrante en la revisión del PR.

| ID | Herramienta | Hallazgo | Componente | Justificación | VEX | Responsable | Revisar |
|---|---|---|---|---|---|---|---|
| EXC-01 | Gitleaks | private-key, commit 0830475, linea 21 | lib/insecurity.ts | Llave ficticia de laboratorio ya publica en el commit base 779106b. El fingerprint limita la excepcion a esa copia historica. | Riesgo heredado del laboratorio | Daniel Martinez | 2026-12-02 |

EXC-02 cubre exclusivamente los cuatro fingerprints de tokens ficticios heredados en test/server/verify.unit.test.ts del commit 66a82fc. Son entradas negativas de pruebas de JWT. Responsable Daniel Martinez, revision 2026-12-02.

EXC-03 identifica los dos fingerprints de contrasenas de cuentas de semilla heredadas en test/api/feedback.test.ts del commit 3dacd8a. Responsable Daniel Martinez, revision 2026-12-02.

Las excepciones EXC-01 a EXC-03 incluyen tambien los fingerprints del commit f47c13d, que normaliza finales de linea sin cambiar los fixtures.

EXC-04 cubre exclusivamente la contrasena ficticia de test/api/basket.test.ts:66 en el commit d01ec61. La prueba actual genera una contrasena aleatoria. Responsable Daniel Martinez, revision 2026-12-02.

## Alcance de infraestructura y evidencia

`infra/` contiene el despliegue del equipo. Los directorios heredados `infrastructure/` y `terraform/` contienen vulnerabilidades intencionales de retos y no se usan para desplegar ni forman parte del gate de fase 5. Checkov cubre el Dockerfile; Compose se valida con su CLI y la política local probada.

Los reportes completos de Checkov y Trivy se guardan en `reporte-iac-contenedor`, incluso si fallan los gates. La evidencia local, los resultados antes/después y la limitación del almacén Docker dañado están en `security/iac/resultado-fase-5.md`. Configurar un gate no demuestra una ejecución aprobada en CI.

> **Cierre de entrega (27/11/2026):** los pendientes de CI descritos al final son históricos y quedaron completados. Las fases 5 y 6 están fusionadas; la ejecución de `main` [45893213451](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/45893213451) aprobó y su evidencia permanente está en el [índice final](../../entrega-final/README.md). Los reportes locales mencionados en el texto se conservan en esa entrega; no se requiere acceder al equipo del autor.

# Fase 5: evidencia de IaC y contenedor

Fecha: 23 de noviembre de 2026. Base: `ab337bd`. Rama: `codex/fase-5-infra`.

## Checkov antes y después

Checkov 3.4.7 se ejecutó mediante su contenedor oficial, con el código montado solo para lectura, framework `dockerfile`, salida JSON y sin descargar políticas externas. El alcance anterior fue `/src/Dockerfile`; el posterior, `/src/infra/Dockerfile`.

| Resultado | Dockerfile original | Dockerfile del equipo |
|---|---:|---:|
| Código de salida | 1 | 0 |
| Comprobaciones aprobadas | 294 | 41 |
| Comprobaciones fallidas | 2 | 0 |
| Omitidas | 0 | 0 |
| Errores de parsing | 0 | 0 |
| Recursos analizados | 1 | 1 |

Los números de comprobaciones cambian con las instrucciones del Dockerfile. La evidencia relevante es que ambos hallazgos desaparecen sin omisiones:

| Check | Hallazgo inicial | Corrección verificada por Checkov |
|---|---|---|
| CKV_DOCKER_7 | La base final usa el tag implícito latest | Tag `nonroot` y digest inmutable; la base de construcción también tiene digest |
| CKV_DOCKER_2 | Falta HEALTHCHECK | Instrucción exec con `/nodejs/bin/node` y comprobación HTTP 200 |

Reportes en el repositorio: `security/iac/reports/checkov-before.json` y `security/iac/reports/checkov-after.json`. Estos cambios locales aún no constituyen evidencia de un PR de remediación.

## Build y comparación de Trivy

Se construyeron la imagen del commit original extraído con `git archive ab337bd` (`juice-shop:fase5-before`) y la nueva con `infra/Dockerfile` (`juice-shop:fase5`). Ambas construcciones terminaron con salida 0 usando un constructor temporal aislado. La configuración de entrega conserva la construcción estándar del runner; el constructor temporal se utilizó para evitar daños previos del motor local, explicados abajo.

Trivy 0.76.2 escaneó las imágenes con la misma base descargada durante esta sesión y `--scanners vuln`, sin filtrar severidades en el reporte completo:

| Severidad | Imagen original | Imagen nueva |
|---|---:|---:|
| CRITICAL | 3 | 3 |
| HIGH | 12 | 12 |
| MEDIUM | 57 | 57 |
| LOW | 19 | 19 |
| UNKNOWN | 3 | 3 |

El endurecimiento no corrige las dependencias de la aplicación. Los tres CRITICAL detectados no tienen corrección indicada por esta base:

| Hallazgo | Componente | Versión | Corrección disponible |
|---|---|---|---|
| CVE-2026-101894 | decompress | 4.2.1 | No indicada |
| CVE-2026-53486 | decompress | 4.2.1 | No indicada |
| GHSA-5mrr-rgp6-x4gr | marsdb | 0.6.11 | No indicada |

El gate `--severity CRITICAL --ignore-unfixed --exit-code 1` terminó con salida 0 en la imagen nueva. No se añadieron excepciones. Esto demuestra el umbral acordado, no ausencia de vulnerabilidades. La priorización y el tratamiento de la deuda siguen pendientes para las siguientes fases.

Reportes en `security/iac/reports/`: `trivy-image-before.json`, `trivy-image-after.json` y `trivy-gate-after.json`.

## Pruebas de rechazo de gates

- Un Dockerfile ausente produjo salida 2 en Checkov; el guard adicional del reporte también falló. Un error o reporte inválido no se transforma en aprobación.
- Una imagen inexistente produjo salida 1 en Trivy usando solo la fuente Docker, sin recurrir a registros externos.
- Una fixture sintética no ejecutable, separada del repositorio de entrega, contenía solo el manifiesto `lodash@4.17.11` bajo `node_modules`. Trivy detectó CVE-2019-10744, CRITICAL, con corrección en 4.17.12; el gate devolvió 1. Su reporte es `security/iac/reports/trivy-gate-fixture.json`. No es un hallazgo de Juice Shop ni se incluyó esa dependencia en la aplicación.
- La política de Compose pasó seis pruebas, incluyendo configuraciones inseguras, JSON inválido, configuración vacía, servicios adicionales y códigos de salida. La revisión independiente encontró vías alternativas de montaje; se reprodujeron con cuatro casos fallidos y se corrigieron para rechazar `use_api_socket`, `volumes_from`, `configs` y `secrets`.

## Compose y comprobación de ejecución

`docker compose config --format json` con Compose 2.39.4 y la política local aprobaron la configuración. Checkov no tiene un framework nativo para Compose. El sondeo de Trivy config solo identificó Dockerfile y no se cuenta como cobertura de Compose.

La prueba efectiva de arranque se realizó con `juice-shop:fase5-local`, una variante temporal con el sistema de archivos de la construcción endurecida copiado a una capa nueva. Esa variante evitó reutilizar snapshots dañados de Docker Desktop. No reemplaza el Dockerfile de entrega ni se utiliza en el workflow.

Resultado de esa prueba, usando el mismo `infra/compose.yaml` y `up --no-build --wait`:

- Estado `healthy`; HTTP de la página y búsqueda de productos exitosos (3 productos en la respuesta de prueba).
- UID y GID efectivos 65532.
- Puerto publicado únicamente en `127.0.0.1:3000`.
- Sin modo privilegiado, sin capabilities añadidas, `cap_drop: ALL` y `no-new-privileges:true`.
- Memoria 1 GiB, 256 procesos y 2 CPU, comprobados en la configuración efectiva del contenedor.
- Sin montajes del host ni volúmenes persistentes.
- El contenedor y la red de esta prueba se eliminaron al terminar.

Trivy también analizó la variante temporal: mismos conteos de severidad y gate con salida 0. Evidencia en `security/iac/reports/`: `container-inspect.json`, `runtime-user.json`, `compose-normalized.json`, `compose-policy.json` y `trivy-image-local-verification.json`.

## Incidente del entorno y límites de la evidencia

El primer build original terminó con EOF. Docker registró la parada de su integración WSL y Trivy reportó falta de espacio al actualizar los checks. El sistema confirmó 0 bytes libres en C:. Solo se eliminaron los ZIP temporales de herramientas de esta tarea; el usuario liberó espacio adicional y se reanudaron las pruebas.

El motor predeterminado conservó daños: `/bin/dash` de la base Node tenía 0 bytes y la consulta de caché encontró un snapshot ausente. Tras construir con un builder aislado, el motor local reutilizó también una capa dañada de distroless (`/nodejs/bin/node` de 0 bytes); por eso el arranque directo de `juice-shop:fase5` falló. Se verificó la ejecución con la variante temporal descrita arriba. No se borraron imágenes, volúmenes ni caché global de otros proyectos. El problema del almacén local no se declara reparado.

Las advertencias de arranque por Alchemy y el servicio LLM opcional se conservaron como limitaciones de retos fuera del alcance; no se configuraron credenciales ni servicios externos.

`actionlint` 1.7.12 validó el workflow sin errores. Los digests se consultaron en los registros oficiales. Los paquetes Trivy y actionlint se comprobaron contra sus archivos oficiales de SHA256.

## Pendientes para cerrar la fase en CI

1. Ejecutar el workflow en un runner limpio para verificar el arranque directo de la imagen de entrega y la preservación de artefactos al fallar un gate.
2. Añadir `iac (checkov + trivy)` a la protección de rama después de observar esa ejecución.
3. Conservar el antes/después en un PR para la evidencia de remediación.

No se afirma que GitHub Actions haya pasado. Los cambios permanecen locales; no se hizo push ni merge. Los comandos reproducibles están en `infra/README.md`.

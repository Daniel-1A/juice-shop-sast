# Infraestructura del laboratorio

Esta configuración ejecuta la instancia propia de Juice Shop únicamente en localhost. La aplicación conserva vulnerabilidades intencionales. `infrastructure/` y `terraform/` son material de retos del proyecto original; no son el despliegue del equipo.

## Ejecutar localmente

Requisitos: Docker Desktop con motor Linux activo, Docker Compose v2 y espacio suficiente para imágenes, dependencias y caché de construcción. Ejecutar desde la raíz del repositorio:

```bash
docker compose -f infra/compose.yaml config -q
docker compose -f infra/compose.yaml build
docker compose -f infra/compose.yaml up --no-build --wait --wait-timeout 240
curl --fail http://127.0.0.1:3000/
docker compose -f infra/compose.yaml exec -T juice-shop /nodejs/bin/node -e 'console.log(process.getuid())'
docker compose -f infra/compose.yaml down --remove-orphans
```

El UID esperado es 65532. Se puede usar una imagen ya construida definiendo `JUICE_SHOP_IMAGE=juice-shop:<SHA>` y ejecutando `up --no-build`. No se conserva información al eliminar el contenedor.

## Controles y limitaciones

- Bases fijadas por digest, runtime distroless, usuario/grupo `65532:65532` y healthcheck que invoca Node sin shell.
- Solo `127.0.0.1:3000`, eliminación de todas las capabilities, `no-new-privileges`, límite de 1 GiB, 256 procesos y 2 CPU.
- Sin montajes del host, socket Docker, volúmenes persistentes ni credenciales reales.
- La capa del contenedor continúa siendo escribible: Juice Shop genera la base SQLite, logs, traducciones, archivos y cargas. No se declara `read_only` sin haber validado todos esos flujos. Esto limita el endurecimiento alcanzado.
- Los digests fijan las imágenes base, pero las dependencias npm siguen los rangos existentes del proyecto; esto no equivale a una construcción reproducible byte por byte.
- `CYPRESS_INSTALL_BINARY=0` evita descargar el navegador de pruebas durante el build. Los scripts existentes compilan frontend y servidor; esta imagen no ejecuta la suite Cypress.

## Validación de Compose

Checkov analiza el Dockerfile; no tiene un framework nativo para este archivo Compose. Trivy 0.76.2 tampoco identificó Compose en la comprobación exploratoria. La cobertura de sus restricciones se realiza explícitamente con una política local sobre el JSON normalizado por Docker:

```bash
python3 -m unittest discover -s infra -p 'test_*.py'
docker compose -f infra/compose.yaml config --format json > compose.json
python3 infra/check-compose.py < compose.json
```

La política devuelve 0 si cumple, 1 por configuración insegura y 2 por JSON inválido. Revisa todos los servicios, rechaza configuraciones vacías y verifica usuario, puertos, capacidades, privilegios, montajes, límites y presencia de un healthcheck de Node. Es un control de las reglas del laboratorio, no un escáner general de Compose ni una verificación de que el código del healthcheck sea correcto.

También rechaza los mecanismos alternativos `use_api_socket`, `volumes_from`, `configs` y `secrets`, para que no introduzcan montajes que eludan la prohibición de `volumes`.

## Checkov y Trivy

Checkov 3.4.7, fijado también por digest:

```bash
mkdir -p reports
docker run --rm -v "$PWD:/src:ro" \
  bridgecrew/checkov:3.4.7@sha256:2df9b825a73bf4d09f0ab0d71b12844801454c3c35430162e7e2cf0e60e34e40 \
  --file /src/infra/Dockerfile --framework dockerfile --skip-download \
  --output json > reports/checkov.json
```

El código de salida se conserva: un hallazgo o error no se transforma en éxito. El alcance es `infra/Dockerfile`, sin exclusiones de checks.

Con Trivy 0.76.2 instalado desde la distribución oficial y su checksum verificado:

```bash
trivy image --scanners vuln --exit-code 0 --timeout 15m \
  --format json --output reports/trivy-image.json juice-shop:local
trivy image --scanners vuln --severity CRITICAL --ignore-unfixed \
  --exit-code 1 --timeout 15m --format json \
  --output reports/trivy-gate.json juice-shop:local
```

El primer reporte incluye todas las severidades y vulnerabilidades sin parche. El segundo bloquea CRITICAL con corrección disponible. El umbral no garantiza que el laboratorio sea seguro. Sin excepciones de Trivy en esta fase.

## CI

`build (docker)` valida Compose, construye `infra/Dockerfile`, arranca con las restricciones de Compose, espera salud y comprueba UID y HTTP. Guarda imagen y evidencia de despliegue. `iac (checkov + trivy)` descarga la misma imagen y conserva los reportes incluso si falla un gate. No reconstruye otra imagen para analizarla.

Después de una ejecución verificada, añadir `iac (checkov + trivy)` a los checks obligatorios de `main`. Los resultados locales y sus pendientes están en `security/iac/resultado-fase-5.md`.

Durante esta validación, Docker Desktop conservó capas dañadas después de quedarse sin espacio. La construcción se realizó en un builder aislado y el arranque se comprobó con una variante temporal que evitaba reutilizar esas capas. La imagen de entrega aún requiere comprobar su arranque directo en un runner limpio; el informe distingue esa limitación de las pruebas locales aprobadas. No se reparó ni se limpió globalmente el almacén de Docker del usuario.

## Fuentes oficiales

- [Checkov: Dockerfile](https://www.checkov.io/7.Scan%20Examples/Dockerfile.html)
- [Checkov: CLI](https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html)
- [Trivy: escaneo de imágenes](https://trivy.dev/docs/latest/references/configuration/cli/trivy_image/)
- [Docker Compose: servicios](https://docs.docker.com/reference/compose-file/services/)
- [Distroless](https://github.com/GoogleContainerTools/distroless)

# ZAP / DAST del laboratorio

La fase 6 usa la imagen de Juice Shop generada por build y aprobada por IaC. La aplicación y el escáner comparten una red Docker **interna**; el objetivo fijo es `http://juice-shop:3000`. No se escanean demos públicas ni sistemas externos. La API de ZAP no se publica.

Imagen del escáner: ZAP 2.17.0, fijada en `image.txt` por digest oficial. Los scripts `zap-baseline.py`, `zap-full-scan.py` y `zap-api-scan.py` proceden de esa imagen; los helpers de este directorio añaden cobertura verificable, recorrido AF y saneamiento.

## Ejecución en Actions

- En cada PR, push a main o ejecución manual: baseline y modo autenticado pasivo.
- Para añadir full y API activos: Actions → devsecops → Run workflow → marcar `extended_scans`. Se ejecutan sobre instancias nuevas del equipo, nunca sobre una URL suministrada por el usuario.
- `dast (zap)` depende de build e iac y tiene límite de 45 minutos. No necesita secretos nuevos de GitHub.
- Descargar el artefacto `reporte-dast`. Contiene `image.json` y subdirectorios `baseline/`, `authenticated/` y, si se habilitaron, `full/` y `api/`.
- Cada modo publica HTML, JSON, log saneado, `coverage.json` y `summary.json`. El artefacto apunta a una carpeta única por ejecución e intento; no mezcla éxitos antiguos con una ejecución fallida.
- La configuración del workflow no acredita ejecución en CI: conservar el enlace, SHA y artefacto del primer PR una vez ejecutado.

## Ejecutar localmente (Bash / WSL)

Desde la raíz, con Docker Linux, Compose v2 y Python 3.10 o superior:

```bash
python3 -m unittest discover -s .zap -p 'test_*.py'
docker compose -f infra/compose.yaml build
bash .zap/scan.sh juice-shop:local false
# Incluye full y API activos sobre datos efímeros propios:
bash .zap/scan.sh juice-shop:local true
```

El script indica la carpeta específica bajo `reports/dast/`. Cada modo recrea la aplicación, comprueba salud, red interna e identidad de imagen. El cleanup elimina únicamente sus contenedores y red, también al fallar. Los resultados generados están ignorados por Git.

El servicio conserva los límites y UID/GID de fase 5. La imagen ZAP trabaja como UID 1000. Un contenedor auxiliar sin red ajusta únicamente el propietario de la nueva carpeta de resultados públicos; ni Juice Shop ni el escáner se ejecutan en modo privilegiado. No se monta el socket Docker en ninguno de los dos.

## Gate y cobertura

`rules.tsv` clasifica como FAIL las reglas 10020 y 10021, que protegen X-Frame-Options y X-Content-Type-Options ya configurados en server.ts. Las demás reglas conservan WARN. Baseline y autenticado usan el mismo archivo y el mismo validador; los WARN no bloquean gracias a `-I`, pero permanecen en los reportes.

Un FAIL, error operativo, timeout, reporte inválido/ausente, falta de respuestas reales o fallo del recorrido autenticado produce salida no cero. No se usan `continue-on-error` ni `|| true` en gates. Las fixtures de prueba demuestran tanto el bloqueo por encabezados ausentes como el paso de un resultado solo con WARN.

`coverage.json` registra URLs del objetivo, una muestra de respuestas exitosas del historial ZAP, versión, fecha y límite activo efectivo. No basta con que el reporte no tenga alertas: ZAP puede crear URLs en su árbol aunque el destino no responda. El baseline comprueba accesibilidad y el validador exige respuestas reales.

El spider está acotado en duración, profundidad y enlaces. El límite activo de cinco minutos se aplica y se verifica mediante la API de ZAP; no se confía en claves CLI desconocidas que ZAP podría ignorar. Un full scan acotado es una muestra de pruebas activas, no cobertura exhaustiva ni un pentest completo.

## Autenticación demostrada

El hook crea una cuenta normal con correo y contraseña aleatorios; obtiene su JWT por el login normal. El plan Automation Framework manda peticiones a:

1. whoami con Cookie token, porque esa ruta concreta lee la cookie.
2. El carrito propio con Authorization: Bearer.
3. El carrito con un token inválido, esperando 401.
4. La búsqueda de productos, como ruta semilla de la API.

Después valida las respuestas **del historial de ZAP**: identidad y UserId correctos, carrito correcto y control negativo rechazado. HTTP 200 con un usuario vacío falla. El header Bearer se añade al spider/active scan solo para el objetivo propio. No se afirma que esto valide autenticación de navegador, localStorage, OAuth, 2FA ni control de acceso entre usuarios.

Contraseñas, JWT y el plan con headers viven solo en el filesystem temporal del contenedor del escáner. El wrapper publica una lista explícita de archivos, redacciona secretos exactos/escapados y JWT, y no publica sesiones ZAP ni el plan generado. Los tests comprueban el saneamiento y los casos negativos.

## Full y API

Los hallazgos activos son informativos para remediación de esta aplicación vulnerable. Los errores operativos, alcance/cobertura inválidos y autenticación fallida siguen bloqueando. No se ocultan todos los códigos de salida.

API usa `swagger.yml` local, reemplazando servers por el servicio interno. El contrato solo documenta B2B `/b2b/v2/orders`. El recorrido autenticado también siembra rutas de identidad, carrito y búsqueda; pueden aparecer alertas de esas rutas y de la raíz de la SPA. No presentar el resultado como cobertura de toda la API ni tratar HTML esperado de la raíz como fallo del contrato B2B.

## Fuentes oficiales

- https://www.zaproxy.org/docs/docker/baseline-scan/
- https://www.zaproxy.org/docs/docker/full-scan/
- https://www.zaproxy.org/docs/docker/api-scan/
- https://www.zaproxy.org/docs/automate/automation-framework/
- https://www.zaproxy.org/docs/desktop/addons/automation-framework/job-requestor/

Análisis y límites de la evidencia: `security/dast/hallazgos.md` y `security/dast/resultado-fase-6.md`.

# Diseño de fase 6: ZAP/DAST

Fecha: 26 de noviembre de 2026. Repositorio: `C:/Users/danie/source/repos/juice-shop-sast`. Base inspeccionada: `4437a9f`, merge del PR #18, rama main sin cambios locales. Estado: aprobado por el usuario en el chat; implementación en fase-6-dast.

## Objetivo

Completar la fase 6 de la rúbrica: ZAP baseline en cada PR, reglas de bloqueo explícitas, escaneo activo completo, escaneo de la API documentada, al menos una prueba autenticada y análisis de cinco hallazgos reales. Conservar reportes y trazabilidad a la imagen del build para el documento final.

## Enfoque y alternativas

Se conserva el orden acordado: primero baseline y su gate; después ampliar cobertura con API, escaneo completo y autenticación.

- Propuesta: baseline y comprobación autenticada pasiva en CI por PR; escaneos activos completo/API mediante ejecución manual del mismo workflow. Evita ejecutar pruebas activas largas en cada PR y permite obtener la evidencia de autenticación en CI.
- Alternativa descartada como propuesta: todos los escaneos activos en cada PR. Añade duración, carga y cambios en los datos del laboratorio a cada revisión sin ser necesario para el mínimo de la rúbrica.

La autenticación pasiva por PR es una decisión propuesta por el implementador; su validación se añade después de que funcione el baseline. No se presume aprobada por separado hasta la aprobación de este documento.

## Alcance y límites

Solo instancias efímeras propias en Docker local o GitHub Actions. No escanear demos públicas, OAuth, Web3, servidores LLM ni servicios externos. No cambiar código de retos ni corregir vulnerabilidades de negocio durante esta integración. No publicar, fusionar ni configurar protección de rama automáticamente.

ZAP pasivo no equivale a un pentest ni demuestra ausencia de SQLi, IDOR o XSS. La aplicación Angular limita el descubrimiento del spider tradicional; la cobertura adicional se obtiene mediante peticiones explícitas, autenticación e importación OpenAPI, sin afirmar cobertura completa de la SPA.

## Integración del baseline

1. Crear la rama `fase-6-dast` desde el main inspeccionado, conservando cualquier cambio posterior del usuario. No usar prefijo codex/.
2. Añadir el job `dast (zap)` al workflow existente, dependiente de `build` e `iac`. Descargar y cargar `imagen-juice-shop`; no reconstruir otra imagen. Registrar el SHA/digest y comprobar su correspondencia con el contenedor.
3. Levantar la aplicación con `infra/compose.yaml` y un override DAST que hace interna la red Docker de la prueba. Mantener UID, restricciones y el puerto en localhost. ZAP se une a esa red y solo tiene como objetivo `http://juice-shop:3000`; no se publica su API. No permitir salida a servicios externos desde esa red. Las herramientas deben descargarse antes de iniciar el escaneo; usar los add-ons ya incluidos en la imagen fijada.
4. Esperar el healthcheck, verificar HTTP y ejecutar `zap-baseline.py`, con duración y timeout finitos. Fijar la imagen oficial de ZAP por versión/digest verificables durante implementación. Montar la configuración solo para lectura y únicamente el directorio de reportes para escritura. Resolver permisos según el UID real de esa imagen.
5. Guardar HTML, JSON y log del baseline en el artefacto `reporte-dast`, aunque falle el gate. Comprobar reportes válidos, objetivo esperado y al menos una URL efectivamente examinada. Un reporte vacío o un arranque fallido deben fallar.
6. Destruir contenedores y red de esta ejecución incluso ante errores, conservando el estado de fallo y los reportes. No detener contenedores de otros proyectos.

## Política de bloqueo propuesta

Archivo `.zap/rules.tsv`:

- FAIL para las reglas ZAP 10020 (encabezado anti-clickjacking ausente o inválido) y 10021 (`X-Content-Type-Options` ausente). Son controles ya configurados globalmente por `helmet.frameguard()` y `helmet.noSniff()` en server.ts; el gate protege contra su pérdida.
- WARN para el resto de reglas pasivas, incluidas las brechas heredadas de CSP, información y configuración. Conservarlas en los reportes y priorizarlas; no convertirlas automáticamente en falsos positivos ni ocultarlas con IGNORE.
- Usar la opción documentada `-I` exclusivamente para que los WARN no bloqueen. FAIL y errores de ZAP siguen fallando. Sin `continue-on-error` ni `|| true` en gates.
- No declarar el gate diferencial: bloqueará esas dos reglas en todo el alcance examinado. Si aparece un fallo heredado en una ruta, investigarlo y reportarlo; no añadir una exclusión solo para lograr verde.
- Errores de herramienta, timeout, imagen equivocada, objetivo sin cobertura, fallo de autenticación o reportes ausentes también bloquean.

Estas dos reglas no son una política basada solo en severidad: una regresión de un encabezado ya presente puede bloquear aunque ZAP la clasifique de riesgo bajo. La deuda restante continúa visible. Actualizar `security/politica-de-bloqueo.md` con esta justificación.

## Autenticación y Automation Framework

- Crear una cuenta normal efímera por ejecución mediante el registro existente `/api/Users`, con correo y contraseña aleatorios. No usar credenciales reales ni cuentas administrativas de semilla.
- Autenticar mediante `/rest/user/login`; obtener el JWT y el identificador de carrito desde la respuesta real. Verificar que la identidad devuelta por `/rest/user/whoami` coincide con la cuenta y que una petición al carrito propio está autenticada. El test de éxito no puede basarse únicamente en HTTP 200.
- Configurar un contexto restringido a la instancia del laboratorio y la gestión de sesión mediante Authorization: Bearer, usando capacidades documentadas de ZAP Automation Framework. Determinar durante implementación la configuración exacta compatible con la versión fijada.
- `.zap/plan.yaml` describe el recorrido autenticado pasivo por PR. Hacer pasar por ZAP las peticiones autenticadas y verificar identidad/autenticación dentro del recorrido observado, sin aceptar una validación externa seguida de un escaneo anónimo. Si la sesión falla o no se demuestra ese recorrido, fallar claramente.
- Mantener token y contraseña solo en memoria o archivos temporales excluidos de Git. Enmascarar los valores en los logs y sanear los reportes antes de publicarlos, verificando que no contienen credenciales ni JWT. No subir sesiones completas sin sanear ni imprimir headers de autorización.
- Añadir reportes separados para baseline y autenticado, con sus objetivos, número de peticiones/cobertura y resultados. El gate pasivo autenticado aplica el mismo criterio de encabezados y fallos de herramienta; sus reglas deben mantenerse consistentes con rules.tsv y tener una comprobación que detecte divergencias.

## Escaneos activos y API

Añadir una opción booleana de `workflow_dispatch`, desactivada por defecto, para ejecutar los escaneos ampliados. No crear cron ni automatización periódica no solicitada.

- Full scan con una configuración acotada y timeout finito, únicamente contra la instancia efímera interna. Registrar alcance, duración y cobertura real.
- API scan importando `swagger.yml` del repositorio, con el servidor dirigido a la instancia propia. El documento es OpenAPI 3.0 y solo describe `/b2b/v2/orders`; no representa toda la API REST de Juice Shop. Aplicar la autenticación requerida o documentar con evidencia el impedimento, sin presentar respuestas 401 como cobertura autenticada.
- Usar instancias nuevas cuando los escaneos activos modifiquen datos o afecten a la sesión, evitando contaminar la evidencia de los otros modos.
- Los hallazgos activos son informativos para priorización y remediación del laboratorio; los errores operativos, alcance incorrecto o ausencia de cobertura fallan. Esta distinción debe constar en la política y reportes, no esconderse mediante un bypass general del código de salida.

## Archivos y entregables previstos

- `.github/workflows/devsecops.yml`: job DAST y opción manual de escaneos ampliados.
- `.zap/rules.tsv`: política del baseline.
- `.zap/plan.yaml` y configuración adicional necesaria: autenticación y escaneos ampliados, con nombres por modo si simplifica su revisión.
- Scripts y pruebas pequeños en `.zap/` para preparación de cuenta, validación de resultados, política y saneamiento, solo donde la CLI no cubra el requisito.
- `infra/compose.dast.yaml`: red interna para las pruebas; no rebajar las restricciones del servicio.
- `security/dast/`: metodología, cinco hallazgos relevantes con evidencia real y resultados verificados. Reportes generados como artefactos/archivos de evidencia; no subir tokens ni sesiones.
- Actualizar README y política para ejecución local y CI, limitaciones y nuevo check requerido después de verificar el primer PR.
- Conservar la evidencia de fase 5 ya guardada en outputs/evidencia-fase-5 para el informe final. No modificar ni reemplazar los ZIP originales.

## Validación y criterio de cierre

1. Workflow validado con actionlint; Compose y red interna verificadas realmente.
2. Baseline sobre la imagen del equipo con HTML/JSON válidos y evidencia de cobertura.
3. Prueba de gate con fixture propia sin un encabezado requerido, fixture solo con WARN, objetivo inaccesible y reporte vacío/malformado. Observar fallo antes de implementar cualquier helper nuevo y éxito después.
4. Cuenta aleatoria, recorrido autenticado comprobado dentro de ZAP y prueba negativa con token inválido. Verificar saneamiento con valores de prueba y buscar los secretos efímeros reales en los artefactos antes de publicarlos.
5. Full/API ejecutados contra instancias propias, con limitaciones documentadas; cinco hallazgos escogidos a partir de resultados reales, sin inventarlos si la cobertura inicial es insuficiente.
6. Evidencia por SHA, versión/digest ZAP, alcance, fecha y modo. No declarar éxito en CI antes de observar la ejecución real.

La implementación se hará en el checkout actual sobre una rama separada. Se comprobará de nuevo el espacio y estado de Docker; no se borrarán imágenes/cachés ajenas ni se reparará globalmente el motor sin autorización. Detalles de versión, CLI y helpers quedan al implementador, sujetos a documentación oficial y pruebas reales.

## Fuentes oficiales consultadas

- https://www.zaproxy.org/docs/docker/baseline-scan/
- https://www.zaproxy.org/docs/alerts/10020/
- https://www.zaproxy.org/docs/alerts/10021/
- https://www.zaproxy.org/docs/automate/automation-framework/

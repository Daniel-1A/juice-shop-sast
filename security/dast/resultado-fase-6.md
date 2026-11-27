> **Cierre de entrega (27/11/2026):** los pendientes de CI descritos al final son históricos y quedaron completados. Las fases 5 y 6 están fusionadas; la ejecución de `main` [45893213451](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/45893213451) aprobó y su evidencia permanente está en el [índice final](../../entrega-final/README.md). Los reportes locales mencionados en el texto se conservan en esa entrega; no se requiere acceder al equipo del autor.

# Fase 6: implementación y validación local de ZAP/DAST

Fecha: 26 de noviembre de 2026. Repositorio: `C:/Users/danie/source/repos/juice-shop-sast`. Rama: `fase-6-dast`, desde main `4437a9f` (merge del PR #18).

## Cambios

Se añadió `dast (zap)` después de build e IaC, consumiendo el artefacto de la misma imagen. Cada modo recrea la aplicación en una red Docker interna, comprueba salud y coincidencia de imagen y destruye sus recursos al finalizar.

Baseline y recorrido autenticado pasivo se ejecutan por PR. Full y API se habilitan con la opción manual `extended_scans`, desactivada por defecto. El artefacto `reporte-dast` contiene únicamente los resultados saneados de esa ejecución, en carpetas por modo.

La imagen oficial de ZAP 2.17.0 quedó fijada a `sha256:9624669db72f54d86c4b46a7064518bd9bf79d8c61a4c31befa9923489f328af`. No se publica la API del escáner ni se monta el socket Docker en él o en Juice Shop.

## Resultados locales observados

El flujo ampliado se ejecutó con Bash desde WSL y terminó con salida 0:

| Modo | URLs registradas | Tipos de alerta | Resultado |
|---|---:|---:|---|
| Baseline | 47 | 3 | Aprobado, sin reglas FAIL |
| Autenticado pasivo | 109 | 4 | Aprobado, identidad y carrito verificados en ZAP |
| Full activo acotado | 109 | 5 | Completado, hallazgos informativos |
| API activo | 49 | 6 | Completado, petición B2B autenticada comprobada |

Los conteos son tipos de alerta del JSON por modo; no sumar las columnas como vulnerabilidades únicas. Cada modo tiene solapamientos. Las URLs registradas tampoco equivalen a cobertura exhaustiva o a respuestas exitosas de todas las rutas.

Se comprobó el límite activo de cinco minutos mediante la API, tanto en ejecución como en coverage.json. La evidencia registra una muestra de hasta 500 respuestas; hubo respuestas exitosas reales en los cuatro modos. La red interna rechazó la apertura de conexión a un destino externo.

La cuenta de prueba se genera aleatoriamente, sin credenciales reales. Automation Framework solicita whoami con la cookie requerida por esa ruta, el carrito con Bearer y el mismo carrito con un token inválido. Se comprueban los cuerpos y códigos de las respuestas vistas por ZAP: identidad y UserId correctos, carrito propio y rechazo 401. No se acepta HTTP 200 anónimo como prueba de autenticación.

## Gates y pruebas negativas

- La fixture HTTP propia sin encabezados produjo fallo por 10020 y 10021.
- La fixture con esos encabezados y solo WARN fue aprobada.
- El objetivo inaccesible produjo fallo del escáner y del wrapper; no se aprobó un reporte vacío.
- Ocho pruebas automatizadas Linux verificaron política, alcance, cobertura real, autenticación, saneamiento y aislamiento de evidencia entre ejecuciones.
- actionlint validó el workflow. La sintaxis Bash y Compose se comprobaron y el script se ejecutó realmente desde WSL.

Se corrigieron durante las pruebas dos supuestos de integración: el loader oficial de hooks no define __file__, y una clave CLI no reconocida de duración no se aplica. Los hooks usan la ruta explícita y la API de ZAP con verificación posterior. El primer escaneo activo de diagnóstico se detuvo de forma controlada; la evidencia conservada del flujo ampliado corresponde a la repetición con límite verificado.

La revisión independiente encontró que los resultados de una ejecución anterior podían mezclarse con otra local. Se reprodujo y corrigió: cada ejecución obtiene una carpeta nueva y Actions recibe su ruta exacta, incluso si falla antes de escanear. Se probaron también los permisos de lectura para un uploader con UID distinto del escáner; los metadatos se escriben antes de transferir la propiedad de esa carpeta pública a ZAP.

## Hallazgos analizados

El repositorio contiene `security/dast/hallazgos.md` con cinco casos:

1. SQLi en búsqueda: High/Low según ZAP; corroborada por la interpolación de q en routes/search.ts y el error Sequelize/SQLite observado. No se afirma extracción de datos.
2. CSP ausente: configuración confirmada, sin atribuirle por sí sola un XSS explotado.
3. CORS permisivo: comodín confirmado; no se afirma lectura automática de datos autenticados desde terceros.
4. Detalles de error internos: corroborados en la búsqueda; un 500 aislado no prueba una fuga.
5. Content-Type HTML en la raíz visto por el modo API: falso positivo de contexto, porque la raíz sirve la SPA y no es la operación B2B de OpenAPI.

No se hicieron correcciones de negocio ni se cuentan estos análisis como cinco PR de remediación. La alerta adicional de error 500 se considera relacionada con manejo de errores para evitar inflar remediaciones.

## Evidencia y límites

La copia de los reportes locales saneados se conserva junto a este informe, en `evidencia-fase-6/`. Incluye ejecución ampliada, ejecución estándar final y controles negativos. Los ZIP y capturas de fase 5 permanecen en `evidencia-fase-5/` sin modificaciones.

Los ensayos locales usaron la imagen funcional `juice-shop:fase5-local`, conservada de la fase anterior por el incidente del almacén Docker. No se modificó código de aplicación desde esa fase; esto no atribuye a esa imagen local el SHA del nuevo commit. CI descargará y verificará la imagen nueva de su propio SHA.

La detección activa y el spider tienen límites deliberados. El contrato swagger.yml solo describe `/b2b/v2/orders`, y el recorrido de sesión siembra también identidad, carrito y búsqueda. No se presenta el resultado como cobertura completa de Angular, toda la API, IDOR, OAuth, Web3 o servicios LLM. No se ejecutó el plan formal de pentest de fase 8.

## Pendiente en GitHub

1. Crear el commit y subir fase-6-dast; abrir PR hacia main.
2. Revisar `dast (zap)` y descargar `reporte-dast` de su ejecución real.
3. Conservar enlace, SHA, ZIP y capturas como evidencia de CI.
4. Verificar el modo ampliado manual y añadir el check a la protección de rama tras la primera ejecución satisfactoria.

No se hizo push, merge ni se cambió la protección de rama. La ejecución real de GitHub Actions de esta fase aún no se ha observado.

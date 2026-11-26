# Cinco hallazgos DAST relevantes

Fecha de análisis: 26 de noviembre de 2026. Instancia local propia de Juice Shop 20.3.0; ZAP 2.17.0 fijado por digest. Se conservan las alertas y su confianza original; los niveles no son una puntuación CVSS nueva ni una declaración de explotación.

Los reportes completos por modo son la fuente dinámica. Las rutas y números de carrito pueden variar entre instancias porque las cuentas de prueba son efímeras. No se hicieron correcciones de negocio durante esta fase y estos hallazgos no cuentan como cinco PR de remediación.

## DAST-01: posible SQL Injection — ZAP 40018

- Severidad/confianza del escáner: High / Low.
- Evidencia: `GET /rest/products/search?q=apple%27` produjo HTTP 500; ZAP registró el parámetro q y la entrada `apple'`.
- Análisis: un 500 por sí solo no demuestra SQLi. La revisión de `routes/search.ts:21-23` corrobora que q se interpola directamente en la consulta a Products. La comprobación local adicional observó un error Sequelize/SQLite. Se clasifica como verdadero positivo corroborado estáticamente, conservando confianza dinámica baja; no se afirma extracción de datos ni una cadena de explotación.
- Prioridad: alta para la etapa de remediación; ya se relaciona con REQ-07 de consultas parametrizadas y con SAST.
- Corrección propuesta para un PR posterior: parámetros enlazados/ORM y regresión con comillas y patrones de búsqueda. [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).

## DAST-02: falta Content Security Policy — ZAP 10038

- Severidad/confianza: Medium / High.
- Evidencia: ausencia de Content-Security-Policy en respuestas de la aplicación; también corroborada en la respuesta raíz. server.ts configura frameguard y noSniff, pero no CSP.
- Análisis: verdadero positivo de defensa en profundidad. No demuestra por sí mismo una inyección XSS; limita una capa de mitigación si otra vulnerabilidad permite inyectar contenido.
- Prioridad: media; trazable a REQ-14. En esta fase avisa porque es deuda conocida, no una regresión de los dos encabezados exigidos por el gate.
- Corrección propuesta: diseñar una CSP compatible con Angular, probarla en modo Report-Only y después aplicarla con pruebas funcionales. Evitar una política copiada que permita scripts arbitrarios o rompa la SPA. [OWASP CSP](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html).

## DAST-03: política CORS permisiva — ZAP 10098

- Severidad/confianza: Medium / Medium.
- Evidencia: `Access-Control-Allow-Origin: *`, también observado al consultar la raíz de la instancia propia.
- Análisis: configuración permisiva confirmada. El impacto depende del recurso. El comodín no demuestra que un sitio externo pueda leer automáticamente datos autenticados: no se ha acreditado una política de credenciales que lo permita ni acceso al JWT de otro usuario. La alerta requiere evaluación por endpoint.
- Prioridad: media, con revisión de los orígenes y consumidores esperados.
- Corrección propuesta: restringir orígenes donde corresponda y probar preflight, contenido público y rutas autenticadas. [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html).

## DAST-04: detalles de error expuestos — ZAP 90022

- Severidad/confianza: Low / Medium.
- Evidencia: alertas sobre rutas incompletas como `/rest` y `/rest/user`, y sobre `/b2b/v2/orders` durante pruebas activas. La comprobación adicional de la búsqueda con una comilla confirmó una respuesta 500 con detalles de Sequelize/SQLite.
- Análisis: exposición de detalles internos corroborada en la búsqueda; un 500 genérico no debe clasificarse automáticamente como fuga. La alerta API 100000 de código 500 se considera evidencia relacionada del manejo de errores, no una segunda remediación independiente del mismo caso.
- Prioridad: media para reducir información útil para reconocimiento y mejorar robustez.
- Corrección propuesta: respuestas genéricas y consistentes, registro interno con identificador de correlación y pruebas de que los detalles no llegan al cliente. No registrar tokens/contraseñas. [OWASP Error Handling](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html).

## DAST-05: Content-Type inesperado en modo API — ZAP 100001

- Severidad/confianza del escáner: Low / High para la observación del tipo de contenido.
- Evidencia: la instancia registrada fue la raíz `http://juice-shop:3000`, con `text/html`.
- Clasificación: falso positivo de contexto respecto al contrato B2B. La raíz sirve la SPA Angular y debe devolver HTML; no es la operación `/b2b/v2/orders` de swagger.yml. El modo API contiene además las rutas sembradas por el recorrido autenticado.
- Siguiente paso: delimitar y revisar cada URL del resultado; comprobar el tipo esperado de los endpoints API reales. Conservar la alerta y la justificación, sin cambiar globalmente el Content-Type del frontend ni ocultar la regla completa.

## Límites de cobertura y próximos pasos

- Baseline no realiza ataques activos ni descubre exhaustivamente una SPA.
- El full scan tiene límites de duración y descubrimiento; API importa un contrato B2B parcial y un recorrido autenticado explícito.
- El rechazo de un token inválido demuestra ese control de autenticación; no prueba ausencia de IDOR, autorización por rol ni otros fallos de sesión.
- Integrar resultados reales en la fase posterior de DefectDojo y relacionarlos con STRIDE, requisitos y PR de corrección. No asignar estados corregidos o riesgos aceptados sin evidencia y responsable.

# Matriz STRIDE para priorizar el pentest

Evaluación sobre el [DFD de la aplicación](../dise%C3%B1o/dfd.md) y los [requisitos de seguridad](../dise%C3%B1o/requisitos-asvs.md). El [modelo del laboratorio](juice-shop-ssdlc.json) incorpora las 13 amenazas a una copia del [diagrama original](../../threat-model.json). Se validó el archivo con el [esquema oficial de Threat Dragon v1](https://github.com/OWASP/threat-dragon/blob/main/td.vue/src/assets/schema/threat-dragon-v1.schema.json). Los IDs T01 a T13 conectan ambas representaciones.

La prioridad combina impacto y probabilidad en el laboratorio. Alta indica impacto alto con probabilidad media o alta, o una brecha respaldada por los resultados del proyecto. La columna de mitigación describe el control esperado. Los estados de remediación se mantienen en el [registro de evidencia](../remediacion.md).

| ID | STRIDE | DFD | Amenaza | Impacto | Prob. | Prioridad | Mitigación | Requisito y verificación |
|---|---|---|---|---|---|---|---|---|
| T01 | Suplantación | P1 · F2 | Identidad asumida por una sesión no válida | Alto | Alta | Alta | Verificar firma, algoritmo y vigencia | REQ-04 · regresión de sesión, PT-01 |
| T02 | Suplantación | P1 · F1 | Acceso con credenciales adivinadas o reutilizadas | Alto | Media | Alta | Limitación por cuenta y origen | REQ-02 · revisión manual, PT-04 |
| T03 | Suplantación | P1 · D3 | Identidad derivada de claves fuera de custodia | Alto | Media | Alta | Custodia y rotación de llaves | REQ-04/12 · Gitleaks y SAST, PT-01 |
| T04 | Manipulación | P1/P2 · F3/F7 | Entradas cambian el significado de una consulta | Alto | Alta | Alta | Vincular parámetros y manejar errores | REQ-07 · Semgrep, PT-03 |
| T05 | Manipulación | P3 · F9 | Usuario cambia un recurso de otra cuenta | Alto | Media | Alta | Verificar propiedad en servidor | REQ-05/06 · pruebas de acceso, PT-02 |
| T06 | Elevación | P5 · F15 | Cliente alcanza una operación administrativa | Alto | Media | Alta | Autorizar el rol en todas las operaciones | REQ-05 · revisión manual, PT-02 |
| T07 | Divulgación | P6 · F17/F18 | Una ruta pública expone archivos internos | Alto | Alta | Alta | Deshabilitar listados y exigir ACL | REQ-10 · DAST pasivo, PT-06 |
| T08 | Repudio | P5 · D3 | Acciones sensibles carecen de rastro atribuible | Medio | Media | Media | Eventos correlacionables sin secretos | REQ-13 · revisión manual, PT-07 |
| T09 | Elevación | P4 · F12 | Datos de perfil alcanzan evaluación dinámica | Alto | Media | Alta | Renderizar contenido como datos | REQ-08 · Semgrep, PT-05 |
| T10 | Denegación de servicio | P4 · F13 | La obtención de recursos remotos agota capacidad | Alto | Media | Alta | Destinos permitidos, límites de tiempo y tamaño | REQ-11 · Semgrep y revisión manual, PT-05 |
| T11 | Divulgación | P1 · D1 | Un almacén expone hashes débiles de contraseñas | Alto | Media | Alta | Hash adaptativo con salt independiente | REQ-03 · Semgrep, PT-04 |
| T12 | Divulgación | P2 · F6/F7 | Un error interno expone detalles de implementación | Medio | Alta | Alta | Respuestas genéricas y logs restringidos | REQ-13 · revisión manual, PT-06 |
| T13 | Manipulación | P2 · F8 | El navegador interpreta contenido de usuario como código | Medio | Media | Media | Codificación contextual y CSP | REQ-09/14 · SAST y DAST pasivo, PT-08 |

# Revisión inicial de hallazgos SAST

Escaneo local del avance con Semgrep 1.182.1 y las cinco reglas de `.semgrep/`. La herramienta produjo ocho alertas. Se revisaron los siguientes casos en el código. La ejecución de Actions también aplica reglas del registro de Semgrep.

| Ubicación | Regla | Clasificación | Evidencia y siguiente paso |
|---|---|---|---|
| [`routes/login.ts:34`](../../routes/login.ts#L34) | `js-sequelize-raw-query-interpolation` | Verdadero positivo | El correo de `req.body` entra directamente en la consulta a SQLite. Usar parámetros de Sequelize y comprobar el login con entradas que contengan comillas. |
| [`lib/insecurity.ts:41`](../../lib/insecurity.ts#L41) | `js-weak-password-hash-md5` | Verdadero positivo | El helper de autenticación aplica MD5 sin salt. El código de login lo usa sobre la contraseña. Migrar a un hash adaptativo con salt y probar registro y autenticación. |
| [`routes/userProfile.ts:65`](../../routes/userProfile.ts#L65) | `js-eval-with-dynamic-input` | Verdadero positivo | Con el reto de perfil habilitado, la ruta extrae parte del nombre de usuario y la pasa a `eval`. Eliminar la evaluación de código y renderizar datos de perfil como texto. |
| [`routes/profileImageUrlUpload.ts:24`](../../routes/profileImageUrlUpload.ts#L24) | `js-ssrf-fetch-user-url` | Verdadero positivo | La ruta de perfil pasa `req.body.imageUrl` a `fetch` cuando la sesión es válida. Validar destinos permitidos y volver a validar después de cada redirección. |
| [`scripts/package.mjs:121`](../../scripts/package.mjs#L121) | `js-weak-password-hash-md5` | Falso positivo para REQ-03 | El script calcula un checksum de un artefacto de empaquetado. El patrón detecta MD5, pero ese valor no protege contraseñas. |

Los estados se basan en revisión estática. Las correcciones y las pruebas de regresión se documentarán en sus PR.

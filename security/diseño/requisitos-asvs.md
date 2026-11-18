# Requisitos de seguridad - OWASP ASVS 4.0.3

Nivel objetivo: una selección de controles **ASVS 4.0.3 de niveles 1 y 2** para el laboratorio. La tabla registra la evidencia del commit de referencia y la verificación prevista.
Cada requisito se traza a un control del pipeline; la Fase 2 (modelo de amenazas) reutiliza estos IDs en la matriz de trazabilidad.

Fuente: [OWASP ASVS 4.0.3](https://github.com/OWASP/ASVS/releases/tag/v4.0.3). Los estados describen la evaluación inicial. Un hallazgo de SAST identifica un patrón que requiere revisión.

| ID | ASVS | Nivel | Categoría | Requisito | Estado en Juice Shop (evidencia) | Control que lo verifica |
|---|---|---|---|---|---|---|
| REQ-01 | V2.1.1 | L1 | Autenticación | Las contraseñas de usuario tienen al menos 12 caracteres | **No cumple**: el registro acepta 5 (`frontend/src/app/register/register.component.ts`) | Revisión manual + caso de pentest |
| REQ-02 | V2.2.1 | L1 | Autenticación | Existen controles anti-automatización contra fuerza bruta y relleno de credenciales | **No cumple**: hay rate limit en reset-password y 2FA, pero no en `/rest/user/login` (`server.ts`) | DAST + caso de pentest |
| REQ-03 | V2.4.1 | L2 | Almacenamiento de credenciales | Las contraseñas se guardan con un algoritmo adaptativo con salt (bcrypt, scrypt, Argon2id o PBKDF2) | **No cumple**: MD5 sin salt (`lib/insecurity.ts`) | SAST: `js-weak-password-hash-md5` |
| REQ-04 | V3.5.3 | L2 | Sesión | Los tokens sin estado (JWT) usan firma y están protegidos contra manipulación y sustitución de llave | **No cumple**: la llave privada de firma está embebida en el código | SAST + caso de pentest (JWT) |
| REQ-05 | V4.1.1 | L1 | Control de acceso | El control de acceso se aplica en el servidor, no en el cliente | **Por verificar** con escaneo autenticado | DAST autenticado + pentest |
| REQ-06 | V4.2.1 | L1 | Control de acceso | Los datos sensibles están protegidos contra IDOR (acceso a recursos de otro usuario) | **No cumple**: carrito accesible por ID (`/rest/basket/:id`) | DAST autenticado + pentest |
| REQ-07 | V5.3.4 | L1 | Validación / inyección | Las consultas a base de datos usan consultas parametrizadas u ORM | **No cumple**: SQL interpolado en `routes/login.ts` y `routes/search.ts` | SAST: `js-sequelize-raw-query-interpolation` |
| REQ-08 | V5.2.4 | L1 | Validación / inyección | La aplicación no usa `eval()` ni ejecución dinámica de código con datos del usuario | **No cumple**: `routes/userProfile.ts` evalúa código derivado del perfil. `routes/captcha.ts` también usa `eval`, con una expresión generada en el servidor | SAST: `js-eval-with-dynamic-input` |
| REQ-09 | V5.3.3 | L1 | Codificación de salida | La salida se codifica según el contexto para prevenir XSS | **Por verificar** (búsqueda y reseñas) | SAST (reglas Angular) + ZAP |
| REQ-10 | V4.3.2 | L1 | Control de acceso | El listado de directorios está deshabilitado | **No cumple**: `/ftp`, `/encryptionkeys`, `/support/logs` (`server.ts`) | ZAP baseline |
| REQ-11 | V5.2.6 | L1 | Archivos / SSRF | Las peticiones del servidor a URLs externas usan lista de permitidos | **No cumple**: `routes/profileImageUrlUpload.ts` hace `fetch(url)` | SAST: `js-ssrf-fetch-user-url` + prueba del destino y redirecciones |
| REQ-12 | V6.4.1 | L2 | Secretos | Un gestor de secretos protege las llaves y permite controlar su acceso | **No cumple**: llave RSA privada en `lib/insecurity.ts` | SAST: `js-hardcoded-private-key` + gitleaks |
| REQ-13 | V7.1.1 | L1 | Registro de eventos | Los logs no contienen credenciales, tokens ni datos de pago | **Por verificar** (morgan registra URLs completas) | Revisión manual de `logs/` |
| REQ-14 | V14.4.3 | L1 | Configuración HTTP | Se envía una Content-Security-Policy que mitiga XSS | **No cumple**: `helmet` sin CSP (`server.ts`) | ZAP baseline |
| REQ-15 | V14.2.1 | L1 | Dependencias | Los componentes están actualizados y sin vulnerabilidades conocidas | **No cumple**: dependencias desactualizadas a propósito | SCA: Grype + Dependabot |

## Resumen
- 15 requisitos: 12 de nivel 1 y 3 de nivel 2.
- 12 registran una brecha inicial y 3 quedan por verificar.
- 5 tienen una regla Semgrep propia para detectar patrones relevantes (`.semgrep/juice-shop-rules.yml`); cada regla lleva el `REQ-xx` en sus metadatos.

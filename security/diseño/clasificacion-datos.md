# Clasificación de datos - Juice Shop

## Niveles de sensibilidad

| Nivel | Definición | Controles mínimos esperados |
|---|---|---|
| **Restringido** | Su exposición permite tomar cuentas, suplantar el sistema o cometer fraude | Hash fuerte o cifrado en reposo, nunca en logs ni en el repositorio, acceso solo por el proceso dueño |
| **Confidencial** | Datos personales cuya exposición afecta la privacidad del usuario | Control de acceso por dueño (anti-IDOR), TLS en tránsito, enmascaramiento al mostrar |
| **Interno** | Información operativa sin datos personales | Acceso autenticado o restringido a administradores |
| **Público** | Diseñado para mostrarse a cualquiera | Integridad (que no se pueda alterar sin autorización) |

## Inventario

| Dato | Dónde vive | Nivel | Estado observado en Juice Shop |
|---|---|---|---|
| Contraseña de usuario | `Users.password` (D1) | Restringido | Hash **MD5 sin salt** (`lib/insecurity.ts`) |
| Llave privada RSA para firmar JWT | `lib/insecurity.ts` | Restringido | **Embebida en el código fuente** |
| Token JWT de sesión | Navegador | Restringido | Expira en 6 h (`expiresIn: '6h'`) |
| Secreto TOTP (2FA) | `Users.totpSecret` (D1) | Restringido | Almacenado en la base de datos |
| Respuesta a pregunta de seguridad | `SecurityAnswers` (D1) | Restringido | Permite restablecer la contraseña |
| Número de tarjeta, titular, vencimiento | `Cards` (D1) | Restringido | Número completo almacenado |
| Token de membresía deluxe | `Users.deluxeToken` (D1) | Restringido | Otorga beneficios pagados |
| Archivos en `/encryptionkeys` | D3 | Restringido | **Listables públicamente** |
| Email, nombre de usuario | `Users` (D1), autor de reseñas (D2) | Confidencial | Visible en reseñas |
| Dirección, teléfono, código postal | `Addresses` (D1) | Confidencial | Vía `/api/Addresss` |
| Historial de pedidos | D2 | Confidencial | Exportable por el usuario |
| Saldo de billetera | `Wallets` (D1) | Confidencial | — |
| IP del último login | `Users.lastLoginIp` (D1) | Confidencial | Dato personal |
| Imagen de perfil y archivos subidos | D3 | Confidencial | Puede contener datos personales |
| Logs de acceso (morgan, con IP) | `logs/` (D3) | Confidencial | **Listables en `/support/logs`** |
| Métricas Prometheus | `/metrics` | Interno | Sin autenticación |
| Documentos en `/ftp` | D3 | Interno | Listado de directorio habilitado |
| Catálogo, precios, reseñas públicas | D1, D2 | Público | — |

## Conclusiones para el diseño
- Los datos **Restringidos** concentran los requisitos REQ-01 a REQ-04, REQ-12 y REQ-13 de `requisitos-asvs.md`.
- El laboratorio utiliza datos de pago ficticios. Los datos con formato de tarjeta se clasifican como Restringidos.
- Los almacenes D1 y D3 comparten contenedor con la aplicación: una ejecución de código en P4 o P7 compromete todos los datos.

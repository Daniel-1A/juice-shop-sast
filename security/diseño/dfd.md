# Diagrama de flujo de datos (DFD) - Juice Shop 20.3.0

Notación: rectángulos = entidades externas, rectángulos redondeados = procesos, cilindros = almacenes de datos, subgrafos = **límites de confianza (TB)**. Este DFD es la base del modelo STRIDE en OWASP Threat Dragon (Fase 2, `security/threat-model/`).

```mermaid
flowchart LR
    subgraph TB1[TB1 - Internet / no confiable]
        CLI[Cliente<br/>anónimo o registrado]
        ADM[Administrador]
    end

    subgraph TB2[TB2 - Contenedor de la aplicación]
        P1([P1 Autenticación<br/>login, registro, 2FA,<br/>passkeys, reset password])
        P2([P2 Catálogo y búsqueda<br/>productos, reseñas])
        P3([P3 Carrito, pedido y pago<br/>basket, checkout, wallet, cupones])
        P4([P4 Perfil y archivos<br/>imagen por URL o upload,<br/>quejas, exportar datos])
        P5([P5 Administración<br/>usuarios, feedback])
        P6([P6 Servidor de archivos<br/>/ftp, /support/logs,<br/>/encryptionkeys])
        P7([P7 API B2B<br/>/b2b/v2/orders])

        subgraph TB3[TB3 - Capa de datos]
            D1[(D1 SQLite<br/>Users, Cards, Addresses,<br/>Baskets, Wallets,<br/>SecurityAnswers)]
            D2[(D2 MarsDB<br/>reseñas, pedidos)]
            D3[(D3 Sistema de archivos<br/>uploads, ftp, logs, llaves)]
        end
    end

    subgraph TB4[TB4 - Servicios externos]
        GO[Google OAuth]
        EXT[Servidor remoto arbitrario<br/>URL de imagen de perfil]
    end

    CLI -- F1 email + contraseña --> P1
    P1 -- F2 JWT RS256 --> CLI
    P1 <-->|F3 consulta usuario / hash| D1
    CLI -. F4 OAuth redirect .-> GO
    GO -. F5 token de acceso .-> P1

    CLI -- F6 criterio de búsqueda --> P2
    P2 <-->|F7 SQL productos| D1
    P2 <-->|F8 reseñas| D2

    CLI -- F9 JWT + items, tarjeta, dirección --> P3
    P3 <-->|F10 carrito, tarjetas, billetera| D1
    P3 -- F11 pedido --> D2

    CLI -- F12 JWT + archivo o URL --> P4
    P4 -- F13 GET a URL del usuario --> EXT
    P4 -- F14 guarda archivo --> D3

    ADM -- F15 JWT rol admin --> P5
    P5 <-->|F16 usuarios, feedback| D1

    CLI -- F17 GET archivo --> P6
    P6 <-->|F18 lee archivo| D3

    CLI -- F19 JWT + orderLinesData --> P7
```

## Elementos

| ID | Elemento | Tipo | Límite | Datos principales |
|---|---|---|---|---|
| CLI | Cliente | Entidad externa | TB1 | Credenciales, datos personales, tarjeta |
| ADM | Administrador | Entidad externa | TB1 | Credenciales con rol `admin` |
| P1 | Autenticación | Proceso | TB2 | Contraseñas, JWT, secreto TOTP |
| P2 | Catálogo y búsqueda | Proceso | TB2 | Datos públicos, texto de búsqueda |
| P3 | Carrito, pedido y pago | Proceso | TB2 | Tarjetas, direcciones, saldo de billetera |
| P4 | Perfil y archivos | Proceso | TB2 | Imágenes, archivos XML/YAML/ZIP, URLs |
| P5 | Administración | Proceso | TB2 | Lista de usuarios |
| P6 | Servidor de archivos | Proceso | TB2 | Documentos, logs de acceso, llaves |
| P7 | API B2B | Proceso | TB2 | Pedidos masivos (OpenAPI en `/api-docs`) |
| D1 | SQLite | Almacén | TB3 | Ver `clasificacion-datos.md` |
| D2 | MarsDB | Almacén | TB3 | Reseñas (autor = email), pedidos |
| D3 | Sistema de archivos | Almacén | TB3 | Uploads, logs con IP, llaves |
| GO | Google OAuth | Entidad externa | TB4 | Identidad federada |
| EXT | Servidor remoto | Entidad externa | TB4 | Contenido descargado por el servidor |

## Flujos que cruzan límites de confianza (prioridad para STRIDE)

| Flujo | Cruza | Por qué importa |
|---|---|---|
| F1, F2 | TB1 ↔ TB2 | Credenciales y token de sesión viajan por HTTP en el entorno local |
| F1/F3 y F6/F7 | TB1 → TB2 → TB3 | El login y la búsqueda incorporan entradas del cliente a consultas SQL |
| F9 | TB1 → TB2 | Datos de pago; riesgo de IDOR sobre el carrito de otro usuario |
| F12, F13 | TB1 → TB2 → TB4 | El servidor hace peticiones a URLs del usuario (SSRF) |
| F15 | TB1 → TB2 | Elevación de privilegios si el rol se toma de un JWT manipulado |
| F17 | TB1 → TB2 → TB3 | Listado de directorios y descarga de archivos internos |
| F19 | TB1 → TB2 | Datos evaluados en un sandbox `vm` (inyección de código) |

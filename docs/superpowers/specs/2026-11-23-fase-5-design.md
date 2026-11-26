# Fase 5: infraestructura y escaneo del contenedor

## Intención y alcance

Completar la fase 5 de la entrega final del 2 de diciembre de 2026 sobre el repositorio `C:/Users/danie/source/repos/juice-shop-sast`. La preentrega conserva sus controles de secretos, SAST y SCA. Esta fase entrega construcción endurecida, despliegue local reproducible, gates de IaC/contenedor y evidencia antes/después. ZAP, publicación, modelo STRIDE y documento final se ejecutarán en las fases siguientes.

## Enfoques considerados

1. Docker Compose local y servicios efímeros de Actions: recomendado y elegido como propuesta de implementación del orden aprobado. Coincide con la arquitectura documentada y evita necesitar una cuenta de nube.
2. Terraform o Kubernetes: añade infraestructura y credenciales sin aportar valor al alcance local del curso. Se descarta para esta fase.

Diseño aprobado por el usuario en el chat el 23 de noviembre de 2026. Las decisiones técnicas siguientes forman parte del alcance aprobado.

## Diseño propuesto

- Crear `infra/Dockerfile`, conservando Node.js 24, construcción multi-etapa, compilación de frontend y servidor, y runtime distroless de la aplicación. Fijar ambas imágenes base por digest verificado durante la implementación y usar versiones exactas de herramientas adicionales. Conservar el UID 65532. Añadir healthcheck ejecutado mediante Node, sin depender de un shell en distroless.
- Crear `infra/compose.yaml`: puerto enlazado exclusivamente a `127.0.0.1:3000`, usuario 65532, sin modo privilegiado ni socket Docker, `cap_drop: ALL`, `no-new-privileges`, límites de memoria/procesos y healthcheck. No añadir persistencia ni secretos reales. Las escrituras normales de Juice Shop requieren inspección y prueba: no activar un filesystem de solo lectura sin demostrar que los directorios de datos, logs, cargas y archivos generados funcionan mediante montajes adecuados. Se permite conservar la capa escribible si esta es necesaria y se documenta como limitación.
- Modificar `.github/workflows/devsecops.yml`: construir con `docker build -f infra/Dockerfile`, conservar la prueba HTTP de arranque, verificar el usuario efectivo del contenedor y exportar la misma imagen como artefacto `imagen-juice-shop`.
- Añadir job `iac`, dependiente de `build`: descargar y cargar la imagen exacta del SHA, ejecutar Checkov sobre `infra/` y Trivy sobre esa imagen. Usar herramientas fijadas a versiones verificadas y acciones fijadas por SHA cuando sea viable. No introducir ejecución de código de PR con secretos ni `pull_request_target`.
- Checkov: generar reporte completo; bloquear todos los checks fallidos aplicables a `infra/` salvo excepciones concretas justificadas y registradas. Los archivos heredados de `infrastructure/` y `terraform/` quedan fuera de este gate porque son material de retos; se explica explícitamente el alcance. No suprimir resultados globalmente.
- Trivy: generar reporte completo y bloquear vulnerabilidades CRITICAL con corrección disponible, alineado con la política SCA existente. Los HIGH y vulnerabilidades sin corrección se conservan en el reporte. Toda excepción debe identificar CVE/componente, evidencia, responsable y revisión; no crear excepciones solo para conseguir un pipeline verde.
- Publicar artefactos de ambos escaneos incluso si falla el gate. Los errores de herramienta, reportes ausentes y violaciones del umbral deben fallar visiblemente. No usar `continue-on-error` ni `|| true` en gates. Asegurar que la publicación no oculta el código de salida del escáner.
- Actualizar `security/politica-de-bloqueo.md`, las referencias de despliegue en `security/diseño/arquitectura.md` y una guía `infra/README.md` con comandos locales, alcance y resultados reales.

## Evidencia y validación

1. Comprobar estado Git y preservar cambios preexistentes antes de editar. Usar el checkout existente; no crear una copia o worktree sin necesidad.
2. Registrar Checkov sobre el Dockerfile actual antes de modificarlo. Si la herramienta no soporta el formato Compose, registrar esa limitación y validar Compose con `docker compose config`; no atribuir cobertura inexistente a Checkov. El implementador puede añadir Trivy config para cubrir el Compose si la cobertura efectiva de Checkov resulta insuficiente.
3. Construir y escanear la imagen base anterior cuando Docker y recursos disponibles lo permitan; después construir y escanear la imagen nueva. Conservar comandos, versiones, fecha y resultados; no inventar evidencia ni afirmar que existe una ejecución de Actions antes de comprobarla.
4. Validar sintaxis del workflow y Compose, arrancar la imagen, comprobar HTTP, healthcheck, usuario no root y restricciones del contenedor. Verificar que los gates fallan ante hallazgos que superan el umbral, y que un error de ejecución también falla.
5. Ejecutar las verificaciones pertinentes del repositorio. No cambiar código de retos, por lo que RSN no es necesario en esta fase. Si falta acceso al motor Docker o a herramientas, declarar los checks pendientes con precisión.

## Criterio de cierre

Los archivos de fase 5 están integrados, documentados y validados con los recursos disponibles; los gates y reportes son revisables. La fase no se considera demostrada en CI hasta observar su ejecución real. La protección de rama debe incluir el nuevo check después de una primera ejecución válida.

## Límites y decisiones de implementación

No se despliega en nube ni se exponen servicios fuera de localhost. No se modifican vulnerabilidades de negocio ni se cuenta el endurecimiento como cinco remediaciones hasta disponer de hallazgos y PR con antes/después. Digests, versiones y checks específicos se obtienen de fuentes oficiales durante la implementación. El implementador determina los montajes y los detalles de empaquetado a partir del arranque real; no se acepta un contenedor endurecido que no arranque.

El repositorio está fuera de las raíces escribibles de este chat. Se solicitará escalación de herramienta para las operaciones necesarias sobre ese directorio, dentro del alcance autorizado por el usuario. Si la revisión automática rechaza una operación, se informará el motivo y se continuará con lo que sea posible.

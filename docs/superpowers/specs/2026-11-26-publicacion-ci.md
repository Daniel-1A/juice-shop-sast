# Publicación verificable dentro de Actions

Se conserva el publicador remoto existente como modalidad opcional. La modalidad predeterminada inicia Dependency-Track y DefectDojo temporalmente dentro del runner, con imágenes oficiales fijadas, credenciales aleatorias privadas y puertos de loopback. Importa los reportes reales del mismo run, espera el procesamiento del SBOM, verifica conteos mediante lectura posterior y publica recibos sin secretos. No requiere infraestructura externa.

Los servicios se inician secuencialmente para reducir memoria. El cleanup elimina solo el proyecto y volúmenes efímeros de esa ejecución. Las instancias persistentes locales y sus volúmenes se conservan. No se atribuye historial persistente a los servicios efímeros de CI.

Decisión de implementación delegada por el usuario al autorizar continuar sin intervención: reutilizar el prototipo ya probado en work/phase7/stage, corregir el reinicio de conexión observado durante el arranque y completar su validación con bases nuevas y un run real. Mantener las funciones de publicación y el resto de fases existentes; no ejecutar pentest ni modificar retos de Juice Shop.

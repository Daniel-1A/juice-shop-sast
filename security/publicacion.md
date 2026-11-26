# Publicación y gestión de hallazgos

GitHub Actions conserva los reportes en PR y publica los SARIF configurados en Code Scanning. El job predeterminado `publicacion (inventarios)` inicia Dependency-Track y DefectDojo en el runner con imágenes oficiales fijadas y credenciales aleatorias de esa ejecución. Importa los artefactos del mismo run y verifica las respuestas mediante lectura posterior. No requiere destinos HTTPS externos ni secretos permanentes.

## Publicación automática comprobable

Los servicios se inician secuencialmente para reducir memoria. Dependency-Track debe terminar de procesar el CycloneDX y devolver un inventario no vacío; se crea una política de advertencia para severidad crítica. DefectDojo recibe formatos nativos completos y los reportes ZAP saneados convertidos a XML. Se comprueba el número de hallazgos importados y los reintentos reutilizan el test de la misma herramienta y commit. Los avisos de parsing de Semgrep se incluyen en los recibos; la publicación no equivale a cobertura total ni validación humana.

El artefacto `reporte-publicacion` contiene los recibos con SHA, run, hashes, IDs, conteos y confirmación de procesamiento. Los errores de arranque, API, procesamiento, conteos o limpieza fallan el job. Una carpeta distinta por ejecución evita publicar éxitos antiguos. No se suben credenciales, configuraciones resueltas ni logs privados de servicios.

Las bases de datos y los volúmenes del runner son **efímeros** y se eliminan al terminar. La instancia de CI demuestra el procesamiento automático; no es un servidor histórico compartido. Las instancias locales persistentes y sus evidencias se conservan por separado. La modalidad remota permanece opcional para cuando existan servidores del equipo.

## Evidencia local comprobada

Se verificaron y descargaron los artefactos del [run 45846349943](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/45846349943), correspondiente al PR #19, y se importaron con el publicador del repositorio. DefectDojo registró seis pruebas en el [engagement local](http://localhost:8082/engagement/2) con el SHA de la rama y el ID del run.

La reimportación del mismo run reutilizó los seis IDs. Se conservan las capturas de [DefectDojo](evidencia/fases-7-8/defectdojo.png) y [Dependency-Track](evidencia/fases-7-8/dependency-track.png) y las [respuestas resumidas de sus API](evidencia/fases-7-8/).

| Prueba | ID local | Hallazgos persistidos |
|---|---:|---:|
| Semgrep | 2 | 37 |
| Grype | 3 | 41 |
| Checkov | 4 | 0 |
| Trivy | 5 | 96 |
| ZAP baseline | 6 | 3 |
| ZAP autenticado | 7 | 4 |

Los conteos corresponden a cada prueba. La importación deja los hallazgos sin verificar y evita cerrar registros automáticamente por ausencia en una nueva ejecución. ZAP se importa por regla con evidencia saneada y el detalle permanece en el artefacto original. Gitleaks queda en GitHub como SARIF redactado.

Dependency-Track registró el procesamiento del CycloneDX para `OWASP Juice Shop SSDLC`, versión `20.3.0`. El archivo contiene 1 221 entradas, mientras el inventario procesado expone 1 167 componentes. Se comprobó que la política `Juice Shop - vulnerabilidad critica`, `SEVERITY IS CRITICAL` con acción `WARN`, está asignada al proyecto. Grype y Trivy aplican sus gates en GitHub con sus propias bases y reglas.

El SBOM de referencia está en [`reporte-sca`](https://github.com/Daniel-1A/juice-shop-sast/actions/runs/45846349943/artifacts/15131817514). SHA-256 del archivo extraído `sbom.cdx.json`: `8df73af4f0914abe0629a8800859e2e27dd140bdcfa444d8cc9abe049b6f7df1`.

## Modalidad remota opcional con servidores del equipo

El job `publicacion remota (opcional)` sigue deshabilitado hasta contar con destinos accesibles y completar lo siguiente:

1. Crear el entorno `seguridad-publicacion` y limitarlo a `main`. Precrear el producto y engagement en DefectDojo y el proyecto de Dependency-Track. Configurar cuentas de servicio limitadas a la importación y carga de sus respectivos inventarios.
2. Guardar las variables del entorno `DOJO_URL`, `DOJO_PRODUCT_NAME`, `DOJO_ENGAGEMENT_NAME`, `DTRACK_URL` y `DTRACK_PROJECT_ID`. Guardar `DOJO_API_TOKEN` y `DTRACK_API_KEY` como secretos del mismo entorno.
3. Habilitar la variable del repositorio `PUBLISH_SECURITY_REPORTS=true` únicamente cuando el runner pueda alcanzar ambas URL HTTPS. El entorno local comprobado se limita a loopback. El runner alojado por GitHub necesita destinos de gestión alcanzables para ejecutar el paso remoto.
4. Verificar ejecución aprobada del job y confirmar las pruebas y el BOM en sus respectivos servicios. Una respuesta aceptada para el BOM indica encolado. Revisar el inventario procesado.

Para publicar localmente, descargar los cuatro artefactos del mismo run y extraerlos en subdirectorios `reporte-semgrep`, `reporte-sca`, `reporte-iac-contenedor` y `reporte-dast`. Exportar las variables y secretos al proceso local y ejecutar `python .github/scripts/publish-reports.py <directorio> --commit <sha> --run <id>`. Los errores de API detienen la publicación y un reintento actualiza los tests de nombre estable.

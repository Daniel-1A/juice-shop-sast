# Diagnóstico de madurez - OWASP SAMM v2

**Alcance:** prácticas del equipo y controles heredados observables en el [commit de referencia](https://github.com/Daniel-1A/juice-shop-sast/tree/779106b4d989879992d94cbc70616a289f84713b), antes de integrar el avance.
**Método:** estimación preliminar por práctica de 0 a 3. Una configuración demuestra que existe una actividad, pero por sí sola no acredita un nivel SAMM completo. Para la evaluación final se contrastarán las evidencias con el [SAMM Toolbox](https://owasp.org/projects/samm/) y se aplicará el mismo método a ambas fechas.

| Función | Práctica | Nivel actual | Evidencia actual | Nivel objetivo | Cómo se alcanza en el proyecto |
|---|---|---|---|---|---|
| Gobierno | Estrategia y métricas | 0 | No hay metas de seguridad | 0 | Fuera del alcance de un proyecto de 4 semanas |
| Gobierno | Políticas y cumplimiento | 0 | Sin políticas de seguridad del desarrollo | 1 | `security/politica-de-bloqueo.md` con umbrales y excepciones |
| Gobierno | Educación y guía | 0 | Sin guía para desarrolladores | 1 | README con instrucciones; Semgrep en el IDE de los tres integrantes |
| Diseño | Evaluación de amenazas | 1 | El commit incluye `threat-model.json` como insumo para la evaluación | 2 | Modelo STRIDE propio con 12+ amenazas, priorización y trazabilidad |
| Diseño | Requisitos de seguridad | 0 | No hay requisitos documentados | 1 | 15 requisitos ASVS trazados a controles |
| Diseño | Arquitectura segura | 0 | Sin documentación de arquitectura de seguridad | 1 | Diagramas de componentes, despliegue y DFD con límites de confianza |
| Implementación | Construcción segura | 1 | El fork incluye el workflow `.github/workflows/sast-bearer.yml` | 2 | Pipeline con SBOM en cada build, acciones fijadas por SHA, gates de SCA |
| Implementación | Despliegue seguro | 1 | El `Dockerfile` usa una imagen final distroless y el usuario 65532 | 2 | Secretos solo en GitHub Actions, imagen escaneada antes de usarse |
| Implementación | Gestión de defectos | 0 | Hallazgos no registrados ni priorizados | 2 | DefectDojo centralizado; priorización con CVSS, EPSS, KEV y alcanzabilidad |
| Verificación | Evaluación de arquitectura | 0 | No existe | 1 | Revisión del diseño contra los requisitos ASVS |
| Verificación | Pruebas guiadas por requisitos | 0 | No existe | 1 | Casos de pentest derivados del modelo de amenazas |
| Verificación | Pruebas de seguridad | 1 | El workflow de Bearer configura SAST y reportes con `exit-code: 0` | 2 | SAST, SCA y DAST automáticos en cada PR con gates reales |
| Operaciones | Gestión de incidentes | 0 | Solo `SECURITY.md` para reportes externos | 0 | Fuera de alcance |
| Operaciones | Gestión del entorno | 0 | Sin endurecimiento propio | 1 | Dockerfile endurecido, escaneo IaC, Dependabot |
| Operaciones | Gestión operativa | 0 | No existe | 0 | Fuera de alcance |

**Promedio simple preliminar:** 0.27 inicial y 1.13 como objetivo.

## Gráfica para el documento
Se recomienda un gráfico de radar con las 15 prácticas (actual vs. objetivo). La misma tabla, con una columna "Nivel final", alimenta la comparación de la Fase 8.

# Evaluación final de madurez OWASP SAMM v2

Corte de evidencia · 26 de noviembre de 2026. Mismo alcance, escala y 15 prácticas de la [evaluación inicial](samm-inicial.md). Los niveles son estimaciones del proyecto. Se asigna el nivel por evidencia operativa y se conserva un valor inferior al objetivo cuando este depende de una actividad por validar. No se usa un puntaje global SAMM formal. [Modelo OWASP SAMM](https://owaspsamm.org/model/).

| Función | Práctica | Inicial | Objetivo | Final | Evidencia del cierre |
|---|---|---:|---:|---:|---|
| Gobierno | Estrategia y métricas | 0 | 0 | 0 | Sin programa formal ni serie de métricas del equipo. |
| Gobierno | Políticas y cumplimiento | 0 | 1 | 1 | Umbrales, excepciones y checks obligatorios documentados. |
| Gobierno | Educación y guía | 0 | 1 | 0 | Hay guías de ejecución. No se dispone de evidencia de uso de la extensión en los tres IDE. |
| Diseño | Evaluación de amenazas | 1 | 2 | 1 | DFD, matriz y modelo Threat Dragon con 13 amenazas. Validado contra el esquema v1. Falta acreditar revisión del equipo y uso sostenido. |
| Diseño | Requisitos de seguridad | 0 | 1 | 1 | Quince requisitos ASVS y controles previstos. |
| Diseño | Arquitectura segura | 0 | 1 | 1 | Arquitectura, límites de confianza y clasificación documentados. |
| Implementación | Construcción segura | 1 | 2 | 2 | Workflow automatizado, dependencias resueltas, SBOM y gates comprobados en Actions. |
| Implementación | Despliegue seguro | 1 | 2 | 2 | Imagen ligada al SHA, build con smoke test, despliegue restringido y escaneo de la misma imagen. |
| Implementación | Gestión de defectos | 0 | 2 | 1 | Registro de correcciones e importación comprobada de seis pruebas en DefectDojo. Falta acreditar gestión y priorización recurrentes. |
| Verificación | Evaluación de arquitectura | 0 | 1 | 0 | Diseño y controles documentados. No se identificó acta independiente de evaluación de arquitectura. |
| Verificación | Pruebas guiadas por requisitos | 0 | 1 | 1 | Casos de validación trazados a ASVS y regresiones existentes de autenticación. El pentest queda planificado. |
| Verificación | Pruebas de seguridad | 1 | 2 | 2 | SAST, SCA y DAST integrados, incluidos recorrido autenticado y evidencias de CI. |
| Operaciones | Gestión de incidentes | 0 | 0 | 0 | Sin operación de producción ni simulacro de incidentes. |
| Operaciones | Gestión del entorno | 0 | 1 | 1 | Compose con límites, usuario no root, escaneo IaC y Dependabot. |
| Operaciones | Gestión operativa | 0 | 0 | 0 | Sin operación continua en producción. |

**Promedio simple** · 0,27 inicial → 0,87 final, frente a 1,13 de objetivo. El avance principal se observa en construcción y verificación. Las brechas restantes son evidencia de formación, evaluación de arquitectura, madurez del modelado y gestión recurrente de defectos.

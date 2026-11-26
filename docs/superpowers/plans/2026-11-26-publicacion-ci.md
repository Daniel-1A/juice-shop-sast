# Plan de publicación de la fase 7

1. Corregir el cliente de readiness con la prueba roja existente para conexiones reiniciadas; ejecutar las doce pruebas, incluida limpieza y artefactos actuales.
2. Probar el bootstrap, importación y cleanup con bases nuevas usando el bundle real conservado. Verificar inventario, política y conteos sin secretos; repetir para comprobar idempotencia.
3. Integrar los helpers en .aspm y añadir el job predeterminado al workflow. Mantener el job remoto opcional y documentar explícitamente la ausencia de historial permanente en CI.
4. Ejecutar actionlint, Bash, pruebas Python y validación real. Pedir una revisión independiente de la rama, corregir hallazgos importantes y abrir PR con sign-off.
5. Seguir Actions hasta su terminación, revisar el artefacto de recibos y conservar evidencia. La aprobación de otro integrante y el merge siguen sujetos a protección de main.

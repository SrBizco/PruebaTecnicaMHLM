# Entrega completa — plan de implementación

**Objetivo:** un ZIP para Windows x64, con tres ejercicios, informes legibles, RPA probado y consulta SQL sin instalar Python ni Git.

**Diseño aprobado:** conservar `1- informe`, `2- RPA Arca` y `3- Operaciones SQL`; guía general en README.md y LEEME.txt; código separado del acceso de uso. Mantener antecedentes en el repo y excluirlos del paquete. El RPA requiere Internet y descarga Chromium si falta. SQL usa su visor portable, licencias y fuentes de terceros existentes.

**Implementación:** empaquetador Python de biblioteca estándar en `entrega/preparar.py`. Lista explícita de fuentes propias. Reutilizar el EXE de rpa-v1.0.2 comprobado por SHA-256 y regenerar el paquete SQL antes del armado general. Validar rutas, archivos esperados y manifiesto de integridad. Salida ignorada por Git en `entrega/dist/`.

**Restricciones:** misma rama; no borrar antecedentes; no incluir cuentas, credenciales, cachés, entornos ni versiones anteriores; no commit, push ni publicación en esta etapa.

- [x] Actualizar README general e instrucciones del RPA.
- [x] Implementar el empaquetador y generar SQL desde la fuente actual.
- [x] Generar ZIP completo, extraer en ruta con espacios y verificar integridad, enlaces locales, PDFs, base y proyecto SQL.
- [x] Dejar ZIP, SHA-256 y texto de release listos para revisión/publicación posterior.

## Verificación

ZIP de 165 archivos, aproximadamente 82 MiB. Hash del RPA idéntico a la entrega validada 1.0.2. Siete consultas ejecutadas sobre la base extraída en modo lectura (41 filas en pagos mensuales). Ambos PDF tienen tres páginas; el informe SQL regenerado conserva el texto del informe versionado. El manifiesto y el SHA-256 externo permiten verificar todos los archivos.

En la primera comprobación, el PDF SQL regenerado no coincidió byte a byte con el anterior por los metadatos de generación; se comprobó su texto completo y se compara el binario contra el paquete SQL recién generado. También se corrigió el cierre explícito de la conexión SQLite del verificador para permitir limpiar la carpeta temporal en Windows. No se modificó la lógica de los ejercicios ni se repitió el login real de ARCA.


## Actualización entrega-v1.0.1
El informe SQL pasa a dos páginas; se regeneran ambos paquetes y sus hashes. El perfil conserva tres páginas y el RPA sigue siendo 1.0.2, sin modificaciones.

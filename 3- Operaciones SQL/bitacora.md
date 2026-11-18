# Bitácora — Ejercicio 3

## 17/11/2026 — Lectura y diagnóstico

Se inspeccionó la totalidad de la única hoja, formatos y estructura del XLSX. Se preservó una copia idéntica con hash. Hallazgos: duplicado exacto, variante de nombre, canal faltante, residuos decimales y CUIT de apariencia sintética. Se identificó que no existe fecha de pago y que Total pagado suma tres tributos, no el costo de la mercadería. Se propuso SQLite con carga trazable; las reglas siguen pendientes de confirmación. No se creó base de datos ni consultas finales. No se hicieron commits ni pushes.


## Revisión aritmética ampliada

A pedido del usuario, se pasó de conciliar el total a reconstruir cada componente. Se encontraron dos diferencias de centavos frente al modelo inferido, una explicable por la etapa de redondeo. Se propuso preservar importes originales y documentar las diferencias. Se distinguieron tributos, gastos adicionales y desembolso incluyendo mercadería para evitar comparar conceptos distintos con el FOB. Ningún tributo total ni gasto adicional observado supera el FOB.

## 17/11/2026 — Implementación aprobada y verificada

El usuario aprobó el plan y el tratamiento de inconsistencias después de commitear el diagnóstico. Se implementaron la carga reproducible, SQLite, siete consultas de lectura y exportaciones CSV/Markdown. Se trabajó en la misma rama y exclusivamente en este directorio, conforme a la organización acordada; no se hicieron commits ni pushes.

Decisión: usar biblioteca estándar de Python para SQLite, Decimal y lectura ZIP/XML del formato concreto recibido. Evita instalaciones adicionales para el evaluador, a cambio de limitar explícitamente el lector a esta estructura XLSX. Los cálculos agregados provienen de SQL; la fuente y los lexemas originales se preservan. La base es una instantánea reconstruible, no un historial de cargas acumuladas.

La revisión de medios centavos permitió corregir una posible interpretación: no existe un criterio uniforme hacia abajo, ya que L38 y L55 quedan hacia arriba. Las diferencias de O20 y L51 son detalles menores del modelo y no modificaciones de pagos. La deduplicación, en cambio, sí cambia el agregado: elimina únicamente la copia exacta de USD 26.495,18.

Se observaron las pruebas fallar antes de implementar la carga. La verificación final pasó 5/5 pruebas de integración tanto en Python 3.9.13 como en 3.15.2: idempotencia de contenido de base/CSV, conciliación, fechas y nombres, preservación de redondeos, cuarentena de valores esenciales inválidos, distinción entre destinación repetida y duplicado exacto, y conservación de la base previa frente a un XLSX ilegible. Una revisión independiente no encontró problemas materiales; sus sugerencias de pruebas de meses/nombres y protección de resultados previos quedaron incorporadas.

Resultado: 61 filas originales, 60 incluidas, 1 duplicada, 0 en revisión; USD 1.381.267,38 en 41 grupos importador/mes. Se comprobó integridad SQLite, claves foráneas y SHA-256 inalterado de la fuente. Pendiente únicamente de revisión del usuario y eventual commit por su cuenta.

## Entrega legible y consulta sin instalación

Se decidió evitar desarrollar un editor SQL propio en WebAssembly: la consigna se resuelve con un informe HTML claro y un visor existente. El HTML muestra datos consultados desde SQLite, con importes legibles, búsqueda por importador/mes y detalle de tratamientos; no contiene totales o nombres fijos en el generador. El paquete Windows x64 incorpora DB Browser 3.13.1 oficial sin modificar, sus bibliotecas, licencias y archivo fuente, con hashes y procedencia documentados.

La prueba real detectó dos particularidades del visor: el archivo de preferencias Qt requiere encabezado `[%General]`, y `--sql` ejecuta sentencias sin cargarlas en el editor de resultados. Se corrigió el primero y se reemplazó el segundo por un proyecto `.sqbpro` con las siete consultas precargadas. El usuario solo abre el acceso y pulsa ejecutar. La base abre en lectura; preferencias locales y chequeo de actualizaciones desactivado.

Verificación: consulta mensual ejecutada en el visor portable con 41 filas y mensaje de finalización sin errores. HTML probado desde archivo local en Chromium: 41 filas, filtro Autopartes con 9 filas, filtro sin resultados, vista de 390 px sin desbordamiento global, sin errores JavaScript ni solicitudes HTTP. Se verificó cambio de importes/nombres al regenerar y escape de texto HTML. Se corrigió además una incompatibilidad del empaquetador con Python 3.9 y se reconstruyó con ese intérprete. El ZIP se mantiene fuera de Git como artefacto local; no se hizo commit, push ni publicación.

## Simplificación posterior: PDF y limpieza

El usuario consideró excesiva la interfaz HTML y aprobó reemplazarla por un PDF. Se retiraron el generador HTML y sus salidas del repositorio activo, el informe Markdown generado y el resumen editorial redundante. El plan de entrega se integró en el plan del ejercicio. Se mantienen diagnóstico y revisión numérica como evidencia del proceso, junto con fuente, SQL y pruebas de carga.

El PDF se genera directamente desde SQLite; ReportLab solo es necesario para producirlo, nunca para el destinatario. La carga SQL sigue usando biblioteca estándar. Se reorganizó el ZIP para no duplicar físicamente base, consultas, planilla y exportaciones: quedan en `codigo/`; el PDF y el acceso al visor están en la raíz. La revisión automática bloqueó la eliminación recursiva de carpetas generadas; se limitó la limpieza a archivos concretos obsoletos. Cachés y extracciones previas siguen ignoradas por Git y no entran en el nuevo ZIP. No se modificaron los ejercicios 1 y 2 ni se realizaron commits o pushes.

Verificación de la entrega PDF: 7/7 pruebas pasan con el entorno de autoría; en Python 3.9 sin librerías PDF pasan las seis pruebas de carga/empaquetado y se omite explícitamente la prueba PDF. Se renderizaron y revisaron visualmente las tres páginas, se comprobó el SHA-256 original, y el ZIP contiene un PDF, una base, una planilla y ningún HTML.


## Informe final conciso
Se reemplazó la presentación SQL por dos páginas con totales mensuales, consultas e incidencias, a partir del ayudamemoria aprobado. El generador sigue consultando SQLite; no se alteraron datos ni reglas. IVA (O20) y seguro (L51) se identifican por nombre.

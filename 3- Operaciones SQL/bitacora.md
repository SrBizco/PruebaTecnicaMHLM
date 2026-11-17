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

# Respuesta al ejercicio 3

Los [totales por importador y mes](resultados/00_respuesta.md) se obtuvieron cargando la planilla en SQLite y ejecutando [esta consulta SQL](sql/01_pagos_mensuales.sql). La tabla completa también está disponible en [CSV](resultados/01_pagos_mensuales.csv).

Se agrupan **pagos declarados por mes de oficialización** porque la fuente no contiene fecha de pago. El total analítico de la muestra es **USD 1.381.267,38**, distribuido en 60 operaciones, 8 importadores y 41 combinaciones importador/mes con registros. No hay registros de mayo: eso no permite afirmar que los pagos reales de ese mes fueran cero.

## Qué se encontró y qué se hizo

| Hallazgo | Tratamiento aplicado |
|---|---|
| Filas 24 y 25 idénticas en las 17 columnas; cada una declara USD 26.495,18. | Se conservaron ambas en la fuente y en la base. Solo la fila 25 se excluyó de los totales; queda vinculada a la 24. |
| `AUTOPARTES SUR S.R.L.` en C53. | Se agrupó por CUIT y se utilizó la denominación más frecuente, `Autopartes Sur S.R.L.`. Se conservó el nombre original. |
| Canal vacío en Q42. | Se almacenó como NULL. La operación permanece incluida porque el canal no es necesario para sumar los pagos. |
| 21 celdas monetarias con residuos de representación binaria. | Se normalizaron a centavos enteros con Decimal y HALF_UP. Los valores XML originales siguen disponibles. |
| CUIT de prueba: 7 de los 8 no superan el control del dígito verificador. | Se conservaron como identificadores de la muestra, sin corregirlos ni excluir operaciones. No se afirma que correspondan a identidades registrales válidas. Hay 52 observaciones de este tipo por fila, no 52 importadores. |
| Diferencias de un centavo en O20 y L51 respecto del modelo HALF_UP reconstruido. | Se clasificaron como detalles menores de redondeo/modelo. No se modificaron IVA, seguro ni pagos. Los otros empates, L38 y L55, quedan hacia arriba: no hay evidencia de una regla uniforme de redondeo hacia abajo. |

**Conciliación:** 61 filas originales = 60 incluidas + 1 copia excluida. USD 1.407.762,56 brutos − USD 26.495,18 duplicados = **USD 1.381.267,38**. Ninguna fila de esta fuente quedó en revisión por datos esenciales inválidos. En las 61 filas, el total registrado coincide con derechos + tasa estadística + IVA.

El detalle auditable está en [incidencias](resultados/02_incidencias.csv) y la conciliación se reproduce con [SQL](sql/03_conciliacion.sql). El XLSX no se modificó. Una inconsistencia futura en fecha o importe esencial queda fuera del agregado con su motivo registrado, sin inventar fechas o pagos cero.

## Coherencia económica y límites

Ningún total pagado supera el FOB: los ratios van de 36,27% a 75,59%. Incluso sumando flete y seguro al pago declarado, los gastos adicionales observados quedan entre 41,97% y 88,45% del FOB. Esto es un control descriptivo; un ratio superior al 100% no sería por sí mismo un error ni justificaría borrar una operación.

FOB + flete + seguro + tributos sí supera el FOB, como es esperable. La planilla no informa todos los costos locales, cantidades, precios de venta o condiciones contractuales: no permite concluir rentabilidad ni validar el valor de mercado de la mercadería. Las tasas reconstruidas son patrones internos de la muestra, no una certificación de su aplicabilidad legal.

Este resumen corresponde al archivo de prueba cuyo SHA-256 es `c90edd30ef38caecc15f062a247f28ac414949a41908efcd7e2b19079a2623b1`. Si se carga otra fuente, deben consultarse los resultados regenerados y revisarse estas conclusiones; no se actualiza automáticamente este resumen editorial.

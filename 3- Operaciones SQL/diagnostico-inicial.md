# Diagnóstico inicial — Operaciones de importación

Revisión del 17/11/2026. Archivo original conservado sin modificar en datos/Operaciones_importacion_prueba.xlsx.
SHA-256: `c90edd30ef38caecc15f062a247f28ac414949a41908efcd7e2b19079a2623b1`.

## Alcance y método

Se leyeron todos los valores y metadatos del XLSX mediante sus partes XML: hoja, celdas, formatos, fórmulas y estructura. No se ejecutó contenido del libro ni se modificó. Esta etapa no crea una base de datos ni consultas SQL.

Una hoja visible, Operaciones, rango A1:Q62: 17 columnas, 61 registros y 60 destinaciones distintas. Fechas de oficialización entre 07/01/2026 y 29/10/2026. Ocho CUIT diferentes, nueve denominaciones literales por una variante de mayúsculas. No hay hojas adicionales, comentarios, vínculos externos, tablas adjuntas ni fórmulas. No se encontraron errores Excel ni filas ocultas. Las fechas son números de serie Excel con formato de fecha, no texto ambiguo.

Columnas: Fecha oficialización, Destinación, Importador, CUIT, Aduana, Subrégimen, Posición NCM, Mercadería, Origen, FOB USD, Flete USD, Seguro USD, Derechos USD, Tasa estadística USD, IVA USD, Total pagado USD, Canal.

## Hallazgos y tratamiento propuesto (aún no aplicado)

| Hallazgo | Evidencia | Tratamiento propuesto |
|---|---|---|
| Duplicado exacto | Filas 24 y 25, destinación 26073IC04001558V, Autopartes Sur, 13/04/2026. Coinciden las 17 columnas; total USD 26.495,18 por fila. | Conservar ambas en la capa original. Incluir la fila 24 en el análisis y marcar la 25 como duplicada excluida. No borrar ni deduplicar por destinación solamente: otro archivo podría tener varias partidas legítimas. |
| Variante del nombre | C53: AUTOPARTES SUR S.R.L.; el mismo CUIT aparece en otras filas como Autopartes Sur S.R.L. | Agrupar por CUIT normalizado como texto; usar nombre canónico y conservar el nombre original. No crear dos importadores. |
| Canal faltante | Q42, destinación 26033IC04001726I. Total USD 18.264,68. | NULL y observación. Incluir la operación en el total: canal no es necesario para esa agregación. No inferir Verde ni sustituir por cero. |
| Precisión de almacenamiento | 21 celdas monetarias tienen residuos binarios, por ejemplo J2 = 9013.540000000001. | Normalizar a centavos con Decimal y redondeo explícito; conservar el valor fuente. No confundir residuos de representación con errores de pago. |
| CUIT de aspecto sintético | Los ocho identificadores siguen el patrón 30-9000000x-1. Un control aritmético preliminar módulo 11 da discrepancia en siete de ocho. | Señalar como identificadores de prueba potencialmente inválidos; conservar y agrupar por su valor. No cambiar dígitos ni excluir la mayoría de la muestra. No implica validación registral de identidad. |
| Mes sin registros | No hay operaciones de mayo de 2026. Sí hay enero-abril y junio-octubre. | Informar ausencia de registros; no afirmar que no hubo pagos reales. Por defecto mostrar meses presentes, sin inventar movimientos. |
| Mercadería y razón social no siempre afines | Ejemplo: Autopartes Sur importa instrumental médico; Insumos Médicos importa remeras. | Observación, no error probado. La razón social no limita las mercaderías que puede importar una empresa. No corregir. |

## Significado de la respuesta

No existe fecha de pago, comprobante ni estado de cobro/pago. Solo podemos atribuir los importes al mes de oficialización, con una aclaración expresa. No debemos afirmar que el dinero efectivamente se pagó en ese mes.

En las 61 filas, a precisión de centavos, Total pagado USD = Derechos USD + Tasa estadística USD + IVA USD. Por lo tanto, usar P como métrica solicitada, sin sumarle FOB, flete o seguro ni volver a sumar los tributos. No equivale al costo integral de importar.

No hay importes vacíos, negativos ni cero en J:P; tampoco discrepancias en esa conciliación. NCM y mercadería mantienen correspondencia interna. Las tasas implícitas de derechos son constantes por NCM en esta muestra; eso no demuestra que las alícuotas sean jurídicamente correctas. No se auditó legislación aduanera, preferencias de origen ni bases imponibles externas.

## Controles numéricos previos (no respuesta SQL final)

Total bruto de P: USD 1.407.762,56. Si se aprueba excluir una copia exacta: USD 1.381.267,38. Diferencia: USD 26.495,18, enteramente atribuible al duplicado. Filas: 61 originales = 60 incluidas + 1 duplicada excluida. Estos controles permitirán conciliar la futura consulta.

Registros por mes, antes de tratar el duplicado: enero 6; febrero 6; marzo 8; abril 8; junio 7; julio 4; agosto 7; septiembre 10; octubre 5. Abril tendrá 7 registros incluidos si se aprueba la propuesta.

## Decisiones pendientes

Confirmar el uso del mes de oficialización como aproximación temporal; excluir solo la copia exacta del agregado; conservar CUIT sintéticos y canal nulo; seleccionar el motor. El resto son propuestas, no modificaciones realizadas sobre los datos.


## Ampliación numérica

Ver revision-numerica.md: se reconstruyeron seguro, derechos, tasa e IVA. Se detectaron diferencias de un centavo en L51 y O20 bajo un modelo decimal explícito. Esto no contradice que P coincida con M+N+O: la suma de importes cargados es correcta, aunque la reconstrucción de sus componentes requiere aclarar redondeos.

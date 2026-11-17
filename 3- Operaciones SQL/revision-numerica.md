# Revisión numérica ampliada

17/11/2026. Se conserva el XLSX original sin cambios. Se revisaron las 61 filas (incluida la duplicada) usando los valores de la fuente, normalización a centavos con Decimal y ROUND_HALF_UP. Las siguientes son reglas inferidas de los datos, no fórmulas declaradas por el autor ni certificación de alícuotas legales.

## Reconstrucción

- CIF reconstruido = FOB + flete + seguro.
- Seguro aparente = 1% del FOB: 60/61 filas coinciden al centavo; excepción L51.
- Derechos = CIF × alícuota aparente por NCM: 61/61 coinciden al centavo.
- Tasa estadística aparente = 3% del CIF: 61/61 coinciden al centavo.
- IVA aparente = 21% × (CIF + derechos registrados + tasa registrada): 60/61 coinciden al centavo; excepción O20.
- Total pagado = derechos registrados + tasa registrada + IVA registrado: 61/61 coinciden exactamente al centavo.

Alícuotas de derechos reconstruidas: 3824.99.89: 14%; 6109.10.00: 35%; 7318.15.00: 16%; 8471.30.12: 16%; 8516.60.00: 20%; 8708.30.90: 18%; 9018.39.99: 8%; 9503.00.99: 35%.

No se puede recalcular el flete sin tarifas, pesos, volúmenes, trayectos o facturas. Tampoco se valida el FOB contra precios de mercado: faltan cantidades, especificaciones y facturas. El ratio flete/FOB observado varía entre 4,51% y 11,99%; es descriptivo, no prueba de razonabilidad de mercado.

## Diferencias y explicación

| Celda | Registrado USD | Reconstruido USD | Diferencia | Lectura |
|---|---:|---:|---:|---|
| O20 (IVA) | 14.434,24 | 14.434,25 | -0,01 | CIF 56.805,37 + derechos 10.224,97 + tasa 1.704,16 = base 68.734,50. El 21% da 14.434,2450; ROUND_HALF_UP produce 14.434,25. Si se calculan derechos y tasa sin redondear antes del IVA, se obtiene 14.434,244517, que redondea a 14.434,24. Compatible con distinta etapa de redondeo; no prueba un error de carga. |
| L51 (seguro) | 263,69 | 263,70 | -0,01 | FOB 26.369,50 × 1% = 263,695. La regla decimal elegida produce 263,70. Puede deberse al método de redondeo o a un seguro real distinto del patrón; no existe fórmula contractual en la planilla para resolverlo. |

Las 21 celdas con residuos de almacenamiento tienen desviaciones de hasta 0,00000000001 USD respecto de sus centavos. Son una cuestión distinta de las diferencias de un centavo detectadas al reconstruir fórmulas.

Propuesta: conservar importes declarados y marcar ambas diferencias como observaciones de redondeo/modelo. No reemplazar valores pagados con importes teóricos; una corrección requiere confirmar fórmula y política de redondeo. Los totales de control del diagnóstico inicial no cambian.

## FOB frente a pagos y gastos adicionales

- Total pagado / FOB: mínimo 36,27% (fila 36), máximo 75,59% (fila 56).
- (Flete + seguro + total pagado) / FOB: mínimo 41,97% (fila 36), máximo 88,45% (fila 56).
- Ninguna fila supera el FOB en ninguno de esos dos indicadores.
- El total que incluye la propia mercadería, FOB + flete + seguro + total pagado, representa entre 141,97% y 188,45% del FOB. Superarlo es esperable porque incluye el FOB más gastos positivos: no debe usarse como detector automático de error.

Mayor ratio, fila 56: Electro Pampa S.A., 28/09/2026, juguetes. FOB 52.504,01; flete 6.225,98; seguro 525,04; derechos 20.739,26; tasa 1.777,65; IVA 17.172,11; total pagado 39.689,02. Gastos adicionales observados 46.440,04. Suma incluyendo mercadería 98.944,05. Los derechos aparentes del 35% del CIF explican parte del peso de los tributos.

No se concluye rentabilidad ni costo integral: faltan precio de venta, gastos locales, honorarios, almacenaje y tratamiento contable/fiscal de los impuestos. Un gasto adicional mayor al FOB sería una alerta para investigar, no una imposibilidad económica ni una razón suficiente para eliminar el registro.

## Límites de esta revisión

Las tasas se infieren y son consistentes dentro de la muestra, pero no se verificó su aplicabilidad legal por fecha, NCM, origen, exenciones o topes. La definición FOB + flete + seguro como aproximación CIF está respaldada por la metodología de comercio exterior del INDEC y la explicación de valor en aduana de ARCA; la planilla no detalla otros ajustes de valoración.

Fuentes conceptuales: https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_comex.pdf ; https://servicioscf.afip.gob.ar/publico/abc/consultas_detalle.aspx?id=11471761 .

No se cargó base de datos, no se ejecutó SQL ni se alteró la fuente. Próxima decisión: aceptar preservación de importes declarados con controles de redondeo separados.

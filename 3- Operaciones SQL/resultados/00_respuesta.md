# Resultados SQL — Operaciones de importación

Importes en USD declarados en la planilla, agrupados por **mes de oficialización**. No existe fecha de pago: estos resultados no certifican cuándo se pagó efectivamente. Los meses sin registros no se completan con ceros.

Generado por `cargar.py` desde las consultas de `sql/`. La base preserva filas y valores originales, y documenta cada tratamiento.

## Cuánto pagó cada importador por mes

| CUIT | Importador | Mes de oficialización | Operaciones | Total declarado USD |
|---|---|---|---:|---:|
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-01 | 1 | 18.928,20 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-02 | 2 | 30.643,55 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-03 | 1 | 42.542,29 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-04 | 2 | 45.198,26 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-06 | 1 | 26.159,06 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-07 | 1 | 27.836,99 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-08 | 1 | 32.512,02 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-09 | 1 | 15.849,52 |
| 30-90000005-1 | Autopartes Sur S.R.L. | 2026-10 | 1 | 3.009,35 |
| 30-90000007-1 | Bazar Norte S.R.L. | 2026-03 | 1 | 2.035,80 |
| 30-90000007-1 | Bazar Norte S.R.L. | 2026-06 | 1 | 25.748,61 |
| 30-90000003-1 | Electro Pampa S.A. | 2026-01 | 1 | 12.085,90 |
| 30-90000003-1 | Electro Pampa S.A. | 2026-04 | 2 | 32.552,03 |
| 30-90000003-1 | Electro Pampa S.A. | 2026-06 | 2 | 42.920,85 |
| 30-90000003-1 | Electro Pampa S.A. | 2026-07 | 1 | 45.420,92 |
| 30-90000003-1 | Electro Pampa S.A. | 2026-08 | 3 | 99.651,45 |
| 30-90000003-1 | Electro Pampa S.A. | 2026-09 | 1 | 39.689,02 |
| 30-90000001-1 | Ferretería Los Andes S.A. | 2026-01 | 1 | 6.446,29 |
| 30-90000001-1 | Ferretería Los Andes S.A. | 2026-02 | 1 | 3.991,17 |
| 30-90000001-1 | Ferretería Los Andes S.A. | 2026-03 | 2 | 41.600,48 |
| 30-90000001-1 | Ferretería Los Andes S.A. | 2026-06 | 2 | 46.532,66 |
| 30-90000001-1 | Ferretería Los Andes S.A. | 2026-08 | 2 | 91.577,93 |
| 30-90000001-1 | Ferretería Los Andes S.A. | 2026-09 | 3 | 111.648,97 |
| 30-90000001-1 | Ferretería Los Andes S.A. | 2026-10 | 1 | 3.002,90 |
| 30-90000008-1 | Insumos Médicos Atlántico S.A. | 2026-02 | 2 | 37.183,70 |
| 30-90000008-1 | Insumos Médicos Atlántico S.A. | 2026-03 | 1 | 39.927,97 |
| 30-90000008-1 | Insumos Médicos Atlántico S.A. | 2026-07 | 1 | 25.226,04 |
| 30-90000008-1 | Insumos Médicos Atlántico S.A. | 2026-08 | 1 | 16.371,04 |
| 30-90000004-1 | Juguetes Patagonia S.A. | 2026-01 | 2 | 58.851,69 |
| 30-90000004-1 | Juguetes Patagonia S.A. | 2026-09 | 2 | 31.180,76 |
| 30-90000004-1 | Juguetes Patagonia S.A. | 2026-10 | 2 | 19.492,30 |
| 30-90000006-1 | Química del Plata S.A. | 2026-01 | 1 | 27.519,02 |
| 30-90000006-1 | Química del Plata S.A. | 2026-03 | 1 | 13.714,43 |
| 30-90000006-1 | Química del Plata S.A. | 2026-04 | 2 | 57.798,38 |
| 30-90000006-1 | Química del Plata S.A. | 2026-07 | 1 | 30.044,88 |
| 30-90000006-1 | Química del Plata S.A. | 2026-09 | 3 | 44.360,36 |
| 30-90000006-1 | Química del Plata S.A. | 2026-10 | 1 | 2.175,93 |
| 30-90000002-1 | Textil Río Bermejo S.R.L. | 2026-02 | 1 | 8.882,85 |
| 30-90000002-1 | Textil Río Bermejo S.R.L. | 2026-03 | 2 | 24.215,60 |
| 30-90000002-1 | Textil Río Bermejo S.R.L. | 2026-04 | 1 | 32.261,68 |
| 30-90000002-1 | Textil Río Bermejo S.R.L. | 2026-06 | 1 | 64.476,53 |

## Conciliación y tratamiento

Los valores monetarios de la conciliación están en **centavos USD**. El bruto cubre las filas normalizables; si hay filas en revisión, no debe interpretarse como total completo de la fuente.

| Control | Resultado |
|---|---:|
| filas_originales | 61 |
| filas_incluidas | 60 |
| duplicadas | 1 |
| en_revision | 0 |
| total_normalizado_bruto_centavos | 140776256 |
| total_analitico_centavos | 138126738 |
| duplicado_centavos | 2649518 |
| totales_no_conciliados | 0 |

| Regla | Observaciones | Filas afectadas | Tratamiento |
|---|---:|---:|---|
| CANAL_FALTANTE | 1 | 1 | Conservar operacion; canal NULL. |
| CUIT_CONTROL | 52 | 52 | Conservar identificador de prueba; control aritmetico, no registral. |
| DUPLICADO_EXACTO | 1 | 1 | Conservar original; excluir copia del agregado. |
| NOMBRE_CANONICO | 1 | 1 | Agrupar por CUIT; nombre mas frecuente, desempate alfabetico. |
| PRECISION_CENTAVOS | 21 | 16 | Normalizar a centavos HALF_UP; conservar lexema original. |
| REDONDEO_MENOR | 2 | 2 | Conservar declarado; comparacion en centavos con modelo inferido, no correccion. |

Una fila puede tener varias observaciones. Los controles de CUIT son aritméticos, no registrales. Los desvíos menores del modelo no reemplazan los importes declarados. Ver [detalle por fila y campo](02_incidencias.csv) y [control numérico](05_control_numerico.csv).

El total declarado corresponde a los tributos registrados; no es el costo integral de importar. La comparación con FOB es descriptiva y no permite concluir rentabilidad ni validar precios de mercado. Ver [ratios por operación](07_fob_y_gastos.csv).

## Fuente

SHA-256: `c90edd30ef38caecc15f062a247f28ac414949a41908efcd7e2b19079a2623b1`.

# Bitácora — Ejercicio 3

## 17/11/2026 — Lectura y diagnóstico

Se inspeccionó la totalidad de la única hoja, formatos y estructura del XLSX. Se preservó una copia idéntica con hash. Hallazgos: duplicado exacto, variante de nombre, canal faltante, residuos decimales y CUIT de apariencia sintética. Se identificó que no existe fecha de pago y que Total pagado suma tres tributos, no el costo de la mercadería. Se propuso SQLite con carga trazable; las reglas siguen pendientes de confirmación. No se creó base de datos ni consultas finales. No se hicieron commits ni pushes.


## Revisión aritmética ampliada

A pedido del usuario, se pasó de conciliar el total a reconstruir cada componente. Se encontraron dos diferencias de centavos frente al modelo inferido, una explicable por la etapa de redondeo. Se propuso preservar importes originales y documentar las diferencias. Se distinguieron tributos, gastos adicionales y desembolso incluyendo mercadería para evitar comparar conceptos distintos con el FOB. Ningún tributo total ni gasto adicional observado supera el FOB.

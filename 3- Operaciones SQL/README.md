# Ejercicio 3 — Operaciones de importación

Solución local con **Python + SQLite**, sin servidor ni paquetes externos. La base y los resultados ya están generados; Python solo es necesario para reproducir la carga. DB Browser for SQLite es opcional para inspeccionarlos visualmente.

## Qué abrir

- [Resultados y decisiones](RESULTADOS.md): respuesta legible a la consigna.
- [Base lista para consultar](resultados/operaciones.sqlite).
- [Pagos por importador y mes](resultados/01_pagos_mensuales.csv): 41 combinaciones con movimientos.
- [Consulta principal](sql/01_pagos_mensuales.sql).
- [Incidencias y tratamiento, celda por celda](resultados/02_incidencias.csv).
- [Conciliación](resultados/03_conciliacion.csv).
- [Fuente preservada](datos/Operaciones_importacion_prueba.xlsx).

**El mes es el de oficialización, no el de pago efectivo:** la fuente no contiene fecha de pago. Se suma `Total pagado USD` tal como fue declarado, sin agregar FOB, flete o seguro. La ausencia de movimientos en un mes no demuestra que los pagos reales hayan sido cero.

## Reproducir en PowerShell

Desde la carpeta de este ejercicio (adaptar la ruta a la ubicación del clon):

```powershell
Set-Location 'C:\Users\Maxi-\PruebaTecnicaMHLM\3- Operaciones SQL'
py -3 .\cargar.py
py -3 -m unittest discover -v
```

Requiere Python **3.9 o posterior** con biblioteca estándar SQLite. No hay `pip install`, entorno virtual ni dependencias del RPA. En equipos sin el lanzador `py`, usar `python` o la ruta del intérprete. Verificar su versión con `python --version`.

El script resuelve sus rutas respecto de `cargar.py`, por lo que también puede invocarse desde otra carpeta. Por defecto reconstruye únicamente sus archivos dentro de `resultados/`; cerrar DB Browser antes de regenerar la base. Repetir la ejecución reemplaza la instantánea, no añade las mismas filas una segunda vez.

Para probar otra copia del mismo formato sin reemplazar los resultados entregados:

```powershell
py -3 .\cargar.py --fuente 'C:\ruta\copia.xlsx' --salida '.\resultado-prueba'
```

El lector está acotado a esta planilla: una hoja `Operaciones`, los mismos 17 encabezados, fechas seriales Excel sin hora y calendario 1900. Admite texto inline y compartido; rechaza fórmulas, errores de Excel y estructuras no previstas. No es un importador universal. Una estructura inválida detiene la carga; una fila con datos esenciales inválidos queda conservada en `originales`, con incidencia y fuera del agregado. Los CSV usan UTF-8 con BOM, separador `;` y punto decimal. Para evitar conversiones automáticas de CUIT/fechas al abrirlos en Excel, importar esas columnas como texto.

## Consultar con DB Browser

1. Abrir `resultados/operaciones.sqlite` desde **Abrir base de datos**.
2. En **Ejecutar SQL**, abrir `sql/01_pagos_mensuales.sql` y ejecutar.
3. Repetir con las otras consultas numeradas. Son consultas de lectura; no ejecutar `esquema.sql` sobre la base entregada, ya que es el esquema de creación utilizado por el cargador.

Puede descargarse DB Browser desde su [sitio oficial](https://sqlitebrowser.org/). No es obligatorio: el cargador ejecuta los mismos archivos SQL y exporta automáticamente sus resultados.

## Organización y trazabilidad

| Objeto | Contenido |
|---|---|
| `fuente` | Nombre, hoja, SHA-256 y versión de reglas de carga. |
| `originales` | Una fila por registro fuente; valores XML originales A:Q como JSON, sin normalizar. El XLSX preserva los formatos y metadatos. |
| `importadores` | CUIT textual y denominación más frecuente; desempate alfabético reproducible. |
| `operaciones` | Valores normalizados, fila de origen y referencia a la copia conservada si es duplicado. |
| `incidencias` | Fila/campo, regla, original, normalizado o referencia del modelo y tratamiento. |
| `incluidas` | Filas normalizables, sin copias exactas. |
| `pagos_mensuales` | Agregación SQL por CUIT y año-mes de oficialización. |
| `reconstruccion` | Control de componentes con tasas inferidas de la muestra; no certificación tributaria. |

Todo importe monetario de la capa analítica es **INTEGER en centavos**. `Decimal` elimina residuos binarios al cargar; no se sustituyen los pagos por cifras teóricas. Los totales USD de la consulta se formatean desde enteros, sin convertir la suma a `REAL`. Solo los porcentajes descriptivos del control FOB usan aproximación decimal.

Consultas adicionales: `02` incidencias; `03` conciliación; `04` duplicados; `05` reconstrucción numérica; `06` resumen de tratamientos; `07` relación entre FOB y gastos observados. Los CSV se generan directamente de estas consultas, sin agregaciones en pandas o Python.

La deduplicación exige igualdad de los 17 valores fuente; compartir una destinación no basta. Se conserva la primera aparición. Una diferencia futura entre el total declarado y sus componentes se señala y conserva para revisión; no se recalcula silenciosamente el pago. Los controles aritméticos de CUIT no validan identidad registral. No se infieren límites legales, rentabilidad ni costos completos de importación.

## Verificación

Las pruebas de integración cubren: conciliación de fuente y agregado, idempotencia, preservación del archivo original, normalización de nombres, canal NULL, conservación de redondeos, agrupación mensual, importes/fechas inválidos, misma destinación con valores distintos y protección de la base anterior ante un XLSX ilegible. Usan bases temporales; no alteran la entrega.

Para el archivo proporcionado: **61 originales = 60 incluidas + 1 duplicada; 0 en revisión**. Bruto USD **1.407.762,56** − duplicado USD **26.495,18** = analítico USD **1.381.267,38**. Las 61 sumas de tributos concilian con su total registrado.

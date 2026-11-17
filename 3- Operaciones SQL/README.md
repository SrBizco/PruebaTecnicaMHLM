# Ejercicio 3 - Operaciones de importación

## Para leer y consultar sin instalar nada

Extraer completo `dist/Entrega-Operaciones-SQL.zip`. Dentro de `3- Operaciones SQL`:

1. Abrir **Informe-operaciones.pdf**: resultados mensuales, inconsistencias y tratamiento.
2. Abrir **CONSULTAR_SQL.cmd**: inicia el visor incluido con la base en lectura y siete consultas preparadas en pestañas.
3. Elegir una pestaña y pulsar **Ejecutar SQL** (botón triangular). Para una consulta propia, modificar el texto y volver a ejecutar.

No hace falta PowerShell ni instalar Python, SQLite o un servidor. El visor es DB Browser for SQLite para Windows x64; el PDF se puede leer en otros sistemas. Extraer el ZIP en una carpeta con permisos de escritura, sin ejecutarlo desde dentro del archivo comprimido. Las preferencias quedan junto al lanzador.

El modo lectura protege la base y permite consultas SELECT propias. Los resultados se pueden exportar desde el visor. Las consultas nuevas no actualizan el PDF: este es una instantánea de la fuente entregada.

## Archivos técnicos

- `datos/Operaciones_importacion_prueba.xlsx`: fuente sin modificar.
- `resultados/operaciones.sqlite`: base consultable y trazabilidad.
- `sql/01_pagos_mensuales.sql`: respuesta principal.
- `sql/02` a `sql/07`: incidencias, conciliación, duplicados, controles numéricos, tratamientos y comparación FOB.
- `resultados/*.csv`: exportaciones técnicas reproducibles, no informe principal.
- `cargar.py`: lectura XLSX, normalización y carga.
- `generar_informe.py`: PDF desde resultados SQL.
- `preparar_entrega.py`: construcción del ZIP portable.

En el repositorio, el PDF se encuentra en `resultados/Informe-operaciones.pdf`. En el ZIP aparece en la raíz, y esta estructura técnica está dentro de `codigo/`, sin duplicar la planilla, la base o los archivos SQL. `Consultas.sqbpro` conserva una copia del texto SQL en las pestañas para facilitar su exploración.

## Reproducir (solo para quien revisa o prepara el código)

La carga requiere Python 3.9+ y solo su biblioteca estándar:

```powershell
py -3 .\cargar.py
py -3 -m unittest discover -v
```

Para regenerar el PDF o construir la entrega, el entorno de autoría necesita ReportLab. **El destinatario no instala esta dependencia.**

```powershell
py -3 -m pip install -r .\requirements-informe.txt
py -3 .\generar_informe.py
py -3 .\preparar_entrega.py
```

La prueba del PDF requiere además `pypdf`; sin él o sin ReportLab se omite esa prueba y se ejecutan las de carga/empaquetado. El empaquetador descarga recursos oficiales fijados por hash la primera vez; después puede ejecutarse con `--offline`. `dist/`, `entrega/` y `.cache-entrega/` no se versionan. No se publica ningún release automáticamente. Procedencia/licencias: [TERCEROS.md](TERCEROS.md).

Los scripts resuelven rutas respecto de su ubicación. La carga reemplaza una instantánea, no acumula lotes. Para evaluar otra copia del mismo formato sin reemplazar la entregada:

```powershell
py -3 .\cargar.py --fuente 'C:\ruta\copia.xlsx' --salida '.\resultado-prueba'
py -3 .\generar_informe.py --base '.\resultado-prueba\operaciones.sqlite' --salida '.\resultado-prueba\Informe.pdf'
```

## Reglas y alcance

El mes es el de **oficialización**, porque no existe fecha de pago. Se suma `Total pagado USD` sin agregar FOB, flete o seguro. Los meses ausentes no se imputan como cero. Importes en centavos INTEGER; Decimal normaliza residuos sin sustituir los pagos por cálculos teóricos.

Se conservan las 61 filas fuente, se excluye solo la copia exacta 25 (vinculada a 24), se agrupa por CUIT y nombre más frecuente, y se mantiene el canal vacío como NULL. Los controles aritméticos de CUIT y las diferencias menores de redondeo no excluyen operaciones. Datos esenciales inválidos quedan en revisión sin imputar cero. La capa original conserva los lexemas XML como JSON; el XLSX conserva formatos y metadatos.

Tablas: `fuente`, `originales`, `importadores`, `operaciones`, `incidencias`. Vistas: `incluidas`, `pagos_mensuales`, `reconstruccion`. El lector se limita a una hoja `Operaciones`, los mismos 17 encabezados y fechas seriales del calendario Excel 1900 sin hora; rechaza fórmulas, errores de Excel y estructuras distintas. No es un importador universal.

Control de esta fuente: **61 originales = 60 incluidas + 1 duplicada**, 0 en revisión; bruto USD **1.407.762,56** menos duplicado USD **26.495,18** = **USD 1.381.267,38**. Los 61 totales coinciden con sus tributos registrados. Los CSV usan UTF-8 con BOM, punto decimal y separador `;`.

El diagnóstico, la revisión numérica y la bitácora se conservan en el repositorio como antecedentes; no se incluyen como múltiples informes en el paquete para el evaluador.

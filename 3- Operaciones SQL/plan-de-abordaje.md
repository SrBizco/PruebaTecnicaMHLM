# Plan propuesto — Ejercicio 3

Estado: plan y tratamientos aprobados por el usuario el 17/11/2026. Implementado con Python + SQLite; instrucciones, base y resultados en README.md y resultados/.

## Opciones

| Opción | Ventajas | Costos o límites |
|---|---|---|
| Python para cargar + SQLite para consultar + DB Browser opcional | Archivo portable, sin servidor; reproducible; permite entregar base y SQL legible. | Importes en centavos INTEGER para evitar REAL aproximado; reglas de tipos y fechas explícitas. |
| PostgreSQL + cliente SQL | Tipos NUMERIC exactos, fechas nativas y buenas restricciones; adecuado si se requiere entorno de servidor. | Instalación, servicio, usuarios y configuración adicionales para 61 registros. |
| pandas solo | Cómodo para explorar y transformar. | No satisface por sí solo el requisito de cargar una base y responder con consultas SQL. Puede complementar, no reemplazar el motor. |

Recomendación: SQLite + carga reproducible en Python (lector XLSX y Decimal), DB Browser opcional para revisar tablas y ejecutar los archivos SQL. pandas no es necesario para este volumen. No elegir una herramienta por complejidad aparente: priorizar trazabilidad y facilidad para el evaluador.

Referencias: https://www.sqlite.org/floatingpoint.html ; https://github.com/sqlitebrowser/sqlitebrowser ; https://www.postgresql.org/docs/current/datatype-numeric.html .

## Flujo posterior a la aprobación

1. Fijar las reglas de diagnóstico-inicial.md y definir qué significa total y mes.
2. Conservar fuente y hash; registrar hoja y fila de procedencia de cada registro.
3. Cargar una tabla original sin pérdidas y sin imponer unicidad sobre Destinación. Registrar lote, hash y valores originales.
4. Generar capa analítica con fechas ISO, CUIT y NCM textuales, nombres normalizados, importes en centavos enteros y Canal nullable. Registrar cada incidencia, regla, valor original/normalizado y si afecta la inclusión.
5. Marcar duplicados exactos, sin borrarlos del original. No rechazar una fila por datos accesorios faltantes. Errores futuros en fecha, importador o importe irían a revisión sin imputar cero.
6. Construir consultas SQL separadas: pagos declarados por importador y año-mes de oficialización; duplicados; faltantes; variantes de nombres; conciliación de tributos y total; resumen del tratamiento.
7. Conciliar 61 registros originales con 60 incluidos y uno excluido; total bruto y analítico con diferencia exacta. Probar que reejecutar la carga no duplique operaciones. Los meses ausentes no representan cero real.
8. Entregar fuente preservada, base .sqlite, scripts de carga, consultas .sql y explicación breve con hallazgos, decisiones y límites. Los resultados finales deben salir de SQL, no de un groupby de pandas.

Todo se mantiene dentro de 3- Operaciones SQL/. La fuente no se modifica; SQLite usa la biblioteca estándar de Python. No commitear ni pushear sin una autorización nueva. El informe y RPA permanecen sin cambios.

## Entrega simplificada aprobada

PDF de lectura y ZIP Windows x64 con DB Browser portable, proyecto de siete consultas y lanzador `.cmd`. Se descarta el informe HTML y cualquier editor propio. El PDF se genera desde SQLite con ReportLab, dependencia exclusiva del entorno de autoría; Mauricio no instala nada para leerlo o consultar. En el paquete hay una sola copia física de fuente, base y SQL dentro de `codigo/`. El proyecto guarda las consultas en pestañas y abre la base en modo lectura con rutas relativas. Los archivos de diagnóstico se conservan como antecedentes en el repositorio, no como informes adicionales en la entrega.

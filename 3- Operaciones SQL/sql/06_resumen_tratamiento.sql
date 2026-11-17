SELECT regla, COUNT(*) AS observaciones, COUNT(DISTINCT fila) AS filas,
       tratamiento FROM incidencias GROUP BY regla, tratamiento ORDER BY regla;

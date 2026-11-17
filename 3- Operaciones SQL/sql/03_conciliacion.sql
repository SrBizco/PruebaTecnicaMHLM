SELECT (SELECT COUNT(*) FROM originales) AS filas_originales,
       (SELECT COUNT(*) FROM incluidas) AS filas_incluidas,
       (SELECT COUNT(*) FROM operaciones WHERE duplicada_de IS NOT NULL) AS duplicadas,
       (SELECT COUNT(*) FROM originales WHERE fila NOT IN (SELECT fila FROM operaciones)) AS en_revision,
       (SELECT SUM(total_centavos) FROM operaciones) AS total_normalizado_bruto_centavos,
       (SELECT SUM(total_centavos) FROM incluidas) AS total_analitico_centavos,
       (SELECT COALESCE(SUM(total_centavos),0) FROM operaciones WHERE duplicada_de IS NOT NULL) AS duplicado_centavos,
       (SELECT COUNT(*) FROM reconstruccion WHERE diferencia_total<>0) AS totales_no_conciliados;
-- Si hay filas en revision, el bruto solo cubre las filas normalizables;
-- no representa un total completo de la fuente.

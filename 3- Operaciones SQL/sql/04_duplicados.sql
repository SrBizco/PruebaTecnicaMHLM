SELECT fila AS fila_excluida, duplicada_de AS fila_conservada,
       destinacion, cuit, fecha, total_centavos
FROM operaciones WHERE duplicada_de IS NOT NULL ORDER BY fila;

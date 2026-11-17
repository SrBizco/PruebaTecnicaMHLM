-- Ratios descriptivos, aqui REAL solo para porcentajes, nunca para pagos.
SELECT fila, destinacion, fob_centavos, total_centavos,
       flete_centavos+seguro_centavos+total_centavos AS adicionales_centavos,
       round(100.0*total_centavos/NULLIF(fob_centavos,0),2) AS pagado_sobre_fob_pct,
       round(100.0*(flete_centavos+seguro_centavos+total_centavos)/NULLIF(fob_centavos,0),2) AS adicionales_sobre_fob_pct
FROM incluidas ORDER BY adicionales_sobre_fob_pct DESC;

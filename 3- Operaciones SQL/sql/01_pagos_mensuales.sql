-- USD declarados, por mes de OFICIALIZACION (no existe fecha de pago).
-- El texto USD se forma desde enteros: nunca SUM sobre REAL.
SELECT cuit, importador, mes AS mes_oficializacion, operaciones,
       total_centavos,
       printf('%d.%02d', total_centavos/100, total_centavos%100) AS total_usd
FROM pagos_mensuales
ORDER BY importador, cuit, mes;

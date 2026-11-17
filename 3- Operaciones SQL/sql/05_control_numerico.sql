SELECT fila, seguro_centavos-seguro_modelo AS diferencia_seguro_centavos,
       derechos_centavos-derechos_modelo AS diferencia_derechos_centavos,
       tasa_centavos-tasa_modelo AS diferencia_tasa_centavos,
       iva_centavos-iva_modelo AS diferencia_iva_centavos, diferencia_total AS diferencia_total_centavos
FROM reconstruccion
WHERE seguro_centavos<>seguro_modelo OR derechos_centavos<>derechos_modelo
   OR tasa_centavos<>tasa_modelo OR iva_centavos<>iva_modelo OR diferencia_total<>0
ORDER BY fila;

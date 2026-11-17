PRAGMA foreign_keys = ON;
CREATE TABLE fuente (
    id INTEGER PRIMARY KEY CHECK(id=1), archivo TEXT NOT NULL,
    sha256 TEXT NOT NULL, hoja TEXT NOT NULL, version_reglas TEXT NOT NULL
);
CREATE TABLE originales (
    fila INTEGER PRIMARY KEY, fuente_id INTEGER NOT NULL REFERENCES fuente(id),
    valores_json TEXT NOT NULL
);
CREATE TABLE importadores (cuit TEXT PRIMARY KEY, nombre TEXT NOT NULL);
CREATE TABLE operaciones (
    fila INTEGER PRIMARY KEY REFERENCES originales(fila),
    fecha TEXT NOT NULL, destinacion TEXT NOT NULL,
    cuit TEXT NOT NULL REFERENCES importadores(cuit), nombre_original TEXT NOT NULL,
    aduana TEXT, subregimen TEXT, ncm TEXT, mercaderia TEXT, origen TEXT,
    fob_centavos INTEGER NOT NULL CHECK(typeof(fob_centavos)='integer' AND fob_centavos>=0),
    flete_centavos INTEGER NOT NULL CHECK(typeof(flete_centavos)='integer' AND flete_centavos>=0),
    seguro_centavos INTEGER NOT NULL CHECK(typeof(seguro_centavos)='integer' AND seguro_centavos>=0),
    derechos_centavos INTEGER NOT NULL CHECK(typeof(derechos_centavos)='integer' AND derechos_centavos>=0),
    tasa_centavos INTEGER NOT NULL CHECK(typeof(tasa_centavos)='integer' AND tasa_centavos>=0),
    iva_centavos INTEGER NOT NULL CHECK(typeof(iva_centavos)='integer' AND iva_centavos>=0),
    total_centavos INTEGER NOT NULL CHECK(typeof(total_centavos)='integer' AND total_centavos>=0),
    canal TEXT, duplicada_de INTEGER REFERENCES operaciones(fila)
);
CREATE TABLE incidencias (
    id INTEGER PRIMARY KEY, fila INTEGER NOT NULL REFERENCES originales(fila),
    regla TEXT NOT NULL, campo TEXT NOT NULL, original TEXT,
    normalizado TEXT, tratamiento TEXT NOT NULL
);
CREATE VIEW incluidas AS SELECT * FROM operaciones WHERE duplicada_de IS NULL;
CREATE VIEW pagos_mensuales AS
SELECT o.cuit, i.nombre AS importador, substr(o.fecha,1,7) AS mes,
       COUNT(*) AS operaciones, SUM(o.total_centavos) AS total_centavos
FROM incluidas o JOIN importadores i ON i.cuit=o.cuit
GROUP BY o.cuit, i.nombre, substr(o.fecha,1,7);

-- Modelos inferidos de esta muestra; NO validan normativa tributaria.
-- Todas las cuentas de dinero permanecen enteras. Para valores positivos,
-- (centavos * porcentaje + 50) / 100 implementa HALF_UP al centavo.
CREATE VIEW reconstruccion AS
WITH bases AS (
 SELECT *, fob_centavos+flete_centavos+seguro_centavos AS cif_centavos,
 CASE ncm WHEN '3824.99.89' THEN 14 WHEN '6109.10.00' THEN 35
 WHEN '7318.15.00' THEN 16 WHEN '8471.30.12' THEN 16
 WHEN '8516.60.00' THEN 20 WHEN '8708.30.90' THEN 18
 WHEN '9018.39.99' THEN 8 WHEN '9503.00.99' THEN 35 END AS tasa_derechos
 FROM operaciones
)
SELECT *, (fob_centavos+50)/100 AS seguro_modelo,
 (cif_centavos*tasa_derechos+50)/100 AS derechos_modelo,
 (cif_centavos*3+50)/100 AS tasa_modelo,
 ((cif_centavos+derechos_centavos+tasa_centavos)*21+50)/100 AS iva_modelo,
 total_centavos-derechos_centavos-tasa_centavos-iva_centavos AS diferencia_total
FROM bases;

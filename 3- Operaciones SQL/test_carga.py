import hashlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'datos/Operaciones_importacion_prueba.xlsx'


class CargaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / 'resultado'

    def run_load(self, source=SOURCE):
        return subprocess.run([sys.executable, str(ROOT / 'cargar.py'),
                               '--fuente', str(source), '--salida', str(self.dest)],
                              capture_output=True, text=True)

    def db(self):
        db = sqlite3.connect(self.dest / 'operaciones.sqlite')
        self.addCleanup(db.close)
        return db

    def changed_source(self, cell, value):
        path = Path(self.tmp.name) / 'alterada.xlsx'
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        with zipfile.ZipFile(SOURCE) as src, zipfile.ZipFile(path, 'w') as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename == 'xl/worksheets/sheet1.xml':
                    sheet = ET.fromstring(data)
                    el = sheet.find(f'.//s:c[@r="{cell}"]/s:v', ns)
                    el.text = value
                    data = ET.tostring(sheet)
                dst.writestr(item, data)
        return path

    def test_reconciliation_and_idempotence(self):
        before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        for _ in range(2):
            result = self.run_load()
            self.assertEqual(result.returncode, 0, result.stderr)
            with sqlite3.connect(self.dest / 'operaciones.sqlite') as snapshot:
                logical = list(snapshot.iterdump())
            snapshot.close()
            csv_data = (self.dest / '01_pagos_mensuales.csv').read_bytes()
            if _ == 0:
                first_logical, first_csv = logical, csv_data
            else:
                self.assertEqual(logical, first_logical)
                self.assertEqual(csv_data, first_csv)
        db = self.db()
        self.assertEqual(db.execute('SELECT COUNT(*) FROM originales').fetchone()[0], 61)
        self.assertEqual(db.execute('SELECT COUNT(*), SUM(total_centavos) FROM incluidas').fetchone(),
                         (60, 138126738))
        self.assertEqual(db.execute('SELECT SUM(total_centavos) FROM operaciones').fetchone()[0], 140776256)
        self.assertEqual(db.execute('SELECT fila, duplicada_de FROM operaciones WHERE duplicada_de IS NOT NULL').fetchall(), [(25, 24)])
        self.assertEqual(db.execute('SELECT COUNT(*) FROM importadores').fetchone()[0], 8)
        self.assertEqual(db.execute('SELECT canal FROM incluidas WHERE fila=42').fetchone(), (None,))
        self.assertEqual(db.execute('SELECT seguro_centavos FROM incluidas WHERE fila=51').fetchone(), (26369,))
        self.assertEqual(db.execute('SELECT iva_centavos FROM incluidas WHERE fila=20').fetchone(), (1443424,))
        self.assertEqual(db.execute('SELECT SUM(total_centavos) FROM pagos_mensuales').fetchone()[0], 138126738)
        self.assertEqual(db.execute("SELECT total_centavos FROM pagos_mensuales WHERE cuit='30-90000005-1' AND mes='2026-04'").fetchone(), (4519826,))
        self.assertEqual(db.execute("SELECT importador FROM pagos_mensuales WHERE cuit='30-90000005-1' AND mes='2026-09'").fetchone(), ('Autopartes Sur S.R.L.',))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM pagos_mensuales WHERE mes='2026-05'").fetchone()[0], 0)
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), before)
        for path in (ROOT / 'sql').glob('[0-9]*.sql'):
            db.execute(path.read_text(encoding='utf-8')).fetchall()
        self.assertTrue((self.dest / '01_pagos_mensuales.csv').exists())
        self.assertTrue((self.dest / '00_respuesta.md').exists())

    def test_missing_amount_quarantined_not_zero(self):
        result = self.run_load(self.changed_source('P2', ''))
        self.assertEqual(result.returncode, 0, result.stderr)
        db = self.db()
        self.assertEqual(db.execute('SELECT COUNT(*) FROM originales').fetchone()[0], 61)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM incluidas WHERE fila=2').fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM incidencias WHERE fila=2 AND regla='DATO_INVALIDO'").fetchone()[0], 1)

    def test_bad_date_quarantined(self):
        result = self.run_load(self.changed_source('A2', 'no-es-fecha'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.db().execute('SELECT COUNT(*) FROM incluidas WHERE fila=2').fetchone()[0], 0)

    def test_same_destination_different_amount_is_not_duplicate(self):
        result = self.run_load(self.changed_source('P25', '26496.18'))
        self.assertEqual(result.returncode, 0, result.stderr)
        db = self.db()
        self.assertEqual(db.execute('SELECT COUNT(*) FROM incluidas').fetchone()[0], 61)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM incidencias WHERE fila=25 AND regla='TOTAL_NO_CONCILIA'").fetchone()[0], 1)

    def test_invalid_workbook_preserves_previous_database(self):
        self.assertEqual(self.run_load().returncode, 0)
        database = self.dest / 'operaciones.sqlite'
        before = database.read_bytes()
        broken = Path(self.tmp.name) / 'roto.xlsx'
        broken.write_text('Esto no es un XLSX', encoding='utf-8')
        self.assertNotEqual(self.run_load(broken).returncode, 0)
        self.assertEqual(database.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

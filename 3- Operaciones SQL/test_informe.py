import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
from cargar import ROOT, build


@unittest.skipUnless(importlib.util.find_spec('reportlab') and importlib.util.find_spec('pypdf'),
                     'Pruebas PDF: requieren reportlab y pypdf en el entorno de autoria.')
class InformeTests(unittest.TestCase):
    def test_pdf_matches_database_and_regenerates(self):
        from generar_informe import generate
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            db = folder / 'operaciones.sqlite'
            pdf = folder / 'informe.pdf'
            build(ROOT / 'datos/Operaciones_importacion_prueba.xlsx', db)
            generate(db, pdf)
            reader = PdfReader(pdf)
            self.assertEqual(len(reader.pages), 2)
            text = '\n'.join(p.extract_text() for p in reader.pages)
            self.assertIn('1.381.267,38', text)
            self.assertIn('CONSULTAR_SQL.cmd', text)
            self.assertIn('O20 (IVA)', text)
            self.assertIn('L51 (seguro)', text)
            self.assertNotIn('Ayudamemoria', text)
            with sqlite3.connect(db) as conn:
                conn.execute('UPDATE operaciones SET total_centavos=total_centavos+100 WHERE fila=2')
                conn.execute("UPDATE importadores SET nombre='Empresa <nueva>' WHERE cuit='30-90000001-1'")
            conn.close()
            generate(db, pdf)
            text = '\n'.join(p.extract_text() for p in PdfReader(pdf).pages)
            self.assertIn('1.381.268,38', text)
            self.assertIn('Empresa <nueva>', text)

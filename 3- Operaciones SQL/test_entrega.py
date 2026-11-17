import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class EntregaTests(unittest.TestCase):
    def test_rejects_modified_vendor_archive_before_packaging(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'dbbrowser.zip').write_bytes(b'archivo alterado')
            result = subprocess.run([sys.executable, str(ROOT / 'preparar_entrega.py'),
                '--cache', str(folder), '--salida', str(folder / 'entrega.zip'), '--offline'],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('SHA-256', result.stderr)
            self.assertFalse((folder / 'entrega.zip').exists())

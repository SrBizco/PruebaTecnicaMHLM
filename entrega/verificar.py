"""Verifica integridad y consulta SQL de la entrega sin abrir cuentas ni ejecutar el RPA."""
import hashlib
from contextlib import closing
import json
from pathlib import Path, PurePosixPath
import re
import sqlite3
import tempfile
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import zipfile
from preparar import OUTPUT, ROOT, RPA_HASH


def verify():
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    assert OUTPUT.with_suffix('.zip.sha256').read_text().split()[0] == digest
    # La carpeta temporal y su limpieza quedan dentro del directorio de entrega.
    base = (ROOT / 'entrega/dist').resolve()
    with tempfile.TemporaryDirectory(prefix='Prueba con espacios ', dir=base) as tmp:
        folder = Path(tmp).resolve()
        assert folder.parent == base
        with zipfile.ZipFile(OUTPUT) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names))
            assert archive.testzip() is None
            for name in names:
                path = PurePosixPath(name)
                assert not path.is_absolute() and '..' not in path.parts
                assert '\\' not in name and ':' not in name
                assert path.parts[0] == 'PruebaTecnicaMHLM'
                assert (folder / name).resolve().is_relative_to(folder)
                assert not {'.git', '.venv', '__pycache__', '.cache-entrega'} & set(path.parts)
            archive.extractall(folder)
        delivery = folder / 'PruebaTecnicaMHLM'
        manifest = json.loads((delivery / 'MANIFIESTO.json').read_text(encoding='utf-8'))
        actual = {p.relative_to(delivery).as_posix() for p in delivery.rglob('*') if p.is_file()}
        assert actual == set(manifest['files']) | {'MANIFIESTO.json'}
        for name, expected in manifest['files'].items():
            assert hashlib.sha256((delivery / name).read_bytes()).hexdigest() == expected, name
        assert manifest['rpa_sha256'] == RPA_HASH
        for required in ('LEEME.txt', 'README.md', '1- informe/informe-mhlm.pdf',
                         '2- RPA Arca/ARCA-RPA.exe', '2- RPA Arca/INSTRUCCIONES.txt',
                         '3- Operaciones SQL/Informe-operaciones.pdf',
                         '3- Operaciones SQL/CONSULTAR_SQL.cmd',
                         '3- Operaciones SQL/visor/DB Browser for SQLite.exe'):
            assert (delivery / required).is_file(), required
        for target in re.findall(r'\]\(([^)]+)\)', (delivery / 'README.md').read_text(encoding='utf-8')):
            if not target.startswith(('https://', 'http://', '#')):
                assert (delivery / unquote(target)).exists(), target
        sql = delivery / '3- Operaciones SQL'
        project = ET.parse(sql / 'Consultas.sqbpro').getroot()
        db = project.find('db')
        assert db.get('readonly') == '1'
        database = (sql / db.get('path')).resolve()
        assert database.is_relative_to(sql.resolve()) and database.is_file()
        queries = project.findall('tab_sql/sql')
        assert len(queries) == 7
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
            assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            for query, source in zip(queries, sorted((sql / 'codigo/sql').glob('[0-9]*.sql'))):
                assert query.text == source.read_text(encoding='utf-8'), source.name
                rows = connection.execute(query.text).fetchall()
                print(source.name, ':', len(rows), 'filas')
        assert (sql / 'codigo/datos/Operaciones_importacion_prueba.xlsx').read_bytes() == (
            ROOT / '3- Operaciones SQL/datos/Operaciones_importacion_prueba.xlsx').read_bytes()
        # Bytes exactos de informes y binario esperados; el empaquetado no los transforma.
        for archived, original in (
            ('1- informe/informe-mhlm.pdf', '1- informe/informe-mhlm.pdf'),
            ('2- RPA Arca/ARCA-RPA.exe', '2- RPA Arca/dist/ARCA-RPA.exe'),
        ):
            assert (delivery / archived).read_bytes() == (ROOT / original).read_bytes(), archived
        with zipfile.ZipFile(ROOT / '3- Operaciones SQL/dist/Entrega-Operaciones-SQL.zip') as source_zip:
            assert (sql / 'Informe-operaciones.pdf').read_bytes() == source_zip.read('3- Operaciones SQL/Informe-operaciones.pdf')
    print('OK: ZIP, hashes, rutas, enlaces, fuentes, PDFs y siete consultas SQL.')


if __name__ == '__main__':
    verify()

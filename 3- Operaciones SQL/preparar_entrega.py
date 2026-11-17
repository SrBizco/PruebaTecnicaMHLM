"""Construye un ZIP listo para usar. Solo el autor necesita Python/internet."""
import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from cargar import ROOT, build, export_queries

ASSETS = [
    ('dbbrowser.zip', 'https://github.com/sqlitebrowser/sqlitebrowser/releases/download/v3.13.1/DB.Browser.for.SQLite-v3.13.1-win64.zip',
     '22375e275ec42d96de1d3b8e9ea4ed86d2a3505c4d0ffcbd1af67aa4003e5e4d'),
    ('dbbrowser-source.zip', 'https://codeload.github.com/sqlitebrowser/sqlitebrowser/zip/refs/tags/v3.13.1',
     'd069ffb40cfbf4785e063610f3b9ee07a52240997929e2411915cff5e204e748'),
    ('Qt-LGPL-3.0.txt', 'https://raw.githubusercontent.com/qt/qtbase/v5.15.2/LICENSE.LGPL3',
     'da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768'),
    ('OpenSSL-LICENSE.txt', 'https://raw.githubusercontent.com/openssl/openssl/OpenSSL_1_1_1w/LICENSE',
     'c32913b33252e71190af2066f08115c69bc9fddadf3bf29296e20c835389841c')
]


def verified_asset(cache, name, url, digest, offline):
    path = cache / name
    if not path.exists():
        if offline:
            raise ValueError('Falta recurso en cache: ' + name)
        request = urllib.request.Request(url, headers={'User-Agent':'OperacionesSQL-Packager/1.0'})
        with urllib.request.urlopen(request, timeout=90) as response:
            content = response.read()
    else:
        content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError('SHA-256 inesperado: ' + name + '. No se empaqueta ni ejecuta.')
    if not path.exists():
        path.write_bytes(content)
    return path


def package(cache, output, offline):
    cache.mkdir(parents=True, exist_ok=True)
    assets = {name: verified_asset(cache, name, url, digest, offline) for name,url,digest in ASSETS}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        parent = Path(tmp)
        delivery = parent / '3- Operaciones SQL'
        delivery.mkdir()
        with zipfile.ZipFile(assets['dbbrowser.zip']) as archive:
            for item in archive.infolist():
                resolved = (delivery / 'visor' / item.filename).resolve()
                if not resolved.is_relative_to((delivery / 'visor').resolve()):
                    raise ValueError('Ruta insegura en el archivo del proveedor.')
            archive.extractall(delivery / 'visor')
        notices = delivery / 'terceros'
        notices.mkdir()
        for name in assets:
            if name != 'dbbrowser.zip':
                shutil.copy2(assets[name], notices / name)
        shutil.copy2(ROOT / 'TERCEROS.md', notices / 'LEEME-LICENCIAS.md')
        # Copia de codigo auditable y reproducible, sin entornos ni caches.
        source = delivery / 'codigo'
        source.mkdir()
        for path in ROOT.glob('*.py'):
            shutil.copy2(path, source / path.name)
        for name in ('README.md','TERCEROS.md','requirements-informe.txt'):
            shutil.copy2(ROOT / name, source / name)
        for folder in ('datos', 'sql'):
            shutil.copytree(ROOT / folder, source / folder)
        # Una sola copia de cada dato/consulta; mismo arbol que el repositorio.
        code_results = source / 'resultados'
        code_results.mkdir()
        build(source / 'datos/Operaciones_importacion_prueba.xlsx', code_results / 'operaciones.sqlite')
        export_queries(code_results / 'operaciones.sqlite', code_results)
        from generar_informe import generate
        generate(code_results / 'operaciones.sqlite', delivery / 'Informe-operaciones.pdf')
        project = ET.Element('sqlb_project')
        ET.SubElement(project, 'db', path='codigo/resultados/operaciones.sqlite', readonly='1', foreign_keys='1')
        window = ET.SubElement(project, 'window')
        ET.SubElement(window, 'main_tabs', open='structure browser pragmas query', current='3')
        sql_tabs = ET.SubElement(project, 'tab_sql')
        for path in sorted((source / 'sql').glob('[0-9]*.sql')):
            ET.SubElement(sql_tabs, 'sql', name=path.stem.replace('_',' ')).text = path.read_text(encoding='utf-8')
        ET.SubElement(sql_tabs, 'current_tab', id='0')
        ET.ElementTree(project).write(delivery / 'Consultas.sqbpro', encoding='utf-8', xml_declaration=True)
        launcher = (
            '@echo off\nsetlocal\n'
            'if not exist "%~dp0visor\\DB Browser for SQLite.exe" goto incompleto\n'
            'if not exist "%~dp0codigo\\resultados\\operaciones.sqlite" goto incompleto\n'
            'if not exist "%~dp0Consultas.sqbpro" goto incompleto\n'
            'start "" /D "%~dp0" "%~dp0visor\\DB Browser for SQLite.exe" '
            '-S "%~dp0preferencias.ini" -R "%~dp0Consultas.sqbpro"\n'
            'exit /b\n:incompleto\necho Extrae el ZIP completo antes de abrir este acceso.\npause\n')
        (delivery / 'CONSULTAR_SQL.cmd').write_bytes(launcher.replace('\n', '\r\n').encode('ascii'))
        (delivery / 'preferencias.ini').write_text(
            '[%General]\nlanguage=es_ES\n[checkversion]\nenabled=false\n', encoding='utf-8')
        (delivery / 'LEEME.txt').write_text(
            'OPERACIONES DE IMPORTACION - ENTREGA WINDOWS X64\n\n'
            '1. Extraer TODO el ZIP a una carpeta con permisos de escritura.\n'
            '2. Abrir Informe-operaciones.pdf para leer los resultados.\n'
            '3. Abrir CONSULTAR_SQL.cmd para ejecutar SQL. No requiere instalar programas.\n\n'
            'El visor abre la base en lectura y deja las siete consultas listas en pestanas.\n'
            'En Ejecutar SQL elegi una consulta y pulsa el boton triangular de ejecucion.\n'
            'Podes modificar el texto o escribir tu propia consulta.\n'
            'Tambien podes abrir codigo/sql. No uses esquema.sql: es para crear la base.\n'
            'La base en lectura permite SELECT y consultas propias sin modificar la entrega.\n'
            'Los importes *_centavos estan en centavos USD; fecha es la de oficializacion.\n\n'
            'El PDF es una instantanea: ejecutar SQL en el visor no lo actualiza.\n'
            'Para reproducir la carga, el codigo Python y la planilla estan en codigo/.\n'
            'Python solo es necesario para regenerar, no para consultar ni leer.\n'
            'Las preferencias del visor se guardan junto a este archivo.\n'
            'No hay servidor ni descargas al usar la entrega. El chequeo de actualizaciones esta desactivado.\n'
            'Visor para Windows x64; el PDF puede abrirse tambien en otros sistemas.\n\n'
            'DB Browser for SQLite es software de terceros sin modificar. Ver terceros/ y visor/licenses/.\n',
            encoding='utf-8-sig')
        manifest = {'assets': [{'name':n,'url':u,'sha256':h} for n,u,h in ASSETS],
                    'files': {str(p.relative_to(delivery)).replace('\\','/'):
                              hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(delivery.rglob('*')) if p.is_file()}}
        (delivery / 'MANIFIESTO.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        temp_zip = parent / 'entrega.zip'
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(delivery.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(parent))
        # Copiar a temporal en el destino y reemplazar solo al finalizar.
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.tmp', delete=False) as handle:
            staged = Path(handle.name)
        try:
            shutil.copyfile(temp_zip, staged)
            staged.replace(output)
        finally:
            staged.unlink(missing_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / '.cache-entrega')
    parser.add_argument('--salida', type=Path, default=ROOT / 'dist/Entrega-Operaciones-SQL.zip')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    try:
        output = package(args.cache, args.salida, args.offline)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(1, str(exc) + '\n')
    print('Entrega preparada: ' + str(output.resolve()))


if __name__ == '__main__':
    main()

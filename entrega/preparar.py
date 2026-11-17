"""Arma la entrega completa desde artefactos locales verificados; no publica nada."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'entrega/dist/PruebaTecnicaMHLM-Completa.zip'
RPA_HASH = '7629ffdd138dbd5b75251cb886c1a170abea8c56ecd61e47247a6f7bde560ecd'
RPA_CODE = (
    'main.py', 'arca_browser.py', 'credential_store.py', 'launcher.py',
    'app_smoke.py', 'requirements.txt', 'requirements-build.txt', 'build.ps1',
    'README.md', 'test_browser_retry.py', 'test_credential_store.py',
    'test_foreground.py', 'test_launcher.py', 'test_portal.py',
)
START = '''PRUEBA TECNICA MHLM - ENTREGA COMPLETA

Extraer TODO el ZIP antes de abrir los programas. Empezar por estos archivos:

1. PERFIL PROFESIONAL
   1- informe/informe-mhlm.pdf
   Las fuentes estan en referencias/ y la version editable en informe-mhlm.md.

2. ROBOT ARCA
   2- RPA Arca/ARCA-RPA.exe
   Windows 10/11 x64. No requiere Python ni Git.
   Necesita Internet; la primera vez descarga Chromium si falta.
   Elegir ingreso manual o un perfil local. El robot consulta Mis servicios.
   Ver INSTRUCCIONES.txt para el acceso, perfiles y cierre de sesion.

3. OPERACIONES DE IMPORTACION
   3- Operaciones SQL/Informe-operaciones.pdf
   Para ejecutar consultas: 3- Operaciones SQL/CONSULTAR_SQL.cmd
   En Ejecutar SQL, elegir una pestana y pulsar el boton triangular.
   Se puede modificar el SQL o escribir consultas SELECT propias.
   El visor abre la base en lectura. No requiere Internet ni instalacion.

El codigo de los ejercicios 2 y 3 esta en sus carpetas codigo/.
La planilla original y la base se conservan dentro del codigo del ejercicio 3.
README.md explica el contenido completo y los limites de cada ejercicio.
Los PDF pueden leerse en otros sistemas; los programas son para Windows x64.
No se incluyen credenciales ni perfiles personales.
'''
RPA_HELP = '''RPA ARCA 1.0.2 - INSTRUCCIONES

1. Abrir ARCA-RPA.exe. Esperar la comprobacion de componentes y, si hace falta,
   la descarga de Chromium. Requiere Internet y espacio en el perfil de Windows.
2. Elegir ingreso manual para escribir los datos en el navegador oficial,
   o usar un perfil guardado en Windows.
3. Para crear un perfil, seleccionar ese modo, pulsar Agregar perfil, ingresar
   alias/CUIT/clave y confirmar el almacenamiento local. Se admiten varios perfiles.
4. Con un perfil seleccionado, el robot completa CUIT, Siguiente, clave e Ingresar.
   Algunas etiquetas de 1.0.2 aun mencionan envio manual; el flujo ya es automatico.
   Resolver personalmente CAPTCHA o verificaciones adicionales si ARCA las pide.
5. El robot abre Mis servicios y muestra las tarjetas de la cuenta activa.
6. Pulsar Cerrar sesion y finalizar. Intenta cerrar la sesion y verificar la salida.
   Si no puede confirmarla, lo informa y cierra el navegador local; no garantiza
   en ese caso el cierre de la sesion del servidor.

No requiere Python ni Git. Windows 10/11 x64.
El programa no esta firmado; Windows puede mostrar una advertencia.
No desactivar las protecciones del equipo.
Los perfiles pertenecen a la cuenta local de Windows y no viajan con el ZIP.
Para borrar uno, usar Eliminar en la app. No cambia la clave fiscal en ARCA.
Ante una descarga fallida, revisar Internet, espacio y permisos, y reabrir.
Ante una lectura fallida, usar Reintentar consulta cuando este disponible.
Codigo, dependencias, pruebas y guia tecnica: codigo/README.md.
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def assemble():
    files = {}

    def add(name, data):
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Ruta insegura: ' + name)
        if name in files:
            raise ValueError('Ruta duplicada: ' + name)
        files[name] = data

    readme = (ROOT / 'README.md').read_text(encoding='utf-8').split('## Organización del repositorio')[0]
    add('README.md', readme.encode('utf-8'))
    add('LEEME.txt', START.encode('utf-8-sig'))
    for name in ('informe-mhlm.pdf', 'informe-mhlm.md'):
        add('1- informe/' + name, (ROOT / '1- informe' / name).read_bytes())
    for name in ('biblia-investigacion.md', 'matriz-fuentes.csv'):
        add('1- informe/referencias/' + name, (ROOT / '1- informe' / name).read_bytes())
    exe = (ROOT / '2- RPA Arca/dist/ARCA-RPA.exe').read_bytes()
    if sha(exe) != RPA_HASH:
        raise ValueError('El EXE no coincide con rpa-v1.0.2 validado. Revisar antes de entregar.')
    add('2- RPA Arca/ARCA-RPA.exe', exe)
    add('2- RPA Arca/INSTRUCCIONES.txt', RPA_HELP.encode('utf-8-sig'))
    for name in RPA_CODE:
        add('2- RPA Arca/codigo/' + name, (ROOT / '2- RPA Arca' / name).read_bytes())

    sql_path = ROOT / '3- Operaciones SQL/dist/Entrega-Operaciones-SQL.zip'
    with zipfile.ZipFile(sql_path) as archive:
        if archive.testzip():
            raise ValueError('El ZIP SQL esta dañado.')
        manifest = json.loads(archive.read('3- Operaciones SQL/MANIFIESTO.json'))
        expected = {'3- Operaciones SQL/' + n: digest for n, digest in manifest['files'].items()}
        actual = {i.filename for i in archive.infolist() if not i.is_dir()}
        if actual != set(expected) | {'3- Operaciones SQL/MANIFIESTO.json'}:
            raise ValueError('Contenido SQL distinto del manifiesto.')
        for name, digest in expected.items():
            data = archive.read(name)
            if sha(data) != digest:
                raise ValueError('Integridad SQL incorrecta: ' + name)
            add(name, data)
        # Evitar entregar una instantanea anterior al codigo, planilla o consultas.
        sql_root = ROOT / '3- Operaciones SQL'
        current = list(sql_root.glob('*.py'))
        current += [sql_root / n for n in ('README.md', 'TERCEROS.md', 'requirements-informe.txt')]
        current += list((sql_root / 'datos').glob('*')) + list((sql_root / 'sql').glob('*.sql'))
        for path in current:
            key = '3- Operaciones SQL/codigo/' + path.relative_to(sql_root).as_posix()
            if files.get(key) != path.read_bytes():
                raise ValueError('Regenerar primero la entrega SQL: ' + str(path))
    package_manifest = {
        'rpa_version': 'rpa-v1.0.2', 'rpa_sha256': RPA_HASH,
        'sql_assets': manifest['assets'],
        'files': {name: sha(data) for name, data in sorted(files.items())},
    }
    add('MANIFIESTO.json', json.dumps(package_manifest, ensure_ascii=False, indent=2).encode('utf-8'))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUTPUT.parent) as temp:
        staged = Path(temp) / OUTPUT.name
        with zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name, data in sorted(files.items()):
                archive.writestr('PruebaTecnicaMHLM/' + name, data)
        with zipfile.ZipFile(staged) as archive:
            if archive.testzip():
                raise ValueError('Fallo de integridad en ZIP completo.')
        staged.replace(OUTPUT)
    OUTPUT.with_suffix('.zip.sha256').write_text(sha(OUTPUT.read_bytes()) + '  ' + OUTPUT.name + '\n', encoding='ascii')
    print(str(OUTPUT))
    print(f'{len(files)} archivos; {OUTPUT.stat().st_size / 1024 / 1024:.1f} MiB')


if __name__ == '__main__':
    assemble()

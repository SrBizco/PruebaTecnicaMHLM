"""Carga reproducible del XLSX de la prueba. Solo biblioteca estandar, Python 3.9+."""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
HEADERS = ['Fecha oficialización', 'Destinación', 'Importador', 'CUIT', 'Aduana',
           'Subrégimen', 'Posición NCM', 'Mercadería', 'Origen', 'FOB USD',
           'Flete USD', 'Seguro USD', 'Derechos USD', 'Tasa estadística USD',
           'IVA USD', 'Total pagado USD', 'Canal']
COLS = 'ABCDEFGHIJKLMNOPQ'
CENT = Decimal('.01')


def read_xlsx(path):
    """Lector deliberadamente acotado al contrato de esta planilla.

    Conserva los lexemas XML; soporta texto inline/compartido. Rechaza formulas,
    errores y estructura distinta para no interpretar silenciosamente otro libro.
    """
    with zipfile.ZipFile(path) as z:
        book = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = book.findall('s:sheets/s:sheet', NS)
        if len(sheets) != 1 or sheets[0].get('name') != 'Operaciones':
            raise ValueError('Se requiere una unica hoja llamada Operaciones.')
        props = book.find('s:workbookPr', NS)
        if props is not None and props.get('date1904') in ('1', 'true'):
            raise ValueError('El lector requiere el calendario Excel 1900.')
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(t.itertext()) for t in
                      ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        rows = []
        sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        for row in sheet.findall('s:sheetData/s:row', NS):
            values = {k: '' for k in COLS}
            for cell in row.findall('s:c', NS):
                address = cell.get('r')
                col = re.sub(r'\d', '', address)
                if col not in values:
                    raise ValueError('Columna fuera del esquema: ' + address)
                if cell.find('s:f', NS) is not None or cell.get('t') == 'e':
                    raise ValueError('Formula o error Excel no admitido: ' + address)
                value = cell.findtext('s:v', default='', namespaces=NS) or ''
                if cell.get('t') == 'inlineStr':
                    value = ''.join(cell.find('s:is', NS).itertext())
                elif cell.get('t') == 's':
                    value = shared[int(value)]
                elif cell.get('t') not in (None, 'n', 'str'):
                    raise ValueError('Tipo de celda no admitido: ' + address)
                values[col] = value
            rows.append((int(row.get('r')), values))
    if not rows or rows[0][0] != 1 or list(rows[0][1].values()) != HEADERS:
        raise ValueError('Los encabezados no coinciden con la planilla esperada.')
    return [(i, v) for i, v in rows[1:] if any(v.values())]


def cents(value):
    number = Decimal(value)
    if not number.is_finite() or number < 0 or number > Decimal('100000000000'):
        raise ValueError('Importe negativo, no finito o fuera de rango.')
    return int(number.quantize(CENT, rounding=ROUND_HALF_UP) * 100)


def iso_date(value):
    serial = Decimal(value)
    if not serial.is_finite() or serial != serial.to_integral_value() or not 61 <= serial <= 2958465:
        raise ValueError('Fecha Excel invalida o con hora no contemplada.')
    return (date(1899, 12, 30) + timedelta(days=int(serial))).isoformat()


def cuit_key(value):
    key = value.strip().replace('-', '').replace(' ', '')
    if not re.fullmatch(r'[0-9]{11}', key):
        raise ValueError('CUIT vacio o sin 11 digitos.')
    return key[:2] + '-' + key[2:10] + '-' + key[10:]


def cuit_check(value):
    digits = value.replace('-', '')
    check = 11 - sum(int(a)*b for a, b in zip(digits[:10], (5,4,3,2,7,6,5,4,3,2))) % 11
    check = 0 if check == 11 else 9 if check == 10 else check
    return check == int(digits[-1])


def build(source, target):
    source_bytes = source.read_bytes()
    rows = read_xlsx(source)
    db = sqlite3.connect(target)
    try:
        db.executescript((ROOT / 'sql/esquema.sql').read_text(encoding='utf-8'))
        with db:
            db.execute('INSERT INTO fuente VALUES (1,?,?,?,?)',
                       (source.name, hashlib.sha256(source_bytes).hexdigest(), 'Operaciones', '1.0'))
            names = defaultdict(Counter)
            for _, v in rows:
                try:
                    if v['C'].strip():
                        names[cuit_key(v['D'])][v['C'].strip()] += 1
                except ValueError:
                    pass
            canonical = {k: sorted(v, key=lambda name: (-v[name], name))[0] for k, v in names.items()}
            db.executemany('INSERT INTO importadores VALUES (?,?)', sorted(canonical.items()))
            seen = {}

            def incident(row, rule, field, original, normalized, treatment):
                db.execute('INSERT INTO incidencias(fila,regla,campo,original,normalizado,tratamiento) VALUES (?,?,?,?,?,?)',
                           (row, rule, field, original, normalized, treatment))

            for row, v in rows:
                raw = json.dumps(v, ensure_ascii=False)
                db.execute('INSERT INTO originales VALUES (?,1,?)', (row, raw))
                try:
                    when, cuit = iso_date(v['A']), cuit_key(v['D'])
                    if not v['B'].strip() or not v['C'].strip():
                        raise ValueError('Destinacion o importador vacio.')
                    amounts = [cents(v[k]) for k in 'JKLMNOP']
                except (ValueError, InvalidOperation, OverflowError) as exc:
                    incident(row, 'DATO_INVALIDO', 'fila', raw, None,
                             'En revision; excluida del agregado, sin imputar cero. ' + str(exc))
                    continue
                # Duplicado solo si coinciden los 17 valores FUENTE, no solo el despacho.
                signature = tuple(v[k] for k in COLS)
                duplicate = seen.get(signature)
                seen.setdefault(signature, row)
                db.execute('INSERT INTO operaciones VALUES (' + ','.join('?' for _ in range(19)) + ')',
                           (row, when, v['B'], cuit, v['C'], v['E'], v['F'], v['G'], v['H'], v['I'],
                            *amounts, v['Q'].strip() or None, duplicate))
                if duplicate is not None:
                    incident(row, 'DUPLICADO_EXACTO', 'fila', str(row), str(duplicate),
                             'Conservar original; excluir copia del agregado.')
                if v['C'] != canonical[cuit]:
                    incident(row, 'NOMBRE_CANONICO', 'C', v['C'], canonical[cuit],
                             'Agrupar por CUIT; nombre mas frecuente, desempate alfabetico.')
                if v['D'] != cuit:
                    incident(row, 'FORMATO_CUIT', 'D', v['D'], cuit, 'Normalizar formato, conservar identidad.')
                if not cuit_check(cuit):
                    incident(row, 'CUIT_CONTROL', 'D', v['D'], cuit,
                             'Conservar identificador de prueba; control aritmetico, no registral.')
                if not v['Q'].strip():
                    incident(row, 'CANAL_FALTANTE', 'Q', v['Q'], None, 'Conservar operacion; canal NULL.')
                for k, amount in zip('JKLMNOP', amounts):
                    if Decimal(v[k]) != Decimal(amount)/100:
                        incident(row, 'PRECISION_CENTAVOS', k, v[k], str(Decimal(amount)/100),
                                 'Normalizar a centavos HALF_UP; conservar lexema original.')
            for row, diff in db.execute('SELECT fila,diferencia_total FROM reconstruccion WHERE diferencia_total<>0').fetchall():
                incident(row, 'TOTAL_NO_CONCILIA', 'P-(M+N+O)', str(diff), None,
                         'Conservar total declarado; revisar diferencia en centavos, sin recalcular pagos.')
            for field, actual, model in [('L','seguro_centavos','seguro_modelo'),
                                         ('M','derechos_centavos','derechos_modelo'),
                                         ('N','tasa_centavos','tasa_modelo'),('O','iva_centavos','iva_modelo')]:
                for row, value, expected in db.execute(f'SELECT fila,{actual},{model} FROM reconstruccion WHERE {actual}<>{model}').fetchall():
                    minor = abs(value-expected) <= 1
                    incident(row, 'REDONDEO_MENOR' if minor else 'MODELO_DIFIERE', field,
                             str(value), str(expected), 'Conservar declarado; comparacion en centavos con modelo inferido, no correccion.')
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('La base no supera los controles de integridad.')
    finally:
        db.close()


def export_queries(database, folder):
    db = sqlite3.connect(database)
    try:
        for path in sorted((ROOT / 'sql').glob('[0-9]*.sql')):
            result = db.execute(path.read_text(encoding='utf-8'))
            headers = [col[0] for col in result.description]
            records = result.fetchall()
            with (folder / (path.stem + '.csv')).open('w', encoding='utf-8-sig', newline='') as out:
                writer = csv.writer(out, delimiter=';')
                writer.writerow(headers)
                writer.writerows(records)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fuente', type=Path, default=ROOT / 'datos/Operaciones_importacion_prueba.xlsx')
    parser.add_argument('--salida', type=Path, default=ROOT / 'resultados')
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    try:
        # Una instantanea por ejecucion. No acumula cargas ni reemplaza la base
        # existente hasta haber construido y validado la nueva.
        with tempfile.TemporaryDirectory(dir=args.salida) as temporary:
            folder = Path(temporary)
            database = folder / 'operaciones.sqlite'
            build(args.fuente, database)
            export_queries(database, folder)
            for path in folder.iterdir():
                path.replace(args.salida / path.name)
    except (OSError, ValueError, InvalidOperation, sqlite3.Error, zipfile.BadZipFile, ET.ParseError) as exc:
        parser.exit(1, 'No se completo la carga: ' + str(exc) + '\n')
    print('Base y resultados SQL generados en: ' + str(args.salida.resolve()))


if __name__ == '__main__':
    main()

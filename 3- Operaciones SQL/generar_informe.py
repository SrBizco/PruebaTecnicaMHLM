"""Genera el PDF desde SQLite. ReportLab solo se requiere al preparar el informe."""
import argparse
import sqlite3
from collections import OrderedDict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def money(value):
    if value is None:
        return 'Sin datos'
    sign = '-' if value < 0 else ''
    whole, fraction = divmod(abs(value), 100)
    return sign + format(whole, ',').replace(',', '.') + ',' + str(fraction).zfill(2)


def generate(database, output):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    db = sqlite3.connect(database)
    try:
        monthly = db.execute((ROOT / 'sql/01_pagos_mensuales.sql').read_text(encoding='utf-8')).fetchall()
        cursor = db.execute((ROOT / 'sql/03_conciliacion.sql').read_text(encoding='utf-8'))
        metrics = dict(zip([c[0] for c in cursor.description], cursor.fetchone()))
        incidents = db.execute((ROOT / 'sql/06_resumen_tratamiento.sql').read_text(encoding='utf-8')).fetchall()
        digest = db.execute('SELECT sha256 FROM fuente').fetchone()[0]
    finally:
        db.close()
    ink, teal, light = colors.HexColor('#173447'), colors.HexColor('#08787d'), colors.HexColor('#edf4f5')
    styles = {
        'title': ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=23, leading=27, textColor=ink, spaceAfter=12),
        'h2': ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=ink, spaceBefore=12, spaceAfter=7),
        'body': ParagraphStyle('Body', fontName='Helvetica', fontSize=10, leading=14, textColor=ink, spaceAfter=8),
        'small': ParagraphStyle('Small', fontName='Helvetica', fontSize=8.4, leading=11, textColor=ink),
        'table': ParagraphStyle('Table', fontName='Helvetica', fontSize=9, leading=12, textColor=ink),
        'num': ParagraphStyle('Num', fontName='Helvetica', fontSize=9, leading=12, textColor=ink, alignment=TA_RIGHT),
    }
    def para(text, style='body'):
        return Paragraph(text, styles[style])
    def grid(data, widths, header=True):
        table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
        commands = [('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),9),
                    ('RIGHTPADDING',(0,0),(-1,-1),9), ('TOPPADDING',(0,0),(-1,-1),5),
                    ('BOTTOMPADDING',(0,0),(-1,-1),5), ('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d8e2e5'))]
        if header:
            commands += [('BACKGROUND',(0,0),(-1,0),light)]
        table.setStyle(TableStyle(commands))
        return table
    story = [para('Operaciones de importación', 'title'),
             para('Ejercicio 3 · Resultados SQL y tratamiento de la planilla', 'small'), Spacer(1,15)]
    groups = OrderedDict()
    for cuit, name, month, count, cents, _ in monthly:
        groups.setdefault((cuit, name), []).append((month,count,cents))
    m = metrics
    story += [para(f'<b>Total declarado incluido: USD {money(m["total_analitico_centavos"])}</b>', 'h2'),
              para(f'{m["filas_incluidas"]} operaciones incluidas · {len(groups)} importadores · {len(monthly)} combinaciones importador/mes.'),
              para('Los importes se agrupan por <b>mes de oficialización</b>: la fuente no informa fecha de pago. '
                   'Se suma la columna “Total pagado USD”, sin agregar FOB, flete o seguro. Los meses sin registros no equivalen a pagos reales de cero.'),
              para('Conciliación', 'h2'),
              para(f'{m["filas_originales"]} filas originales = {m["filas_incluidas"]} incluidas + '
                   f'{m["duplicadas"]} duplicadas + {m["en_revision"]} en revisión.<br/>'
                   f'Bruto normalizable: USD {money(m["total_normalizado_bruto_centavos"])} - '
                   f'copias excluidas: USD {money(m["duplicado_centavos"])} = '
                   f'<b>USD {money(m["total_analitico_centavos"])}</b>.<br/>'
                   f'Totales que no concilian con los tributos registrados: {m["totales_no_conciliados"]}.'),
              para('Inconsistencias y decisiones', 'h2')]
    descriptions = {
        'DUPLICADO_EXACTO': ('Duplicado exacto', 'Se conserva cada fila original; solo se excluye la copia idéntica en los 17 campos. Compartir una destinación no basta para eliminar una operación.'),
        'NOMBRE_CANONICO': ('Variación del nombre', 'Se agrupa por CUIT y se usa la denominación más frecuente. El nombre original queda disponible.'),
        'CANAL_FALTANTE': ('Canal vacío', 'Se registra NULL y se incluye la operación: el canal no es necesario para sumar el pago.'),
        'PRECISION_CENTAVOS': ('Precisión numérica', 'Se normaliza a centavos enteros con Decimal; se conserva el valor fuente. No se confunden residuos binarios con errores de pago.'),
        'CUIT_CONTROL': ('CUIT de prueba', 'Se conservan los identificadores aunque su dígito verificador no coincida. El control es aritmético, no una validación registral.'),
        'REDONDEO_MENOR': ('Redondeos menores', 'Se conservan los importes declarados. Diferencias de un centavo respecto del modelo reconstruido no justifican corregir pagos.'),
    }
    data = [[para('<b>Hallazgo</b>','table'),para('<b>Tratamiento aplicado</b>','table')]]
    for rule,count,rows,treatment in incidents:
        title, description = descriptions.get(rule,(rule,treatment))
        data.append([para(escape(title)+f'<br/>{count} observación(es); {rows} fila(s)','small'),
                     para(escape(description),'table')])
    story += [grid(data,[145,365]), Spacer(1,9),
              para('Una fila puede acumular varias observaciones. El detalle por fila, campo y valor está en la tabla '
                   '<b>incidencias</b> de la base. Si hay filas en revisión, el bruto normalizable no representa la fuente completa.','small'),
              para('Alcance', 'h2'),
              para('La fuente permanece intacta. Las tasas reconstruidas son patrones internos, no una certificación tributaria. '
                   'El total declarado refleja los tributos registrados, no el costo integral de importar; faltan otros gastos y precios de venta para evaluar rentabilidad.','small')]
    # Grupos completos para esta muestra; si cambian los datos, Platypus pagina
    # automaticamente las tablas largas y repite encabezados sin truncar filas.
    items = list(groups.items())
    for start in range(0,len(items),4):
        story += [PageBreak(), para('Pagos mensuales declarados','title'),
                  para('USD · Mes de oficialización · Solo combinaciones con registros','small'), Spacer(1,5)]
        for (cuit,name), records in items[start:start+4]:
            heading = para(escape(name)+f' <font size="9">/ {escape(cuit)}</font>','h2')
            data = [[para('<b>Mes</b>','table'),para('<b>Operaciones</b>','num'),para('<b>Total USD</b>','num')]]
            data += [[para(month,'table'),para(str(count),'num'),para(money(cents),'num')] for month,count,cents in records]
            table = grid(data,[220,115,175])
            table.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),3),
                                       ('BOTTOMPADDING',(0,0),(-1,-1),3)]))
            story.extend([heading,table])
        if start+4 >= len(items):
            story += [Spacer(1,8),para('Cómo comprobar o escribir una consulta','h2'),
                      para('1. Extraer el ZIP completo en una carpeta.<br/>'
                           '2. Abrir <b>CONSULTAR_SQL.cmd</b> con doble clic.<br/>'
                           '3. Elegir una pestaña y pulsar <b>Ejecutar SQL</b> (botón triangular).<br/>'
                           '4. Para una consulta propia, editar el texto y volver a ejecutar.','small'),
                      Spacer(1,5),para('El visor Windows x64 está incluido: no requiere instalar Python ni otras dependencias. '
                           'La base abre en modo lectura; el SQL del editor sigue siendo editable. '
                           'Este PDF es una instantánea y no cambia al ejecutar consultas.','small')]
    def page_footer(canvas, doc):
        canvas.setStrokeColor(teal)
        canvas.line(42, A4[1]-27, A4[0]-42, A4[1]-27)
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(ink)
        canvas.drawString(42,27,'Prueba técnica | Operaciones de importación')
        canvas.drawRightString(A4[0]-42,27,str(doc.page))
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    doc = SimpleDocTemplate(str(output),pagesize=A4,leftMargin=42,rightMargin=42,
                            topMargin=42,bottomMargin=43,title='Operaciones de importación - Resultados SQL',
                            author='Prueba técnica MHLM',subject='Fuente SHA-256: '+digest)
    doc.build(story,onFirstPage=page_footer,onLaterPages=page_footer)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=ROOT/'resultados/operaciones.sqlite')
    parser.add_argument('--salida',type=Path,default=ROOT/'resultados/Informe-operaciones.pdf')
    args=parser.parse_args()
    generate(args.base,args.salida)
    print('PDF generado: '+str(args.salida.resolve()))

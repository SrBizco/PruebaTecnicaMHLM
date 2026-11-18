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
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted

    db = sqlite3.connect(database)
    try:
        monthly = db.execute((ROOT / 'sql/01_pagos_mensuales.sql').read_text(encoding='utf-8')).fetchall()
        cursor = db.execute((ROOT / 'sql/03_conciliacion.sql').read_text(encoding='utf-8'))
        m = dict(zip([c[0] for c in cursor.description], cursor.fetchone()))
        incidents = db.execute((ROOT / 'sql/06_resumen_tratamiento.sql').read_text(encoding='utf-8')).fetchall()
        detail = db.execute('SELECT fila,regla,campo,original,normalizado FROM incidencias ORDER BY fila').fetchall()
        digest = db.execute('SELECT sha256 FROM fuente').fetchone()[0]
    finally:
        db.close()
    ink, teal, light = colors.HexColor('#173447'), colors.HexColor('#08787d'), colors.HexColor('#edf4f5')
    styles = {
        'title': ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=18,leading=22,textColor=ink,spaceAfter=9),
        'h2': ParagraphStyle('h2',fontName='Helvetica-Bold',fontSize=11,leading=14,textColor=teal,spaceBefore=9,spaceAfter=6),
        'body': ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=12,textColor=ink,spaceAfter=7),
        'small': ParagraphStyle('small',fontName='Helvetica',fontSize=8.2,leading=10.5,textColor=ink),
        'code': ParagraphStyle('code',fontName='Courier',fontSize=8,leading=10,textColor=ink,spaceAfter=7),
    }
    def para(text, style='body'):
        return Paragraph(text,styles[style])
    def grid(data,widths,compact=False):
        table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),light),
            ('TOPPADDING',(0,0),(-1,-1),1.2 if compact else 5),
            ('BOTTOMPADDING',(0,0),(-1,-1),1.2 if compact else 5),
            ('LINEBELOW',(0,0),(-1,-1),.25,colors.HexColor('#d8e2e5')),
        ]))
        return table
    importers=len({r[0] for r in monthly})
    story=[para('Operaciones de importación - Resultados SQL','title'),
           para('La planilla se cargó en SQLite para obtener los totales mensuales por importador y documentar las inconsistencias y su tratamiento.'),
           para('<b>Criterio:</b> se suma «Total pagado USD» por CUIT y mes de oficialización, porque la fuente no informa fecha de pago. No se agregan FOB, flete ni seguro.'),
           para(f'<b>Total incluido: USD {money(m["total_analitico_centavos"])}</b> · {m["filas_incluidas"]} operaciones · {importers} importadores.','h2')]
    data=[[para('<b>Importador</b>','small'),para('<b>Mes</b>','small'),para('<b>Total USD</b>','small')]]
    last=None
    for cuit,name,month,count,cents,_ in monthly:
        key=(cuit,name)
        data.append([para(escape(name) if key!=last else '', 'small'),para(month,'small'),para(money(cents),'small')])
        last=key
    table=grid(data,[315,80,116],True)
    story += [table,Spacer(1,7),para('Solo se muestran combinaciones con registros. Un mes sin registros no equivale a pagos reales de cero.','small'),PageBreak(),
              para('Consultas y tratamiento de datos','title'),para('Total por importador y mes','h2'),
              para('Lógica abreviada de la vista <b>pagos_mensuales</b>, consultada por <b>01_pagos_mensuales.sql</b>. Se suma en centavos enteros y se presenta en USD; <b>incluidas</b> excluye las copias exactas.')]
    query="""SELECT i.nombre AS importador, o.cuit,
       substr(o.fecha, 1, 7) AS mes,
       SUM(o.total_centavos) AS total_centavos
FROM incluidas o
JOIN importadores i ON i.cuit = o.cuit
GROUP BY o.cuit, i.nombre, substr(o.fecha, 1, 7)
ORDER BY importador, o.cuit, mes;"""
    story += [Preformatted(query,styles['code']),para('Detalle de inconsistencias: 02_incidencias.sql','h2'),
              Preformatted('SELECT fila, regla, campo, original, normalizado, tratamiento\nFROM incidencias ORDER BY fila, regla, campo;',styles['code']),
              para('Controles de apoyo: <b>03_conciliacion</b> (conteos y totales), <b>04_duplicados</b> (copia y original), <b>05_control_numerico</b> (diferencias de cálculo) y <b>06_resumen_tratamiento</b> (resumen de observaciones).','small'),
              para('Datos observados y tratamiento aplicado','h2')]
    descriptions={
        'DUPLICADO_EXACTO':('Duplicado exacto','Se conservó el original y se excluyó la copia del agregado.'),
        'NOMBRE_CANONICO':('Variación del nombre','Se agrupó por CUIT y se unificó la presentación; se conservó el nombre original.'),
        'CANAL_FALTANTE':('Canal vacío','Se guardó como NULL y se incluyó la operación: no impide sumar el importe.'),
        'CUIT_CONTROL':('CUIT de prueba','Se conservó el identificador y se registró el dígito verificador no coincidente. No se inventaron CUIT corregidos.'),
        'PRECISION_CENTAVOS':('Precisión numérica','Se normalizó a centavos con Decimal, preservando el valor fuente. Los residuos decimales no se interpretan como errores de pago.'),
        'REDONDEO_MENOR':('Redondeo menor','Se conservaron los importes declarados: diferencias de un centavo frente al modelo HALF_UP no justifican corregir pagos.'),
    }
    data=[[para('<b>Dato observado</b>','small'),para('<b>Tratamiento</b>','small')]]
    order={'DUPLICADO_EXACTO':0,'NOMBRE_CANONICO':1,'CANAL_FALTANTE':2,'CUIT_CONTROL':3,'PRECISION_CENTAVOS':4,'REDONDEO_MENOR':5}
    for rule,count,rows,treatment in sorted(incidents,key=lambda r:order.get(r[0],6)):
        title,description=descriptions.get(rule,(rule,treatment))
        matches=[r for r in detail if r[1]==rule]
        label=f'{title}: {count} observación(es), {rows} fila(s).'
        if rule in ('DUPLICADO_EXACTO','NOMBRE_CANONICO','CANAL_FALTANTE') and len(matches)==1:
            row,_,field,original,normalized=matches[0]
            label=f'{title}: fila {row}.'
            if rule=='DUPLICADO_EXACTO':
                description=f'Se conservó la fila {normalized} y se excluyó la copia. Total excluido por duplicados: USD {money(m["duplicado_centavos"])}.'
            if rule=='NOMBRE_CANONICO':
                description=f'Se agrupó por CUIT y se presentó como {normalized}; se conservó el nombre recibido.'
        if rule=='REDONDEO_MENOR':
            fields={'O':'IVA','L':'seguro','M':'derechos','N':'tasa estadística'}
            label='; '.join(f'{r[2]}{r[0]} ({fields.get(r[2],r[2])})' for r in matches)+': redondeo menor.'
            description+=' Valores conservados: '+ '; '.join(f'{r[2]}{r[0]}: USD {money(int(r[3]))}' for r in matches)+'.'
        data.append([para(escape(label),'small'),para(escape(description),'small')])
    story += [grid(data,[192,319]),Spacer(1,8),
              para(f'<b>Comprobación:</b> {m["filas_originales"]} filas originales = {m["filas_incluidas"]} incluidas + {m["duplicadas"]} duplicadas + {m["en_revision"]} en revisión. '
                   f'USD {money(m["total_normalizado_bruto_centavos"])} - USD {money(m["duplicado_centavos"])} = <b>USD {money(m["total_analitico_centavos"])}</b>. '
                   f'Totales normalizados que no coinciden con derechos + tasa estadística + IVA: {m["totales_no_conciliados"]}. La fuente permanece intacta.'),
              para('Una fila puede acumular observaciones. Los controles de cálculo usan un modelo inferido de la muestra, no una validación tributaria. Para ejecutar las consultas incluidas, abrir <b>CONSULTAR_SQL.cmd</b>.','small')]
    def page_footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(ink)
        canvas.drawString(42,23,'Ejercicio 3 · Importes en USD')
        canvas.drawRightString(A4[0]-42,23,str(doc.page))
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(output),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=38,
                      title='Operaciones de importación - Resultados SQL',author='Prueba técnica MHLM',
                      subject='Fuente SHA-256: '+digest).build(story,onFirstPage=page_footer,onLaterPages=page_footer)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=ROOT/'resultados/operaciones.sqlite')
    parser.add_argument('--salida',type=Path,default=ROOT/'resultados/Informe-operaciones.pdf')
    args=parser.parse_args()
    generate(args.base,args.salida)
    print('PDF generado: '+str(args.salida.resolve()))

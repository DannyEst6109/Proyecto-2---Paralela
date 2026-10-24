"""Convierte la guía de exposición en un PDF académico de estudio."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

ROOT = Path(__file__).resolve().parent
FONT_DIRS = [Path('C:/Windows/Fonts'), Path('/usr/share/fonts/truetype/dejavu')]
for folder in FONT_DIRS:
    names = ('times.ttf', 'timesbd.ttf', 'timesi.ttf') if folder.name == 'Fonts' else (
        'DejaVuSerif.ttf', 'DejaVuSerif-Bold.ttf', 'DejaVuSerif-Italic.ttf')
    if all((folder/name).is_file() for name in names):
        for label,name in zip(['Study','StudyBold','StudyItalic'], names):
            pdfmetrics.registerFont(TTFont(label, str(folder/name)))
        break
else:
    raise RuntimeError('Se requieren Times New Roman o DejaVu Serif.')
pdfmetrics.registerFontFamily('Study', normal='Study', bold='StudyBold', italic='StudyItalic', boldItalic='StudyBold')
styles = {
    'h1': ParagraphStyle('h1', fontName='StudyBold', fontSize=17, leading=21, spaceAfter=14),
    'h2': ParagraphStyle('h2', fontName='StudyBold', fontSize=11.5, leading=14, spaceBefore=7, spaceAfter=4, keepWithNext=True),
    'body': ParagraphStyle('body', fontName='Study', fontSize=10.5, leading=13.5, spaceAfter=5),
    'bullet': ParagraphStyle('bullet', fontName='Study', fontSize=10.5, leading=13.5, leftIndent=12, firstLineIndent=-9, spaceAfter=5),
    'code': ParagraphStyle('code', fontName='Study', fontSize=10, leading=13, spaceAfter=8, splitLongWords=True),
    'cell': ParagraphStyle('cell', fontName='Study', fontSize=9, leading=11),
}

def rich(text):
    text=escape(text)
    text=re.sub(r'`([^`]+)`',r'<font color="#333333">\1</font>',text)
    return text

def para(text,style='body'):
    return Paragraph(rich(text),styles[style])

class StudyDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='h1':
            key=f'section-{self.page}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(),key,level=0)

def build_table(lines):
    rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in lines]
    rows=[r for r in rows if not all(re.fullmatch(r':?-+:?',c) for c in r)]
    n=len(rows[0]); widths={2:[204,264],3:[156,156,156],4:[117]*4}.get(n,[468/n]*n)
    cells=[[para(c,'cell') for c in row] for row in rows]
    t=Table(cells,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LINEABOVE',(0,0),(-1,0),.6,colors.black),
        ('LINEBELOW',(0,0),(-1,0),.5,colors.black),
        ('LINEBELOW',(0,1),(-1,-1),.2,colors.HexColor('#aaaaaa')),
        ('LINEBELOW',(0,-1),(-1,-1),.6,colors.black),
    ]))
    return t

source=(ROOT/'Preparacion_Exposicion.md').read_text(encoding='utf-8')
sections=source.split('<!-- page -->')
story=[]
for index,section in enumerate(sections):
    if index: story.append(PageBreak())
    lines=section.strip().splitlines(); i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith('|'):
            table=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                table.append(lines[i]); i+=1
            story += [build_table(table),Spacer(1,8)]
            continue
        if line.startswith('# '): story.append(para(line[2:],'h1'))
        elif line.startswith('## '): story.append(para(line[3:],'h2'))
        elif line.startswith('- '): story.append(para('- '+line[2:],'bullet'))
        else: story.append(para(line,'code' if line.startswith('`') else 'body'))
        i+=1

def footer(c,doc):
    c.setFont('Study',8)
    c.drawString(72,30,'Proyecto 02 - Material de preparación oral')
    c.drawRightString(540,30,str(doc.page))

out=ROOT/'Guia_Exposicion_15_minutos.pdf'
doc=StudyDoc(str(out),pagesize=(612,792),leftMargin=72,rightMargin=72,
             topMargin=50,bottomMargin=48,title='Proyecto 02 - Preparación de la exposición',
             author='Equipo Proyecto 02')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
if doc.page != len(sections):
    raise RuntimeError(f'Desbordamiento: {doc.page} páginas, {len(sections)} previstas.')
print(f'{out}: {doc.page} páginas')

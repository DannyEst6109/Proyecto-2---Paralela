"""Genera el informe a partir del código y las evidencias conservadas en el repositorio.

Ejecutar con Python 3 y ReportLab: python informe/crear_informe.py
No ejecuta ni modifica las mediciones del proyecto.
Diseño académico basado en los informes de referencia proporcionados por el usuario:
Times New Roman, carátula centrada, integrantes en texto y tablas sin rellenos.
"""
from pathlib import Path
from statistics import median
import re
import json
import hashlib
from xml.sax.saxutils import escape

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                               Table, TableStyle, Image, Preformatted)
from reportlab.graphics.shapes import Drawing, Rect, Line, Polygon, String

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'informe/Informe_Proyecto_02.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
FONT_DIRS = [Path('C:/Windows/Fonts'), Path('/usr/share/fonts/truetype/dejavu')]
for folder in FONT_DIRS:
    normal = folder / ('times.ttf' if folder.name == 'Fonts' else 'DejaVuSerif.ttf')
    bold = folder / ('timesbd.ttf' if folder.name == 'Fonts' else 'DejaVuSerif-Bold.ttf')
    italic = folder / ('timesi.ttf' if folder.name == 'Fonts' else 'DejaVuSerif-Italic.ttf')
    mono = folder / ('consola.ttf' if folder.name == 'Fonts' else 'DejaVuSansMono.ttf')
    if normal.exists():
        pdfmetrics.registerFont(TTFont('Body', str(normal)))
        pdfmetrics.registerFont(TTFont('BodyBold', str(bold)))
        pdfmetrics.registerFont(TTFont('BodyItalic', str(italic)))
        pdfmetrics.registerFont(TTFont('Code', str(mono)))
        break
else:
    raise RuntimeError('Se requieren Times New Roman/Consolas o DejaVu Serif/Mono.')
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='BodyItalic', boldItalic='BodyBold')
GREEN = colors.black
INK = colors.black
PALE = colors.white
GRAY = colors.HexColor('#333333')
WIDTH = 468
ST = {
    'body': ParagraphStyle('body', fontName='Body', fontSize=12, leading=15.2,
                           textColor=INK, alignment=TA_JUSTIFY, spaceAfter=9),
    'small': ParagraphStyle('small', fontName='Body', fontSize=10, leading=12,
                            textColor=INK, spaceAfter=6),
    'cell': ParagraphStyle('cell', fontName='Body', fontSize=9.5, leading=11.2, textColor=INK),
    'headcell': ParagraphStyle('headcell', fontName='BodyBold', fontSize=9.5,
                               leading=11.2, textColor=INK),
    'h1': ParagraphStyle('h1', fontName='BodyBold', fontSize=14, leading=18,
                         textColor=GREEN, spaceAfter=12),
    'h2': ParagraphStyle('h2', fontName='BodyBold', fontSize=12, leading=15,
                         textColor=GREEN, spaceBefore=9, spaceAfter=7),
    'caption': ParagraphStyle('caption', fontName='BodyItalic', fontSize=9, leading=10.5,
                              textColor=GRAY, spaceBefore=4, spaceAfter=6),
    'code': ParagraphStyle('code', fontName='Code', fontSize=7.5, leading=10,
                           textColor=INK, backColor=PALE, borderPadding=8, spaceAfter=10),
    'cover': ParagraphStyle('cover', fontName='Body', fontSize=12, leading=17,
                            alignment=TA_CENTER, textColor=INK, spaceAfter=3),
    'subtitle': ParagraphStyle('subtitle', fontName='Body', fontSize=12, leading=17,
                               alignment=TA_CENTER, textColor=INK, spaceAfter=4),
    'title': ParagraphStyle('title', fontName='BodyBold', fontSize=15, leading=20,
                            alignment=TA_CENTER, textColor=INK, spaceAfter=6),
}
story = []
pages = []

def p(text, kind='body'):
    return Paragraph(text, ST[kind])

def add(text, kind='body'):
    story.append(p(text, kind))

def page(title, label=None):
    if pages:
        story.append(PageBreak())
    pages.append(label or title)
    if title:
        add(title, 'h1')

def table(headers, rows, widths=None):
    if widths is not None and abs(sum(widths)-WIDTH) > .01:
        raise ValueError('La tabla excede el ancho de composición')
    data = [[p(escape(str(x)), 'headcell') for x in headers]]
    data += [[p(escape(str(x)), 'cell') for x in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, 0), (-1, 0), .7, INK),
        ('LINEBELOW', (0, 0), (-1, 0), .5, INK),
        ('LINEBELOW', (0, 1), (-1, -1), .2, colors.HexColor('#AAAAAA')),
        ('LINEBELOW', (0, -1), (-1, -1), .7, INK),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

def code(text):
    story.append(Preformatted(text.strip(), ST['code']))

def shot(relative, height=390):
    path = ROOT / relative
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w, h = im.size
    scale = min(WIDTH / w, height / h)
    story.append(Image(str(path), w * scale, h * scale, hAlign='CENTER'))

def box(d, x, y, w, h, text, fill=PALE, size=8):
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=INK, strokeWidth=.6))
    ls = text.split('\n')
    for i, line in enumerate(ls):
        d.add(String(x+w/2, y+h/2+(len(ls)-1)*5-i*10-3, line,
                     fontName='Body', fontSize=size, textAnchor='middle', fillColor=INK))

def arrow(d, x1, y1, x2, y2):
    d.add(Line(x1, y1, x2, y2, strokeColor=GREEN, strokeWidth=1))
    dx, dy = x2-x1, y2-y1
    n = max((dx*dx+dy*dy)**.5, 1)
    ux, uy = dx/n, dy/n
    d.add(Polygon([x2,y2,x2-6*ux+3*uy,y2-6*uy-3*ux,x2-6*ux-3*uy,y2-6*uy+3*ux],
                  fillColor=GREEN, strokeColor=GREEN))

def flow(items):
    h = len(items)*57
    d = Drawing(WIDTH, h)
    for i, text in enumerate(items):
        y = h-45-i*57
        box(d, 34, y, 400, 39, text)
        if i:
            arrow(d, 234, y+57, 234, y+39)
    story.append(d)

def caption(text):
    add(text, 'caption')

data=json.loads((ROOT/'evidencias/inciso2/resultados.json').read_text(encoding='utf-8'))
metadata=data['metadata']
all_runs=data['runs']
runs=[r for r in all_runs if r['phase']=='principal']
cutoff=metadata['corte']
reps=metadata['repeticiones']
date=metadata['fecha'][:10]
cpu_match=re.search(r'Model name:\s*(.+)', metadata['cpu'])
cpu_name=cpu_match[1].strip() if cpu_match else 'Consultar metadata.cpu en resultados.json'
assert len(runs)==9*reps, 'Faltan mediciones principales'
assert len(all_runs)==12*reps, 'Falta control exhaustivo'
assert metadata.get('completo'), 'La serie debe finalizar correctamente'
test_log=(ROOT/'evidencias/pruebas/ultima_prueba.txt').read_text(encoding='utf-8')
assert 'Código de salida: 0' in test_log, 'Las pruebas finales deben pasar'


def selection(tag, mode):
    return [r for r in runs if r['tag']==tag and r['mode']==mode]

def med(tag, mode, field='time'):
    return median(r[field] for r in selection(tag,mode))

keys = {'a':123456, 'b':2**54, 'c':2**54+1}

validation=json.loads((ROOT/'evidencias/pruebas/resultado_final.json').read_text(encoding='utf-8'))
assert validation['codigo']==0, 'La última suite debe aprobar'
for source_set in (metadata['fuentes_sha256'], validation['fuentes_sha256']):
    for name,digest in source_set.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, f'Fuentes sin evidencia vigente: {name}'

page('', 'Carátula')
story.append(Spacer(1, 18))
add('<b>Universidad del Valle de Guatemala</b>', 'cover')
for line in ['Facultad de Ingeniería',
             'Computación Paralela y Distribuida - Semestre 2, 2026']:
    add(line, 'cover')
story.append(Spacer(1, 44))
shot('informe/recursos/escudo_uvg.png', 145)
story.append(Spacer(1, 46))
add('Proyecto 02', 'title')
add('Búsqueda de claves AES-128 con Open MPI', 'subtitle')
add('Distribución estática y búsqueda por familias', 'cover')
story.append(Spacer(1, 42))
add('<b>Integrantes:</b>', 'cover')
for line in ['Daniel Estrada - 20853', 'Andre Pivaral - 23574', 'Sebastian Estrada - 21405']:
    add(line, 'cover')
story.append(Spacer(1, 42))
add('Guatemala, 28 de octubre de 2026', 'cover')

page('Índice')
index_position = len(story)
story.append(Spacer(1, 1))
add('Resumen', 'h2')
add('Se implementaron el cifrado y descifrado de archivos, una búsqueda secuencial y dos '
    'versiones MPI. La base redujo el tiempo frente a la secuencial en las búsquedas '
    'completadas. La alternativa encontró las claves grandes al priorizar potencias '
    'de dos y sus vecinos, pero fue más lenta en la clave pequeña y en el control sin familias.')
add('El informe reúne los resultados de 60 ejecuciones, las pruebas funcionales y las siete '
    'capturas de evidencia. Los recorridos exhaustivos de las claves grandes terminaron '
    'por límite de tiempo; sus estimaciones se presentan aparte.')

page('1. Introducción y fundamentos')
add('El proyecto estudia cómo el reparto de trabajo y el orden de búsqueda afectan el tiempo '
    'necesario para recuperar una clave AES-128. Parte del Laboratorio 03 y cumple las '
    'actividades del enunciado: procesar archivos, probar tres claves con cuatro procesos '
    'MPI y comparar una estrategia base con una alternativa [7].')
add('Objetivo y alcance', 'h2')
add('Implementar y evaluar una búsqueda paralela que identifique la clave mediante la frase '
    '«es una prueba de». Se comparan tiempo, intentos y speedup frente a una referencia '
    'secuencial. El experimento usa enteros de hasta 64 bits convertidos en claves de '
    '16 bytes; estudia ese subconjunto, sin recorrer las 2^128 claves de AES-128.')
add('Conceptos necesarios', 'h2')
table(['Concepto', 'Aplicación en el proyecto'], [
    ('AES-128', 'Cifrador simétrico con bloques y clave de 128 bits [1]. Los ocho bytes iniciales de la clave se dejan en cero; los últimos ocho contienen el entero en big endian.'),
    ('ECB y PKCS#7', 'ECB procesa cada bloque por separado [2]. El relleno completa el último bloque y añade un bloque si la longitud ya es múltiplo de 16 [3].'),
    ('Búsqueda por fuerza bruta', 'Cada candidata descifra el mensaje y se busca la frase requerida. Un acierto se confirma con HMAC-SHA256 para descartar falsos positivos.'),
    ('Open MPI', 'Cada proceso prueba candidatas con su propia memoria. La base comparte resultados por ronda; la alternativa solicita bloques y envía avisos de hallazgo [4-6].'),
], [108,360])
add('NIST precisa: <i>«Each of them transforms data in blocks of 128 bits»</i>.<super>1</super> '
    'La longitud del bloque se mantiene aunque las claves del experimento procedan de enteros.', 'small')
add('Cómo se mide la mejora', 'h2')
code('S = T_secuencial / T_MPI       E = S / 4\nR = intentos / tiempo          G = T_base / T_alternativa')
add('S es el speedup y E la eficiencia con cuatro procesos. G compara las dos estrategias: '
    'un valor mayor que uno favorece a la alternativa. Cambiar el orden de candidatas '
    'también cambia el trabajo hasta el hallazgo; por eso G no mide solo paralelismo.', 'small')

page('2. Archivos, cifrado y validación')
add('El programa aes_archivo carga hasta 4096 bytes, cifra con una clave decimal y recupera '
    'el contenido con la misma clave. Lee y escribe bytes para conservar UTF-8 y saltos '
    'de línea. Las salidas se crean en modo exclusivo para proteger archivos existentes.')
flow(['Leer archivo y validar operación, rutas, clave y tamaño',
      'Cifrar: AES-128-ECB + PKCS#7; calcular HMAC\nDescifrar: verificar HMAC; recuperar y validar bytes',
      'Guardar en un archivo nuevo\nAnte un error: informar y eliminar la salida parcial'])
caption('Figura 1. Flujo del inciso 1. Fuente: aes_archivo.c y aes_comun.h.')
add('Formato y claves', 'h2')
add('AESECB2 guarda cuatro líneas: versión, longitud original, cifrado hexadecimal y '
    'etiqueta HMAC-SHA256. La etiqueta cubre versión, longitud y cifrado; la clave MAC '
    'se deriva con el dominio Proyecto02/AESECB2/HMAC-SHA256. El archivo se autentica '
    'antes de descifrar [8]. El formato GCM del laboratorio se conserva como antecedente separado.')
table(['Caso', 'Clave decimal', 'Clave AES de 16 bytes (hexadecimal)'], [
    (tag+')', str(key), key.to_bytes(16,'big').hex()) for tag,key in keys.items()
], [34,144,290])
add('Verificación', 'h2')
add('cmp y SHA-256 comprueban que el archivo recuperado coincide byte a byte con el original. '
    'La suite incluye un vector AES-128-ECB, 24 casos de archivos y 75 de búsqueda. '
    'Se prueban archivos vacíos, límites de tamaño, claves incorrectas, contenido alterado, '
    'rangos extremos, tiempo agotado y hallazgos simultáneos. El registro final terminó con código 0.')
code('./proyecto02/build/aes_archivo cifrar entrada.txt salida.aes 123456\n./proyecto02/build/aes_archivo descifrar salida.aes recuperado.txt 123456\ncmp entrada.txt recuperado.txt')

page('3. Estrategia base: lotes estáticos')
add('El proceso 0 valida el archivo y difunde los parámetros y el cifrado. Con cuatro procesos '
    'y lotes de B = 65536 candidatas, cada ronda entrega un lote disjunto a cada proceso. '
    'La referencia secuencial recorre el mismo intervalo en orden ascendente.')
table(['Ronda', 'P0', 'P1', 'P2', 'P3'], [
    ('0', '[0, B)', '[B, 2B)', '[2B, 3B)', '[3B, 4B)'),
    ('1', '[4B, 5B)', '[5B, 6B)', '[6B, 7B)', '[7B, 8B)'),
], [40,107,107,107,107])
code('inicio(p, r) = offset + (4*r + p)*B\nfin(p, r) = min(inicio + B, offset + limite)')
flow(['P0 carga y valida; MPI_Bcast comparte datos\nMPI_Barrier sincroniza el inicio del reloj',
      'Cada proceso descifra su lote y busca la frase\nSi aparece, confirma el HMAC y guarda la candidata',
      'MPI_Allreduce(MIN) acuerda el hallazgo\nSin acierto: acordar tiempo agotado o avanzar de ronda',
      'Al hallar o terminar el rango/tiempo: reducir estadísticas\nP0 muestra el resultado; todos finalizan MPI'])
caption('Figura 2. Flujo de la base. Las reducciones mantienen el mismo estado entre procesos [4].')
add('Comportamiento esperado', 'h2')
add('El reparto requiere poca gestión, pero la parada espera al cierre de la ronda. '
    'Para 123456, P1 encuentra la clave en la primera ronda mientras los demás '
    'completan sus lotes. El trabajo adicional explica por qué un aumento de '
    'claves por segundo no se traduce en la misma reducción del tiempo de búsqueda.')
add('El valor UINT64_MAX indica ausencia de hallazgo. Los rangos que desbordan se '
    'rechazan antes de buscar. Los estados son: 0 hallada, 1 entrada/error, '
    '2 rango agotado y 3 tiempo agotado.', 'small')

page('4. Alternativa: familias y avisos')
add('La alternativa genera candidatas por familias y asigna sus bloques de forma dinámica. '
    'Cada proceso empieza por la familia de su rank y, al agotarla, sigue en orden circular. '
    'Las claves objetivo nunca se reciben como argumento de búsqueda.')
table(['Familia', 'Candidatas'], [
    ('F0. Valores bajos', 'Enteros en [0, 2^24). Incluye 123456.'),
    ('F1. Patrones', 'Fechas numéricas, dígitos repetidos, potencias de 2 y 10 con vecinos y constantes. Incluye 2^54 y 2^54 + 1.'),
    ('F2. ASCII', 'Cadenas de 1 a 5 caracteres de [a-z0-9], empaquetadas como entero big endian.'),
    ('F3. Barrido', 'Intervalo configurable. Por defecto comienza en 2^24 y contiene 2^63 candidatas.'),
], [110,358])
d = Drawing(WIDTH, 115)
box(d, 0, 70, WIDTH, 35, 'P0 expone cuatro contadores RMA: uno por familia')
for i in range(4):
    box(d, i*118, 5, 112, 35, f'Proceso {i}\nPrefiere F{i}')
    arrow(d, i*118+56, 40, i*118+56, 70)
story.append(d)
caption('Figura 3. MPI_Fetch_and_op reserva un bloque exclusivo; MPI_Win_flush completa la operación [5].')
code('publicar recepción de aviso; sincronizar e iniciar reloj\nmientras haya trabajo y no haya aviso ni tiempo agotado:\n    elegir familia; reservar bloque con incremento atómico\n    para cada candidata del bloque:\n        descifrar, buscar frase y confirmar HMAC\n        si acierta: enviar clave/familia con MPI_Issend; salir\n        cada 4096 intentos: consultar MPI_Test y reloj\n    consultar aviso y reloj entre bloques\nacordar clave y estado; reducir tiempo e intentos\ndrenar avisos hasta completar envíos; liberar recursos')
add('Cada proceso deja un MPI_Irecv abierto y sondea el aviso de hallazgo [6]. '
    'El consenso final resuelve aciertos simultáneos. Los índices no se repiten dentro '
    'de una familia, aunque distintas familias pueden producir la misma candidata. '
    'El modo -e conserva solo F3 y permite comparar la distribución sin priorizar patrones.', 'small')

page('5. Método y resultados')
add(f'Se registraron {len(all_runs)} ejecuciones el {date}: cinco por combinación de '
    'programa y caso, incluido un control. Las versiones MPI usaron cuatro procesos. '
    'Se informa la mediana; el Anexo 2 reúne las muestras y resultados.md conserva su dispersión.')
table(['Condición', 'Configuración registrada'], [
    ('Entrada', 'Esta es una prueba de proyecto 2; frase: es una prueba de.'),
    ('Entorno', f'WSL; {cpu_name}. GCC 15.2.0, OpenSSL 3.5.5 y Open MPI 5.0.10; C11 y -O2.'),
    ('Serie principal', f'Base/secuencial: [0, 2^56), sin offset cercano a la clave. Lote 65536; corte de {cutoff} s en recorridos largos.'),
    ('Control', 'Clave 750123; rango [0, 1000000); lote 4096; alternativa con -e.'),
], [94,374])
add('Tiempo hasta hallar la clave', 'h2')
table(['Caso / clave', 'Secuencial (s)', 'Base MPI (s)', 'Alternativa (s)'], [
    (f'{tag}) {keys[tag]}', f'{med(tag,"secuencial"):.6f}' if tag=='a' else 'Sin hallazgo*',
     f'{med(tag,"base"):.6f}' if tag=='a' else 'Sin hallazgo*', f'{med(tag,"alternativa"):.6f}')
    for tag in keys
], [150,106,106,106])
caption('* En b) y c), secuencial y base finalizaron por tiempo con código 3. El intervalo sí incluye las claves.')
add('Duración de las búsquedas interrumpidas', 'h2')
table(['Caso / programa', 'Tiempo (s)', 'Intentos (mediana)', 'Claves/s'], [
    (f'{tag}) {mode}', f'{med(tag,mode):.6f}', f'{med(tag,mode,"attempts"):,.0f}',
     f'{med(tag,mode,"rate"):,.0f}')
    for tag in ['b','c'] for mode in ['secuencial','base']
], [115,90,143,120])
add('Los relojes miden la búsqueda: excluyen lectura, lanzamiento MPI y reporte. '
    'La alternativa incluye el consenso de clave y excluye el drenaje posterior. '
    'El entorno WSL comparte recursos; las cinco muestras describen esta ejecución, '
    'sin establecer escalabilidad entre máquinas.', 'small')

page('6. Análisis del rendimiento')
control=[r for r in all_runs if r['phase']=='control']
def ctrl(mode,field='time'):
    return median(r[field] for r in control if r['mode']==mode)
seq,base,alt=(med('a',mode) for mode in ['secuencial','base','alternativa'])
table(['Comparación medida', 'S base/sec.', 'E base', 'G base/alt.'], [
    ('a) Clave 123456', f'{seq/base:.3f}', f'{100*seq/base/4:.1f} %', f'{base/alt:.3f}'),
    ('Control: clave 750123', f'{ctrl("secuencial")/ctrl("base"):.3f}',
     f'{100*ctrl("secuencial")/ctrl("base")/4:.1f} %', f'{ctrl("base")/ctrl("alternativa"):.3f}'),
], [180,96,96,96])
add(f'Para a), S = {seq:.6f} / {base:.6f} = <b>{seq/base:.3f}</b>. '
    'La base fue más rápida que la secuencial y que la alternativa. Esta última '
    'dedica parte del trabajo a otras familias y añade coordinación. Esos costos '
    'pueden explicar su mayor tiempo en una búsqueda tan corta.')
add('El control sin heurísticas', 'h2')
table(['Programa', 'Mediana (s)', 'Mínimo (s)', 'Máximo (s)'], [
    (mode, f'{ctrl(mode):.6f}', f'{min(r["time"] for r in control if r["mode"]==mode):.6f}',
     f'{max(r["time"] for r in control if r["mode"]==mode):.6f}')
    for mode in ['secuencial','base','alternativa']
], [150,106,106,106])
add('Con el mismo rango y lote, la base vuelve a obtener el menor tiempo. '
    'La asignación dinámica y los avisos anticipados no bastaron para superarla. '
    'El número de intentos puede variar por la asignación y el momento de parada; '
    'el control compara esas políticas sin el efecto de las familias.')
add('Por qué las claves grandes se encuentran pronto', 'h2')
add('2^54 y 2^54 + 1 aparecen cerca dentro de la familia de potencias y vecinos. '
    'Su ventaja proviene del orden de candidatas. El costo de AES por intento '
    'no crece con el valor decimal de la clave; crece el número de intentos '
    'necesarios para alcanzarla en un recorrido ascendente.')
add('Proyección del recorrido exhaustivo', 'h2')
table(['Caso', 'Secuencial (años)', 'Base MPI (años)'], [
    (tag+')', f'{(keys[tag]+1)/med(tag,"secuencial","rate")/31557600:.1f}',
     f'{(keys[tag]+1)/med(tag,"base","rate")/31557600:.1f}') for tag in ['b','c']
], [80,194,194])
add('Se calcula T = (clave + 1) / mediana(claves/s), con tasa constante y año de '
    '365,25 días. Es una extrapolación desde cinco segundos de búsqueda. '
    'No se calcula speedup de hallazgo para b) y c), porque faltan tiempos '
    'exhaustivos completos.', 'small')

page('7. Discusión y conclusiones')
add('Retos y soluciones', 'h2')
add('La revisión del programa resolvió tres problemas principales: aceptar claves '
    'incorrectas con relleno válido, desbordar rangos de 64 bits y coordinar la '
    'terminación MPI. Se incorporaron autenticación HMAC, validación de intervalos '
    'y consenso de estado con drenaje de avisos. Las regresiones cubren esas rutas.')
add('En WSL con Open MPI 5, el helper evita una ruta problemática de PRRTE y '
    'recupera el estado explícito que imprime el programa. Si falta ese estado '
    'o vence el timeout externo, la ejecución falla. Las mediciones conservan '
    'comandos, intentos, estados y hashes de las fuentes para comprobar su procedencia.')
add('Conclusiones', 'h2')
for text in [
    '1. Se completaron el procesamiento de archivos, la búsqueda secuencial y ambas estrategias MPI. El registro final confirma los vectores AES, 24 casos de archivos y 75 de búsqueda.',
    f'2. La base obtuvo speedups medidos de {seq/base:.3f} en 123456 y {ctrl("secuencial")/ctrl("base"):.3f} en el control. Fue la opción más rápida en las dos comparaciones sin ventaja por patrones.',
    f'3. La alternativa recuperó 2^54 y 2^54 + 1 en medianas de {med("b","alternativa"):.6f} s y {med("c","alternativa"):.6f} s. La priorización explica el hallazgo; los resultados no demuestran una ventaja para claves arbitrarias.',
    '4. Las búsquedas exhaustivas grandes quedaron interrumpidas por costo computacional. El experimento está cerrado con esa limitación documentada; las proyecciones no equivalen a ejecuciones completadas.',
]: add(text)
add('Recomendaciones', 'h2')
add('Para ampliar el estudio conviene medir claves sin estructura, variar el tamaño de '
    'lote y repetir con afinidad de procesos y carga controlada. Esas pruebas permitirían '
    'evaluar si la asignación dinámica mejora en problemas más largos. Para la entrega '
    'actual, deben conservarse las fuentes y evidencias verificadas, junto con el '
    'paquete reproducible. ECB y las claves numéricas se limitan al objetivo didáctico.')

page('Referencias bibliográficas')
refs = [
    ('1', 'National Institute of Standards and Technology. (2023). <i>Advanced Encryption Standard (AES), FIPS 197-upd1.</i>', 'https://csrc.nist.gov/pubs/fips/197/final'),
    ('2', 'Dworkin, M. (2001). <i>Recommendation for Block Cipher Modes of Operation: Methods and Techniques. NIST SP 800-38A.</i>', 'https://csrc.nist.gov/pubs/sp/800/38/a/final'),
    ('3', 'OpenSSL Project. (s. f.). <i>EVP_EncryptInit: EVP cipher routines, OpenSSL 3.5.</i> Secciones de relleno y notas.', 'https://docs.openssl.org/3.5/man3/EVP_EncryptInit/'),
    ('4', 'Open MPI. (s. f.). <i>MPI_Allreduce. Documentación de Open MPI 5.0.x.</i>', 'https://docs.open-mpi.org/en/v5.0.x/man-openmpi/man3/MPI_Allreduce.3.html'),
    ('5', 'Open MPI. (s. f.). <i>MPI_Fetch_and_op. Documentación de Open MPI 5.0.x.</i>', 'https://docs.open-mpi.org/en/v5.0.x/man-openmpi/man3/MPI_Fetch_and_op.3.html'),
    ('6', 'Open MPI. (s. f.). <i>MPI_Issend. Documentación de Open MPI 5.0.x.</i>', 'https://docs.open-mpi.org/en/v5.0.x/man-openmpi/man3/MPI_Issend.3.html'),
    ('8', 'OpenSSL Project. (s. f.). <i>HMAC. Documentación de OpenSSL 3.5.</i>', 'https://docs.openssl.org/3.5/man3/HMAC/'),
]
for n,desc,url in refs:
    add(f'[{n}] {desc}')
    add(f'<link href="{url}" color="#1A4C8B">{url}</link>', 'small')
add('[7] Universidad del Valle de Guatemala. (2026). <i>CC3069 - Proyecto 02.</i> '
    'Enunciado y rúbrica del curso Computación Paralela y Distribuida, Ciclo 2. Documento proporcionado con el proyecto.')
add('Los diagramas y cálculos se elaboraron a partir del código y las evidencias del repositorio.', 'small')

page('Anexo 1. Catálogo de funciones', 'Anexo 1. Funciones AES y archivos')
add('A1.1. AES y formato: proyecto02/include/aes_comun.h', 'h2')
table(['Función', 'Entradas', 'Salida y funcionamiento'], [
    ('dataset_tag', 'Candidato, Dataset y etiqueta destino.', 'Deriva una clave MAC por dominio; calcula HMAC-SHA256 sobre versión, longitud y cifrado.'),
    ('verify_dataset', 'Candidato y Dataset.', 'Recalcula y compara la etiqueta; 1 auténtico, 0 no válido, -1 error de biblioteca.'),
    ('cipher_length', 'Longitud original.', 'Devuelve (longitud/16 + 1)·16; reserva relleno de 1 a 16 bytes.'),
    ('make_key', 'Candidato uint64_t y arreglo de 16 bytes.', 'Llena el arreglo: ocho bytes iniciales en cero y entero en big endian.'),
    ('parse_number', 'Cadena y puntero a entero.', '1 si es decimal válido y distinto de UINT64_MAX; escribe el valor. 0 ante error.'),
    ('encrypt_message', 'Contexto EVP, candidato, texto, longitud y Dataset.', 'Cifra con AES-128-ECB; llena Dataset, autentica y comprueba la longitud; devuelve éxito.'),
    ('decrypt_message', 'Contexto, candidato, Dataset, búfer y puntero de longitud.', '1 si HMAC, longitud y relleno son válidos; 0 si fallan; -1 ante error de inicialización/proceso. Escribe texto y longitud.'),
    ('print_hex', 'FILE*, bytes y longitud.', 'Escribe hexadecimal minúsculo y salto de línea; no devuelve estado.'),
    ('read_hex', 'FILE*, destino y cantidad de bytes.', 'Lee pares hexadecimales y exige salto final; 1 válido, 0 inválido.'),
    ('save_dataset', 'Ruta y Dataset.', 'Escribe AESECB2, longitud, cifrado y etiqueta; devuelve éxito de E/S. Utilidad disponible, no usada por aes_archivo.'),
    ('load_dataset', 'Ruta y Dataset de destino.', 'Valida cabecera, longitud, hexadecimal y fin de archivo; llena Dataset y devuelve éxito.'),
], [98,125,245])
add('A1.2. Archivos: proyecto02/src/aes_archivo.c', 'h2')
table(['Función', 'Entradas', 'Salida y funcionamiento'], [
    ('read_text', 'Ruta, destino y puntero de longitud.', 'Lee hasta 4096 bytes; rechaza excedentes o errores; conserva bytes y devuelve éxito.'),
    ('write_output', 'Ruta, Dataset, texto y modo.', 'Abre con wbx; guarda contenedor o texto; elimina salida parcial si falla.'),
    ('main', 'argc y argv: operación, entrada, salida, clave.', 'Coordina validación, EVP y E/S; limpia memoria. Código 0 si termina; 1 si falla.'),
], [98,125,245])

page('Anexo 1. Búsqueda y MPI', 'Anexo 1. Funciones de búsqueda y MPI')
add('A1.3. Comunes: proyecto02/include/busqueda.h y busqueda_mpi.h', 'h2')
table(['Función', 'Entradas', 'Salida y funcionamiento'], [
    ('init_params', 'Params*, límite, lote y offset.', 'Inicializa valores, tiempo sin límite y frase por defecto.'),
    ('parse_params', 'argc, argv, Params* y ruta de salida.', 'Lee -e, -f, -l, -b, -o y -t; rechaza rangos que desbordan y valida límites y un archivo; devuelve 1/0.'),
    ('contains_phrase', 'Texto, longitud, frase y tamaño.', 'Compara ventanas con memcmp; devuelve 1 si contiene la frase.'),
    ('try_phrase', 'EVP, candidato, Dataset, destino y frase.', 'Descifra, busca la frase y confirma con HMAC; 1 acierto, 0 ausente, -1 error EVP.'),
    ('phrase_fits', 'Params y Dataset.', 'Devuelve si la longitud de la frase cabe en la longitud original declarada.'),
    ('wall_seconds', 'Sin parámetros.', 'Tiempo double con CLOCK_MONOTONIC; termina con error si falla el reloj.'),
    ('print_report', 'Modo, procesos, clave, intentos, tiempo, estado, EVP, datos y parámetros.', 'Muestra estado, clave hexadecimal, mensaje, tiempo y rendimiento.'),
    ('mpi_setup', 'argc, argv, uso, Params y Dataset.', 'P0 valida y carga; difunde estado y datos mediante Bcast; todos reciben el mismo estado.'),
    ('mpi_fail', 'Mensaje de error.', 'Escribe en stderr e invoca MPI_Abort para terminar el comunicador.'),
    ('mpi_finish', 'Estado local de aplicación.', 'Consenso MAX, imprime Estado MPI en P0, finaliza y devuelve el estado. El helper WSL recupera ese código.'),
], [98,145,225])
add('A1.4. Puntos de entrada de las búsquedas', 'h2')
table(['Archivo / función', 'Entradas', 'Salida y funcionamiento'], [
    ('busqueda_secuencial.c / main', 'Opciones y archivo AES.', 'Recorre desde offset hasta el fin, prueba frase y mide tiempo. Libera EVP.'),
    ('busqueda_base.c / main', 'Opciones y archivo AES; rank y tamaño MPI.', 'Reparte lotes, reduce el acierto por ronda y obtiene tiempo máximo e intentos totales.'),
    ('busqueda_alternativa.c / main', 'Opciones y archivo AES; rank y tamaño MPI.', 'Crea contadores RMA, asigna bloques, sondea avisos, acuerda resultado y libera recursos.'),
], [145,100,223])
add('Códigos de salida de las búsquedas: 0 = clave hallada; 1 = entrada o error; '
    '2 = rango agotado sin hallar; 3 = tiempo agotado. Un aborto MPI puede '
    'producir un diagnóstico adicional del lanzador.', 'small')

page('Anexo 1. Generadores y scripts', 'Anexo 1. Familias y herramientas')
add('A1.5. Familias: proyecto02/src/busqueda_alternativa.c', 'h2')
table(['Función', 'Entradas', 'Salida y funcionamiento'], [
    ('pow_u64', 'Base y exponente entero.', 'Producto iterado en uint64_t; calcula potencias usadas por los generadores.'),
    ('key_patrones', 'Índice de la familia.', 'Devuelve fecha, repetición, potencia/vecino o constante según el segmento del índice.'),
    ('ascii_total', 'Sin parámetros.', 'Suma 36^l para l de 1 a 5: cantidad de índices de la familia ASCII.'),
    ('key_ascii', 'Índice ASCII.', 'Determina longitud, descompone en base 36 y empaqueta caracteres como entero.'),
    ('family_count', 'Identificador de familia y Params.', 'Devuelve el número de índices: límite de bajos, patrones, ASCII o barrido.'),
    ('family_key', 'Familia, índice y Params.', 'Selecciona el generador; en el barrido devuelve offset + índice.'),
], [98,125,245])
add('A1.6. Automatización de pruebas y mediciones', 'h2')
table(['Módulo / rutinas', 'Entradas y salidas; propósito'], [
    ('probar_inciso1.py: run, main', 'run ejecuta y comprueba éxito/error esperado; main crea archivos temporales, verifica bytes y 24 casos.'),
    ('probar_busqueda.py: run, encrypt, found_key, main', 'run valida el código con timeout; encrypt genera un caso; found_key extrae la clave; main comprueba 75 casos; Open MPI es obligatorio.'),
    ('ejecutar_pruebas.py: field, main; save y execute internas', 'field extrae métricas; execute valida estados; save conserva datos crudos; main mide serie principal y control con metadatos, JSON y tablas.'),
    ('mpi_utils.py: mpi_prefix, run_command', 'Selecciona flags de Open MPI según entorno; ejecuta con timeout y termina el grupo completo si se excede.'),
    ('registrar_pruebas.py: main', 'Ejecuta make test y guarda stdout, stderr, fecha y código en evidencias/pruebas/.'),
    ('empaquetar.py: main', 'Reúne fuentes, ejecutables, informe y evidencias; genera ZIP y comprueba su integridad.'),
], [178,290])
add('Alcance del catálogo: todas las funciones C de proyecto02 y las rutinas Python '
    'que verifican, miden y empaquetan la implementación. El Laboratorio 03 se conserva '
    'como antecedente; su API GCM no interviene en las búsquedas ECB del proyecto.', 'small')

page('Anexo 1. Librerías y rutinas externas', 'Anexo 1. Librerías y comunicación')
table(['Librería / API', 'Entradas, salidas y uso en el proyecto'], [
    ('OpenSSL: EVP_CIPHER_CTX_new / free', 'Crea un contexto o NULL; free lo libera. Un contexto independiente por proceso.'),
    ('EVP_aes_128_ecb; EncryptInit/Update/Final', 'Selecciona cifrador; recibe clave y bytes; produce cifrado, longitudes y estado.'),
    ('DecryptInit/Update/Final; set_padding', 'Recibe clave/cifrado y política de relleno; devuelve bytes y estado. Final verifica el relleno si está habilitado.'),
    ('OPENSSL_cleanse', 'Puntero y cantidad de bytes; limpia búferes antes de liberar o descartar datos.'),
    ('MPI_Init / Finalize; Comm_rank / size', 'Inicializa/finaliza el entorno y consulta identificador y cantidad de procesos.'),
    ('MPI_Bcast / Barrier / Wtime', 'Difunde estado y datos desde P0; sincroniza el inicio; devuelve reloj local en segundos.'),
    ('MPI_Allreduce / Reduce', 'Recibe valores, tipo y operador; combina MIN de claves, MAX de tiempo/estado y SUM de intentos. Allreduce devuelve a todos; Reduce a P0.'),
    ('MPI_Win_create / lock_all / unlock_all / free', 'Expone contadores, abre/cierra época de acceso y libera ventana. Devuelve manejador/estado.'),
    ('MPI_Fetch_and_op / Win_flush', 'Recibe incremento, destino y desplazamiento; retorna contador anterior y asegura finalización remota.'),
    ('MPI_Irecv / Issend / Test', 'Publica recepción/envíos de clave y familia; devuelve solicitudes. Test consulta finalización y datos recibidos.'),
    ('MPI_Testall / Cancel / Wait', 'Progresa y consulta envíos mientras se drenan avisos; cancela/completa la recepción pendiente.'),
    ('HMAC / EVP_sha256 / CRYPTO_memcmp', 'Derivación por dominio y etiqueta SHA-256 de 32 bytes; comparación de autenticación sin memcmp ordinario.'),
    ('MPI_Iprobe / Recv / Abort', 'Consulta y drena mensajes adicionales; Abort termina el comunicador ante error no recuperable.'),
    ('C: stdio, stdlib, string, stdint, inttypes, errno', 'Archivos y E/S, conversión decimal, memoria/cadenas, enteros y formato portable, detección de errores.'),
    ('POSIX: getopt y clock_gettime', 'Procesa opciones desde argv y obtiene reloj monotónico. Encabezados unistd.h y time.h.'),
    ('Python: pathlib, subprocess, tempfile, re, statistics, zipfile', 'Rutas, procesos, archivos temporales, extracción de métricas, mediana y empaquetado. ReportLab genera este informe.'),
], [178,290])
add('Dataset conserva longitud, cifrado y etiqueta HMAC. Params contiene rangos, tiempo, modo y frase. La difusión usa MPI_UINT64_T, MPI_INT y caracteres explícitos; no transmite el padding de estructuras nativas.', 'small')

page('Anexo 2. Compilación y verificación', 'Anexo 2. Compilación y pruebas')
shot('evidencias/inciso1/01_compilacion.png', 300)
caption('A2.1. Compilación en WSL de los ejecutables del proyecto y del laboratorio. Transcripción: inciso1/compilacion.txt.')
shot('evidencias/inciso1/04_verificacion.png', 300)
caption('A2.2. Archivos idénticos, rechazo de clave incorrecta y pruebas de archivos. Transcripción: inciso1/verificacion.txt.')

page('Anexo 2. Cifrado y recuperación', 'Anexo 2. Archivos')
shot('evidencias/inciso1/02_cifrado.png', 300)
caption('A2.3. Texto original, clave 123456 y cifrado hexadecimal. Transcripción: inciso1/cifrado.txt.')
shot('evidencias/inciso1/03_descifrado.png', 300)
caption('A2.4. Recuperación del mensaje con la misma clave. Transcripción: inciso1/descifrado.txt.')

for tag,num in [('a',1),('b',2),('c',3)]:
    page(f'Anexo 2. Caso {tag}): clave {keys[tag]}', f'Anexo 2. Búsqueda del caso {tag})')
    shot(f'evidencias/inciso2/0{num}_clave_{tag}.png', 400)
    caption(f'A2.{num+4}. Ejecución de las tres versiones. Transcripción: inciso2/clave_{tag}.txt.')
    if tag=='a':
        add('Las tres versiones recuperan 123456 y muestran el mensaje requerido. '
            'Los tiempos de esta captura pertenecen a una sesión de demostración; '
            'las comparaciones del cuerpo usan las cinco muestras de la serie experimental.')
    else:
        add(f'La secuencial y la base detienen el recorrido [0, 2^56) tras el corte '
            f'de {cutoff} segundos, sin hallar la clave. La alternativa la recupera '
            'en la familia de patrones, sin recibirla como parámetro.')
    add('Procedencia de las capturas', 'h2')
    add('Las siete imágenes son capturas de sesiones xterm con Xvfb. Sus comandos y '
        'salidas se conservan en archivos .txt; capturas.json registra sus hashes. '
        'La serie de medianas tiene su propia bitácora y se mantiene separada.', 'small')

page('Anexo 2. Bitácora y reproducción', 'Anexo 2. Muestras y reproducción')
add('Tiempos individuales en segundos. Cada fila reúne cinco ejecuciones; en las '
    'filas marcadas con * se alcanzó el corte sin hallazgo. Los intentos, tasas, '
    'estados, comandos y dispersión se conservan en resultados.json y resultados.md.', 'small')
rows=[]
for phase,tag in [('principal','a'),('principal','b'),('principal','c'),('control','control')]:
    for mode in ['secuencial','base','alternativa']:
        rs=[r for r in all_runs if r['phase']==phase and r['tag']==tag and r['mode']==mode]
        label=f'{tag} / {mode}' + (' *' if tag in ['b','c'] and mode!='alternativa' else '')
        rows.append([label]+[f'{r["time"]:.4f}' for r in rs]+[f'{median(r["time"] for r in rs):.4f}'])
table(['Caso / programa','1','2','3','4','5','Mediana'], rows, [126,57,57,57,57,57,57])
add('Reproducir en Ubuntu o WSL', 'h2')
code('sudo apt install build-essential libssl-dev libopenmpi-dev openmpi-bin python3\nmake\nmake test\npython3 proyecto02/tests/ejecutar_pruebas.py 5 5')
add('Para ejecutar MPI en el entorno WSL registrado, usar el helper del repositorio:', 'small')
code('python3 scripts/mpi_utils.py --run proyecto02/build/busqueda_base '+chr(92)+'\n  -l 72057594037927936 -t 5 evidencias/inciso2/datos/clave_b.aes')
add('La entrega incluye fuentes, ejecutables Linux, datos cifrados, evidencias e informe. '
    'scripts/empaquetar.py comprueba su procedencia y crea el manifiesto SHA-256; '
    'scripts/verificar_entrega.py --ejecutar recompila y prueba una extracción nueva. '
    'Las instrucciones para regenerar el PDF están en README.md.', 'small')

# Índice con números de página físicos; cada sección comienza en página nueva.
index_rows = [(title, str(i+1)) for i,title in enumerate(pages) if i>=2]
idx = Table([[p(escape(t),'small'),p(n,'small')] for t,n in index_rows], colWidths=[430,38])
idx.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                         ('TOPPADDING',(0,0),(-1,-1),2),
                         ('BOTTOMPADDING',(0,0),(-1,-1),2),
                         ('LINEBELOW',(0,0),(-1,-1),.2,colors.HexColor('#DFE7E2'))]))
story[index_position]=idx

def furniture(c, doc):
    c.setFillColor(INK)
    c.setFont('Body',9)
    c.drawCentredString(306,30,str(doc.page))
    if doc.page==3:
        c.line(72,83,235,83)
        c.setFont('Body',7)
        c.drawString(72,72,'1. NIST (2023), FIPS 197-upd1, resumen. Cita en inglés; enlace completo en la referencia [1].')

doc=SimpleDocTemplate(str(OUT), pagesize=(612,792), rightMargin=72,leftMargin=72,
                      topMargin=60,bottomMargin=54,
                      title='Proyecto 02 - Búsqueda de claves AES-128 con Open MPI',
                      author='Daniel Estrada; Andre Pivaral; Sebastian Estrada',
                      subject='Informe experimental, estrategias, resultados y anexos')
doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
if doc.page != len(pages):
    raise RuntimeError(f'El contenido desborda: {doc.page} paginas reales, {len(pages)} planificadas.')
inputs=['evidencias/inciso2/resultados.json','evidencias/capturas.json',
        'evidencias/pruebas/ultima_prueba.txt','informe/crear_informe.py','evidencias/pruebas/resultado_final.json',
        'informe/recursos/escudo_uvg.png']
provenance={'inputs':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in inputs},
            'pdf_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'paginas':doc.page}
(ROOT/'informe/procedencia.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
print(f'PDF: {OUT}\nPáginas planificadas: {len(pages)}')
for i,title in enumerate(pages,1):
    print(i,title)

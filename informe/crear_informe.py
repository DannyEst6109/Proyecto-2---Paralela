"""Genera el informe a partir del código y las evidencias conservadas en el repositorio.

Ejecutar con Python 3 y ReportLab: python informe/crear_informe.py
No ejecuta ni modifica las mediciones del proyecto.
"""
from pathlib import Path
from statistics import median
import re
import json
import hashlib
import shutil
from xml.sax.saxutils import escape

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                               Table, TableStyle, Image, Preformatted, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, Line, Polygon, String

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/Informe_Proyecto_02.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
FONT_DIRS = [Path('C:/Windows/Fonts'), Path('/usr/share/fonts/truetype/dejavu')]
for folder in FONT_DIRS:
    normal = folder / ('arial.ttf' if folder.name == 'Fonts' else 'DejaVuSans.ttf')
    bold = folder / ('arialbd.ttf' if folder.name == 'Fonts' else 'DejaVuSans-Bold.ttf')
    mono = folder / ('consola.ttf' if folder.name == 'Fonts' else 'DejaVuSansMono.ttf')
    if normal.exists():
        pdfmetrics.registerFont(TTFont('Body', str(normal)))
        pdfmetrics.registerFont(TTFont('BodyBold', str(bold)))
        pdfmetrics.registerFont(TTFont('Code', str(mono)))
        break
else:
    raise RuntimeError('Se requieren Arial/Consolas o DejaVu Sans/Mono.')
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')
GREEN = colors.HexColor('#006B54')
INK = colors.HexColor('#192D35')
PALE = colors.HexColor('#EDF4F1')
GRAY = colors.HexColor('#55646B')
WIDTH = 468
ST = {
    'body': ParagraphStyle('body', fontName='Body', fontSize=10, leading=15,
                           textColor=INK, alignment=TA_JUSTIFY, spaceAfter=9),
    'small': ParagraphStyle('small', fontName='Body', fontSize=8, leading=11,
                            textColor=INK, spaceAfter=6),
    'cell': ParagraphStyle('cell', fontName='Body', fontSize=8, leading=10.6, textColor=INK),
    'headcell': ParagraphStyle('headcell', fontName='BodyBold', fontSize=8,
                               leading=10.5, textColor=colors.white),
    'h1': ParagraphStyle('h1', fontName='BodyBold', fontSize=18, leading=23,
                         textColor=GREEN, spaceAfter=16),
    'h2': ParagraphStyle('h2', fontName='BodyBold', fontSize=11, leading=15,
                         textColor=GREEN, spaceBefore=9, spaceAfter=7),
    'caption': ParagraphStyle('caption', fontName='Body', fontSize=8, leading=11,
                              textColor=GRAY, spaceBefore=5, spaceAfter=10),
    'code': ParagraphStyle('code', fontName='Code', fontSize=7.5, leading=10.5,
                           textColor=INK, backColor=PALE, borderPadding=8, spaceAfter=10),
    'cover': ParagraphStyle('cover', fontName='Times-Roman', fontSize=13, leading=20,
                            alignment=TA_CENTER, textColor=INK, spaceAfter=10),
    'title': ParagraphStyle('title', fontName='Times-Bold', fontSize=23, leading=30,
                            alignment=TA_CENTER, textColor=INK, spaceAfter=12),
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
    data = [[p(escape(str(x)), 'headcell') for x in headers]]
    data += [[p(escape(str(x)), 'cell') for x in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PALE]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 0), (-1, 0), .7, GREEN),
        ('LINEBELOW', (0, 1), (-1, -1), .3, colors.HexColor('#DCE4E0')),
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
    d.add(Rect(x, y, w, h, rx=4, fillColor=fill, strokeColor=GREEN, strokeWidth=.7))
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

page('', 'Carátula')
story.append(Spacer(1, 12))
for line in ['UNIVERSIDAD DEL VALLE DE GUATEMALA', 'Facultad de Ingeniería',
             'Departamento de Ciencias de la Computación', 'CC3069 - Computación Paralela y Distribuida']:
    add(line, 'cover')
story.append(Spacer(1, 20))
shot('informe/recursos/escudo_uvg.png', 135)
story.append(Spacer(1, 28))
add('Proyecto 02', 'title')
add('Búsqueda de claves AES-128 con Open MPI:<br/>distribución estática y estrategia por familias', 'cover')
story.append(Spacer(1, 35))
for line in ['Daniel Estrada - 20853', 'Andre Pivaral - 23574', 'Sebastian Estrada - 21405']:
    add(line, 'cover')
story.append(Spacer(1, 30))
add('Guatemala, 27 de octubre de 2026<br/>Ciclo 2 de 2026', 'cover')

page('Índice')
index_position = len(story)
story.append(Spacer(1, 1))
add('Criterio de lectura', 'h2')
add('Las mediciones proceden de las evidencias conservadas en el repositorio. Los valores '
    'proyectados se identifican como estimaciones; no representan búsquedas completadas. '
    'Las limitaciones y hallazgos de validación se exponen en la discusión y en los anexos.')

page('1. Introducción y objetivos')
add('La búsqueda de una clave por fuerza bruta constituye un problema adecuado para estudiar '
    'computación paralela: cada candidata puede probarse de forma independiente, pero el orden '
    'del recorrido y la comunicación necesaria para detener el trabajo afectan el tiempo de respuesta. '
    'Este proyecto adapta los programas del Laboratorio 03 para cifrar archivos de texto con AES-128 '
    'y comparar dos estrategias de búsqueda mediante cuatro procesos MPI.')
add('La estrategia base distribuye lotes consecutivos y sincroniza los resultados al final de cada ronda. '
    'La alternativa combina familias de candidatas con asignación dinámica y notificación no bloqueante. '
    'El estudio utiliza el mensaje y las tres claves establecidos en el enunciado [7].')
add('Objetivo general', 'h2')
add('Implementar y evaluar estrategias de distribución del trabajo con Open MPI para reducir el tiempo '
    'de búsqueda de claves numéricas utilizadas en un cifrado AES-128.')
add('Objetivos específicos', 'h2')
for t in [
    '1. Cargar un archivo .txt, cifrarlo con una clave de entrada y recuperar sus bytes originales con la misma clave.',
    '2. Implementar una referencia secuencial y una búsqueda paralela base que reconozcan la frase «es una prueba de».',
    '3. Comparar las claves 123456, 18014398509481984 y 18014398509481985 con cuatro procesos en las ejecuciones MPI.',
    '4. Explicar el reparto, la búsqueda y la comunicación de una estrategia alternativa mediante diagramas y pseudocódigo.',
    '5. Analizar tiempos, speedups, costos de coordinación y límites de las mediciones, con evidencia verificable.'
]: add(t)
add('Alcance', 'h2')
add('El cifrado usa claves AES de 16 bytes construidas desde enteros de hasta 64 bits. Se estudia un '
    'subconjunto de claves, no todo el espacio de 2^128 posibilidades. Los mensajes admitidos miden '
    'hasta 4096 bytes. Las ejecuciones registradas se realizaron en WSL; no constituyen una evaluación '
    'de escalabilidad en un clúster de varias máquinas.')

page('2. Antecedentes conceptuales')
add('AES-128 y representación de la clave', 'h2')
add('AES es un cifrador simétrico por bloques. FIPS 197 define bloques de 128 bits y variantes '
    'con claves de 128, 192 y 256 bits [1]. En este proyecto, <b>make_key</b> inicializa 16 bytes en cero '
    'y coloca el entero candidato en los últimos ocho, en orden big endian. Por ejemplo, 123456 '
    'se representa como <font face="Code">0000000000000000000000000001e240</font>. '
    'El arreglo cumple la longitud de AES-128, aunque la selección de claves tiene menos entropía. '
    'NIST indica: <i>«Each of them transforms data in blocks of 128 bits»</i>.<super>1</super>')
add('Modo ECB y relleno', 'h2')
add('El modo ECB cifra cada bloque por separado [2]. La implementación usa la interfaz EVP de '
    'OpenSSL y relleno PKCS#7: se añaden entre 1 y 16 bytes para completar el bloque, incluso '
    'cuando la longitud original ya es múltiplo de 16 [3]. El formato AESECB2 añade HMAC-SHA256 '
    'sobre versión, longitud y cifrado, con clave MAC derivada mediante un dominio distinto [8]. ')
add('Fuerza bruta y validación por frase', 'h2')
add('Una búsqueda exhaustiva enumera candidatas, descifra el mensaje y aplica un criterio de aceptación. '
    'Aquí se busca la secuencia «es una prueba de» en el resultado, como exige el enunciado. '
    'Durante la búsqueda se desactiva la comprobación de relleno y se evalúa la frase sobre '
    'el texto original declarado. Solo si aparece se verifica el HMAC; así se conserva el criterio '
    'del enunciado sin aceptar falsos positivos de frases cortas.')
add('MPI y coordinación del trabajo', 'h2')
add('Cada proceso conserva su propio contexto AES y su copia del cifrado. La base usa una reducción '
    'colectiva para compartir el hallazgo: <b>MPI_Allreduce</b> combina valores y entrega el resultado '
    'a todos [4]. La alternativa obtiene bloques mediante una operación atómica sobre una ventana '
    'remota [5], y utiliza envíos no bloqueantes para avisar un acierto [6].')
add('Tiempo, speedup y eficiencia', 'h2')
code('R = claves probadas / tiempo de búsqueda\nS_base = T_secuencial / T_base\nE_base = S_base / 4\nG_alt/base = T_base / T_alternativa')
add('S compara la referencia secuencial con la base. G compara estrategias con distinto orden de '
    'candidatas; debe interpretarse como una razón de tiempos. Cuando interviene una proyección, '
    'la razón también es estimada.', 'small')

page('3. Diseño e implementación')
add('Organización del proyecto', 'h2')
table(['Componente', 'Responsabilidad'], [
    ('laboratorio03/', 'Conserva los programas originales AES-128-GCM usados como punto de partida.'),
    ('proyecto02/src/', 'aes_archivo; búsqueda secuencial; base MPI; alternativa MPI.'),
    ('proyecto02/include/', 'AES y formato de archivo; argumentos y frase; preparación común de MPI.'),
    ('proyecto02/tests/', 'Pruebas de archivos, búsquedas y generación de la bitácora de tiempos.'),
    ('evidencias/', 'Capturas originales, comandos, salidas, archivos cifrados y tablas de resultados.'),
], [110, 358])
add('Entrada, salida y formato', 'h2')
add('El programa <b>aes_archivo</b> recibe operación, archivo de entrada, archivo de salida y clave '
    'decimal. La salida se abre en modo exclusivo para evitar sobrescribir archivos existentes. '
    'El contenedor de texto <b>AESECB2</b> almacena una cabecera, la longitud original y el cifrado '
    'hexadecimal. Esta representación permite mostrar el texto cifrado en las evidencias.')
code('AESECB2\n<longitud original en bytes>\n<cifrado hexadecimal>\n<etiqueta HMAC-SHA256 hexadecimal>')
add('El cambio respecto al Laboratorio 03 es explícito: los archivos AESLAB1 del laboratorio '
    '(GCM), y los antiguos AESECB1 sin autenticación, no son compatibles con AESECB2. Se rechazan en lugar de '
    'interpretarlos con un esquema distinto.')
add('Claves de los casos de estudio', 'h2')
table(['Caso', 'Entero decimal', 'Clave AES de 16 bytes (hexadecimal)'], [
    (tag+')', str(key), key.to_bytes(16,'big').hex()) for tag,key in keys.items()
], [35, 137, 296])
add('Programación defensiva y memoria', 'h2')
add('Se verifican números decimales, longitudes, formato, archivos ausentes y retornos de EVP. '
    'Los arreglos de texto/cifrado son acotados y los contextos EVP se liberan al finalizar. '
    'El proceso 0 valida las entradas MPI y difunde el resultado a los demás para evitar que '
    'unos continúen y otros abandonen antes de una operación colectiva.')

page('4. Inciso 1: cifrado y descifrado')
add('El archivo se lee como bytes para conservar codificación y saltos de línea. En el cifrado '
    'se convierte la clave, se aplica AES-128-ECB con relleno y se guarda el contenedor. '
    'En el descifrado se carga el cifrado, se procesa con la clave recibida y se escribe el texto recuperado.')
flow(['Validar operación, clave, rutas y tamaño de entrada',
      'Cifrar: leer .txt y convertir el entero a 16 bytes\nDescifrar: cargar y validar el formato AESECB2',
      'Cifrar: EVP Encrypt + relleno y HMAC\nDescifrar: verificar HMAC, descifrar y validar longitud/relleno',
      'Si ocurre un error: informar y terminar\nSi termina: guardar en un archivo nuevo y mostrar el resultado'])
caption('Figura 1. Flujo de procesamiento de archivos. Elaboración propia a partir de aes_archivo.c.')
add('Verificación de recuperación', 'h2')
code('./proyecto02/build/aes_archivo cifrar entrada.txt salida.aes 123456\n./proyecto02/build/aes_archivo descifrar salida.aes recuperado.txt 123456\ncmp entrada.txt recuperado.txt\nsha256sum entrada.txt recuperado.txt')
add('Las capturas del Anexo 2 muestran texto original, cifrado, texto recuperado y hashes iguales. '
    'La suite del inciso 1 contiene 24 casos, entre ellos archivo vacío, UTF-8, saltos CRLF, '
    '4096 bytes, exceso de tamaño, formatos dañados y protección de la entrada.')
add('Autenticación y regresión corregida', 'h2')
add('La revisión inicial detectó que una clave incorrecta podía producir relleno válido. '
    'Se corrigió con HMAC-SHA256 en esquema encrypt-then-MAC: la etiqueta autentica el '
    'formato, la longitud y el cifrado antes de recuperar el archivo. La comparación usa '
    'CRYPTO_memcmp. El caso 44 se rechaza sin crear salida; también se verifican cambios '
    'en el primer bloque, en la etiqueta y en la longitud. Un vector independiente de '
    'clave cero y bloque cero comprueba AES-128-ECB, además de la recuperación [3, 8].')


page('5. Estrategia base: lotes estáticos')
add('Con n = 4 procesos y B = 65536 claves por lote, el proceso p recibe en la ronda r el intervalo '
    '[offset + (r·n+p)·B, offset + (r·n+p+1)·B), recortado al fin del rango. '
    'Los lotes de una ronda son disjuntos. Al terminar, una reducción MIN selecciona la '
    'clave encontrada; UINT64_MAX representa ausencia de acierto.')
table(['Ronda', 'P0', 'P1', 'P2', 'P3'], [
    ('0', '[0, B)', '[B, 2B)', '[2B, 3B)', '[3B, 4B)'),
    ('1', '[4B, 5B)', '[5B, 6B)', '[6B, 7B)', '[7B, 8B)'),
    ('r', 'Desde 4rB', 'Desde (4r+1)B', 'Desde (4r+2)B', 'Desde (4r+3)B'),
], [40,107,107,107,107])
caption('Tabla 1. Reparto base para offset = 0; B = 65536. No es una partición en cuatro bloques gigantes.')
flow(['P0 valida y carga; MPI_Bcast difunde parámetros y cifrado',
      'MPI_Barrier; iniciar reloj\nCada proceso descifra y busca la frase en su lote',
      'MPI_Allreduce(MIN) comparte el acierto\nSin acierto: comprobar tiempo/rango y pasar de ronda',
      'Con acierto o fin: MPI_Reduce de tiempo y número de intentos\nP0 muestra clave, mensaje y estadísticas'])
caption('Figura 2. Flujo de la base. La repetición continúa mientras no haya acierto, límite o agotamiento.')
add('Ventajas y limitaciones', 'h2')
add('El reparto es simple y no requiere un coordinador que asigne cada lote. Sin embargo, '
    'todos esperan la finalización de la ronda. Un proceso puede seguir trabajando mientras '
    'otro ya encontró la clave. Para 123456, el hallazgo ocurre en el lote de P1 de la '
    'primera ronda, pero los demás completan sus lotes antes del consenso.')

page('6. Alternativa: familias de claves')
add('La alternativa cambia el orden de exploración y la asignación de trabajo. Conserva '
    'la prueba de descifrado por candidata y añade cuatro familias, cada una con un '
    'contador de bloques. La familia se genera por índice; no se almacena una lista completa.')
table(['Familia', 'Candidatas y cobertura'], [
    ('F0: valores bajos', 'Enteros desde 0 hasta 2^24 - 1. Incluye 123456.'),
    ('F1: patrones humanos', 'Fechas numéricas, dígitos repetidos, potencias de 2 y de 10 con sus vecinos y constantes. Incluye 2^54 y 2^54+1.'),
    ('F2: texto ASCII', 'Cadenas de 1 a 5 caracteres de [a-z0-9] convertidas a un entero big endian.'),
    ('F3: barrido de respaldo', 'Intervalo desde offset; por defecto offset = 2^24 y cantidad = 2^63. La cobertura depende de estos parámetros.'),
], [115,353])
d = Drawing(WIDTH, 180)
for i, label in enumerate(['F0: bajos','F1: patrones','F2: ASCII','F3: barrido']):
    box(d, i*118, 135, 112, 30, label, size=8)
    arrow(d, i*118+56, 135, i*118+56, 109)
box(d, 0, 67, 466, 42, 'Ventana RMA en P0: un contador atómico por familia\nMPI_Fetch_and_op(+1) obtiene el siguiente bloque libre')
for i in range(4):
    box(d,i*118, 5,112,35,f'Proceso {i}\nInicia en F{i}',size=8)
    arrow(d,i*118+56,40,i*118+56,67)
story.append(d)
caption('Figura 3. Asignación dinámica por familia. El tamaño habitual de bloque es 65536 candidatas.')
add('Asignación y balanceo', 'h2')
add('P0 expone cuatro contadores mediante MPI_Win_create. Cada proceso incrementa el contador '
    'de su familia con MPI_Fetch_and_op y completa la operación con MPI_Win_flush. El valor '
    'anterior identifica un bloque exclusivo dentro de esa familia [5]. Cuando una familia '
    'se agota, el proceso solicita trabajo de las siguientes en orden circular.')
add('La asignación evita duplicar índices de una misma familia. No elimina coincidencias '
    'entre familias: un entero puede aparecer como valor bajo, patrón o parte del barrido. '
    'El proceso conserva su preferencia de familia hasta agotarla; no hay redistribución '
    'continua basada en el tiempo restante de cada familia.')

add('Modo de control -e', 'h2')
add('La opción -e desactiva F0, F1 y F2; todos los procesos solicitan bloques del mismo barrido. Con offset, límite y lote iguales a la base, permite comparar la asignación dinámica sin el efecto de priorizar patrones.', 'small')

page('7. Comunicación y pseudocódigo')
add('Antes de buscar, cada proceso deja una recepción MPI_Irecv pendiente. Si encuentra la '
    'frase y confirma el HMAC, envía la clave y familia con MPI_Issend [6]. Los receptores '
    'consultan MPI_Test cada 4096 intentos por familia y también entre bloques. '
    'El aviso reduce el trabajo posterior al acierto sin exigir una reducción por lote.')
code('P0 valida y difunde parámetros y texto cifrado\ncrear ventana con contador[0..3] = 0\npublicar recepción no bloqueante de aviso\nsincronizar e iniciar reloj\nmientras haya trabajo y no haya finalizado:\n    elegir primera familia no agotada según preferencia del rank\n    bloque = incremento atómico del contador de esa familia\n    si bloque fuera de la familia: marcar agotada y continuar\n    para cada índice del bloque:\n        candidata = generar_clave(familia, índice)\n        descifrar y buscar la frase\n        si hay acierto:\n            guardar clave y familia; enviar aviso a todos; finalizar\n        cada 4096 intentos:\n            consultar aviso y tiempo límite\n    consultar aviso entre bloques\nacordar clave mínima y familia mediante MPI_Allreduce\nreducir tiempo máximo e intentos; drenar mensajes mientras MPI_Testall completa envíos\nliberar ventana y contexto; P0 reporta; MPI_Finalize')
d = Drawing(WIDTH, 150)
for i in range(4):
    x=54+i*120
    box(d,x-35,115,70,25,f'P{i}')
    d.add(Line(x,110,x,35,strokeColor=GRAY,strokeDashArray=[3,3]))
for target in [54,174,414]:
    arrow(d,294,92,target,65)
box(d,0,0,468,30,'MPI_Allreduce: consenso final; MPI_Reduce: estadísticas')
d.add(String(300,97,'P2 encuentra la frase',fontName='BodyBold',fontSize=8,fillColor=GREEN))
story.append(d)
caption('Figura 4. Ejemplo de aviso de P2 al resto. Los receptores detienen su búsqueda al detectar el mensaje.')
add('Al terminar se cancela/completa la recepción pendiente y se drenan avisos mientras '
    'MPI_Testall progresa los envíos. La reducción final permite resolver aciertos '
    'simultáneos conservando la clave menor. El tiempo informado incluye el consenso, '
    'pero excluye la creación de la ventana y la limpieza posterior.', 'small')

page('8. Metodología experimental')
table(['Variable','Configuración'],[
    ('Mensaje / frase','Esta es una prueba de proyecto 2 / es una prueba de. Se conservan los saltos del archivo.'),
    ('Procesos y rango','4 procesos MPI. Base y secuencial: [0, 2^56), que incluye las tres claves.'),
    ('Compilación','C11, -O2, -Wall, -Wextra, -Wpedantic; GCC 15.2.0; OpenSSL 3.5.5; Open MPI 5.0.10.'),
    ('Sistema',metadata['sistema']),('CPU visible a WSL',cpu_name),
    ('Serie principal',f'{date}; {reps} repeticiones por cada combinación. Corte de {cutoff} s para las búsquedas largas.'),
    ('Lote / sondeo','Principal: 65536 claves por lote; sondeo cada 4096 intentos. Control: lote 4096.'),
    ('Fuentes','resultados.json, bitacora.txt y resultados.md. Metadatos de CPU, versiones, comandos y SHA-256 de fuentes.'),
], [110,358])
add('Procedimiento y tiempo medido','h2')
add('Se cifra el texto con cada clave y se ejecutan las tres versiones cinco veces. '
    'Todos los códigos de salida y métricas se validan. Las búsquedas largas finalizan '
    'con código 3; las completadas con 0 y la clave esperada. La salida se guarda tras '
    'cada comando y un timeout externo invalida la medición. Se informa mediana, '
    'mínimo, máximo y desviación estándar muestral en resultados.md.')
add('MPI_Wtime se inicia tras una barrera; la secuencial usa CLOCK_MONOTONIC. '
    'Se excluyen lectura, lanzamiento y reporte. El intervalo alternativo incluye '
    'el consenso de clave, pero excluye el drenaje y liberación posteriores. Son '
    'tiempos de búsqueda, no tiempos completos de la aplicación.')
add('Control y límites de validez','h2')
add('Se agrega la clave 750123 con rango [0, 1000000), lote 4096 y alternativa '
    'en modo -e. Las tres versiones exploran el mismo espacio ascendente por bloques; '
    'la asignación y la parada pueden variar el trabajo efectivo. El entorno WSL '
    'es una máquina compartida: no hay aislamiento de carga ni estudio de varios nodos. '
    'Se registra la CPU visible, pero no se infiere de ella el hardware físico reservado.')


page('9. Resultados medidos')
add('Caso a): clave 123456', 'h2')
table(['Programa', 'Mediana (s)', 'Rendimiento (claves/s)', 'Estado'], [
    (m, f'{med("a",m):.9f}', f'{med("a",m,"rate"):,.0f}', 'Hallada; n = 5')
    for m in ['secuencial','base','alternativa']
], [100,105,145,118])
add('La base obtiene una pequeña reducción del tiempo frente a la secuencial. '
    'La alternativa tarda más en este caso porque los otros procesos exploran '
    'familias que no contienen el acierto inmediato, mientras la búsqueda de '
    'valores bajos avanza hacia 123456. Un mayor total de claves por segundo '
    'no implica menor tiempo hasta el hallazgo si se prueban más candidatas.')
add('Casos b) y c): alternativa', 'h2')
table(['Caso', 'Clave', 'Mediana (s)', 'Familia / estado'], [
    (tag+')', str(keys[tag]), f'{med(tag,"alternativa"):.9f}', 'Patrones; hallada, n = 5')
    for tag in ['b','c']
], [35,145,105,183])
add('Ambas claves se encuentran en la familia de potencias y vecinos. Son candidatas '
    'contiguas dentro de esa enumeración. La diferencia de sus medianas es pequeña '
    'y no permite concluir que aumentar en uno la clave produzca por sí mismo un '
    'cambio estable del rendimiento.')
add('Muestras interrumpidas desde cero', 'h2')
table(['Caso / programa', 'Tiempo real (s)', 'Intentos', 'Claves/s'], [
    (f'{tag}) {m}', f'{med(tag,m):.6f}',
     f'{med(tag,m,"attempts"):,.0f}', f'{med(tag,m,"rate"):,.0f}')
    for tag in ['b','c'] for m in ['secuencial','base']
], [115,105,138,110])
caption('Tabla 2. Medianas de cinco muestras por fila; código 3: tiempo agotado sin hallazgo. Cada campo se resume por separado.')
add(f'Las capturas del Anexo 2 son sesiones independientes con cortes de {cutoff} s. Sus tiempos individuales no sustituyen las medianas de esta serie.', 'small')

page('10. Estimaciones y speedup')
add('Proyección de las búsquedas exhaustivas', 'h2')
code('T_estimado(k) = (k + 1) / mediana(R_medido)\nSupuestos: inicio en 0; rango [0, 2^56); tasa constante.\nAños de referencia = segundos / (365.25 * 24 * 3600)')
table(['Caso', 'Programa', 'Proyección (s)', 'Años aprox.'], [
    (tag+')',m, f'{(keys[tag]+1)/med(tag,m,"rate"):.6g}',
     f'{(keys[tag]+1)/med(tag,m,"rate")/31557600:.1f}')
    for tag in ['b','c'] for m in ['secuencial','base']
], [40,100,180,148])
add('Estos valores son extrapolaciones del rendimiento de una muestra corta a '
    'décadas o siglos de cómputo. No son tiempos medidos hasta el hallazgo, ni '
    'predicciones con incertidumbre cuantificada. En MPI la expresión aproxima '
    'el trabajo por rondas; para claves tan grandes, el lote final es despreciable '
    'frente al número proyectado de intentos.')
add('Razones de tiempo', 'h2')
rows=[]
for tag in keys:
    seq=med(tag,'secuencial') if tag=='a' else (keys[tag]+1)/med(tag,'secuencial','rate')
    base=med(tag,'base') if tag=='a' else (keys[tag]+1)/med(tag,'base','rate')
    alt=med(tag,'alternativa')
    rows.append((tag+')', f'{seq/base:.2f}',f'{seq/base/4:.3f}',f'{base/alt:.3g}',
                 'Medida' if tag=='a' else 'Proyectada'))
table(['Caso','S base/sec','E base','G alt/base','Naturaleza'],rows,[40,95,75,100,158])
seq,base,alt=(med('a',m) for m in ['secuencial','base','alternativa'])
add(f'Para a), S = {seq:.9f} / {base:.9f} = <b>{seq/base:.3f}</b> y '
    f'E = <b>{100*seq/base/4:.1f} %</b>. La razón base/alternativa es '
    f'<b>{base/alt:.3f}</b>. Una razón menor que uno indica que la alternativa tarda más.')
add('Las razones de b) y c) combinan un tiempo exhaustivo proyectado con uno heurístico '
    'medido. Expresan una ventaja condicionada por las familias y la extrapolación; '
    'no son un speedup paralelo puro por usar cuatro procesos.')

page('10.1. Control de distribución', '10.1. Control de distribución')
control=[r for r in all_runs if r['phase']=='control']
def ctrl(mode,field='time'):
    return median(r[field] for r in control if r['mode']==mode)
table(['Programa','Mediana (s)','Mínimo (s)','Máximo (s)','Intentos med.'],[
    (m,f'{ctrl(m):.6f}',f'{min(r["time"] for r in control if r["mode"]==m):.6f}',
     f'{max(r["time"] for r in control if r["mode"]==m):.6f}',f'{ctrl(m,"attempts"):,.0f}')
    for m in ['secuencial','base','alternativa']], [100,95,85,85,103])
add('Condiciones: clave 750123, mismo archivo, rango [0, 1000000), lote 4096, '
    'cinco repeticiones por versión, cuatro procesos en MPI y -e en la alternativa. '
    'Se desactivan las familias heurísticas para comparar el reparto sobre el '
    'mismo espacio. Los intentos pueden diferir por la asignación y la anticipación '
    'de la parada, que forman parte del comportamiento de cada estrategia.')
add(f'La base obtiene S = <b>{ctrl("secuencial")/ctrl("base"):.3f}</b> y eficiencia '
    f'<b>{100*ctrl("secuencial")/ctrl("base")/4:.1f} %</b>. La razón base/alternativa '
    f'es <b>{ctrl("base")/ctrl("alternativa"):.3f}</b>; debe interpretarse con '
    'las muestras, los intentos y la dispersión conservada en resultados.md.')
add('Este control permite separar la priorización de patrones de la asignación '
    'dinámica. No demuestra superioridad universal ni garantiza el mismo resultado '
    'con otro tamaño de lote, hardware o clave. La variación de WSL y las diferencias '
    'de sondeo pueden modificar tanto el número de intentos como el tiempo.')
add('Correcciones verificadas','h2')
table(['Área','Validación realizada'],[
    ('Archivos','Clave 44 rechazada; alteración de primer bloque, longitud y etiqueta rechazada sin salida.'),
    ('Aritmética','Rangos que desbordan se rechazan; pruebas de búsqueda hasta UINT64_MAX - 1 sin vuelta a cero.'),
    ('MPI','Aciertos simultáneos, tiempo límite común, solicitudes dimensionadas según procesos y drenaje de envíos.'),
    ('Entorno','WSL/Open MPI 5: el lanzador trata retornos como normales y el helper recupera el consenso Estado MPI. Sin estado o ante timeout, falla.'),
], [110,358])


page('11. Discusión de resultados')
add('Influencia de la clave y el recorrido', 'h2')
add('En el recorrido ascendente, una clave baja se visita pronto y una clave '
    'alta requiere muchos intentos. El costo de descifrar con AES no crece '
    'por el valor decimal de la candidata; cambia su posición en la búsqueda. '
    'En la alternativa, una clave numéricamente grande puede visitarse pronto '
    'si tiene una estructura favorecida por las familias. La posición en la '
    'enumeración explica mejor el resultado que la magnitud aislada del entero.')
add('Distribución y comunicación', 'h2')
add('La base hace trabajo extra hasta cerrar la ronda y el proceso con más '
    'trabajo determina la espera colectiva. La alternativa permite avisar '
    'antes y asignar bloques a quien los solicite, a cambio de operaciones '
    'RMA, sondeo y generación de patrones. Para búsquedas cortas esos costos '
    'pueden dominar. En a), el número de intentos de la base es mayor que '
    'el secuencial, por lo que el cociente de tasas no coincide con el speedup '
    'hasta encontrar la clave.')
add('Ventajas y limitaciones de la alternativa', 'h2')
add('La priorización es útil para valores estructurados y evita fijar un '
    'offset junto a la clave en b) y c). Sin embargo, el conjunto de pruebas '
    'favorece precisamente las familias elegidas: una clave sin estructura '
    'puede depender del barrido de respaldo y tardar mucho más. Hay '
    'solapamiento de candidatas entre familias y la cobertura total depende '
    'de los límites; no se demuestra una aceleración general de AES-128.')
add('Retos y soluciones implementadas', 'h2')
add('Se separó el código original del laboratorio, se definió un formato de '
    'archivo verificable, se compartió la validación MPI desde P0 y se '
    'reutilizó un contexto EVP por proceso. Para las ejecuciones impracticables '
    'se añadió un corte de tiempo y se conservaron rendimiento e intentos. '
    'Las capturas usan --mca osc ^ucx para evitar avisos de ese componente en WSL.')
add('Correcciones y aprendizaje', 'h2')
add('Se corrigieron la aceptación de claves incorrectas con HMAC, la configuración '
    'del rango de medición, los desbordamientos en extremos de 64 bits, el consenso '
    'del tiempo agotado y el drenaje de aciertos simultáneos. Los parámetros se '
    'difunden con tipos MPI explícitos. En WSL se evita la ruta PRRTE de errores '
    'no-cero y el helper devuelve el consenso explícito Estado MPI del programa. '
    'La ausencia de ese estado invalida la ejecución; los timeouts no se reintentan. '
    'El aprendizaje es separar corrección, orden de búsqueda, coordinación y '
    'calidad de la evidencia antes de afirmar una mejora de rendimiento.')


page('12. Conclusiones y recomendaciones')
add('Conclusiones', 'h2')
for t in [
    '1. Se completaron carga, cifrado y recuperación autenticada de archivos, referencia secuencial y dos estrategias MPI. La verificación incluye un vector AES-128-ECB, 24 casos de archivos y 75 casos de búsqueda, con entradas inválidas, extremos numéricos y aciertos simultáneos.',
    f'2. Para 123456, la base obtiene un speedup medido de {seq/base:.3f} y eficiencia de {100*seq/base/4:.1f} %. La razón base/alternativa es {base/alt:.3f}. Estos valores corresponden a medianas de cinco ejecuciones y no garantizan mejoras para toda clave.',
    f'3. Las medianas alternativas para 2^54 y 2^54+1 son {med("b","alternativa"):.6f} s y {med("c","alternativa"):.6f} s. La priorización de potencias y vecinos permite encontrarlas sin fijar el offset junto a la clave.',
    f'4. El control exhaustivo de la clave 750123 obtiene una razón base/alternativa de {ctrl("base")/ctrl("alternativa"):.3f} con el mismo rango y lote. Es una comparación de distribución y parada sin priorización de familias.',
    '5. Las búsquedas largas de base y secuencial están correctamente configuradas para incluir las claves, pero se interrumpen por tiempo. Las proyecciones no representan hallazgos medidos. Tampoco se recorrió el espacio completo de AES-128.'
]: add(t)
add('Recomendaciones y continuidad', 'h2')
for t in [
    '1. Mantener los casos de regresión de autenticación, rangos y terminación en cada cambio; compilar y ejecutar las pruebas desde el ZIP antes de entregar.',
    '2. Usar los JSON y comandos conservados para repetir las mediciones. Para estudios de rendimiento más precisos, aislar carga, registrar afinidad y repetir en máquinas o nodos dedicados.',
    '3. Evaluar más claves sin estructura y tamaños de lote. Analizar dispersión e intentos junto con las medianas, sin atribuir al paralelismo la ganancia causada por el orden de candidatas.',
    '4. Conservar AES-128-ECB como esquema didáctico del experimento. Para una aplicación real, emplear un diseño autenticado normalizado y claves aleatorias de entropía completa.'
]: add(t)


page('13. Referencias bibliográficas')
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
    add(f'<link href="{url}" color="#006B54">{url}</link>', 'small')
add('[7] Universidad del Valle de Guatemala. (2026). <i>CC3069 - Proyecto 02.</i> '
    'Enunciado y rúbrica del curso Computación Paralela y Distribuida, Ciclo 2. Documento proporcionado con el proyecto.')
add('Fuentes primarias del experimento', 'h2')
add('Repositorio del Proyecto 02: proyecto02/src/, proyecto02/include/ y proyecto02/tests/. '
    'Resultados: evidencias/inciso2/bitacora.txt, resultados.json y resultados.md. '
    'Capturas y transcripciones: evidencias/inciso1/ y evidencias/inciso2/. '
    'Registro final de pruebas: evidencias/pruebas/ultima_prueba.txt.', 'small')
add('Las referencias web se consultaron para la elaboración del informe. Las explicaciones '
    'conceptuales están parafraseadas y señaladas con referencias numéricas en el cuerpo. '
    'Los diagramas y cálculos son de elaboración propia a partir del código y los registros.', 'small')

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

page('Anexo 2. Evidencia de compilación', 'Anexo 2. Compilación')
add('Las capturas reales de xterm se obtuvieron con Xvfb, en un namespace privado para no alterar WSLg. Cada una tiene transcripción .txt y hashes en evidencias/capturas.json. Son sesiones independientes de la serie de medianas.')
shot('evidencias/inciso1/01_compilacion.png',440)
caption('Figura A2.1. Entorno WSL, compilación de los cuatro ejecutables del proyecto y programas originales. Fuente: evidencias/inciso1/01_compilacion.png y compilacion.txt.')
add('Interpretación', 'h2')
add('Se observan los comandos make clean, make y make laboratorio, así como GCC '
    'y mpicc con enlace a libcrypto. Se generan aes_archivo, busqueda_secuencial, '
    'busqueda_base y busqueda_alternativa. La captura contiene la versión GCC '
    '15.2.0, Open MPI 5.0.10 y OpenSSL 3.5.5.')

page('Anexo 2. Evidencia de archivos', 'Anexo 2. Cifrado y descifrado')
shot('evidencias/inciso1/02_cifrado.png',240)
caption('Figura A2.2. Texto original, clave 123456 y representación hexadecimal del cifrado. Fuente: evidencias/inciso1/02_cifrado.png y cifrado.txt.')
shot('evidencias/inciso1/03_descifrado.png',240)
caption('Figura A2.3. Descifrado con la misma clave y lectura del archivo recuperado. Fuente: evidencias/inciso1/03_descifrado.png y descifrado.txt.')
add('Estas ejecuciones satisfacen la demostración de entrada, cifrado y recuperación '
    'del inciso 1. La equivalencia byte a byte se comprueba en la siguiente página.', 'small')

page('Anexo 2. Verificación y pruebas', 'Anexo 2. Verificación')
shot('evidencias/inciso1/04_verificacion.png',325)
caption('Figura A2.4. cmp, hashes SHA-256 iguales, rechazo de la clave incorrecta 44 y 24 casos de archivos. Fuente: evidencias/inciso1/04_verificacion.png y verificacion.txt.')
add('Registro final de pruebas', 'h2')
summary=[x for x in test_log.splitlines() if any(word in x for word in ['Fecha:','PASS:', 'limites,','Pruebas de','Código de salida:'])]
code('\n'.join(summary))
caption('Extracto de evidencias/pruebas/ultima_prueba.txt. El vector GCM corresponde al laboratorio y el vector ECB verifica el cifrado utilizado por el proyecto.')
add('Las regresiones cubren autenticación de contenido, longitud y etiqueta, límites de '
    'archivos y rangos, frases cortas, tiempo límite y aciertos simultáneos. El helper '
    'MPI conserva los códigos reales: 1 para entrada inválida, 2 para ausencia y '
    '3 para tiempo agotado. Un timeout externo provoca un fallo y no se contabiliza '
    'como prueba superada.', 'small')


for tag, num in [('a',5),('b',6),('c',7)]:
    page(f'Anexo 2. Caso {tag}): clave {keys[tag]}',f'Anexo 2. Captura del caso {tag})')
    shot(f'evidencias/inciso2/0{num-4}_clave_{tag}.png',455)
    caption(f'Figura A2.{num}. Ejecución de las tres versiones para la clave {keys[tag]}. '
            f'Fuente: evidencias/inciso2/0{num-4}_clave_{tag}.png y clave_{tag}.txt.')
    if tag=='a':
        add('Las tres versiones encuentran 123456. La captura corresponde a una ejecución '
            'individual de evidencia y no sustituye la mediana de las cinco muestras '
            'de la serie principal. Los comandos, la clave y la frase son visibles.')
    else:
        add(f'La secuencial y la base se interrumpen tras aproximadamente {cutoff} s '
            'sin hallar la clave y devuelven 3. El rango explícito [0, 2^56) incluye '
            'la candidata objetivo. La alternativa encuentra la clave en la familia '
            'de patrones sin conocerla como argumento de búsqueda. La configuración '
            'de PRRTE evita su ruta problemática de errores no-cero; el helper '
            'recupera el código real desde Estado MPI, mostrado en la salida.')


page('Anexo 2. Bitácora de mediciones', 'Anexo 2. Mediciones individuales')
add(f'Serie principal: {date}. Las columnas enumeran las cinco '
    'ejecuciones de la bitácora y la mediana calculada sin mezclar las sesiones de capturas.')
headers=['Caso / programa','1 (s)','2 (s)','3 (s)','4 (s)','5 (s)','Mediana']
rows=[]
for tag,mode in [('a','secuencial'),('a','base'),('a','alternativa'),('b','alternativa'),('c','alternativa')]:
    rs=selection(tag,mode)
    rows.append([f'{tag}) {mode}']+[f'{r["time"]:.6f}' for r in rs]+[f'{med(tag,mode):.6f}'])
table(headers,rows,[102,61,61,61,61,61,61])
add('Trazabilidad de las ejecuciones largas', 'h2')
table(['Caso / programa','Tiempo (s)','Intentos','Salida'],[
    (f'{tag}) {m}',f'{med(tag,m):.9f}',
     f'{med(tag,m,"attempts"):,.0f}', '3: tiempo agotado')
    for tag in ['b','c'] for m in ['secuencial','base']
], [115,115,125,113])
add(f'Cada fila larga resume {reps} ejecuciones con corte de {cutoff} s y rango '
    '[0, 2^56). Se conservan las muestras individuales, tasas, intentos y estados '
    'en resultados.json. Las medianas de intentos y de tiempo se calculan por '
    'separado, por lo que su cociente no necesariamente es la mediana de tasas.')


add('Cálculo reproducible de un ejemplo', 'h2')
r=med('b','base','rate')
code(f'Caso b), base: R = {r:.0f} claves/s\nT_proyectado = (18014398509481984 + 1) / {r:.0f}\nT_proyectado = {(keys["b"]+1)/r:.6g} s\nCondición: rango ampliado y rendimiento constante.\nLa ejecución registrada no encontró la clave.')
add('Archivos completos de soporte', 'h2')
add('bitacora.txt conserva comandos, salidas, intentos, tasas y códigos de '
    'salida; resultados.md conserva la tabla original; datos/clave_a.aes, '
    'clave_b.aes y clave_c.aes permiten comprobar cada entrada. Este informe '
    'mantiene las cifras originales y explicita sus condiciones de interpretación.')

page('Apéndice. Reproducción y entrega', 'Apéndice. Reproducción y entrega')
add('Desde una extracción nueva en Ubuntu o WSL', 'h2')
code('sudo apt install build-essential libssl-dev libopenmpi-dev openmpi-bin python3\nmake\nmake test\npython3 proyecto02/tests/ejecutar_pruebas.py 5 5\npython3 scripts/registrar_pruebas.py\npython3 informe/crear_informe.py\npython3 scripts/empaquetar.py')
add('Para generar el informe se necesitan ReportLab, Pillow y fuentes Arial o DejaVu '
    'Sans/Mono. Las pruebas y mediciones no requieren las librerías de PDF. '
    'Los archivos de salida AES deben ser nuevos. Para las claves grandes, los '
    'comandos de cifrado reciben el entero; la búsqueda solo recibe el archivo, '
    'la frase y los límites del recorrido, nunca la clave objetivo.')
add('Demostración de búsqueda con cuatro procesos', 'h2')
code('python3 scripts/mpi_utils.py --run proyecto02/build/busqueda_base '+chr(92)+'\n  -l 72057594037927936 -t 5 evidencias/inciso2/datos/clave_b.aes\npython3 scripts/mpi_utils.py --run '+chr(92)+'\n  proyecto02/build/busqueda_alternativa '+chr(92)+'\n  evidencias/inciso2/datos/clave_b.aes')
add('Estado final y límites del experimento', 'h2')
table(['Área','Estado'],[
    ('Programa','Cifrado autenticado, frase con confirmación, rangos sin desbordamiento y terminación MPI verificados.'),
    ('Pruebas','Vector AES-128-ECB, 24 casos de archivos y 75 casos de búsqueda; make test exige Open MPI.'),
    ('Mediciones','Cinco muestras por combinación, rango correcto, metadatos y control sin heurísticas. Proyecciones separadas.'),
    ('Entrega','Fuentes, ejecutables Linux, informe, evidencias, manifiesto SHA-256 y registro final de pruebas.'),
    ('Límites','Las búsquedas exhaustivas grandes siguen interrumpidas por costo. No se afirma haberlas completado ni haber roto AES-128.'),
], [105,363])
add('Las ampliaciones propuestas en recomendaciones corresponden a futuros estudios '
    'de rendimiento. Los fallos funcionales identificados durante la revisión fueron '
    'corregidos y se incorporaron regresiones.', 'small')


# Índice con números de página físicos; cada sección comienza en página nueva.
index_rows = [(title, str(i+1)) for i,title in enumerate(pages) if i>=2]
idx = Table([[p(escape(t),'small'),p(n,'small')] for t,n in index_rows], colWidths=[430,38])
idx.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                         ('TOPPADDING',(0,0),(-1,-1),2),
                         ('BOTTOMPADDING',(0,0),(-1,-1),2),
                         ('LINEBELOW',(0,0),(-1,-1),.2,colors.HexColor('#DFE7E2'))]))
story[index_position]=idx

def furniture(c, doc):
    if doc.page==1:
        return
    c.setStrokeColor(colors.HexColor('#CCDAD2'))
    c.setLineWidth(.5)
    c.line(72,748,540,748)
    c.setFillColor(GRAY)
    c.setFont('Body',7.5)
    c.drawString(72,759,'UVG  |  CC3069  |  Proyecto 02')
    c.drawRightString(540,759,'AES-128 y Open MPI')
    c.line(72,47,540,47)
    c.drawString(72,34,'Estrada · Pivaral · Estrada  |  Ciclo 2 de 2026')
    c.drawRightString(540,34,str(doc.page))
    if doc.page==4:
        c.line(72,83,235,83)
        c.setFont('Body',7)
        c.drawString(72,72,'1. NIST (2023), FIPS 197-upd1, resumen. Cita en inglés; enlace completo en la referencia [1].')

doc=SimpleDocTemplate(str(OUT), pagesize=(612,792), rightMargin=72,leftMargin=72,
                      topMargin=60,bottomMargin=60,
                      title='Proyecto 02 - Búsqueda de claves AES-128 con Open MPI',
                      author='Daniel Estrada; Andre Pivaral; Sebastian Estrada',
                      subject='Informe experimental, estrategias, resultados y anexos')
doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
if doc.page != len(pages):
    raise RuntimeError(f'El contenido desborda: {doc.page} paginas reales, {len(pages)} planificadas.')
shutil.copy2(OUT,ROOT/'informe/Informe_Proyecto_02.pdf')
inputs=['evidencias/inciso2/resultados.json','evidencias/capturas.json',
        'evidencias/pruebas/ultima_prueba.txt','informe/crear_informe.py']
provenance={'inputs':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in inputs},
            'pdf_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'paginas':doc.page}
(ROOT/'informe/procedencia.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
print(f'PDF: {OUT}\nPáginas planificadas: {len(pages)}')
for i,title in enumerate(pages,1):
    print(i,title)

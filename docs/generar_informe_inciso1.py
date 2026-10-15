"""Genera el informe del inciso 1 a partir del codigo y capturas reales de WSL.

Ejecutar con Python, reportlab y Pillow desde cualquier directorio.
"""
from pathlib import Path
from hashlib import sha256
from html import escape

from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "pdf" / "Informe_Inciso_1.pdf"
EVID = ROOT / "evidencias" / "inciso1" / "terminal"
FONT_DIR = Path("C:/Windows/Fonts")
if not FONT_DIR.exists():
    FONT_DIR = Path("/mnt/c/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("ArialBold", str(FONT_DIR / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("TimesNewRoman", str(FONT_DIR / "times.ttf")))
pdfmetrics.registerFont(TTFont("TimesNewRomanBold", str(FONT_DIR / "timesbd.ttf")))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="ArialBold")
W, H = 792, 612
M = 44
CW = W - 2 * M
INK = colors.HexColor("#172B35")
GREEN = colors.HexColor("#006B54")
GRAY = colors.HexColor("#53646D")
PALE = colors.HexColor("#EDF5F2")
BODY = ParagraphStyle("body", fontName="Arial", fontSize=11, leading=16,
                      textColor=INK, spaceAfter=8)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=9, leading=12)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=9, leading=12)


def p(text, y, x=M, width=CW, style=BODY):
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, H)
    paragraph.drawOn(c, x, y - height)
    return y - height - 9


def page(title, number, subtitle="PROYECTO 02 / CC3069 / INCISO 1"):
    c.setFillColor(GREEN)
    c.rect(0, H - 8, W, 8, fill=1, stroke=0)
    c.setFillColor(GRAY)
    c.setFont("Arial", 9)
    c.drawString(M, H - 35, subtitle)
    c.setFont("ArialBold", 23)
    c.setFillColor(INK)
    c.drawString(M, H - 68, title)
    c.setStrokeColor(colors.HexColor("#D8E1DD"))
    c.line(M, 38, W - M, 38)
    c.setFillColor(GRAY)
    c.setFont("Arial", 8)
    c.drawString(M, 23, "Universidad del Valle de Guatemala | Computación Paralela y Distribuida | 14 de octubre de 2026")
    c.drawRightString(W - M, 23, f"{number + 1} / 9")


def table(rows, widths, y, fontsize=9):
    data = [[Paragraph(escape(str(value)), CELL) for value in row] for row in rows]
    tab = Table(data, colWidths=widths)
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E1DD")),
    ]))
    _, height = tab.wrap(CW, H)
    assert y - height >= 45, ("Tabla fuera de pagina", y, height)
    tab.drawOn(c, M, y - height)
    return y - height - 12


def evidence_page(number, title, filename, caption, note):
    page(title, number, "ANEXO 2 / BITÁCORA DE PRUEBAS / CAPTURAS DIRECTAS")
    image = EVID / filename
    iw, ih = PILImage.open(image).size
    height = CW * ih / iw
    c.drawImage(str(image), M, 487 - height, width=CW, height=height)
    y = p(caption, 487 - height - 12, style=SMALL)
    p(note, y, style=SMALL)
    c.showPage()


def main():
    global c
    original = (ROOT / "datos" / "mensaje.txt").read_bytes()
    recovered = (EVID / "recuperado.txt").read_bytes()
    assert original == recovered
    assert not (EVID / "no_crear.txt").exists()
    digest = sha256(original).hexdigest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("Proyecto 02 - Inciso 1: cifrado y descifrado de archivos AES-128")
    c.setAuthor("Daniel Estrada; Andre Pivaral; Sebastian Estrada")
    c.setSubject("Informe técnico y evidencias de ejecución en Ubuntu / WSL")

    # Caratula vertical basada en la referencia del usuario. El cuerpo conserva
    # orientacion horizontal para mantener legibles las capturas de terminal.
    c.setPageSize((612, 792))
    c.setFillColor(colors.black)
    def centered(text, y, size=14, bold=False):
        c.setFont("TimesNewRomanBold" if bold else "TimesNewRoman", size)
        c.drawCentredString(306, y, text)
    centered("Universidad del Valle de Guatemala", 706, 16, True)
    centered("Facultad de Ingeniería", 687)
    centered("Computación Paralela y Distribuida - Semestre 2, 2026", 669)
    c.drawImage(str(ROOT / "docs/assets/escudo_uvg.png"), 176, 345,
                width=260, height=260, mask="auto")
    centered("Proyecto 02 - Entrega del inciso 1", 291, 16, True)
    centered("Cifrado y descifrado de archivos de texto", 268)
    centered("AES-128 con OpenSSL", 247, 13)
    centered("Integrantes:", 194, 13, True)
    centered("Daniel Estrada - 20853", 175, 13)
    centered("Andre Pivaral - 23574", 157, 13)
    centered("Sebastian Estrada - 21405", 139, 13)
    centered("Guatemala, 14 de octubre de 2026", 84, 13)
    centered("1", 37, 10)
    c.showPage()
    c.setPageSize((W, H))
    page("Índice", 1)
    y = p("Introducción, fundamentos y diseño ........................................................................ 3<br/>"
          "Evidencia de compilación ........................................................................................ 4<br/>"
          "Evidencia de cifrado ................................................................................................. 5<br/>"
          "Evidencia de descifrado ........................................................................................... 6<br/>"
          "Verificación y pruebas ............................................................................................. 7<br/>"
          "Anexo 1: catálogo de funciones y bibliotecas ........................................................... 8<br/>"
          "Discusión, conclusiones, recomendaciones y referencias ....................................... 9", 490)
    c.showPage()

    page("Introducción, fundamentos y diseño", 2)
    y = p("Se adaptó el código del Laboratorio 03 para leer un archivo de texto, cifrar su contenido "
          "con una clave numérica recibida como parámetro y recuperar los mismos bytes usando esa clave. "
          "El objetivo de este inciso es demostrar lectura, cifrado, descifrado y exactitud del resultado.", 503)
    y = p("<b>Fundamentos.</b> AES-128 utiliza claves de 128 bits (16 bytes) [1]. Se conserva el modo "
          "GCM del laboratorio, que combina cifrado y autenticación [2], mediante la interfaz EVP de OpenSSL [3]. "
          "El programa genera un nonce aleatorio de 12 bytes y conserva una etiqueta de 16 bytes. "
          "El texto descifrado solo se muestra y guarda después de verificar la autenticación.", y)
    y = p("<b>Representación de la clave.</b> <font name='Courier'>make_key</font> pone a cero los 16 bytes "
          "y coloca el entero en los últimos ocho, en orden big-endian. Para 123456, la clave es "
          "<font name='Courier'>0000000000000000000000000001e240</font>. "
          "Se preserva así la convención experimental del laboratorio; no se recorre todo el espacio de claves AES.", y)
    y = table([["Archivo AESLAB1 (texto ASCII)", "Contenido"],
               ["Líneas 1 y 2", "Identificador AESLAB1 y longitud original en bytes."],
               ["Líneas 3, 4 y 5", "Nonce, etiqueta y contenido cifrado en hexadecimal; no incluye la clave ni el texto original."]],
              [260, 444], y)
    y = p("<b>Flujo de ejecución</b>", y)
    y = p("<b>Cifrar:</b> validar argumentos → leer bytes del .txt → convertir clave → generar nonce → "
          "cifrar y obtener etiqueta → crear archivo AESLAB1 → mostrar original y cifrado.<br/>"
          "<b>Descifrar:</b> validar argumentos → cargar AESLAB1 → convertir clave → descifrar y autenticar → "
          "si autentica, guardar y mostrar el texto; si falla, salir con error sin guardar texto.", y, style=SMALL)
    p("<b>Alcance:</b> esta entrega desarrolla el inciso 1. La búsqueda por fuerza bruta, las estrategias MPI y "
      "las mediciones de speedup corresponden a los siguientes incisos; aquí no se presentan resultados de rendimiento.", y, style=SMALL)
    c.showPage()

    evidence_page(3, "Compilación y entorno", "01_compilacion.png",
        "<b>Figura 1.</b> Captura directa de Windows Terminal ejecutando Ubuntu mediante WSL. "
        "Se muestran la fecha, el núcleo Linux, OpenSSL y los comandos de GCC y mpicc generados por Make.",
        "<b>Resultado:</b> compilación de los cuatro ejecutables sin diagnósticos de error ni advertencias en esta ejecución. "
        "El ejecutable añadido para este inciso es <font name='Courier'>programas/aes_archivo</font>.")
    evidence_page(4, "Lectura del .txt y cifrado", "02_cifrado.png",
        "<b>Figura 2.</b> Lectura de datos/mensaje.txt y cifrado AES-128-GCM con el parámetro 123456. "
        "La salida muestra el texto original, la clave convertida a 16 bytes y el contenido cifrado en hexadecimal.",
        "<b>Resultado:</b> se guarda mensaje.aes con 33 bytes de contenido cifrado. La frase tiene 32 bytes ASCII "
        "y el archivo de prueba añade un salto de línea final. El nonce aleatorio hace que una nueva ejecución pueda producir otro cifrado.")
    evidence_page(5, "Descifrado y recuperación del texto", "03_descifrado.png",
        "<b>Figura 3.</b> Descifrado del archivo generado con la misma clave numérica 123456. "
        "El comando completo es visible; la terminal ajusta la última parte de la clave a la línea siguiente.",
        "<b>Resultado:</b> autenticación GCM correcta y escritura de recuperado.txt. "
        "El texto recuperado es la frase original y conserva su salto de línea final.")
    evidence_page(6, "Igualdad de archivos y manejo de errores", "04_verificacion.png",
        "<b>Figura 4.</b> Comparación con cmp, hashes SHA-256, ejecución de los 20 casos de prueba y rechazo de la clave 123457.",
        "<b>Resultado:</b> cmp retorna 0 y ambos hashes coinciden. Las 20 pruebas pasan. "
        "La clave incorrecta retorna 1 y no crea no_crear.txt. El hash del original y del recuperado es "
        f"<font name='Courier'>{digest}</font>.")

    page("Anexo 1. Catálogo de funciones y bibliotecas", 7)
    y = table([
        ["Función / archivo", "Entradas", "Salida y funcionamiento"],
        ["main / aes_archivo.c", "Operación, entrada, salida y clave.", "0 si termina correctamente; 1 si falla. Coordina validación, AES, guardado y presentación."],
        ["read_text / aes_archivo.c", "Ruta, buffer y puntero a longitud.", "1 o 0; lee hasta 4096 bytes en binario, detecta exceso o error y conserva bytes exactos."],
        ["write_output / aes_archivo.c", "Ruta, Dataset, texto y modo.", "1 o 0; crea la salida de forma exclusiva, serializa AESLAB1 o guarda el texto autenticado."],
        ["parse_number / aes_comun.h", "Texto decimal y puntero a uint64_t.", "1 o 0; valida dígitos y rango; rechaza UINT64_MAX, reservado por la búsqueda heredada."],
        ["make_key / aes_comun.h", "Entero de 64 bits y buffer de 16 bytes.", "Completa el buffer con la clave AES usando ceros iniciales y orden big-endian."],
        ["encrypt_message / aes_comun.h", "Contexto, clave, texto, longitud y Dataset con nonce.", "1 o 0; cifra con EVP y almacena longitud, cifrado y etiqueta GCM."],
        ["try_key / aes_comun.h", "Contexto, clave, Dataset y buffer de texto.", "1 si autentica, 0 si no, -1 si falla la API. Borra el texto provisional ante autenticación fallida."],
        ["load_dataset / aes_comun.h", "Ruta AESLAB1 y Dataset de destino.", "1 o 0; valida identificador, longitud, campos hexadecimales y fin de archivo."],
        ["read_hex / aes_comun.h", "Archivo, buffer y longitud.", "1 o 0; convierte pares hexadecimales y comprueba el salto de línea."],
        ["print_hex / aes_comun.h", "Flujo, bytes y longitud.", "Escribe los bytes como pares hexadecimales y termina con un salto de línea."],
    ], [171, 189, 344], 505)
    p("<b>Bibliotecas utilizadas:</b> stdio.h para archivos y presentación; stdlib.h, errno.h y stdint.h para "
      "conversión y tipos; string.h para buffers; openssl/evp.h para AES, contextos y autenticación; "
      "openssl/rand.h para RAND_bytes. La compilación enlaza libcrypto. Python 3 ejecuta las pruebas. "
      "Open MPI pertenece a los programas heredados y no participa en el cifrado de este inciso.", y, style=SMALL)
    c.showPage()

    page("Discusión, conclusiones y referencias", 8)
    y = p("<b>Discusión.</b> Los retos principales fueron conservar el formato del laboratorio, mantener exactamente "
          "los bytes del .txt y evitar escribir texto provisional antes de autenticarlo. Se reutilizaron las rutinas AES "
          "y se añadieron lectura binaria, comandos de archivo y creación exclusiva de salidas. El cargador se adaptó para archivos vacíos.", 503)
    y = p("<b>Conclusiones.</b> La demostración recuperó los 33 bytes originales y verificó su igualdad con cmp y SHA-256. "
          "Las pruebas cubrieron vacío, un byte, UTF-8, CRLF, 4096 bytes, claves grandes, claves inválidas, autenticación fallida, "
          "archivo alterado o truncado, lectura y escritura fallidas, protección de archivos y compatibilidad con el laboratorio. "
          "Se cumplieron los pasos funcionales de lectura, cifrado, descifrado y presentación requeridos para el inciso 1.", y)
    y = p("<b>Limitaciones y recomendaciones.</b> Se conserva el máximo de 4096 bytes por archivo y el dominio de claves "
          "numéricas de 0 a 18446744073709551614. Para archivos mayores se requerirá ampliar el manejo de datos. "
          "Para repetir las demostraciones se deben elegir archivos de salida nuevos. Los resultados de este inciso "
          "no permiten concluir nada sobre speedup ni sobre la eficiencia de la búsqueda MPI.", y)
    y = p("<b>Referencias bibliográficas</b>", y - 3)
    references = [
        '[1] NIST. (2023). <i>FIPS 197: Advanced Encryption Standard (AES).</i> '
        '<link href="https://csrc.nist.gov/pubs/fips/197/final" color="#006B54">https://csrc.nist.gov/pubs/fips/197/final</link>',
        '[2] Dworkin, M. (2007). <i>NIST SP 800-38D: Galois/Counter Mode (GCM) and GMAC.</i> '
        '<link href="https://csrc.nist.gov/pubs/sp/800/38/d/final" color="#006B54">https://csrc.nist.gov/pubs/sp/800/38/d/final</link>',
        '[3] OpenSSL Project. (s. f.). <i>EVP_CIPHER-AES.</i> '
        '<link href="https://docs.openssl.org/3.0/man7/EVP_CIPHER-AES/" color="#006B54">https://docs.openssl.org/3.0/man7/EVP_CIPHER-AES/</link>',
        '[4] Estrada, C. D. <i>Laboratorio 03: código base.</i> Commit e20c920fe0d105d2844889d7410563e12a3b3d1d. '
        '<link href="https://github.com/DannyEst6109/Laboratorio-3---Paralela" color="#006B54">Repositorio del Laboratorio 03</link>. '
        'Referencias consultadas el 14 de octubre de 2026.',
    ]
    for ref in references:
        y = p(ref, y, style=SMALL)
    y = p("<b>Material suplementario y reproducción.</b> El paquete de entrega incluye código fuente, Makefile, "
          "datos/mensaje.txt, pruebas, instrucciones de ejecución y capturas PNG con su registro de sesión. "
          "Desde la raíz: <font name='Courier'>make -C programas</font> y "
          "<font name='Courier'>python3 programas/probar_inciso1.py</font>. "
          "Los comandos de cifrado y descifrado se describen en README.md. Los archivos del ejemplo terminal "
          "y sus capturas se encuentran en evidencias/inciso1/terminal/.", y, style=SMALL)
    assert y >= 45, y
    c.showPage()
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()

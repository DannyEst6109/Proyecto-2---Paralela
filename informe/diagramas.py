"""Diagramas vectoriales del informe (ReportLab): flujos, esquemas de reparto y comunicacion."""
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors

INK = colors.HexColor("#172B35")
GREEN = colors.HexColor("#006B54")
PALE = colors.HexColor("#EDF5F2")
SOFT = colors.HexColor("#D8E1DD")
GOLD = colors.HexColor("#FFF4D6")
RED = colors.HexColor("#B3261E")
PROC = [colors.HexColor(c) for c in ("#CFE8DF", "#D6E4F5", "#F5E3CF", "#E8D6F0")]
FONT, BOLD = "Arial", "ArialBold"


def _text(d, cx, cy, text, size=7.5, font=FONT, color=INK):
    lines = text.split("\n")
    lead = size * 1.25
    top = cy + (len(lines) - 1) * lead / 2 - size * 0.35
    for i, line in enumerate(lines):
        d.add(String(cx, top - i * lead, line, fontName=font, fontSize=size,
                     fillColor=color, textAnchor="middle"))


def box(d, cx, cy, w, h, text, kind="proc", fill=PALE, size=7.5):
    """Nodo centrado en (cx, cy): proc (rectangulo), term (inicio/fin) o dec (rombo)."""
    if kind == "dec":
        d.add(Polygon([cx, cy + h / 2, cx + w / 2, cy, cx, cy - h / 2, cx - w / 2, cy],
                      fillColor=GOLD, strokeColor=INK, strokeWidth=0.7))
    else:
        r = h / 2 if kind == "term" else 3
        d.add(Rect(cx - w / 2, cy - h / 2, w, h, rx=r, ry=r,
                   fillColor=GREEN if kind == "term" else fill,
                   strokeColor=INK, strokeWidth=0.7))
    _text(d, cx, cy, text, size, BOLD if kind == "term" else FONT,
          colors.white if kind == "term" else INK)


def arrow(d, points, label=None, label_at=None, color=INK, dash=None):
    """Polilinea con punta de flecha en el ultimo punto."""
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.8, strokeDashArray=dash))
    (x1, y1), (x2, y2) = points[-2], points[-1]
    dx, dy = x2 - x1, y2 - y1
    n = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    ux, uy = dx / n, dy / n
    s = 5
    d.add(Polygon([x2, y2, x2 - s * ux + s * 0.45 * uy, y2 - s * uy - s * 0.45 * ux,
                   x2 - s * ux - s * 0.45 * uy, y2 - s * uy + s * 0.45 * ux],
                  fillColor=color, strokeColor=color, strokeWidth=0.5))
    if label:
        lx, ly = label_at or ((x1 + x2) / 2 + 4, (y1 + y2) / 2)
        d.add(String(lx, ly, label, fontName=BOLD, fontSize=7, fillColor=color))


def flujo_base(width=468):
    d = Drawing(width, 470)
    cx, w = 170, 230
    box(d, cx, 452, 120, 22, "Inicio (mpirun -np 4)", "term")
    box(d, cx, 410, w, 34, "Proceso 0: valida argumentos, carga\nel archivo AESECB1 y la frase")
    box(d, cx, 362, w, 34, "MPI_Bcast: parámetros y texto cifrado\na todos los procesos")
    box(d, cx, 318, w, 26, "base = offset; MPI_Barrier; inicia MPI_Wtime")
    box(d, cx, 270, w, 40, "Proceso p prueba su lote\n[base + p·B, base + (p+1)·B)\ndescifra y busca la frase")
    box(d, cx, 218, w, 28, "MPI_Allreduce(MIN) del resultado local")
    box(d, cx, 166, 150, 44, "¿Algún proceso\nencontró la clave?", "dec")
    box(d, cx, 104, 150, 44, "¿Rango agotado o\ntiempo límite?", "dec")
    box(d, 395, 104, 120, 28, "base = base + n·B\n(siguiente ronda)")
    box(d, cx, 46, w, 30, "MPI_Reduce: tiempo máximo y claves probadas.\nProceso 0 descifra y reporta")
    box(d, cx, 10, 80, 18, "Fin", "term")
    for y1, y2 in ((441, 427), (393, 379), (345, 331), (305, 290), (250, 232), (204, 188), (144, 126), (31, 19)):
        arrow(d, [(cx, y1), (cx, y2)])
    arrow(d, [(cx - 75, 166), (30, 166), (30, 46), (cx - w / 2, 46)], "sí", (34, 170))
    arrow(d, [(cx, 82), (cx, 61)], "sí", (cx + 5, 70))
    arrow(d, [(cx + 75, 104), (335, 104)], "no", (cx + 82, 108))
    arrow(d, [(395, 118), (395, 270), (cx + w / 2, 270)])
    d.add(String(cx + 5, 136, "no", fontName=BOLD, fontSize=7, fillColor=INK))
    return d


def reparto_base(width=468):
    """Rondas de lotes entrelazados: cada ronda cubre n·B claves consecutivas."""
    d = Drawing(width, 150)
    left, cell = 60, 100
    d.add(String(left, 138, "Claves en orden creciente  →", fontName=BOLD, fontSize=8, fillColor=INK))
    for r in range(3):
        y = 105 - r * 32
        d.add(String(8, y + 8, f"Ronda {r}" if r < 2 else "Ronda r", fontName=BOLD, fontSize=7.5, fillColor=INK))
        for p in range(4):
            x = left + p * cell
            d.add(Rect(x, y, cell - 4, 24, fillColor=PROC[p], strokeColor=INK, strokeWidth=0.5))
            lo = ["0", "B", "2B", "3B"][p] if r == 0 else (["4B", "5B", "6B", "7B"][p] if r == 1 else f"(4r+{p})B")
            _text(d, x + (cell - 4) / 2, y + 12, f"P{p}: desde {lo}", 7)
    d.add(String(left, 6, "B = 65 536 claves por lote. Al final de cada ronda hay un MPI_Allreduce: "
                 "ningún proceso avanza sin los demás.", fontName=FONT, fontSize=7, fillColor=INK))
    return d


def reparto_bloques(width=468):
    """Particion contigua de [0, 2^56) en 4 bloques y ubicacion de las claves de prueba."""
    d = Drawing(width, 120)
    left, seg = 20, 107
    labels = ["[0, 2^54)", "[2^54, 2·2^54)", "[2·2^54, 3·2^54)", "[3·2^54, 2^56)"]
    for p in range(4):
        x = left + p * seg
        d.add(Rect(x, 50, seg - 3, 26, fillColor=PROC[p], strokeColor=INK, strokeWidth=0.5))
        _text(d, x + seg / 2, 69, f"P{p}", 8, BOLD)
        _text(d, x + seg / 2, 57, labels[p], 6.8)
    for x, txt, y in ((left + 2, "a) 123 456\n(P0, intento 123 457)", 26),
                      (left + seg + 2, "b) 2^54 (P1, intento 1)\nc) 2^54+1 (P1, intento 2)", 26)):
        arrow(d, [(x, y + 12), (x, 49)], color=RED)
        d.add(String(x + 3, y + 4, txt.split("\n")[0], fontName=BOLD, fontSize=7, fillColor=RED))
        d.add(String(x + 3, y - 5, txt.split("\n")[1], fontName=FONT, fontSize=7, fillColor=RED))
    d.add(String(left, 100, "Reparto por bloques contiguos (análisis): cada proceso recorre 2^54 claves desde su inicio",
                 fontName=BOLD, fontSize=8, fillColor=INK))
    return d


def esquema_alternativa(width=468):
    d = Drawing(width, 215)
    fams = ["F0 valores bajos\n0 … 2^24−1", "F1 patrones humanos\nfechas, 2^k±1, 10^k±1,\nrepetidos, constantes",
            "F2 texto ASCII\n[a-z0-9]{1,5}", "F3 barrido exhaustivo\noffset … offset+límite"]
    for f in range(4):
        x = 12 + f * 114
        box(d, x + 52, 168, 104, 44, fams[f], fill=PROC[f], size=6.8)
        arrow(d, [(x + 52, 146), (x + 52, 118)])
    d.add(Rect(12, 86, 444, 30, fillColor=GOLD, strokeColor=INK, strokeWidth=0.7))
    _text(d, 234, 101, "Ventana RMA en el proceso 0: contador[f] = siguiente bloque libre de la familia f  "
          "(MPI_Fetch_and_op + MPI_Win_flush)", 7.2, BOLD)
    for p in range(4):
        x = 12 + p * 114 + 52
        box(d, x, 34, 90, 30, f"P{p}: empieza en F{p}\nluego F{(p + 1) % 4}, F{(p + 2) % 4}, F{(p + 3) % 4}",
            fill=PROC[p], size=6.8)
        arrow(d, [(x, 50), (x, 85)], "pide bloque", (x + 3, 66))
    d.add(String(12, 4, "Cuando un proceso agota su familia toma bloques de las demás (balanceo dinámico). "
                 "Bloque = 65 536 claves.", fontName=FONT, fontSize=7, fillColor=INK))
    return d


def flujo_alternativa(width=468):
    d = Drawing(width, 520)
    cx, w = 175, 240
    box(d, cx, 504, 120, 22, "Inicio (mpirun -np 4)", "term")
    box(d, cx, 466, w, 30, "mpi_setup: proceso 0 valida y difunde\nparámetros y texto cifrado (MPI_Bcast)")
    box(d, cx, 424, w, 30, "Crear ventana RMA con 4 contadores (proceso 0)\ny dejar abierto MPI_Irecv(TAG_ENCONTRADA)")
    box(d, cx, 382, w, 26, "familia f = (rank + s) mod 4\n(s vuelve a 0 al pedir cada bloque nuevo)")
    box(d, cx, 340, w, 30, "MPI_Fetch_and_op(+1) sobre contador[f]\n→ número de bloque asignado")
    box(d, cx, 286, 150, 44, "¿Bloque dentro\nde la familia?", "dec")
    box(d, 395, 286, 110, 34, "Marcar f agotada\ns = s + 1\n(si todas: terminar)")
    box(d, cx, 232, w, 34, "Probar cada clave del bloque: descifrar\ny buscar la frase; cada 4096 claves MPI_Test")
    box(d, cx, 176, 150, 44, "¿Clave hallada\no aviso recibido?", "dec")
    box(d, 395, 176, 110, 34, "MPI_Isend del aviso\n(clave, familia) a\ntodos los demás")
    box(d, cx, 116, w, 34, "Consenso: MPI_Allreduce(MIN) de la clave\ny de la familia; MPI_Reduce de tiempos")
    box(d, cx, 66, w, 34, "Limpieza: MPI_Waitall, MPI_Cancel, drenar\navisos repetidos, MPI_Win_free")
    box(d, cx, 24, 150, 22, "Proceso 0 reporta → Fin", "term")
    for y1, y2 in ((493, 481), (451, 439), (409, 395), (369, 355), (325, 308), (264, 249), (215, 198),
                   (154, 133), (99, 83), (49, 35)):
        arrow(d, [(cx, y1), (cx, y2)])
    arrow(d, [(cx + 75, 286), (340, 286)], "no", (cx + 80, 290))
    arrow(d, [(395, 303), (395, 382), (cx + w / 2, 382)])
    d.add(String(cx + 5, 258, "sí", fontName=BOLD, fontSize=7, fillColor=INK))
    arrow(d, [(cx - 75, 176), (30, 176), (30, 382), (cx - w / 2, 382)], "no: siguiente bloque", (34, 300))
    arrow(d, [(cx + 75, 176), (340, 176)], "hallada", (cx + 78, 180))
    arrow(d, [(395, 159), (395, 116), (cx + w / 2, 116)])
    d.add(String(cx + 5, 145, "aviso recibido", fontName=BOLD, fontSize=7, fillColor=INK))
    return d


def secuencia_aviso(width=468):
    """Diagrama de secuencia: P2 encuentra la clave y avisa al resto sin bloquearse."""
    d = Drawing(width, 250)
    xs = [60, 170, 280, 390]
    for p, x in enumerate(xs):
        box(d, x, 232, 70, 18, f"Proceso {p}", fill=PROC[p], size=7.5)
        d.add(Line(x, 222, x, 12, strokeColor=INK, strokeWidth=0.6, strokeDashArray=[3, 2]))
    for p, x in enumerate(xs):
        if p != 2:
            d.add(Rect(x - 4, 150, 8, 60, fillColor=PROC[p], strokeColor=INK, strokeWidth=0.5))
    d.add(Rect(xs[2] - 4, 168, 8, 42, fillColor=PROC[2], strokeColor=INK, strokeWidth=0.5))
    d.add(String(xs[2] + 8, 172, "¡frase encontrada!", fontName=BOLD, fontSize=7, fillColor=RED))
    for p in (0, 1, 3):
        arrow(d, [(xs[2], 164), (xs[p] + (5 if p < 2 else -5), 150 - abs(p - 2) * 4)], color=RED)
    d.add(String(xs[2] + 8, 162, "MPI_Isend(clave, familia)", fontName=FONT, fontSize=6.8, fillColor=RED))
    for p in (0, 1, 3):
        d.add(String(xs[p] + 8, 132, "MPI_Test = verdadero", fontName=FONT, fontSize=6.5, fillColor=INK))
        d.add(String(xs[p] + 8, 123, "→ deja de buscar", fontName=FONT, fontSize=6.5, fillColor=INK))
    d.add(Rect(30, 80, 390, 22, fillColor=GOLD, strokeColor=INK, strokeWidth=0.6))
    _text(d, 225, 91, "MPI_Allreduce(MIN): todos acuerdan la clave (y la familia)", 7.5, BOLD)
    d.add(Rect(30, 44, 390, 22, fillColor=PALE, strokeColor=INK, strokeWidth=0.6))
    _text(d, 225, 55, "MPI_Waitall / MPI_Cancel / MPI_Iprobe + MPI_Recv: no quedan mensajes pendientes", 7.2)
    d.add(String(xs[0] + 6, 22, "Proceso 0 imprime clave, mensaje y tiempo", fontName=BOLD, fontSize=7, fillColor=GREEN))
    return d


def flujo_cifrado(width=468):
    d = Drawing(width, 120)
    steps = ["Validar\nargumentos", "Leer .txt\n(≤ 4096 bytes)", "make_key:\nentero → 16 bytes",
             "AES-128-ECB\n+ PKCS#7", "Guardar AESECB1\n(archivo nuevo)"]
    steps2 = ["Cargar\nAESECB1", "make_key", "Descifrar y\nvalidar relleno", "¿Relleno\nválido?", "Guardar y mostrar\ntexto recuperado"]
    for row, (items, label, y) in enumerate(((steps, "cifrar", 88), (steps2, "descifrar", 28))):
        d.add(String(0, y + 20, label, fontName=BOLD, fontSize=7.5, fillColor=GREEN))
        for i, s in enumerate(items):
            x = 46 + i * 92
            box(d, x, y, 80, 32, s, "dec" if s.startswith("¿") else "proc", size=6.8)
            if i:
                arrow(d, [(x - 52, y), (x - 41, y)])
    d.add(String(310, 2, "no → error, no se crea archivo", fontName=FONT, fontSize=6.8, fillColor=RED))
    return d

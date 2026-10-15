#!/usr/bin/env python3
"""Ejecuta el inciso 1 y conserva comandos y salidas reales en TXT y HTML."""
from datetime import datetime
from html import escape
from pathlib import Path
import shlex
import subprocess
import tempfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidencias" / "inciso1"


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    date = datetime.now(ZoneInfo("America/Guatemala")).isoformat(timespec="seconds")
    with tempfile.TemporaryDirectory(prefix="proyecto02-evidencia-") as folder:
        cipher = Path(folder) / "mensaje.aes"
        recovered = Path(folder) / "recuperado.txt"
        rejected = Path(folder) / "clave_incorrecta.txt"
        steps = [
            ("01_compilacion", ["make", "-B", "-C", "programas"], 0),
            ("02_cifrado", ["programas/aes_archivo", "cifrar", "datos/mensaje.txt", str(cipher), "123456"], 0),
            ("03_descifrado", ["programas/aes_archivo", "descifrar", str(cipher), str(recovered), "123456"], 0),
            ("04_comparacion", ["cmp", "datos/mensaje.txt", str(recovered)], 0),
            ("05_clave_incorrecta", ["programas/aes_archivo", "descifrar", str(cipher), str(rejected), "123457"], 1),
            ("06_pruebas", ["python3", "programas/probar_inciso1.py"], 0),
        ]
        for name, args, expected in steps:
            result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            log = f"Fecha (Guatemala): {date}\nEntorno: Ubuntu / WSL\n"
            log += f"Directorio: {ROOT}\n\n$ {shlex.join(args)}\n"
            log += result.stdout + result.stderr + f"\nCodigo de salida: {result.returncode}\n"
            if name == "04_comparacion" and result.returncode == 0:
                log += "Verificacion: original y recuperado identicos byte a byte.\n"
            (EVIDENCE / f"{name}.txt").write_text(log, encoding="utf-8")
            page = '<!doctype html><html lang="es"><meta charset="utf-8">'
            page += '<title>Proyecto 02 - Evidencia de ejecucion</title><style>'
            page += 'body{margin:40px;background:#f5f6f8;color:#172334;font-family:Arial,sans-serif}'
            page += 'h1{font-size:26px}p{font-size:16px}pre{background:white;border:1px solid #ccd3dc;'
            page += 'padding:24px;font:15px/1.65 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}'
            page += '</style><h1>Proyecto 02 · Inciso 1</h1>'
            page += '<p>Registro de comandos y salidas reales. Vista del registro, no captura de una terminal.</p>'
            page += f'<pre>{escape(log)}</pre></html>'
            (EVIDENCE / f"{name}.html").write_text(page, encoding="utf-8")
            if result.returncode != expected:
                raise RuntimeError(log)
        assert recovered.read_bytes() == (ROOT / "datos/mensaje.txt").read_bytes()
        assert not rejected.exists()
        # Se conservan copias de los resultados de esta ejecucion, no datos del laboratorio.
        (EVIDENCE / "mensaje.aes").write_bytes(cipher.read_bytes())
        (EVIDENCE / "recuperado.txt").write_bytes(recovered.read_bytes())
    print(f"PASS: evidencia real guardada en {EVIDENCE}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Ejecuta las pruebas del enunciado (incisos 2 y 3) y guarda la bitacora en evidencias/.

Uso: python3 proyecto02/tests/ejecutar_pruebas.py [segundos_limite_claves_grandes] [repeticiones]
Para la base y la secuencial no es practico recorrer hasta 2^54 claves, por lo que esas
ejecuciones se cortan con -t y el tiempo total se estima con el rendimiento medido. La
alternativa, en cambio, mide esas claves de verdad: 2^56/4 (= 2^54) y 2^56/4+1 son una
potencia de 2 y una potencia de 2 mas uno, y caen en la familia "patrones humanos".
"""
from datetime import datetime
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "proyecto02" / "build"
OUT = ROOT / "evidencias" / "inciso2"
TEXT = ROOT / "proyecto02" / "datos" / "prueba_proyecto2.txt"
KEYS = {"a": 123456, "b": 2**56 // 4, "c": 2**56 // 4 + 1}
MPI = ["mpirun", "-np", "4"]
PROGRAMS = {
    "secuencial": [str(BUILD / "busqueda_secuencial")],
    "base": MPI + [str(BUILD / "busqueda_base")],
    "alternativa": MPI + [str(BUILD / "busqueda_alternativa")],
}


def rel(path):
    return str(Path(path).relative_to(ROOT)) if str(path).startswith(str(ROOT)) else str(path)


def run(log, command):
    shown = " ".join(rel(c) for c in command)
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    log.append(f"$ {shown}\n{result.stdout}[codigo de salida: {result.returncode}]\n")
    return result.stdout


def field(out, pattern):
    match = re.search(pattern, out)
    return float(match.group(1)) if match else None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    (OUT / "datos").mkdir(parents=True, exist_ok=True)
    log = [f"Fecha: {datetime.now(ZoneInfo('America/Guatemala')).isoformat(timespec='seconds')}\n"]
    cipher = {}
    for tag, key in KEYS.items():
        cipher[tag] = OUT / "datos" / f"clave_{tag}.aes"
        cipher[tag].unlink(missing_ok=True)
        run(log, [str(BUILD / "aes_archivo"), "cifrar", str(TEXT), str(cipher[tag]), str(key)])
    results = {}   # (tag, programa) -> (tiempo, claves/s, estimado)
    for tag, key in KEYS.items():
        for name, command in PROGRAMS.items():
            big = tag != "a"
            # Para la base y la secuencial, recorrer hasta 2^54 es inviable: se cortan
            # con -t y el tiempo se estima con el rendimiento. La alternativa SI mide
            # estas claves: 2^56/4 = 2^54 y 2^56/4+1 caen en la familia "patrones
            # humanos" (potencias de 2 y potencias +-1) y se hallan de inmediato.
            capped = big and name != "alternativa"
            extra = ["-t", str(limit)] if capped else []
            times, rates = [], []
            for _ in range(1 if capped else reps):
                out = run(log, command + extra + [str(cipher[tag])])
                times.append(field(out, r"Tiempo de busqueda: ([\d.]+)"))
                rates.append(field(out, r"Rendimiento: ([\d.]+)"))
                if not capped and f"Clave encontrada: {key}" not in out:
                    raise SystemExit(f"{name} no hallo la clave {key}")
            rate = median(rates)
            # Estimado (solo base y secuencial, que recorren en orden creciente): la clave
            # se halla tras ~key intentos a la tasa medida.
            results[(tag, name)] = (median(times), rate, (key + 1) / rate if capped else None)
    stamp = f"{datetime.now(ZoneInfo('America/Guatemala')):%Y%m%d-%H%M%S}"
    (OUT / "bitacora.txt").write_text("\n".join(log), encoding="utf-8")
    lines = [f"# Resultados (generado {stamp}, mediana de {reps} ejecuciones; -np 4)\n",
             "| Prueba | Clave | Programa | Tiempo (s) | Claves/s | Tipo |", "|---|---|---|---|---|---|"]
    for (tag, name), (seconds, rate, estimate) in results.items():
        shown = estimate if estimate else seconds
        kind = f"estimado (corte a {limit} s)" if estimate else "medido"
        lines.append(f"| {tag}) | {KEYS[tag]} | {name} | {shown:.6g} | {rate:.0f} | {kind} |")
    lines += ["", "| Prueba | Speedup base/sec | Eficiencia base | Alternativa vs base | Alternativa vs sec |", "|---|---|---|---|---|"]
    for tag in KEYS:
        seq, base, alt = (results[(tag, n)] for n in PROGRAMS)
        t = [(r[2] or r[0]) for r in (seq, base, alt)]
        lines.append(f"| {tag}) | {t[0]/t[1]:.2f} | {t[0]/t[1]/4:.2f} | {t[1]/t[2]:.3g} | {t[0]/t[2]:.3g} |")
    (OUT / "resultados.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

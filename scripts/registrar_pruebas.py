#!/usr/bin/env python3
"""Guarda el resultado de la compilación y las pruebas sin modificar las capturas."""
from datetime import datetime
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent


def main():
    date = datetime.now(ZoneInfo("America/Guatemala"))
    folder = ROOT / "evidencias" / "pruebas" / date.strftime("%Y%m%d-%H%M%S-%f")
    folder.mkdir(parents=True)
    result = subprocess.run(["make", "test"], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = f"Fecha: {date.isoformat(timespec='seconds')}\n$ make test\n"
    log += result.stdout + f"\nCódigo de salida: {result.returncode}\n"
    (folder / "pruebas.txt").write_text(log, encoding="utf-8")
    print(log, end="")
    print(f"Registro: {folder / 'pruebas.txt'}")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Guarda el resultado de la compilación y las pruebas sin modificar las capturas."""
from datetime import datetime
from pathlib import Path
from mpi_utils import run_command
import hashlib
import json
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent


def main():
    date = datetime.now(ZoneInfo("America/Guatemala"))
    folder = ROOT / "evidencias" / "pruebas"
    folder.mkdir(parents=True, exist_ok=True)
    result = run_command(['make', '-B', 'test'], cwd=ROOT, timeout=300)
    log = f"Fecha: {date.isoformat(timespec='seconds')}\n$ make -B test\n"
    log += result.stdout + f"\nCódigo de salida: {result.returncode}\n"
    (folder / 'ultima_prueba.txt').write_text(log, encoding='utf-8')
    sources=[ROOT/'Makefile', ROOT/'proyecto02/Makefile', ROOT/'scripts/mpi_utils.py']
    sources += [p for folder in ['proyecto02/src','proyecto02/include','proyecto02/tests']
                for p in (ROOT/folder).rglob('*') if p.suffix in {'.c','.h','.py'}]
    state={'codigo':result.returncode,'fecha':date.isoformat(timespec='seconds'),
           'fuentes_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sources}}
    (ROOT/'evidencias/pruebas/resultado_final.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(log, end="")
    print(f"Registro: {folder / 'ultima_prueba.txt'}")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

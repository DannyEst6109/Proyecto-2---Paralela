#!/usr/bin/env python3
"""Pruebas de los incisos 2 y 3: busqueda secuencial, base MPI y alternativa MPI."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys

PROJECT = Path(__file__).resolve().parents[1]
BUILD = PROJECT / "build"
TEXT = b"Esta es una prueba de proyecto 2"
KEY_BIG = 2**56 // 4
sys.path.insert(0, str(PROJECT.parent / 'scripts'))
from mpi_utils import mpi_prefix, run_command
MPIRUN = mpi_prefix() if shutil.which('mpirun') else None


def run(args, ok=(0,)):
    result = run_command(args, timeout=90)
    assert result.returncode in ok, (args, result.returncode, result.stdout, result.stderr)
    return result


def encrypt(root, name, key, text=TEXT):
    source, cipher = root / f"{name}.txt", root / f"{name}.aes"
    source.write_bytes(text)
    run([BUILD / "aes_archivo", "cifrar", source, cipher, key])
    return cipher


def found_key(output):
    match = re.search(r"Clave encontrada: (\d+)", output)
    return int(match.group(1)) if match else None


def main():
    count = 0
    programs = [[BUILD / "busqueda_secuencial"]]
    if MPIRUN:
        programs += [MPIRUN + [BUILD / "busqueda_base"], MPIRUN + [BUILD / "busqueda_alternativa"]]
    else:
        raise SystemExit('Falta mpirun: la verificacion completa requiere Open MPI.')
    with tempfile.TemporaryDirectory(prefix="proyecto02-busqueda-") as folder:
        root = Path(folder)
        # Claves bajas: las tres versiones deben hallar exactamente la misma clave.
        for key in (0, 1, 7, 123456, 70000):
            cipher = encrypt(root, f"k{key}", key)
            for program in programs:
                out = run(program + [cipher]).stdout
                assert found_key(out) == key and "es una prueba de" in out, (program, key, out)
                count += 1
        # Familias de la estrategia alternativa. Las claves estructuradas se hallan
        # por su familia sin offset: la clave del enunciado 2^56/4 = 2^54 es potencia
        # de 2 y 2^56/4+1 es potencia de 2 mas uno, asi que caen en "patrones humanos".
        # El barrido exhaustivo (clave sin estructura) solo se mide acotandolo con -o.
        if MPIRUN:
            alt = MPIRUN + [BUILD / "busqueda_alternativa"]
            for key, family, off in ((20240131, "patrones humanos", None),
                    (int.from_bytes(b"clave", "big"), "texto ASCII", None),
                    (KEY_BIG, "patrones humanos", None),
                    (KEY_BIG + 1, "patrones humanos", None),
                    (5_000_123_456, "barrido exhaustivo", 5_000_000_000)):
                cipher = encrypt(root, f"a{key}", key)
                extra = ["-o", off] if off is not None else []
                out = run(alt + extra + [cipher]).stdout
                assert found_key(out) == key and f"Familia de la clave: {family}" in out, (key, out)
                count += 1
            # Lotes pequenos y rango con clave en la frontera.
            cipher = encrypt(root, "lote", 999)
            for program in programs[1:]:
                out = run(program + ["-b", 7, cipher]).stdout
                assert found_key(out) == 999
                count += 1
        # La busqueda base respeta el limite y el tiempo maximo.
        cipher = encrypt(root, "fuera", 5000)
        for program in programs[:2]:
            result = run(program + ["-l", 5000, cipher], ok=(2,))
            assert "No se encontro la clave" in result.stdout
            assert found_key(run(program + ["-l", 5001, cipher]).stdout) == 5000
            count += 2
        cipher = encrypt(root, "grande", KEY_BIG)
        for program in programs:
            if program[-1].name == "busqueda_alternativa":
                continue
            result = run(program + ["-t", 1, "-l", 2**40, cipher], ok=(3,))
            assert "Tiempo limite alcanzado" in result.stdout
            count += 1
        # Frase propia y frase que no aparece en el mensaje.
        cipher = encrypt(root, "frase", 321, b"hola mundo secreto")
        for program in programs:
            assert found_key(run(program + ["-f", "mundo", cipher]).stdout) == 321
            extra = ['-e', '-o', 0] if program[-1].name == 'busqueda_alternativa' else []
            run(program + extra + ["-f", "ausente", "-l", 1000, cipher], ok=(2,))
            count += 2
        # Mismo intervalo, frase corta (HMAC evita falsos positivos) y extremo uint64.
        for key, offset, limit in ((321, 0, 1000), (2**64-2, 2**64-5, 4)):
            cipher = encrypt(root, f'borde{key}', key, b'x es una prueba de')
            for program in programs:
                extra = ['-e'] if program[-1].name == 'busqueda_alternativa' else []
                result = run(program + extra + ['-o', offset, '-l', limit, '-b', 7, '-f', 'x', cipher])
                assert found_key(result.stdout) == key
                count += 1
        # La alternativa debe devolver 3 en todos los ranks cuando vence el tiempo.
        cipher = encrypt(root, 'tiempo_alt', KEY_BIG)
        run(programs[2] + ['-e', '-o', 0, '-l', 2**56, '-t', 1, cipher], ok=(3,))
        count += 1
        # Aciertos simultaneos: 0 aparece en bajos y patrones; no debe bloquearse.
        cipher = encrypt(root, 'simultaneo', 0)
        for _ in range(4):
            assert found_key(run(programs[2] + ['-b', 1, cipher]).stdout) == 0
            count += 1
        # Entradas invalidas: no deben bloquearse ni fallar con senales.
        bad = root / "malo.aes"
        bad.write_text("AESECB1\n5\nzz\n")
        cipher = encrypt(root, "ok", 1)
        for program in programs:
            for args in ([root / "no_existe.aes"], [bad], ["-l", 0, cipher], ["-l", "abc", cipher],
                         ["-b", 0, cipher], ["-f", "", cipher], ["-f", "x" * 65, cipher],
                         ["-f", "esta frase es mas larga que el mensaje del archivo ok.", cipher],
                         ['-o', 2**64-2, '-l', 4, cipher], []):
                run(program + args, ok=(1,))
                count += 1
    print(f"Pruebas de busqueda (incisos 2 y 3): {count} casos correctos")


if __name__ == "__main__":
    main()

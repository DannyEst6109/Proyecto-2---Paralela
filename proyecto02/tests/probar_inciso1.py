#!/usr/bin/env python3
"""Pruebas de archivos, autenticacion y compatibilidad del inciso 1."""
from pathlib import Path
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parent / "laboratorio03" / "programas"


def run(*args, ok=True):
    executable = PROJECT / "build" / args[0] if args[0] == "aes_archivo" else LAB / args[0]
    result = subprocess.run([str(executable), *map(str, args[1:])],
                            capture_output=True)
    assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
    return result


def main():
    count = 0
    with tempfile.TemporaryDirectory(prefix="proyecto02-inciso1-") as folder:
        root = Path(folder)
        # Exactitud byte a byte: vacio, UTF-8, CRLF y limite de lectura.
        for index, message in enumerate((b"", b"x", b"Esta es una prueba de proyecto 2",
                "Texto con tildes: áéíóú y ñ\nSegunda línea.\n".encode(),
                b"linea 1\r\nlinea 2\r\n", b"z" * 4096)):
            source = root / f"entrada {index}.txt"
            cipher = root / f"cifrado {index}.aes"
            recovered = root / f"recuperado {index}.txt"
            source.write_bytes(message)
            key = "18014398509481985" if index % 2 else "123456"
            run("aes_archivo", "cifrar", source, cipher, key)
            run("aes_archivo", "descifrar", cipher, recovered, key)
            assert recovered.read_bytes() == message
            count += 1

        source = root / "entrada 2.txt"
        cipher = root / "cifrado 2.aes"
        output = root / "no_crear.txt"
        for key in ("123457", "-1", "abc", "18446744073709551616"):
            run("aes_archivo", "descifrar", cipher, output, key, ok=False)
            assert not output.exists()
            count += 1

        damaged = root / "alterado.aes"
        lines = cipher.read_text().splitlines()
        lines[3] = ("0" if lines[3][0] != "0" else "1") + lines[3][1:]
        damaged.write_text("\n".join(lines) + "\n")
        run("aes_archivo", "descifrar", damaged, output, "123456", ok=False)
        assert not output.exists()
        count += 1
        damaged.write_bytes(cipher.read_bytes()[:15])
        run("aes_archivo", "descifrar", damaged, output, "123456", ok=False)
        assert not output.exists()
        count += 1

        oversized = root / "grande.txt"
        oversized.write_bytes(b"x" * 4097)
        for path in (oversized, root / "ausente.txt", root):
            run("aes_archivo", "cifrar", path, output, "123456", ok=False)
            assert not output.exists()
            count += 1

        original = source.read_bytes()
        run("aes_archivo", "cifrar", source, source, "123456", ok=False)
        run("aes_archivo", "descifrar", cipher, source, "123456", ok=False)
        assert source.read_bytes() == original
        count += 1
        run("aes_archivo", "cifrar", source, root / "ausente" / "salida.aes",
            "123456", ok=False)
        run("aes_archivo", ok=False)
        count += 2

        # Archivos compatibles en ambas direcciones con la base del laboratorio.
        legacy = root / "laboratorio.aes"
        run("busqueda_clave_aes_mejorada", "preparar", legacy, "7", "Mensaje heredado")
        run("aes_archivo", "descifrar", legacy, output, "7")
        assert output.read_bytes() == b"Mensaje heredado"
        new = root / "nuevo.aes"
        run("aes_archivo", "cifrar", source, new, "7")
        result = run("busqueda_clave_aes_mejorada", "buscar", new, "8")
        assert b"Clave encontrada: 7\n" in result.stdout
        count += 2
    print(f"PASS: {count} casos del inciso 1; archivos identicos byte a byte,")
    print("limites, errores, autenticacion y compatibilidad con el Laboratorio 03.")


if __name__ == "__main__":
    main()

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
        for key in ("44", "123457", "-1", "abc", "18446744073709551616"):
            run("aes_archivo", "descifrar", cipher, output, key, ok=False)
            assert not output.exists()
            count += 1

        # Formato (cabecera, longitud y texto cifrado) en lineas 0, 1 y 2.
        damaged = root / "alterado.aes"
        lines = cipher.read_text().splitlines()
        # Alterar el ultimo bloque del texto cifrado invalida el relleno PKCS#7.
        lines[2] = lines[2][:-1] + ("0" if lines[2][-1] != "0" else "1")
        damaged.write_text("\n".join(lines) + "\n")
        run("aes_archivo", "descifrar", damaged, output, "123456", ok=False)
        assert not output.exists()
        count += 1
        # Un cambio en un bloque inicial conserva el relleno, pero debe fallar el HMAC.
        for line_index, byte_index in ((2, 0), (3, 0)):
            lines = cipher.read_text().splitlines()
            value = lines[line_index]
            lines[line_index] = ('1' if value[byte_index] != '1' else '0') + value[1:]
            damaged.write_text('\n'.join(lines) + '\n')
            run('aes_archivo', 'descifrar', damaged, output, '123456', ok=False)
            assert not output.exists()
            count += 1
        # Cambiar la longitud sin cambiar el numero de bloques tambien se autentica.
        lines = cipher.read_text().splitlines()
        lines[1] = str(int(lines[1]) + 1)
        damaged.write_text('\n'.join(lines) + '\n')
        run('aes_archivo', 'descifrar', damaged, output, '123456', ok=False)
        assert not output.exists()
        count += 1
        damaged.write_bytes(cipher.read_bytes()[:15])
        run("aes_archivo", "descifrar", damaged, output, "123456", ok=False)
        assert not output.exists()
        count += 1
        # Un formato sin autenticacion no se acepta como el formato nuevo.
        lines = cipher.read_text().splitlines()
        damaged.write_text('AESECB1\n' + '\n'.join(lines[1:3]) + '\n')
        run('aes_archivo', 'descifrar', damaged, output, '123456', ok=False)
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

        # El Laboratorio 03 usa AES-128-GCM (cabecera AESLAB1); este proyecto usa
        # AES-128-ECB (cabecera AESECB1). Los formatos son incompatibles a proposito:
        # un archivo del laboratorio debe rechazarse en lugar de leerse mal.
        legacy = root / "laboratorio.aes"
        run("busqueda_clave_aes_mejorada", "preparar", legacy, "7", "Mensaje heredado")
        run("aes_archivo", "descifrar", legacy, output, "7", ok=False)
        assert not output.exists()
        count += 1
    print(f"PASS: {count} casos del inciso 1; archivos identicos byte a byte,")
    print("limites, autenticacion HMAC, errores y formatos ajenos (AES-128-ECB).")


if __name__ == "__main__":
    main()

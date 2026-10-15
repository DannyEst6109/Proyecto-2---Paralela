"""Empaqueta las fuentes, el informe y las evidencias del inciso 1."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output" / "Entrega_Inciso_1.zip"


def main():
    files = [ROOT / "README.md", ROOT / ".gitignore"]
    for folder in ("programas", "docs", "datos", "evidencias/inciso1"):
        files += [path for path in (ROOT / folder).rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts
                  and (path.suffix in {".c", ".h", ".py", ".sh", ".md", ".txt", ".html", ".png", ".aes"}
                       or path.name == "Makefile")]
    files.append(ROOT / "output/pdf/Informe_Inciso_1.pdf")
    # Se incluyen los binarios Linux producidos por la compilacion fotografiada.
    for name in ("aes_archivo", "busqueda_clave_aes_secuencial",
                 "busqueda_clave_aes_mejorada", "busqueda_clave_aes_mpi"):
        files.append(ROOT / "programas" / name)
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
    print(f"{OUTPUT}: {len(set(files))} archivos, {OUTPUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()

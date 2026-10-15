"""Empaqueta fuentes, ejecutables Linux, informe y evidencias del inciso 1."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "entregas" / "Entrega_Inciso_1.zip"


def main():
    files = [ROOT / name for name in ("README.md", ".gitignore", ".gitattributes", "Makefile")]
    for folder in ("laboratorio03", "proyecto02", "informe", "evidencias/inciso1", "scripts"):
        files += [path for path in (ROOT / folder).rglob("*")
                  if path.is_file()
                  and not {"__pycache__", "build", "resultados", "evidencias"}.intersection(path.relative_to(ROOT / folder).parts[:-1])
                  and (path.suffix in {".c", ".h", ".py", ".md", ".txt", ".png", ".aes", ".pdf"}
                       or path.name == "Makefile")]
    binaries = [ROOT / "proyecto02/build/aes_archivo"]
    binaries += [ROOT / "laboratorio03/programas" / name for name in
                 ("busqueda_clave_aes_secuencial", "busqueda_clave_aes_mejorada", "busqueda_clave_aes_mpi")]
    if not all(path.is_file() for path in binaries):
        raise SystemExit("Primero ejecute make test para compilar ambos proyectos.")
    OUTPUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(set(files + binaries)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        print(f"{OUTPUT}: {len(archive.namelist())} archivos")


if __name__ == "__main__":
    main()

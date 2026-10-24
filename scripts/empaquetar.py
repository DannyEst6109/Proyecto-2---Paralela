"""Empaqueta fuentes, ejecutables Linux, informe y evidencias del proyecto."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "entregas" / "Entrega_Proyecto_02.zip"


def main():
    files = [ROOT / name for name in ("README.md", ".gitignore", ".gitattributes", "Makefile")]
    required = ['informe/Informe_Proyecto_02.pdf', 'evidencias/pruebas/ultima_prueba.txt',
                'evidencias/inciso2/resultados.json', 'evidencias/capturas.json',
                'informe/procedencia.json','evidencias/pruebas/resultado_final.json']
    for name in required:
        if not (ROOT/name).is_file():
            raise SystemExit(f'Falta el entregable obligatorio: {name}')
        files.append(ROOT/name)
    if not (ROOT/required[0]).read_bytes().startswith(b'%PDF-'):
        raise SystemExit('El informe no es un PDF valido.')
    if 'Código de salida: 0' not in (ROOT/required[1]).read_text(encoding='utf-8'):
        raise SystemExit('Las pruebas finales no pasaron.')
    results=json.loads((ROOT/required[2]).read_text(encoding='utf-8'))
    if not results['metadata'].get('completo') or len(results['runs'])!=12*results['metadata']['repeticiones']:
        raise SystemExit('Las mediciones estan incompletas.')
    for name, digest in results['metadata']['fuentes_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise SystemExit(f'Las fuentes cambiaron desde las mediciones: {name}')
    validation=json.loads((ROOT/required[5]).read_text(encoding='utf-8'))
    if validation['codigo']!=0: raise SystemExit('Fallo la ultima verificacion.')
    for name,digest in validation['fuentes_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise SystemExit(f'Hay cambios sin probar: {name}')
    provenance=json.loads((ROOT/required[4]).read_text(encoding='utf-8'))
    for name,digest in provenance['inputs'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise SystemExit(f'El informe esta desactualizado respecto a {name}')
    if hashlib.sha256((ROOT/required[0]).read_bytes()).hexdigest()!=provenance['pdf_sha256']:
        raise SystemExit('El PDF no coincide con su procedencia.')
    screenshots=json.loads((ROOT/required[3]).read_text(encoding='utf-8'))
    if len(screenshots)!=7: raise SystemExit('Deben existir siete capturas finales.')
    for record in screenshots:
        image=ROOT/record['captura']
        transcript=image.parent/(record['sesion']+'.txt')
        if (hashlib.sha256(image.read_bytes()).hexdigest()!=record['png_sha256']
            or hashlib.sha256(transcript.read_bytes()).hexdigest()!=record['txt_sha256']):
            raise SystemExit('Captura o transcripcion desactualizada: '+record['sesion'])
    for folder in ("laboratorio03", "proyecto02", "informe", "evidencias/inciso1", "evidencias/inciso2", "scripts"):
        files += [path for path in (ROOT / folder).rglob("*")
                  if path.is_file()
                  and not {"__pycache__", "build", "resultados", "evidencias"}.intersection(path.relative_to(ROOT / folder).parts[:-1])
                  and (path.suffix in {".c", ".h", ".py", ".sh", ".ps1", ".md", ".txt", ".png", ".aes", ".pdf", ".json"}
                       or path.name == "Makefile")]
    binaries = [ROOT / "proyecto02/build" / name for name in
                ("aes_archivo", "busqueda_secuencial", "busqueda_base", "busqueda_alternativa")]
    binaries += [ROOT / "laboratorio03/programas" / name for name in
                 ("busqueda_clave_aes_secuencial", "busqueda_clave_aes_mejorada", "busqueda_clave_aes_mpi")]
    if not all(path.is_file() for path in binaries):
        raise SystemExit("Primero ejecute make test para compilar ambos proyectos.")
    OUTPUT.parent.mkdir(exist_ok=True)
    manifest={}
    temporary=OUTPUT.with_suffix('.zip.tmp')
    with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(set(files + binaries)):
            name=path.relative_to(ROOT).as_posix()
            archive.write(path, name)
            info=archive.getinfo(name)
            info.create_system=3
            info.external_attr=(stat.S_IFREG | (0o755 if path in binaries else 0o644)) << 16
            manifest[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        archive.writestr('MANIFIESTO_SHA256.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(OUTPUT)
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        print(f"{OUTPUT}: {len(archive.namelist())} archivos")


if __name__ == "__main__":
    main()

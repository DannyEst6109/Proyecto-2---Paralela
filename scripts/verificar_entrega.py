#!/usr/bin/env python3
"""Verifica integridad, manifiesto, ejecutables y entregables del ZIP final."""
import hashlib
import json
from pathlib import Path
import sys
import argparse
from datetime import datetime
import os
import tempfile
from zoneinfo import ZoneInfo
from mpi_utils import run_command
from zipfile import ZipFile


def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip',nargs='?',type=Path,default=root/'entregas/Entrega_Proyecto_02.zip')
    parser.add_argument('--ejecutar',action='store_true',help='Recompila y prueba una extraccion temporal en Linux/WSL.')
    args=parser.parse_args()
    path=args.zip
    with ZipFile(path) as archive:
        assert archive.testzip() is None, 'Error CRC del ZIP'
        names=archive.namelist()
        assert len(names)==len(set(names)), 'Rutas duplicadas'
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names), 'Ruta insegura'
        manifest=json.loads(archive.read('MANIFIESTO_SHA256.json'))
        assert set(manifest)==set(names)-{'MANIFIESTO_SHA256.json'}, 'Manifiesto incompleto'
        for name,digest in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest, name
        for name in ['aes_archivo','busqueda_secuencial','busqueda_base','busqueda_alternativa']:
            name='proyecto02/build/'+name
            assert archive.read(name).startswith(b'\x7fELF'), 'Ejecutable no Linux: '+name
            assert (archive.getinfo(name).external_attr>>16)&0o111, 'Falta permiso ejecutable'
        assert archive.read('informe/Informe_Proyecto_02.pdf').startswith(b'%PDF-')
        assert 'Código de salida: 0' in archive.read('evidencias/pruebas/ultima_prueba.txt').decode()
        data=json.loads(archive.read('evidencias/inciso2/resultados.json'))
        assert data['metadata']['completo']
        assert len(data['runs'])==12*data['metadata']['repeticiones']
        for name in ['a','b','c','control']:
            assert archive.read(f'evidencias/inciso2/datos/clave_{name}.aes').startswith(b'AESECB2\n')
        print(f'PASS: ZIP, {len(manifest)} archivos SHA-256, PDF, ELF y mediciones completos.')
        if args.ejecutar:
            with tempfile.TemporaryDirectory(prefix='proyecto02-entrega-') as folder:
                target=Path(folder)
                archive.extractall(target)
                for info in archive.infolist():
                    destination=target/info.filename
                    if destination.is_file(): os.chmod(destination,(info.external_attr>>16)&0o777)
                log=(f'Fecha: {datetime.now(ZoneInfo("America/Guatemala")).isoformat(timespec="seconds")}\n'
                     f'ZIP SHA256: {hashlib.sha256(path.read_bytes()).hexdigest()}\n')
                for command in [['make','clean'],['make','-B','test']]:
                    result=run_command(command,cwd=target,timeout=300)
                    log+='$ '+' '.join(command)+'\n'+result.stdout+f'\nCódigo de salida: {result.returncode}\n'
                    (root/'evidencias/pruebas/entrega_extraida.txt').write_text(log,encoding='utf-8')
                    if result.returncode:
                        raise RuntimeError('Fallo en la extraccion nueva; consultar entrega_extraida.txt')
                print('PASS: extraccion nueva, limpieza, recompilacion y suite completa.')


if __name__=='__main__':
    main()

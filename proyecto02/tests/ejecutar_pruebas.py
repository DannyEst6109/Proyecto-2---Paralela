#!/usr/bin/env python3
"""Mide las tres claves y un control exhaustivo; guarda datos crudos y estados.

Uso: python3 proyecto02/tests/ejecutar_pruebas.py [segundos_corte] [repeticiones]
Las proyecciones se calculan aparte; no sustituyen los tiempos realmente medidos.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import shlex
from statistics import median, stdev
import subprocess
import sys
import os
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from mpi_utils import mpi_prefix, run_command
BUILD = ROOT / 'proyecto02/build'
OUT = ROOT / 'evidencias/inciso2'
TEXT = ROOT / 'proyecto02/datos/prueba_proyecto2.txt'
KEYS = {'a': 123456, 'b': 2**54, 'c': 2**54+1}
RANGE = 2**56


def field(output, name, *, integer=False):
    match = re.search(r'^' + re.escape(name) + r': ([\d.]+)', output, re.M)
    if not match:
        raise ValueError(f'No se encontro el campo {name}:\n{output}')
    return int(match[1]) if integer else float(match[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('seconds', nargs='?', type=int, default=5)
    parser.add_argument('repetitions', nargs='?', type=int, default=5)
    parser.add_argument('--resume', action='store_true', help='Continua muestras validas de las mismas fuentes y parametros.')
    args = parser.parse_args()
    if args.seconds < 1 or args.repetitions < 2:
        parser.error('El corte debe ser >= 1 segundo y las repeticiones >= 2.')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'datos').mkdir(exist_ok=True)
    mpi = mpi_prefix()
    programs = {'secuencial': [str(BUILD/'busqueda_secuencial')],
                'base': mpi + [str(BUILD/'busqueda_base')],
                'alternativa': mpi + [str(BUILD/'busqueda_alternativa')]}
    stamp = datetime.now(ZoneInfo('America/Guatemala')).isoformat(timespec='seconds')
    metadata = {'fecha': stamp, 'sistema': platform.platform(), 'host': platform.node(),
                'corte': args.seconds, 'repeticiones': args.repetitions, 'rango': RANGE,
                'mpi': mpi, 'texto_sha256': hashlib.sha256(TEXT.read_bytes()).hexdigest()}
    for name, cmd in [('cpu',['lscpu']),('gcc',['gcc','--version']),
                      ('openssl',['openssl','version']),('openmpi',['mpirun','--version'])]:
        metadata[name] = subprocess.run(cmd,capture_output=True,text=True,timeout=10,check=True).stdout.strip()
    metadata['fuentes_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for folder in ['proyecto02/src','proyecto02/include']
                                for p in sorted((ROOT/folder).glob('*')) if p.is_file()}
    log = [f'Fecha: {stamp}\n',json.dumps(metadata,ensure_ascii=False,indent=2)+'\n']
    runs = []
    if args.resume:
        previous=json.loads((OUT/'resultados.json').read_text(encoding='utf-8'))
        for key in ['corte','repeticiones','fuentes_sha256','texto_sha256','sistema','cpu','mpi']:
            if metadata[key]!=previous['metadata'][key]:
                raise RuntimeError(f'No se puede continuar: cambio {key}.')
        metadata=previous['metadata']
        runs=previous['runs']
        log=[(OUT/'bitacora.txt').read_text(encoding='utf-8'), '\nContinuacion de muestras pendientes.\n']

    def atomic_write(path, text):
        # DrvFS puede rechazar la apertura truncada si un visor de Windows mantiene
        # el archivo abierto. Reemplazar un temporal evita dejar datos parciales.
        temporary=path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(text,encoding='utf-8')
        for attempt in range(6):
            try:
                os.replace(temporary,path)
                return
            except OSError:
                if attempt==5: raise
                time.sleep(.2)

    def save():
        atomic_write(OUT/'bitacora.txt','\n'.join(log))
        atomic_write(OUT/'resultados.json',json.dumps({'metadata':metadata,'runs':runs},
                                          ensure_ascii=False,indent=2)+'\n')

    def execute(cmd, expected=0):
        shown = shlex.join(str(x.relative_to(ROOT)) if isinstance(x,Path) and x.is_relative_to(ROOT)
                           else str(x) for x in cmd)
        try:
            result = run_command(cmd,cwd=ROOT,timeout=max(90,args.seconds+30))
        except subprocess.TimeoutExpired:
            log.append(f'$ {shown}\nERROR: timeout externo; ejecucion invalida.\n')
            save()
            raise
        log.append(f'$ {shown}\n{result.stdout}[codigo de salida: {result.returncode}; '
                   f'lanzador: {result.launcher_returncode}]\n')
        save()
        if result.returncode != expected:
            raise RuntimeError(f'Codigo {result.returncode}, esperado {expected}: {shown}')
        return result.stdout

    try:
        for phase, pairs in [('principal',list(KEYS.items())),('control',[('control',750123)])]:
            for tag,key in pairs:
                cipher=OUT/'datos'/f'clave_{tag}.aes'
                cipher.unlink(missing_ok=True)
                execute([BUILD/'aes_archivo','cifrar',TEXT,cipher,key])
                for name,command in programs.items():
                    capped=phase=='principal' and tag!='a' and name!='alternativa'
                    extra=['-l',str(RANGE)] if name!='alternativa' else []
                    if phase=='control':
                        extra=['-o','0','-l','1000000','-b','4096']
                        if name=='alternativa': extra=['-e']+extra
                    if capped: extra+=['-t',str(args.seconds)]
                    for repeat in range(1,args.repetitions+1):
                        if any(r['phase']==phase and r['tag']==tag and r['mode']==name
                               and r['repeat']==repeat for r in runs):
                            continue
                        cmd=command+extra+[str(cipher)]
                        output=execute(cmd,3 if capped else 0)
                        if not capped and field(output,'Clave encontrada',integer=True)!=key:
                            raise RuntimeError('La clave hallada no coincide con la del caso.')
                        run={'phase':phase,'tag':tag,'key':key,'mode':name,'repeat':repeat,
                             'time':field(output,'Tiempo de busqueda'),
                             'attempts':field(output,'Claves probadas',integer=True),
                             'rate':field(output,'Rendimiento'),'capped':capped,
                             'exit':3 if capped else 0,'command':shlex.join(cmd)}
                        if run['time']<=0 or run['attempts']<=0 or run['rate']<=0:
                            raise RuntimeError('Metrica invalida.')
                        runs.append(run); save()
                        print(f'{phase}/{tag}/{name} {repeat}/{args.repetitions}: '
                              f'{run["time"]:.6f} s; '+('corte' if capped else 'hallada'),flush=True)
    finally:
        save()
    lines=[f'# Resultados - {stamp}', '',
           f'Cada celda resume {args.repetitions} ejecuciones; MPI usa -np 4. Corte: {args.seconds} s.',
           'Los tiempos siguientes son reales. Las proyecciones estan en una tabla separada.', '',
           '| Caso | Programa | Mediana (s) | Min (s) | Max (s) | Desv. (s) | Claves/s | Estado |',
           '|---|---|---|---|---|---|---|---|']
    grouped={}
    for tag in list(KEYS)+['control']:
        for name in programs:
            group=[r for r in runs if r['tag']==tag and r['mode']==name]
            grouped[(tag,name)]=group
            times=[r['time'] for r in group]; rate=median(r['rate'] for r in group)
            lines.append(f'| {tag} | {name} | {median(times):.9f} | {min(times):.9f} | '
                         f'{max(times):.9f} | {stdev(times):.9f} | {rate:.0f} | '
                         f'{"censurada, sin hallazgo" if group[0]["capped"] else "hallada"} |')
    lines += ['', '## Proyecciones del recorrido completo', '',
              'Supuesto: tasa constante y rango [0, 2^56). No son mediciones de hallazgo.', '',
              '| Caso | Programa | Proyeccion (s) |', '|---|---|---|']
    for tag in ['b','c']:
        for name in ['secuencial','base']:
            rate=median(r['rate'] for r in grouped[(tag,name)])
            lines.append(f'| {tag} | {name} | {(KEYS[tag]+1)/rate:.9g} |')
    lines += ['', '## Razones de tiempos medidos', '',
              '| Caso | S base/sec | E base | G alternativa/base |', '|---|---|---|---|']
    for tag in ['a','control']:
        seq,base,alt=[median(r['time'] for r in grouped[(tag,n)]) for n in programs]
        lines.append(f'| {tag} | {seq/base:.4f} | {seq/base/4:.4f} | {base/alt:.4f} |')
    lines += ['', 'El control usa la clave 750123 y el mismo rango [0,1000000), lote 4096,',
              'y solo barrido (-e) en la alternativa. Se mantiene el orden ascendente por bloques;',
              'el trabajo efectivo hasta el aviso puede variar segun la asignacion y la parada.']
    atomic_write(OUT/'resultados.md','\n'.join(lines)+'\n')
    metadata['completo']=True
    save()


if __name__=='__main__':
    main()

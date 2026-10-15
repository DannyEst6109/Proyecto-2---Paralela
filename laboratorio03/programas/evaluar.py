#!/usr/bin/env python3
"""Compila los programas, comprueba los resultados y mide los tiempos."""
import csv
import json
import os
from pathlib import Path
import re
import shlex
import statistics
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
OUT = HERE.parent / 'resultados'
EVID = HERE.parent / 'evidencias' / 'registros'
OUT.mkdir(exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)
MPI = ['mpirun'] + (['--allow-run-as-root'] if os.geteuid() == 0 else [])
MPI += ['--bind-to', 'core']

def run(args, expected=0, timeout=120):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    log = '$ ' + shlex.join(args) + '\n' + p.stdout + f'[codigo de salida: {p.returncode}]\n'
    if p.returncode != expected:
        raise RuntimeError(log)
    return p.stdout, log

def evidence(name, log):
    (EVID / (name + '.txt')).write_text(log, encoding='utf-8')

def seq(path, limit):
    return ['./busqueda_clave_aes_mejorada', 'buscar', str(path), str(limit)]

def mpi(path, limit, n, batch=4096):
    return MPI + ['-n', str(n), './busqueda_clave_aes_mpi', str(path), str(limit), str(batch)]

def result(text):
    return float(re.search(r'Tiempo de busqueda: ([0-9.]+)', text)[1])

def main():
    temporary = tempfile.TemporaryDirectory(prefix='laboratorio3_')
    test_dir = Path(temporary.name)
    _, log = run(['make', '-B'])
    evidence('01_compilacion', log)
    _, log = run(['./busqueda_clave_aes_secuencial'])
    evidence('02_original', log)
    _, log = run(['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Wpedantic', 'test_aes.c', '-o', 'test_aes', '-lcrypto'])
    _, more = run(['./test_aes']); log += more
    test_count = 1
    cases = [(0,1,3,4), (6,7,3,2), (7,11,4,2), (32,33,2,7), (4097,4101,4,4096)]
    for i, (key, limit, n, batch) in enumerate(cases):
        path = test_dir / f'test_{i}.aes'
        message = 'Mensaje de prueba con varios bloques y longitud variable.'
        _, l = run(['./busqueda_clave_aes_mejorada', 'preparar', str(path), str(key), message]); log += l
        a, l = run(seq(path, limit)); log += l
        b, l = run(mpi(path, limit, n, batch)); log += l
        for output in (a,b):
            assert f'Clave encontrada: {key}\n' in output and f'Mensaje: {message}\n' in output
        test_count += 1
    path = test_dir / 'fuera_rango.aes'
    _, l = run(['./busqueda_clave_aes_mejorada','preparar',str(path),'100','Clave fuera del rango']); log += l
    for args in (seq(path,17), mpi(path,17,3,4), mpi(path,17,4,7)):
        text, l = run(args,2); log += l
        assert 'Candidatas probadas: 17\n' in text and 'No se encontro' in text
        test_count += 1
    # Una etiqueta alterada debe rechazarse aunque el cifrado sea valido.
    path = test_dir / 'test_0.aes'
    lines = path.read_text().splitlines()
    lines[3] = ('1' if lines[3][0] != '1' else '2') + lines[3][1:]
    bad = test_dir / 'alterado.aes'; bad.write_text('\n'.join(lines)+'\n')
    for args in (seq(bad,4), mpi(bad,4,3,1)):
        text, l = run(args,2); log += l
        assert 'No se encontro' in text
        test_count += 1
    for args in (seq(path,0), seq(path,-1), mpi(path,0,3), mpi(test_dir/'no_existe.aes',10,2)):
        _, l = run(args,1); log += l; test_count += 1
    for length in (1,4096):
        path = test_dir / f'longitud_{length}.aes'; message = 'x'*length
        run(['./busqueda_clave_aes_mejorada','preparar',str(path),'2',message])
        for args in (seq(path,3),mpi(path,3,2,1)):
            text,_ = run(args); assert f'Mensaje: {message}\n' in text
        test_count += 1
    temporary.cleanup()
    evidence('07_pruebas_completas', log)
    evidence('07_pruebas_resumen', '$ python3 evaluar.py\n'
        + f'PASS: {test_count} comprobaciones funcionales.\n'
        + 'Vector GCM; etiqueta alterada; claves inicial, intermedia y final;\n'
        + 'rangos no divisibles; mas procesos que candidatas; mensajes de 1 y 4096 bytes;\n'
        + 'rango agotado (17 candidatas); entradas invalidas; archivo inexistente.\n')
    data = OUT / 'datos.aes'
    _, prep = run(['./busqueda_clave_aes_mejorada','preparar','../resultados/datos.aes','1048575','Puedes lograrlo!'])
    evidence('03_preparacion',prep)
    commands = {1:seq('../resultados/datos.aes',1048576)}
    commands.update({n:mpi('../resultados/datos.aes',1048576,n) for n in (2,3,4)})
    # Una ejecucion de calentamiento por configuracion, excluida de las mediciones.
    for cmd in commands.values(): run(cmd)
    rows=[]; raw=''
    # Alternar el orden reduce el sesgo por temperatura/carga durante la sesion.
    for repeat in range(1,6):
        order=[1,2,3,4] if repeat % 2 else [4,3,2,1]
        for n in order:
            text,l=run(commands[n]); raw += f'REPETICION {repeat}\n'+l+'\n'
            assert 'Clave encontrada: 1048575\n' in text and 'Mensaje: Puedes lograrlo!\n' in text
            assert 'Candidatas probadas: 1048576\n' in text
            rows.append({'procesos':n,'repeticion':repeat,'segundos':result(text),'candidatas':1048576})
            if repeat==1: evidence(f'04_secuencial' if n==1 else f'05_mpi_{n}',l)
    evidence('06_mediciones_completas',raw)
    with (OUT/'tiempos.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader();w.writerows(rows)
    medians={n:statistics.median(r['segundos'] for r in rows if r['procesos']==n) for n in commands}
    summary=[]
    for n,t in medians.items():
        samples=[r['segundos'] for r in rows if r['procesos']==n]
        summary.append(dict(procesos=n,mediana=t,minimo=min(samples),maximo=max(samples),speedup=medians[1]/t,eficiencia=medians[1]/t/n))
    (OUT/'resumen.json').write_text(json.dumps({'pruebas':test_count,'resultados':summary},indent=2))
    table='$ python3 evaluar.py\nResultados: 5 repeticiones por configuracion; mediana.\n'
    table+='Procesos  Tiempo (s)  Speedup  Eficiencia\n'
    for s in summary: table+=f"{s['procesos']:8d}  {s['mediana']:10.6f}  {s['speedup']:7.3f}  {s['eficiencia']*100:8.2f}%\n"
    evidence('06_mediciones_resumen',table)
    # Datos del entorno obtenidos de las aplicaciones instaladas.
    environment=''
    for args in (['uname','-r'],['lsb_release','-ds'],['gcc','--version'],['ompi_info','--version'],['openssl','version'],['lscpu']):
        _,l=run(args);environment+=l+'\n'
    evidence('00_entorno',environment)
    print(table)
    print(f'PASS: {test_count} comprobaciones. Evidencias y CSV guardados.')

if __name__=='__main__': main()

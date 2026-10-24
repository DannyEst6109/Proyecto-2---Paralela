#!/usr/bin/env python3
"""Capturas reales de xterm en Xvfb; ejecuta las sesiones, no dibuja sus salidas.

Dependencias opcionales: xvfb xterm x11-apps netpbm xfonts-base.
Uso desde Linux/WSL: python3 scripts/capturar_xvfb.py [segundos_corte]
"""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
SESSIONS=[('compilacion','inciso1','01'),('cifrado','inciso1','02'),
          ('descifrado','inciso1','03'),('verificacion','inciso1','04'),
          ('clave_a','inciso2','01'),('clave_b','inciso2','02'),('clave_c','inciso2','03')]


def main():
    cutoff=int(sys.argv[1]) if len(sys.argv)>1 else 5
    if cutoff<1: raise SystemExit('El corte debe ser positivo.')
    read_fd,write_fd=os.pipe()
    display=subprocess.Popen(['Xvfb','-screen','0','1360x850x24','-nolisten','tcp',
                              '-displayfd',str(write_fd)],pass_fds=(write_fd,),
                              stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    os.close(write_fd)
    records=[]
    try:
        if not select.select([read_fd],[],[],10)[0]:
            display.terminate()
            _,errors=display.communicate(timeout=10)
            raise RuntimeError('Xvfb no inicio en 10 segundos: '+errors.decode(errors='replace')[:2000])
        with os.fdopen(read_fd) as channel:
            number=channel.readline().strip()
        env=dict(os.environ,DISPLAY=':'+number,LC_ALL='C.UTF-8')
        with tempfile.TemporaryDirectory(prefix='proyecto02-captura-') as temp:
            for name,folder,index in SESSIONS:
                marker=Path(temp)/f'{name}.status'
                command=f'bash scripts/sesion_evidencia.sh {name} {cutoff}'
                shell=f'{command}; status=$?; printf "%s" "$status" > "{marker}"; sleep 120'
                term=subprocess.Popen(['xterm','-fn','9x15','-geometry','150x55+0+0',
                                       '-bg','#101819','-fg','#e8efeb','-e','bash','-lc',shell],
                                      cwd=ROOT,env=env,start_new_session=True,
                                      stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
                try:
                    deadline=time.monotonic()+180
                    while not marker.exists():
                        if term.poll() is not None:
                            raise RuntimeError('xterm termino: '+term.stderr.read().decode(errors='replace'))
                        if time.monotonic()>deadline: raise TimeoutError(name)
                        time.sleep(.2)
                    if marker.read_text()!='0': raise RuntimeError(f'Fallo la sesion {name}.')
                    time.sleep(.3)  # permite presentar el ultimo frame del terminal
                    xwd=subprocess.run(['xwd','-root','-silent'],env=env,capture_output=True,check=True)
                    pnm=subprocess.run(['xwdtopnm'],input=xwd.stdout,capture_output=True,check=True)
                    png=subprocess.run(['pnmtopng'],input=pnm.stdout,capture_output=True,check=True)
                    image=ROOT/'evidencias'/folder/f'{index}_{name}.png'
                    image.write_bytes(png.stdout)
                    transcript=image.parent/f'{name}.txt'
                    records.append({'sesion':name,'comando':command,'codigo':0,
                                    'fecha':datetime.now(ZoneInfo('America/Guatemala')).isoformat(timespec='seconds'),
                                    'captura':str(image.relative_to(ROOT)),
                                    'png_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                                    'txt_sha256':hashlib.sha256(transcript.read_bytes()).hexdigest()})
                    print('Captura real:',image.relative_to(ROOT),flush=True)
                finally:
                    if term.poll() is None:
                        os.killpg(term.pid,signal.SIGTERM)
                    term.communicate(timeout=10)
        (ROOT/'evidencias/capturas.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    finally:
        display.terminate()
        display.communicate(timeout=10)


if __name__=='__main__':
    if '--wsl-namespace' in sys.argv:
        # Ejecutar con sudo unshare --mount --propagation private. WSLg monta
        # /tmp/.X11-unix de solo lectura; un bind privado no altera WSLg global.
        with tempfile.TemporaryDirectory(prefix='proyecto02-x11-') as sockets:
            subprocess.run(['mount','--bind',sockets,'/tmp/.X11-unix'],check=True)
            os.chmod(sockets,0o1777)
            main()
    else:
        main()

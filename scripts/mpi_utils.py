"""Configuracion portable de Open MPI y ejecucion acotada de procesos.

En WSL/Open MPI 5, PRRTE puede bloquearse ante retornos no-cero. Se configura
esa terminacion como normal en el lanzador y se recupera el estado real del
programa desde su consenso MPI. Un estado ausente o un timeout siempre falla.
"""
from pathlib import Path
import os
import platform
import shlex
import signal
import re
import sys
import subprocess


def mpi_prefix(processes=4):
    version = subprocess.run(['mpirun', '--version'], capture_output=True,
                             text=True, timeout=10, check=True).stdout
    if 'Open MPI' not in version:
        raise RuntimeError('Este proyecto requiere Open MPI.')
    command = ['mpirun', '--oversubscribe']
    if 'microsoft' in platform.release().lower():
        command += ['--mca', 'osc', '^ucx']
        if 'Open MPI) 5.' in version:
            command += ['--runtime-options', 'ERROR-NONZERO-STATUS=0']
    if os.geteuid() == 0:
        command += ['--allow-run-as-root']
    return command + ['-np', str(processes)]


def run_command(command, *, cwd=None, timeout=90):
    """Mata el grupo completo en caso de timeout, sin reintentar ni alterar estados."""
    process = subprocess.Popen([str(x) for x in command], cwd=cwd,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, start_new_session=True)
    try:
        output, _ = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    status=process.returncode
    if 'ERROR-NONZERO-STATUS=0' in command and status==0:
        matches=re.findall(r'^Estado MPI: ([0-3])$',output,re.M)
        if len(matches)!=1:
            raise RuntimeError('MPI termino sin un estado de aplicacion unico:\n'+output)
        status=int(matches[0])
    result=subprocess.CompletedProcess(command, status, output, '')
    result.launcher_returncode=process.returncode
    return result


if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--run':
        command=mpi_prefix()+sys.argv[2:]
        print('$ '+shlex.join(command),flush=True)
        result=run_command(command,timeout=300)
        print(result.stdout,end='')
        sys.exit(result.returncode)
    else:
        print(shlex.join(mpi_prefix()))

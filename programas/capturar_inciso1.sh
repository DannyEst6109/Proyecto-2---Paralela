#!/usr/bin/env bash
# Ejecutar desde la raiz del proyecto en una terminal Ubuntu / WSL.
# El segundo argumento opcional permite avanzar las capturas desde otra sesion.
set -eu
control=${1:-$(mktemp -d /tmp/proyecto02-capturas.XXXXXX)}
mkdir -p "$control" evidencias/inciso1/terminal
out="$PWD/evidencias/inciso1/terminal"
exec > >(tee "$out/sesion.txt") 2>&1
run() {
    printf '$ '
    printf '%q ' "$@"
    printf '\n'
    "$@"
}
pause_capture() {
    printf '\n[Etapa %s terminada; captura de la terminal]\n' "$1"
    printf '%s' "$1" > "$control/etapa"
    while [ ! -f "$control/continuar-$1" ]; do sleep 0.3; done
}
clear
printf 'PROYECTO 02 - INCISO 1 | COMPILACION EN UBUNTU\n\n'
run date --iso-8601=seconds
run uname -sr
run openssl version
run make -B -C programas
pause_capture 01

clear
printf 'PROYECTO 02 - INCISO 1 | CIFRADO DEL ARCHIVO TXT\n\n'
run cat datos/mensaje.txt
run ./programas/aes_archivo cifrar datos/mensaje.txt evidencias/inciso1/terminal/mensaje.aes 123456
pause_capture 02

clear
printf 'PROYECTO 02 - INCISO 1 | DESCIFRADO CON LA MISMA CLAVE\n\n'
run ./programas/aes_archivo descifrar evidencias/inciso1/terminal/mensaje.aes evidencias/inciso1/terminal/recuperado.txt 123456
pause_capture 03

clear
printf 'PROYECTO 02 - INCISO 1 | VERIFICACION Y PRUEBAS\n\n'
run cmp datos/mensaje.txt evidencias/inciso1/terminal/recuperado.txt
printf 'cmp: codigo 0; archivos identicos byte a byte.\n\n'
run sha256sum datos/mensaje.txt evidencias/inciso1/terminal/recuperado.txt
run python3 programas/probar_inciso1.py
if run ./programas/aes_archivo descifrar evidencias/inciso1/terminal/mensaje.aes evidencias/inciso1/terminal/no_crear.txt 123457; then
    printf 'ERROR: se acepto una clave incorrecta.\n'
    exit 1
else
    code=$?
    printf 'Codigo de salida de la clave incorrecta: %s (esperado: 1).\n' "$code"
    test "$code" -eq 1
    test ! -e evidencias/inciso1/terminal/no_crear.txt
    printf 'Verificado: no se creo un archivo con texto invalido.\n'
fi
pause_capture 04
printf 'Capturas y pruebas terminadas.\n'

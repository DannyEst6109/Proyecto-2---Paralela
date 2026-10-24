#!/usr/bin/env bash
# Reproduce en la terminal una sesion de evidencia del proyecto: muestra cada comando
# con su prompt, lo ejecuta y guarda la misma salida en evidencias/<inciso>/<sesion>.txt.
# Uso: scripts/sesion_evidencia.sh <sesion> [segundos_corte]
# Sesiones: compilacion cifrado descifrado verificacion clave_a clave_b clave_c pruebas
set -uo pipefail
cd "$(dirname "$0")/.."
SESION=${1:?Indique la sesion}
CORTE=${2:-30}
BUILD=proyecto02/build
I1=evidencias/inciso1
I2=evidencias/inciso2
# Se excluye el componente UCX de RMA: en WSL imprime errores inofensivos al crear la ventana.
NP="python3 scripts/mpi_utils.py --run"
PROMPT="\033[1;32mProyecto02\033[0m$ "

# Imprime el comando como si se hubiera escrito en la terminal y luego lo ejecuta.
run() {
    local expected=0
    if [[ "$1" = --esperado=* ]]; then expected=${1#*=}; shift; fi
    printf "%b%s\n" "$PROMPT" "$*"
    bash -c "$*" 2>&1
    local status=$?
    [ "$status" -ne 0 ] && printf "\033[33m[codigo de salida: %d]\033[0m\n" "$status"
    if [ "$status" -ne "$expected" ]; then
        printf 'ERROR: se esperaba salida %s y se obtuvo %s\n' "$expected" "$status"
        exit 1
    fi
}

sesion() {
    case "$SESION" in
    compilacion)
        run "date '+%Y-%m-%d %H:%M:%S %Z' && uname -sr"
        run "gcc --version | head -1 && mpirun --version | head -1 && openssl version"
        run "make clean >/dev/null && make && make laboratorio | grep -E 'gcc|mpicc'"
        run "ls proyecto02/build" ;;
    cifrado)
        rm -f "$I1/mensaje.aes" "$I1/recuperado.txt" "$I1/no_crear.txt"
        run "cat proyecto02/datos/mensaje.txt"
        run "$BUILD/aes_archivo cifrar proyecto02/datos/mensaje.txt $I1/mensaje.aes 123456"
        run "cat $I1/mensaje.aes" ;;
    descifrado)
        rm -f "$I1/recuperado.txt"
        run "$BUILD/aes_archivo descifrar $I1/mensaje.aes $I1/recuperado.txt 123456"
        run "cat $I1/recuperado.txt" ;;
    verificacion)
        run "cmp proyecto02/datos/mensaje.txt $I1/recuperado.txt && echo 'Archivos identicos'"
        run "sha256sum proyecto02/datos/mensaje.txt $I1/recuperado.txt"
        rm -f "$I1/no_crear.txt"
        run --esperado=1 "$BUILD/aes_archivo descifrar $I1/mensaje.aes $I1/no_crear.txt 44"
        run "test ! -e $I1/no_crear.txt && echo 'Clave 44 rechazada; no se genero salida'"
        run "python3 proyecto02/tests/probar_inciso1.py" ;;
    clave_a)
        mkdir -p "$I2/datos"; rm -f "$I2/datos/clave_a.aes"
        run "$BUILD/aes_archivo cifrar proyecto02/datos/prueba_proyecto2.txt $I2/datos/clave_a.aes 123456 | tail -4"
        run "$BUILD/busqueda_secuencial $I2/datos/clave_a.aes"
        run "$NP $BUILD/busqueda_base $I2/datos/clave_a.aes"
        run "$NP $BUILD/busqueda_alternativa $I2/datos/clave_a.aes" ;;
    clave_b|clave_c)
        local key=18014398509481984; [ "$SESION" = clave_c ] && key=18014398509481985
        local f="$I2/datos/$SESION.aes"; rm -f "$f"
        run "$BUILD/aes_archivo cifrar proyecto02/datos/prueba_proyecto2.txt $f $key | tail -4"
        run --esperado=3 "$BUILD/busqueda_secuencial -l 72057594037927936 -t $CORTE $f"
        run --esperado=3 "$NP $BUILD/busqueda_base -l 72057594037927936 -t $CORTE $f"
        run "$NP $BUILD/busqueda_alternativa $f" ;;
    pruebas)
        run "timeout 180 make test" ;;
    *) echo "Sesion desconocida: $SESION" >&2; exit 1 ;;
    esac
}

case "$SESION" in compilacion|cifrado|descifrado|verificacion) DEST=$I1 ;; *) DEST=$I2 ;; esac
mkdir -p "$DEST"
# La copia en texto se guarda sin codigos de color.
registro=$(mktemp)
trap 'rm -f "$registro"' EXIT
sesion | tee "$registro"
estado=$?
sed -r 's/\x1b\[[0-9;]*m//g' "$registro" > "$DEST/$SESION.txt" || exit 1
exit "$estado"

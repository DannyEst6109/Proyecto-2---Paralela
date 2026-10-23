#!/usr/bin/env bash
# Reproduce en la terminal una sesion de evidencia del proyecto: muestra cada comando
# con su prompt, lo ejecuta y guarda la misma salida en evidencias/<inciso>/<sesion>.txt.
# Uso: scripts/sesion_evidencia.sh <sesion> [segundos_corte]
# Sesiones: compilacion cifrado descifrado verificacion clave_a clave_b clave_c pruebas
set -u
cd "$(dirname "$0")/.."
SESION=${1:?Indique la sesion}
CORTE=${2:-30}
BUILD=proyecto02/build
I1=evidencias/inciso1
I2=evidencias/inciso2
# Se excluye el componente UCX de RMA: en WSL imprime errores inofensivos al crear la ventana.
NP="mpirun --mca osc ^ucx -np 4"
PROMPT="\033[1;32m$(whoami)@$(hostname)\033[0m:\033[1;34m~/Proyecto-2---Paralela\033[0m$ "

# Imprime el comando como si se hubiera escrito en la terminal y luego lo ejecuta.
run() {
    printf "%b%s\n" "$PROMPT" "$*"
    bash -c "$*" 2>&1
    local status=$?
    [ "$status" -ne 0 ] && printf "\033[33m[codigo de salida: %d]\033[0m\n" "$status"
    return 0
}

sesion() {
    case "$SESION" in
    compilacion)
        run "date '+%Y-%m-%d %H:%M:%S %Z' && uname -sr"
        run "gcc --version | head -1 && mpirun --version 2>/dev/null | head -1 && openssl version"
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
        run "$BUILD/aes_archivo descifrar $I1/mensaje.aes $I1/no_crear.txt 123457"
        run "ls $I1/no_crear.txt"
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
        run "$BUILD/busqueda_secuencial -t $CORTE $f"
        run "$NP $BUILD/busqueda_base -t $CORTE $f"
        run "$NP $BUILD/busqueda_alternativa $f" ;;
    pruebas)
        run "timeout 600 make test 2>&1 | grep -E 'PASS|Pruebas|Error|Timeout'" ;;
    *) echo "Sesion desconocida: $SESION" >&2; exit 1 ;;
    esac
}

case "$SESION" in compilacion|cifrado|descifrado|verificacion) DEST=$I1 ;; *) DEST=$I2 ;; esac
mkdir -p "$DEST"
# La copia en texto se guarda sin codigos de color.
sesion | tee >(sed -r 's/\x1b\[[0-9;]*m//g' > "$DEST/$SESION.txt")

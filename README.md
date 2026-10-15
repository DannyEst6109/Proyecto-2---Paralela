# Proyecto 02 - Computación Paralela y Distribuida

Base de trabajo importada del [Laboratorio 03](https://github.com/DannyEst6109/Laboratorio-3---Paralela), commit `e20c920fe0d105d2844889d7410563e12a3b3d1d`.
Los archivos de `programas/` conservan su contenido y autoría originales.
Las instrucciones originales están en [docs/laboratorio-03-original.md](docs/laboratorio-03-original.md).

## Código disponible

- `programas/aes_comun.h`: AES-128-GCM mediante OpenSSL, conversión de claves numéricas y formato de archivos `AESLAB1`.
- `programas/busqueda_clave_aes_secuencial.c`: programa secuencial original.
- `programas/busqueda_clave_aes_mejorada.c`: preparación de mensajes y búsqueda secuencial mejorada.
- `programas/busqueda_clave_aes_mpi.c`: búsqueda paralela por lotes con parada colectiva.
- `programas/test_aes.c`: vector de prueba AES-GCM y rechazo de una etiqueta alterada.
- `programas/evaluar.py`: pruebas y mediciones del Laboratorio 03; todavía no implementa el protocolo de pruebas del Proyecto 02.

El informe, las capturas y los tiempos del laboratorio anterior no se importaron: las evidencias del proyecto deben generarse con sus propias ejecuciones.

## Compilar en Ubuntu o WSL

Se requieren GCC, Make, OpenSSL con encabezados de desarrollo, Open MPI y Python 3.
Si faltan dependencias:

```bash
sudo apt update
sudo apt install build-essential libssl-dev libopenmpi-dev openmpi-bin python3
```

Desde la raíz del proyecto:

```bash
make -C programas
```

## Comprobar la base del laboratorio

```bash
cd programas
gcc -std=c11 -O2 -Wall -Wextra -Wpedantic test_aes.c -o test_aes -lcrypto
./test_aes

mkdir -p ../resultados
./busqueda_clave_aes_mejorada preparar ../resultados/ejemplo.aes 123456 'Esta es una prueba de proyecto 2'
./busqueda_clave_aes_mejorada buscar ../resultados/ejemplo.aes 123457
mpirun -np 4 ./busqueda_clave_aes_mpi ../resultados/ejemplo.aes 123457 4096
```

Si se ejecuta como root, Open MPI requiere agregar `--allow-run-as-root` después de `mpirun`.
Estos comandos comprueban el comportamiento heredado; no completan el inciso 1.

## Pendiente para el inciso 1

1. Leer el mensaje desde un archivo `.txt`, en lugar de recibirlo como texto en la línea de comandos.
2. Añadir descifrado directo con una clave recibida como parámetro y guardar el texto recuperado.
3. Mostrar el texto original, el cifrado y el recuperado; comprobar que los archivos original y recuperado coinciden.
4. Capturar los comandos de compilación y ejecución y sus resultados.

La base convierte el entero a una clave de 16 bytes con ceros iniciales y el entero en los últimos ocho bytes, en orden big-endian. Mantener esta representación permite reutilizar el cifrado y la búsqueda existentes.

Para los siguientes incisos también habrá que revisar el límite de búsqueda actual (`2^32`) y añadir la comprobación de la frase `es una prueba de`: el laboratorio identifica la clave mediante autenticación GCM.

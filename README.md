# Proyecto 02 - Computación Paralela y Distribuida

## Entrega del inciso 1

- Equipo: Daniel Estrada (20853), Andre Pivaral (23574) y Sebastian Estrada (21405).
- Informe: [output/pdf/Informe_Inciso_1.pdf](output/pdf/Informe_Inciso_1.pdf).
- Capturas directas de Windows Terminal ejecutando Ubuntu / WSL: `evidencias/inciso1/terminal/01_compilacion.png` a `04_verificacion.png`.
- La misma carpeta conserva `sesion.txt`, `mensaje.aes` y `recuperado.txt` de la ejecución fotografiada.
- Paquete de entrega: `output/Entrega_Inciso_1.zip`, con informe, fuentes, datos y evidencia.

El informe tiene carátula, índice, explicación del cifrado y descifrado, catálogo de funciones y bibliotecas, resultados, conclusiones y referencias. Su alcance es el inciso 1.

Base de trabajo importada del [Laboratorio 03](https://github.com/DannyEst6109/Laboratorio-3---Paralela), commit `e20c920fe0d105d2844889d7410563e12a3b3d1d`.
Se conserva la autoría del laboratorio. El proyecto añade `aes_archivo.c` y sus scripts de verificación; `aes_comun.h` se adapta para aceptar archivos vacíos y el Makefile incorpora el nuevo ejecutable.
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

## Inciso 1: cifrar y descifrar archivos

Desde la raíz del repositorio, en Ubuntu / WSL:

```bash
make -C programas
mkdir -p resultados
./programas/aes_archivo cifrar datos/mensaje.txt resultados/mensaje.aes 123456
./programas/aes_archivo descifrar resultados/mensaje.aes resultados/recuperado.txt 123456
cmp datos/mensaje.txt resultados/recuperado.txt && echo 'Archivos identicos'
```

El cifrado muestra el texto original y los bytes cifrados en hexadecimal. El descifrado muestra el cifrado, el texto recuperado y la autenticación GCM. Se preservan exactamente los bytes, incluidos tildes y saltos de línea. `datos/mensaje.txt` contiene la frase del proyecto con un salto de línea final.

La clave es un entero decimal entre `0` y `18446744073709551614`; incluye las tres claves exigidas por el proyecto. Se conserva el formato `AESLAB1`: longitud, nonce aleatorio de 12 bytes, etiqueta de autenticación de 16 bytes y contenido cifrado, sin guardar la clave ni el texto original. GCM no necesita padding.

Se admiten archivos vacíos y textos de hasta **4096 bytes**, límite heredado del laboratorio. Los archivos mayores se rechazan. El programa rechaza claves y archivos inválidos, y no guarda texto si la autenticación falla. La salida debe ser un archivo nuevo: nunca sobrescribe un archivo existente. Para repetir los comandos, utilice otros nombres de salida.

### Verificación y evidencia

```bash
python3 programas/probar_inciso1.py
python3 programas/evidencia_inciso1.py
```

Las pruebas cubren 20 casos: igualdad byte a byte, UTF-8, CRLF, archivo vacío, límites de tamaño, claves grandes, clave incorrecta, archivo alterado o truncado, lectura/escritura fallida, protección de archivos existentes y compatibilidad con el laboratorio.

`evidencias/inciso1/terminal/` contiene las capturas directas y el registro de sesión utilizados en el informe. `cmp` retornó 0 y los hashes SHA-256 del original y del recuperado coincidieron. La clave incorrecta retornó 1 sin crear el archivo de salida.

Los TXT y HTML en `evidencias/inciso1/` y las imágenes de `output/playwright/inciso1/` corresponden a una ejecución anterior que se conservó como registro auxiliar. El script `evidencia_inciso1.py` renueva esos registros auxiliares; no modifica las capturas directas de `terminal/`. Las capturas deben renovarse si se repite la demostración que ilustran.

La base convierte el entero a una clave de 16 bytes con ceros iniciales y el entero en los últimos ocho bytes, en orden big-endian. Mantener esta representación permite reutilizar el cifrado y la búsqueda existentes.

Para los siguientes incisos también habrá que revisar el límite de búsqueda actual (`2^32`) y añadir la comprobación de la frase `es una prueba de`: el laboratorio identifica la clave mediante autenticación GCM.

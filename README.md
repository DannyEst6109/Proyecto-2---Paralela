# Proyecto 02 - Computación Paralela y Distribuida

Integrantes: Daniel Estrada (20853), Andre Pivaral (23574) y Sebastian Estrada (21405).

## Estructura

```text
laboratorio03/          Código base del Laboratorio 03
proyecto02/
  src/                 Cifrado/descifrado y busquedas (secuencial, base MPI, alternativa MPI)
  include/             Funciones AES adaptadas para el proyecto
  tests/               Pruebas de los incisos 1 a 3 y ejecutor de la bitacora
  datos/               Archivo de texto de ejemplo
  build/               Ejecutables generados al compilar
informe/               Informe PDF, fuente y recursos de la carátula
evidencias/inciso1/     Capturas de terminal, registro y archivos de prueba
evidencias/inciso2/     Archivos cifrados, bitacora y tabla de tiempos/speedups
scripts/               Registro de pruebas y empaquetado de la entrega
entregas/              ZIP de entrega
```

El código original está en [laboratorio03](laboratorio03/README.md). La implementación del proyecto tiene su propia copia de las funciones AES y se compila por separado.

## Compilar y probar

En Ubuntu o WSL se necesitan GCC, Make, OpenSSL, Open MPI y Python 3:

```bash
sudo apt install build-essential libssl-dev libopenmpi-dev openmpi-bin python3
make
make test
```

`make` compila el proyecto. `make laboratorio` compila las versiones originales. `make test` compila ambos, verifica el vector AES-GCM, ejecuta los 20 casos del inciso 1 y las pruebas de busqueda (incisos 2 y 3).

## Cifrar y descifrar

Desde la raíz del repositorio:

```bash
mkdir -p proyecto02/resultados
./proyecto02/build/aes_archivo cifrar proyecto02/datos/mensaje.txt proyecto02/resultados/mensaje.aes 123456
./proyecto02/build/aes_archivo descifrar proyecto02/resultados/mensaje.aes proyecto02/resultados/recuperado.txt 123456
cmp proyecto02/datos/mensaje.txt proyecto02/resultados/recuperado.txt
```

Se usa AES-128-GCM con una clave numérica convertida a 16 bytes. El formato `AESLAB1` guarda longitud, nonce, etiqueta y cifrado. Se admiten archivos vacíos y textos de hasta 4096 bytes. Las salidas deben ser archivos nuevos; una clave incorrecta no genera texto recuperado.

## Busqueda de la clave (incisos 2 y 3)

Se cifra el texto de prueba y se busca la clave validando que el descifrado contenga la frase `es una prueba de`:

```bash
./proyecto02/build/aes_archivo cifrar proyecto02/datos/prueba_proyecto2.txt prueba.aes 123456
./proyecto02/build/busqueda_secuencial prueba.aes
mpirun -np 4 ./proyecto02/build/busqueda_base prueba.aes
mpirun -np 4 ./proyecto02/build/busqueda_alternativa prueba.aes
```

Opciones: `-f frase`, `-l limite` (base/secuencial: claves 0..limite-1; alternativa: claves del barrido), `-b lote`, `-o offset` (alternativa: inicio del barrido, por defecto 2^56/4) y `-t segundos` (tiempo maximo; codigo de salida 3). Codigos de salida: 0 clave hallada, 1 argumentos invalidos, 2 no hallada.

- **Base:** reparto estatico por lotes con `MPI_Allreduce` al final de cada ronda.
- **Alternativa:** 4 familias (valores bajos, patrones humanos, texto ASCII y barrido desde un offset alto) con contador atomico por familia (`MPI_Fetch_and_op`) y aviso no bloqueante (`MPI_Isend`/`MPI_Test`).

`python3 proyecto02/tests/ejecutar_pruebas.py [segundos] [repeticiones]` ejecuta las pruebas a), b) y c) del enunciado y escribe `evidencias/inciso2/bitacora.txt` y `resultados.md`. Con la secuencial y la base las claves 2^56/4 no se pueden recorrer completas: se cortan con `-t` y el tiempo se estima con el rendimiento medido.

## Informe y entrega

- [Informe del inciso 1](informe/Informe_Inciso_1.pdf).
- [Capturas y registro de ejecución](evidencias/inciso1/README.md).
- Paquete: `entregas/Entrega_Proyecto_02.zip`.

```bash
python3 scripts/registrar_pruebas.py
python3 scripts/empaquetar.py
```

El informe se genera con `python3 informe/generar.py`; requiere ReportLab, Pillow y las fuentes Arial y Times New Roman de Windows.

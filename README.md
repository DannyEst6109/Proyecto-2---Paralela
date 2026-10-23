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

`make` compila el proyecto (los 4 ejecutables en `proyecto02/build/`). `make laboratorio` compila las versiones originales. `make test` compila ambos, verifica el vector AES del Laboratorio 03, ejecuta los casos del inciso 1 y las pruebas de busqueda (incisos 2 y 3).

## Cifrar y descifrar

Desde la raíz del repositorio:

```bash
mkdir -p proyecto02/resultados
./proyecto02/build/aes_archivo cifrar proyecto02/datos/mensaje.txt proyecto02/resultados/mensaje.aes 123456
./proyecto02/build/aes_archivo descifrar proyecto02/resultados/mensaje.aes proyecto02/resultados/recuperado.txt 123456
cmp proyecto02/datos/mensaje.txt proyecto02/resultados/recuperado.txt
```

Se usa AES-128 en modo ECB con relleno PKCS#7 y una clave numérica convertida a 16 bytes. El formato `AESECB1` guarda la longitud del texto plano y el cifrado. Se admiten archivos vacíos y textos de hasta 4096 bytes. Las salidas deben ser archivos nuevos; una clave incorrecta no genera texto recuperado (el relleno inválido la delata). Los archivos del Laboratorio 03 (formato `AESLAB1`, AES-128-GCM) no son compatibles y se rechazan.

## Busqueda de la clave (incisos 2 y 3)

Todas las busquedas usan 4 procesos MPI (`-np 4`) y validan que el descifrado contenga la frase `es una prueba de`. Primero se cifra el texto de prueba con cada clave del enunciado (en archivos nuevos):

```bash
rm -f a.aes b.aes c.aes
./proyecto02/build/aes_archivo cifrar proyecto02/datos/prueba_proyecto2.txt a.aes 123456
./proyecto02/build/aes_archivo cifrar proyecto02/datos/prueba_proyecto2.txt b.aes 18014398509481984
./proyecto02/build/aes_archivo cifrar proyecto02/datos/prueba_proyecto2.txt c.aes 18014398509481985
```

**Inciso 2 — estrategia base (y secuencial de referencia).** La clave `123456` se halla recorriendo desde 0; las claves altas `2^56/4` y `2^56/4+1` son inviables desde 0, por lo que se mide una ventana con `-o`:

```bash
# a) clave 123456
./proyecto02/build/busqueda_secuencial -l 200000 a.aes
mpirun -np 4 ./proyecto02/build/busqueda_base -l 200000 a.aes
# b) y c) claves altas, ventana de medicion con -o
mpirun -np 4 ./proyecto02/build/busqueda_base -o 18014398509480000 -l 5000 b.aes
mpirun -np 4 ./proyecto02/build/busqueda_base -o 18014398509480000 -l 5000 c.aes
```

**Inciso 3 — estrategia alternativa.** No necesita `-o`: halla las tres claves por su familia (`123456` en valores bajos; `2^56/4 = 2^54` y `2^56/4+1` en patrones humanos, por ser potencia de 2 y potencia de 2 mas uno):

```bash
mpirun -np 4 ./proyecto02/build/busqueda_alternativa a.aes
mpirun -np 4 ./proyecto02/build/busqueda_alternativa b.aes
mpirun -np 4 ./proyecto02/build/busqueda_alternativa c.aes
```

Opciones: `-f frase`, `-o offset` (inicio del recorrido; en la alternativa es el inicio del barrido exhaustivo, por defecto 2^24), `-l limite` (claves a recorrer desde el offset), `-b lote` y `-t segundos` (tiempo maximo). Codigos de salida: 0 clave hallada, 1 argumentos invalidos, 2 no hallada, 3 tiempo agotado.

- **Base:** reparto estatico por lotes sobre `[offset, offset+limite)` con `MPI_Allreduce` al final de cada ronda.
- **Alternativa:** 4 familias (valores bajos, patrones humanos, texto ASCII y barrido exhaustivo) con contador atomico por familia (`MPI_Fetch_and_op`), balanceo dinamico y aviso no bloqueante (`MPI_Isend`/`MPI_Test`).

### Bitacora de tiempos y speedup

```bash
python3 proyecto02/tests/ejecutar_pruebas.py [segundos] [repeticiones]   # p. ej. 15 5
```

Ejecuta las pruebas a), b) y c) y escribe `evidencias/inciso2/bitacora.txt` y `resultados.md` con las tablas de tiempos y speedup. Con la secuencial y la base las claves `2^56/4` no se pueden recorrer completas: se **cortan con `-t segundos`** y el tiempo total se **estima** con el rendimiento medido. Por eso el script tarda ~`4 × segundos` (los cuatro barridos de base y secuencial para b y c); baja el primer argumento para que corra mas rapido. La alternativa, en cambio, mide esas claves de verdad.

## Informe y entrega

- [Informe del inciso 1](informe/Informe_Inciso_1.pdf).
- [Capturas y registro de ejecución](evidencias/inciso1/README.md).
- Paquete: `entregas/Entrega_Proyecto_02.zip`.

```bash
python3 scripts/registrar_pruebas.py
python3 scripts/empaquetar.py
```

El informe se genera con `python3 informe/generar.py`; requiere ReportLab, Pillow y las fuentes Arial y Times New Roman de Windows.

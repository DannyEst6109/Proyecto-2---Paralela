# Proyecto 02 - Computación Paralela y Distribuida

Integrantes: Daniel Estrada (20853), Andre Pivaral (23574) y Sebastian Estrada (21405).

## Entrega

- Informe: [informe/Informe_Proyecto_02.pdf](informe/Informe_Proyecto_02.pdf).
- Código y pruebas: `proyecto02/`; antecedente original: `laboratorio03/`.
- Evidencias actuales: `evidencias/inciso1/`, `evidencias/inciso2/` y `evidencias/pruebas/ultima_prueba.txt`.
- Mediciones crudas, metadatos y control: `evidencias/inciso2/resultados.json`.
- ZIP: `entregas/Entrega_Proyecto_02.zip`, con manifiesto SHA-256 interno.

## Compilar y verificar

En Ubuntu o WSL, desde la raíz de una extracción nueva:

```bash
sudo apt install build-essential libssl-dev libopenmpi-dev openmpi-bin python3
make
make test
```

`make` compila los cuatro ejecutables del proyecto. `make laboratorio` compila los originales.
`make test` exige Open MPI y comprueba el vector GCM del laboratorio, un vector AES-128-ECB,
24 casos de archivos/autenticación y 75 casos de búsqueda. Incluye tiempo agotado,
frases cortas, aciertos simultáneos y extremos de enteros de 64 bits.

Los scripts usan `scripts/mpi_utils.py`: detecta WSL y Open MPI 5, configura UCX/PRRTE,
conserva los códigos de salida y termina el grupo completo si se excede el timeout externo.
No reintenta ni contabiliza bloqueos como éxitos. Para ver el comando MPI recomendado:

```bash
python3 scripts/mpi_utils.py
```

En WSL/Open MPI 5 se usa `--mca osc ^ucx --runtime-options ERROR-NONZERO-STATUS=0`
para evitar el bloqueo de PRRTE al gestionar retornos no-cero. **Ese ajuste hace que el
lanzador devuelva 0**, por lo que los scripts recuperan el consenso `Estado MPI: n` que
imprime el programa. El helper devuelve ese estado real (0, 1, 2 o 3); si falta el consenso,
la ejecución falla. No se interpreta el 0 del lanzador como éxito del programa.

Para conservar correctamente el código de salida en WSL, use el helper en los ejemplos:

```bash
python3 scripts/mpi_utils.py --run proyecto02/build/busqueda_base -l 1000 archivo.aes
```

El helper usa cuatro procesos. Los comandos directos `mpirun -np 4` funcionan en Open MPI
normal; en este entorno WSL se recomienda el helper. Como root también agrega
`--allow-run-as-root`. Un timeout externo termina el grupo completo y falla sin reintentar.

## Cifrar y descifrar

```bash
mkdir -p proyecto02/resultados
./proyecto02/build/aes_archivo cifrar proyecto02/datos/mensaje.txt proyecto02/resultados/mensaje.aes 123456
./proyecto02/build/aes_archivo descifrar proyecto02/resultados/mensaje.aes proyecto02/resultados/recuperado.txt 123456
cmp proyecto02/datos/mensaje.txt proyecto02/resultados/recuperado.txt
```

Las salidas deben ser archivos nuevos. Se admiten archivos vacíos y hasta 4096 bytes.
La clave es un entero decimal entre 0 y 18446744073709551614: se coloca en los últimos
ocho bytes de una clave AES de 16 bytes, en big endian, con los primeros ocho en cero.
Se experimenta con un subconjunto numérico; no se recorre el espacio completo AES-128.

Se usa AES-128-ECB con PKCS#7. El formato autenticado `AESECB2` contiene cuatro líneas:
cabecera, longitud original, cifrado hexadecimal y HMAC-SHA256 hexadecimal. La clave MAC
se deriva con el dominio `Proyecto02/AESECB2/HMAC-SHA256`. Se autentican versión, longitud
y cifrado antes de recuperar el texto. La clave incorrecta 44, los cambios del primer bloque,
la etiqueta y la longitud se rechazan sin crear salida. Los formatos anteriores `AESECB1`
y `AESLAB1` no son compatibles: deben regenerarse con la versión actual.

## Buscar las claves del enunciado

Las evidencias ya incluyen los archivos de prueba autenticados. La búsqueda recibe el
archivo y la frase `es una prueba de`, sin recibir la clave. Cada candidata se descifra y se
busca la frase; un posible acierto se confirma con HMAC para evitar falsos positivos.

```bash
# a): recorrido desde cero, sin conocer la clave.
./proyecto02/build/busqueda_secuencial -l 72057594037927936 evidencias/inciso2/datos/clave_a.aes
mpirun -np 4 ./proyecto02/build/busqueda_base -l 72057594037927936 evidencias/inciso2/datos/clave_a.aes

# b) y c): el rango incluye las claves; la base se interrumpe por tiempo.
mpirun -np 4 ./proyecto02/build/busqueda_base -l 72057594037927936 -t 5 evidencias/inciso2/datos/clave_b.aes
mpirun -np 4 ./proyecto02/build/busqueda_base -l 72057594037927936 -t 5 evidencias/inciso2/datos/clave_c.aes

# Alternativa sin offset: prioriza familias de candidatas.
mpirun -np 4 ./proyecto02/build/busqueda_alternativa evidencias/inciso2/datos/clave_a.aes
mpirun -np 4 ./proyecto02/build/busqueda_alternativa evidencias/inciso2/datos/clave_b.aes
mpirun -np 4 ./proyecto02/build/busqueda_alternativa evidencias/inciso2/datos/clave_c.aes
```

Opciones: `-f frase`, `-o offset`, `-l cantidad`, `-b lote`, `-t segundos`.
El rango es `[offset, offset+cantidad)`; las sumas que desbordan se rechazan.
La base/secuencial usan por defecto offset 0 y cantidad 2^32; para incluir las claves
grandes se debe indicar `-l 72057594037927936` (2^56). En la alternativa, `-l` y `-o`
afectan al barrido de respaldo: por defecto empieza en 2^24 con 2^63 candidatas.

Estados: 0 hallada; 1 argumentos/archivo inválidos; 2 rango agotado; 3 tiempo agotado.
El código 3 es esperado en las mediciones largas y no significa que se encontró la clave.

- Base: lotes estáticos disjuntos y `MPI_Allreduce` al final de la ronda.
- Alternativa: valores bajos, patrones humanos, ASCII y barrido; asignación atómica por
  familia con `MPI_Fetch_and_op`. Avisos con `MPI_Issend`/`MPI_Test` y drenaje de mensajes.
- Alternativa `-e`: solo barrido, sin familias heurísticas. Permite comparar la distribución
  con el mismo rango y tamaño de lote.

## Medir y reproducir

```bash
python3 proyecto02/tests/ejecutar_pruebas.py 5 5
```

Realiza 60 ejecuciones de búsqueda: cinco por combinación de caso/programa, para las
tres claves y un control. Las cuatro combinaciones largas se cortan a 5 segundos por
muestra: aproximadamente 100 segundos más las otras ejecuciones y el inicio de MPI.
Se validan estados y métricas; se conservan datos tras cada comando. Ante una interrupción
de E/S puede continuarse con `5 5 --resume`, solo si coinciden fuentes y configuración.

El control usa la clave 750123, intervalo `[0,1000000)`, lote 4096 y `-e` en la alternativa.
`resultados.md` separa tiempos medidos, dispersión, proyecciones y razones de tiempo.
Las claves grandes se hallan realmente en la alternativa por ser potencias de dos y vecinos;
sus recorridos exhaustivos desde cero quedan interrumpidos. Las proyecciones no son hallazgos
medidos y la ganancia de las familias no debe atribuirse solo al paralelismo.

## Capturas reales

Hay siete capturas de ejecución, con transcripciones `.txt` y hashes en `evidencias/capturas.json`:
compilación, cifrado, descifrado, verificación, y casos a), b), c). Corresponden a sesiones
independientes de las medianas. Se capturó el framebuffer de xterm con Xvfb; no son
imágenes dibujadas a partir de los registros. No se abren ventanas en el escritorio.

Dependencias opcionales para renovar capturas:

```bash
sudo apt install --no-install-recommends xvfb xterm x11-apps netpbm xfonts-base
# Linux:
python3 scripts/capturar_xvfb.py 5
# WSLg, con socket protegido; monta un directorio temporal en un namespace privado:
sudo unshare --mount --propagation private python3 scripts/capturar_xvfb.py 5 --wsl-namespace
```

Desde PowerShell: `powershell -ExecutionPolicy Bypass -File scripts/capturar_pantallas.ps1 -Corte 5`.
Una sesión de texto: `bash scripts/sesion_evidencia.sh clave_b 5`.

## Informe y paquete

El generador necesita Python 3, ReportLab, Pillow y Arial o DejaVu Sans/Mono. Para regenerar:

```bash
python3 -m venv .venv-informe
.venv-informe/bin/pip install reportlab pillow
python3 scripts/registrar_pruebas.py
.venv-informe/bin/python informe/crear_informe.py
python3 scripts/empaquetar.py
python3 scripts/verificar_entrega.py
```

El informe se guarda en `informe/` y `output/pdf/`. El empaquetador exige informe, pruebas
aprobadas, capturas y mediciones completas, y verifica que las fuentes coincidan con sus
hashes de medición. Incluye fuentes, ejecutables Linux con permiso de ejecución, scripts,
datos, evidencias y `MANIFIESTO_SHA256.json`. La verificación comprueba CRC, rutas, hashes,
formato ELF, informe y datos. El ZIP final también se valida mediante recompilación y pruebas
desde una extracción nueva. No es necesario instalar las herramientas de captura o PDF
para compilar y ejecutar el proyecto.

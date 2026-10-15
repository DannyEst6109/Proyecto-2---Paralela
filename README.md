# Proyecto 02 - Computación Paralela y Distribuida

Integrantes: Daniel Estrada (20853), Andre Pivaral (23574) y Sebastian Estrada (21405).

## Estructura

```text
laboratorio03/          Código base del Laboratorio 03
proyecto02/
  src/                 Programa de cifrado y descifrado
  include/             Funciones AES adaptadas para el proyecto
  tests/               Pruebas del inciso 1
  datos/               Archivo de texto de ejemplo
  build/               Ejecutables generados al compilar
informe/               Informe PDF, fuente y recursos de la carátula
evidencias/inciso1/     Capturas de terminal, registro y archivos de prueba
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

`make` compila el proyecto. `make laboratorio` compila las versiones originales. `make test` compila ambos, verifica el vector AES-GCM y ejecuta los 20 casos del inciso 1.

## Cifrar y descifrar

Desde la raíz del repositorio:

```bash
mkdir -p proyecto02/resultados
./proyecto02/build/aes_archivo cifrar proyecto02/datos/mensaje.txt proyecto02/resultados/mensaje.aes 123456
./proyecto02/build/aes_archivo descifrar proyecto02/resultados/mensaje.aes proyecto02/resultados/recuperado.txt 123456
cmp proyecto02/datos/mensaje.txt proyecto02/resultados/recuperado.txt
```

Se usa AES-128-GCM con una clave numérica convertida a 16 bytes. El formato `AESLAB1` guarda longitud, nonce, etiqueta y cifrado. Se admiten archivos vacíos y textos de hasta 4096 bytes. Las salidas deben ser archivos nuevos; una clave incorrecta no genera texto recuperado.

## Informe y entrega

- [Informe del inciso 1](informe/Informe_Inciso_1.pdf).
- [Capturas y registro de ejecución](evidencias/inciso1/README.md).
- Paquete: `entregas/Entrega_Inciso_1.zip`.

```bash
python3 scripts/registrar_pruebas.py
python3 scripts/empaquetar.py
```

El informe se genera con `python3 informe/generar.py`; requiere ReportLab, Pillow y las fuentes Arial y Times New Roman de Windows. Los siguientes incisos desarrollarán la búsqueda de claves y la comparación de estrategias MPI.

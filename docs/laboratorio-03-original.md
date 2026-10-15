# Laboratorio 03

## [Informe del laboratorio](Informe.pdf)

Carlos Daniel Estrada Vega - 20853  
Computación Paralela y Distribuida. Trabajo individual.

- `programas/`: código original, versión mejorada, versión MPI y pruebas.
- `resultados/`: archivo cifrado, tiempos medidos y speedups.
- `evidencias/`: las seis capturas; los registros completos están en `registros/`.

## Compilar

En Ubuntu o WSL, desde la raíz del repositorio:

```bash
sudo apt update
sudo apt install build-essential libssl-dev libopenmpi-dev openmpi-bin python3
cd programas
make
```

## Ejecutar

Desde `programas/`:

```bash
./busqueda_clave_aes_secuencial
./busqueda_clave_aes_mejorada buscar ../resultados/datos.aes 1048576
mpirun --bind-to core -n 2 ./busqueda_clave_aes_mpi ../resultados/datos.aes 1048576 4096
mpirun --bind-to core -n 3 ./busqueda_clave_aes_mpi ../resultados/datos.aes 1048576 4096
mpirun --bind-to core -n 4 ./busqueda_clave_aes_mpi ../resultados/datos.aes 1048576 4096
```

Si Ubuntu se ejecuta como `root`, agregar `--allow-run-as-root` después de `mpirun`.

Para preparar otro ejemplo:

```bash
./busqueda_clave_aes_mejorada preparar ../resultados/ejemplo.aes 12345 'Puedes lograrlo!'
./busqueda_clave_aes_mejorada buscar ../resultados/ejemplo.aes 1048576
```

Las claves numeradas y el rango reducido se usan para el experimento del laboratorio.

## Repetir las pruebas

```bash
python3 evaluar.py
```

El script comprueba los programas y mide cinco repeticiones por configuración.
Actualiza los archivos de resultados y registros; guardar una copia antes de
ejecutarlo si se desean conservar las mediciones del informe. Los tiempos de
las capturas se encuentran por separado en `resultados/tiempos_capturas.csv`.

Las capturas se tomaron antes de reorganizar las carpetas, por eso muestran
la ruta anterior `entrega/programas`. Los comandos y programas son los mismos.

# Laboratorio 03

Código base tomado de [Laboratorio-3---Paralela](https://github.com/DannyEst6109/Laboratorio-3---Paralela), commit `e20c920fe0d105d2844889d7410563e12a3b3d1d`.

Los siete archivos de `programas/` mantienen el contenido original. Las adaptaciones del Proyecto 02 están en `../proyecto02/`.

Desde la raíz del repositorio:

```bash
make laboratorio
mkdir -p laboratorio03/resultados
./laboratorio03/programas/busqueda_clave_aes_mejorada preparar laboratorio03/resultados/ejemplo.aes 12345 'Puedes lograrlo!'
./laboratorio03/programas/busqueda_clave_aes_mejorada buscar laboratorio03/resultados/ejemplo.aes 12346
mpirun -np 4 ./laboratorio03/programas/busqueda_clave_aes_mpi laboratorio03/resultados/ejemplo.aes 12346 4096
```

Si Ubuntu se ejecuta como root, Open MPI requiere `--allow-run-as-root` después de `mpirun`.

`programas/evaluar.py` ejecuta las pruebas y mediciones del laboratorio original. Genera sus resultados en `laboratorio03/resultados/` y sus registros en `laboratorio03/evidencias/`.

# Resultados (generado 20261022-222256, mediana de 5 ejecuciones; -np 4)

| Prueba | Clave | Programa | Tiempo (s) | Claves/s | Tipo |
|---|---|---|---|---|---|
| a) | 123456 | secuencial | 0.0674355 | 1830742 | medido |
| a) | 123456 | base | 0.0348831 | 7296631 | medido |
| a) | 123456 | alternativa | 0.0680462 | 6608147 | medido |
| b) | 18014398509481984 | secuencial | 8.83361e+09 | 2039303 | estimado (corte a 60 s) |
| b) | 18014398509481984 | base | 2.83115e+09 | 6362918 | estimado (corte a 60 s) |
| b) | 18014398509481984 | alternativa | 0.0434638 | 6654777 | medido |
| c) | 18014398509481985 | secuencial | 9.98335e+09 | 1804445 | estimado (corte a 60 s) |
| c) | 18014398509481985 | base | 2.76422e+09 | 6517001 | estimado (corte a 60 s) |
| c) | 18014398509481985 | alternativa | 0.0460467 | 6338764 | medido |

| Prueba | Speedup base/sec | Eficiencia base | Alternativa vs base | Alternativa vs sec |
|---|---|---|---|---|
| a) | 1.93 | 0.48 | 0.513 | 0.991 |
| b) | 3.12 | 0.78 | 6.51e+10 | 2.03e+11 |
| c) | 3.61 | 0.90 | 6e+10 | 2.17e+11 |

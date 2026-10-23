# Resultados (generado 20261023-134905, mediana de 5 ejecuciones; -np 4)

| Prueba | Clave | Programa | Tiempo (s) | Claves/s | Tipo |
|---|---|---|---|---|---|
| a) | 123456 | secuencial | 0.0486519 | 2537557 | medido |
| a) | 123456 | base | 0.0460391 | 5528545 | medido |
| a) | 123456 | alternativa | 0.0721733 | 6193997 | medido |
| b) | 18014398509481984 | secuencial | 7.1334e+09 | 2525361 | estimado (corte a 60 s) |
| b) | 18014398509481984 | base | 3.58174e+09 | 5029515 | estimado (corte a 60 s) |
| b) | 18014398509481984 | alternativa | 0.0547697 | 5430626 | medido |
| c) | 18014398509481985 | secuencial | 7.84238e+09 | 2297057 | estimado (corte a 60 s) |
| c) | 18014398509481985 | base | 3.69007e+09 | 4881855 | estimado (corte a 60 s) |
| c) | 18014398509481985 | alternativa | 0.0561706 | 5362255 | medido |

| Prueba | Speedup base/sec | Eficiencia base | Alternativa vs base | Alternativa vs sec |
|---|---|---|---|---|
| a) | 1.06 | 0.26 | 0.638 | 0.674 |
| b) | 1.99 | 0.50 | 6.54e+10 | 1.3e+11 |
| c) | 2.13 | 0.53 | 6.57e+10 | 1.4e+11 |

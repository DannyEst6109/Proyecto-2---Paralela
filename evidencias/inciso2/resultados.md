# Resultados - 2026-10-27T22:22:54-06:00

Cada celda resume 5 ejecuciones; MPI usa -np 4. Corte: 5 s.
Los tiempos siguientes son reales. Las proyecciones estan en una tabla separada.

| Caso | Programa | Mediana (s) | Min (s) | Max (s) | Desv. (s) | Claves/s | Estado |
|---|---|---|---|---|---|---|---|
| a | secuencial | 0.080493276 | 0.062623538 | 0.088181903 | 0.010436699 | 1533755 | hallada |
| a | base | 0.054260777 | 0.050401683 | 0.055286642 | 0.001957422 | 4690847 | hallada |
| a | alternativa | 0.096404394 | 0.085552232 | 0.122601561 | 0.014144194 | 4628486 | hallada |
| b | secuencial | 5.001533946 | 5.000320568 | 5.001653767 | 0.000682606 | 1979846 | censurada, sin hallazgo |
| b | base | 5.020116443 | 5.007694642 | 5.033090144 | 0.009880168 | 3600815 | censurada, sin hallazgo |
| b | alternativa | 0.071108893 | 0.056482186 | 0.076513474 | 0.007672262 | 4182796 | hallada |
| c | secuencial | 5.000481566 | 5.000202409 | 5.001056589 | 0.000342207 | 1903562 | censurada, sin hallazgo |
| c | base | 5.054247210 | 5.053296809 | 5.066482662 | 0.006454833 | 3466635 | censurada, sin hallazgo |
| c | alternativa | 0.063716091 | 0.053489297 | 0.083910543 | 0.012691622 | 4276876 | hallada |
| control | secuencial | 0.460884002 | 0.411778369 | 0.552827205 | 0.054142800 | 1627577 | hallada |
| control | base | 0.242584697 | 0.216768572 | 0.266417282 | 0.019916020 | 3092215 | hallada |
| control | alternativa | 0.329375918 | 0.283342305 | 0.347525739 | 0.029148415 | 2302281 | hallada |

## Proyecciones del recorrido completo

Supuesto: tasa constante y rango [0, 2^56). No son mediciones de hallazgo.

| Caso | Programa | Proyeccion (s) |
|---|---|---|
| b | secuencial | 9.09888876e+09 |
| b | base | 5.00286699e+09 |
| c | secuencial | 9.46352076e+09 |
| c | base | 5.19650858e+09 |

## Razones de tiempos medidos

| Caso | S base/sec | E base | G alternativa/base |
|---|---|---|---|
| a | 1.4835 | 0.3709 | 0.5628 |
| control | 1.8999 | 0.4750 | 0.7365 |

El control usa la clave 750123 y el mismo rango [0,1000000), lote 4096,
y solo barrido (-e) en la alternativa. Se mantiene el orden ascendente por bloques;
el trabajo efectivo hasta el aviso puede variar segun la asignacion y la parada.

# Plan de análisis del Objetivo 4 (fijado antes de ejecutar BLAST)

## Comparación
- Métodos: Random Forest (k=3, k=4), SVM (k=3, k=4), SVM sobre embeddings de NT50M y DNABERT-2, y BLAST.
- Misma partición del Objetivo 3 (resultados_objetivo3/particion_pliegues.csv).
- Comparación principal (confirmatoria): SVM sobre NT50M frente a BLAST. El resto de comparaciones es exploratoria.

## Línea base BLAST
- Para cada pliegue, base de datos con SOLO los registros de entrenamiento; consulta con los de prueba.
- blastn -task blastn, e-value 1e-5, hasta 100 hits por consulta, un HSP por hit.
- Género asignado: el del hit de mayor puntaje de bits. Si empatan hits de varios géneros, el género con más hits empatados; si persiste el empate, orden alfabético (se registra cuántos casos ocurren).
- Sin hit: "sin_asignacion"; cuenta como error.
- Sin umbral de identidad en la comparación principal.

## Métricas
- F1 macro (principal), exactitud balanceada, exactitud y métricas por género, sobre las predicciones reunidas de los cinco pliegues.

## Inferencia
- Intervalos de confianza: remuestreo de los 861 grupos con reemplazo, 2000 remuestras, semilla 2026, percentiles 2,5 y 97,5.
- Diferencias entre métodos: calculadas sobre las mismas remuestras (prueba pareada por remuestreo de grupos); valor p bilateral.
- Prueba secundaria: Wilcoxon de rangos con signo sobre las diferencias de F1 por género (14 pares).
- Ajuste de Holm para las comparaciones exploratorias.

## Identidad con la referencia más cercana
- Estratos de identidad del mejor hit de BLAST contra el entrenamiento: <90 %, 90-95 %, 95-98 %, 98-99 % y >=99 %.
- Se reporta el desempeño de cada método en cada estrato; los registros sin hit forman un estrato aparte.

## Adición del 20 de octubre de 2026 (posterior a ver los resultados de BLAST)
- Observación: 4 371 de los 4 847 errores de BLAST son registros del grupo G00001 (Stomoxys, pliegue 0) asignados a Hydrotaea. Su mejor hit es el registro GBDP0769-06.COI-5P (rotulado Hydrotaea albuquerquei, sin BIN), cuyos 500 hits más cercanos son todos Stomoxys calcitrans (identidad de 99,6 a 100 %).
- El análisis principal no cambia: se reporta con todos los datos y todas las etiquetas originales.
- Sensibilidad 1 (post hoc): BLAST con GBDP0769-06.COI-5P retirado de la base de referencia; se evalúan los mismos registros.
- Sensibilidad 2 (post hoc): todas las métricas con el grupo G00001 excluido de la evaluación, sin reentrenar.
- Otros pares con errores de identidad >=99 % hacia otro género (Calliphora a Chrysomya, Hydrotaea a Phaonia, Fannia a Hydrotaea) se informan como candidatos; no se retira ningún otro registro.

## Detalles de la inferencia fijados antes de calcular los intervalos (20 de octubre de 2026)
- Comparaciones: los 21 pares entre los siete métodos, con la diferencia A menos B del F1 macro. La confirmatoria es SVM sobre NT50M frente a BLAST (sin ajuste); las otras 20 son exploratorias, con ajuste de Holm.
- En cada remuestra, los promedios macro usan solo los géneros con al menos un registro real en esa remuestra (los géneros con pocos grupos pueden faltar).
- Valor p del remuestreo: 2 * min(P(d <= 0), P(d >= 0)) con (conteo + 1) / (2000 + 1), acotado a 1.
- Wilcoxon de rangos con signo sobre las diferencias de F1 por género de las 14 clases (con ceros descartados).
- Todo se calcula también en el escenario posterior a ver los resultados que excluye el grupo G00001 de la evaluación (sin reentrenar).

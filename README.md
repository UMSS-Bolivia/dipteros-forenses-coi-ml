# Monografia - Diplomado en Estadistica Aplicada (UMSS)
Autora: Sandy Valeria Gonzales Vargas

- `datos/fuente/original/`: datos tal como se obtuvieron (BOLD, GenBank, MD5).
- `datos/fuente/estructurado/`: tablas limpias y diccionario de datos.
- `codigo/`: scripts de Python (Anexo 2).

Consultas a GenBank y BOLD: 14 de octubre de 2026.
No se incluyen los genomas completos (3,9 GB): accesiones y MD5 en `procedencia_genomas.csv` y `md5_*.txt`.
Los datos provienen de NCBI, GigaDB, Ensembl y BOLD; cada uno debe citarse a su fuente original.

## Notas de reproducibilidad

- Tablas por género del Objetivo 2: `python codigo/tabla_dataset_bold.py` (apartado 3.5.1) y `python codigo/tabla_depuracion_por_genero.py` (apartado 3.5.2). Reproducen exactamente `resultados_objetivo2/tabla_dataset_bold.csv` y `tabla_depuracion_por_genero.csv`.
- Anexo 1 (Objetivo 1): `python codigo/armar_anexo1.py` regenera `datos/fuente/estructurado/Anexo1_tablas.xlsx` a partir de los archivos de `datos/fuente/`.
- Tabla de brecha: `python codigo/tabla_brecha_v2.py datos/fuente/estructurado/lista_maestra_taxones.csv` (requiere la variable de entorno `NCBI_EMAIL` y el programa `datasets` de NCBI). Este script consulta BOLD y NCBI en línea: el archivo `datos/fuente/estructurado/tabla_brecha_v2.csv` es la instantánea del 14 de octubre de 2026 en que se hicieron las consultas del Objetivo 1, y una nueva ejecución puede dar cifras algo mayores porque las bases siguen creciendo.
- Integridad de los JSON de BOLD (en el CD, `datos/fuente/original/bold_coi/`): `cd datos/fuente/original/bold_coi && md5sum -c ../../../../resultados_objetivo2/MD5_bold_json.txt`.

## Objetivo 3: modelos de clasificación a nivel de género

Orden de ejecución (desde la raíz del repositorio, con el entorno virtual activado):

1. `python codigo/particion_grupos.py`: grupos de registros relacionados (misma especie formal, mismo BIN o misma secuencia idéntica).
2. `python codigo/particion_pliegues.py`: partición en 5 pliegues por grupos (`StratifiedGroupKFold`, semilla elegida solo por la forma de la partición).
3. `python codigo/entrenar_kmers.py {rf|svm} {3|4}`: Random Forest y SVM sobre frecuencias de k-mers (k=3 y k=4).
4. `python codigo/extraer_embeddings.py <nombre>`, con `<nombre>` igual a `nt50m` o `dnabert2`: embeddings por promedio de los tokens de cada secuencia.
5. `python codigo/entrenar_embeddings.py <nombre>`: SVM RBF sobre los embeddings, con el mismo `<nombre>`.

Los resultados quedan en `resultados_objetivo3/`: predicciones (`pred_*`), hiperparámetros por pliegue (`params_*`), métricas por género (`metricas_genero_*`) y registros de ejecución (`log_*`). Los archivos con sufijo `_rejilla1` corresponden a la primera rejilla de hiperparámetros, exploratoria; los demás, a la rejilla definitiva, fijada antes de ver sus resultados.

Diseño: las métricas se calculan sobre las predicciones de los cinco pliegues juntas (cada registro se predice una sola vez, con un modelo que no vio su grupo). Escalado y ajuste de hiperparámetros se hacen solo con datos de entrenamiento, mediante validación cruzada interna por grupos. El desbalance se trata con `class_weight`, sin sobremuestreo.

Entorno: Python 3.14.4, scikit-learn 1.9.1, numpy 2.5.4, pandas 3.0.6, torch 2.14.1 (CPU), transformers 4.57.6. Dependencias de los modelos de ADN en `requirements_modelo_adn.txt`. Los embeddings no se versionan por su tamaño; se regeneran con el paso 4 (las revisiones exactas de los modelos quedan registradas en los archivos `embeddings_*_info.json`).

Limitaciones: una sola partición y una sola semilla; géneros con pocos registros (Hemilucilia, Cochliomyia, Tricharaea, Boettcheria) con resultados inestables; grupos muy grandes que dejan pocas referencias de su género en el entrenamiento de su pliegue; hiperparámetros óptimos en el borde de la rejilla en varios pliegues; los modelos preentrenados pudieron ver secuencias similares durante su preentrenamiento. Las comparaciones entre modelos con intervalos de confianza corresponden al Objetivo 4.

# ETL con Pentaho (Objetivo 2)

Herramienta: Pentaho Data Integration 11 (Spoon). Las rutas son relativas a esta carpeta
(`${Internal.Entry.Current.Directory}`), por lo que las transformaciones se ejecutan sin cambios.

## Orden de ejecución

| Transformación | Qué hace | Salida |
|---|---|---|
| `01_limpieza_bold.ktr` | Lee `entrada/bold_registros_crudos.csv`. Filtra COI-5P con secuencia, quita los guiones de alineamiento, calcula largo y proporción de bases no ACGT, descarta largo < 500 pb o > 1 % no ACGT y marca el nivel de asignación (especie formal o solo género). | `salida/bold_coi_limpio.csv`, `salida/bold_coi_descartados.csv` |
| `02_criterio_inclusion.ktr` | Cuenta por género los registros, los registros con especie formal y las especies distintas. Cumple si tiene al menos 3 especies y 100 registros con especie. | `salida/criterio_inclusion.csv` |
| `03_filtrar_incluidos.ktr` | Une la tabla limpia con el criterio y separa los géneros incluidos de los que quedan fuera de alcance. | `salida/bold_coi_modelado.csv`, `salida/bold_coi_fuera_alcance.csv` |

## Cifras de verificación

71 806 registros de entrada, 69 622 COI-5P, 69 605 con secuencia, 67 537 tras el control de calidad
(2 068 descartados). De ellos, 66 787 pertenecen a los 14 géneros incluidos y 750 quedan fuera de alcance.

## Archivos comprimidos

Por tamaño, los CSV grandes se guardan como `.gz` (`entrada/bold_registros_crudos.csv.gz`,
`salida/bold_coi_limpio.csv.gz`, `salida/bold_coi_modelado.csv.gz`). Antes de abrir las transformaciones:

    gunzip -k entrada/bold_registros_crudos.csv.gz      # necesario para 01
    gunzip -k salida/bold_coi_limpio.csv.gz              # necesario para 02 y 03 si no se ejecuta 01

## Procedencia de la entrada

`entrada/bold_registros_crudos.csv` resulta de unir los JSON descargados de BOLD por género
(`codigo/descargar_bold_generos.py` y `codigo/extraer_bold_registros.py`). Las sumas MD5 de esos JSON
están en `resultados_objetivo2/MD5_bold_json.txt`.

## Paso posterior (Python)

`codigo/calcular_kmers.py` lee `bold_coi_modelado.csv` y calcula las frecuencias de k-mers (k = 3 y k = 4, canónicos).

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

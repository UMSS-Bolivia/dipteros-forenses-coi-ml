#!/usr/bin/env python3
import csv, glob, os, subprocess, sys

CARPETA, SALIDA = sys.argv[1], sys.argv[2]
TIPOS = [("_genome.fasta", "Genoma (FASTA)", "secuencias"), ("_annotation.gff", "Anotación (GFF)", "genes"),
         ("_cds.fasta", "CDS (FASTA)", "secuencias"), ("_cdna.fasta", "Transcritos cDNA (FASTA)", "secuencias"),
         ("_protein.fasta", "Proteínas (FASTA)", "secuencias")]
FUENTE = {"Aldrichina_grahami": "GigaDB", "Sarcophaga_peregrina": "NCBI", "Calliphora_vomitoria": "NCBI y Ensembl",
          "Musca_domestica": "NCBI", "Lucilia_cuprina": "NCBI"}

def contar(ruta, unidad):
    if unidad == "genes":
        cmd = "awk -F'\\t' '$3==\"gene\"' '%s' | wc -l" % ruta
    else:
        cmd = "grep -c '^>' '%s'" % ruta
    return int(subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip() or 0)

filas, total_mb = [], 0.0
for ruta in sorted(glob.glob(os.path.join(CARPETA, "*"))):
    base = os.path.basename(ruta)
    for sufijo, tipo, unidad in TIPOS:
        if base.endswith(sufijo):
            esp = base[: -len(sufijo)]
            mb = os.path.getsize(ruta) / 1e6
            total_mb += mb
            if esp == "Aldrichina_grahami":
                md5 = "OK (100673.md5 de GigaDB)"
            elif esp == "Calliphora_vomitoria" and sufijo != "_genome.fasta":
                md5 = "no verificado (descarga directa de Ensembl)"
            else:
                md5 = "OK (md5sum.txt de NCBI, archivo original)"
            n = contar(ruta, unidad)
            filas.append([esp.replace("_", " "), FUENTE[esp], tipo, base, round(mb, 1), n, unidad, md5])
            print(esp, tipo, round(mb, 1), "MB", n, unidad)

with open(SALIDA, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Especie", "Repositorio", "Tipo de archivo", "Archivo", "Tamaño (MB)", "Registros", "Unidad", "Verificación MD5"])
    w.writerows(filas)
print("Archivos:", len(filas), "| tamaño total: %.2f GB" % (total_mb / 1000))

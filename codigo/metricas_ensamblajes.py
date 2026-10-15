#!/usr/bin/env python3
import sys, glob, os, csv

def leer_fasta(ruta):
    nombre = None
    largo = gc = n = acgt = 0
    with open(ruta) as f:
        for linea in f:
            if linea.startswith(">"):
                if nombre is not None:
                    yield nombre, largo, gc, n, acgt
                nombre = linea[1:].strip()
                largo = gc = n = acgt = 0
            else:
                s = linea.strip().upper()
                largo += len(s)
                g = s.count("G") + s.count("C")
                gc += g
                acgt += g + s.count("A") + s.count("T")
                n += s.count("N")
    if nombre is not None:
        yield nombre, largo, gc, n, acgt

def n50_l50(largos):
    orden = sorted(largos, reverse=True)
    mitad = sum(orden) / 2
    acum = 0
    for i, l in enumerate(orden, 1):
        acum += l
        if acum >= mitad:
            return l, i

carpeta, prefijo = sys.argv[1], sys.argv[2]
filas, detalle = [], []
for ruta in sorted(glob.glob(os.path.join(carpeta, "*_genome.fasta"))):
    esp = os.path.basename(ruta).replace("_genome.fasta", "").replace("_", " ")
    largos, gc_t, acgt_t, n_t, org_len = [], 0, 0, 0, 0
    for nombre, largo, gc, n, acgt in leer_fasta(ruta):
        es_org = int(("mitochond" in nombre.lower()) or ("organelle" in nombre.lower()))
        detalle.append([esp, nombre.split()[0], largo, round(100 * gc / acgt, 2) if acgt else 0, es_org])
        if es_org:
            org_len += largo
            continue
        largos.append(largo)
        gc_t += gc
        acgt_t += acgt
        n_t += n
    total = sum(largos)
    n50, l50 = n50_l50(largos)
    filas.append([esp, len(largos), total, n50, l50, round(100 * gc_t / acgt_t, 2),
                  round(100 * n_t / total, 4), sum(1 for l in largos if l >= 1000), org_len])
    print(esp, "secuencias:", len(largos), "total:", total, "N50:", n50, "L50:", l50)

with open(prefijo + "_agregado.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["especie", "num_secuencias_nucleares", "longitud_total_nuclear", "n50", "l50", "gc_pct", "gaps_pct", "secuencias_ge_1kb", "longitud_organelos"])
    w.writerows(filas)
with open(prefijo + "_contigs.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["especie", "secuencia_id", "longitud", "gc_pct", "es_organelo"])
    w.writerows(detalle)

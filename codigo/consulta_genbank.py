#!/usr/bin/env python3
import csv, sys, time, datetime, os
from Bio import Entrez

Entrez.email = os.environ["NCBI_EMAIL"]
COI = '(COI[Gene] OR COX1[Gene] OR "cytochrome c oxidase subunit I"[Title] OR "cytochrome oxidase subunit I"[Title])'

def contar(term):
    h = Entrez.esearch(db="nucleotide", term=term, retmax=0)
    r = Entrez.read(h)
    h.close()
    return int(r["Count"])

taxa = [l.strip() for l in open(sys.argv[1]) if l.strip()]
hoy = datetime.date.today().isoformat()
with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["taxon", "registros_nucleotido_totales", "registros_COI", "fecha_consulta"])
    for t in taxa:
        total = contar('"%s"[Organism]' % t)
        time.sleep(0.4)
        coi = contar('"%s"[Organism] AND %s' % (t, COI))
        time.sleep(0.4)
        w.writerow([t, total, coi, hoy])
        print(t, total, coi)

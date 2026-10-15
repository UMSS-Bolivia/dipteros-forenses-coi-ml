#!/usr/bin/env python3
import csv, sys, time, os
from Bio import Entrez, SeqIO

Entrez.email = os.environ["NCBI_EMAIL"]
COI = '(COI[Gene] OR COX1[Gene] OR "cytochrome c oxidase subunit I"[Title] OR "cytochrome oxidase subunit I"[Title])'
familias = ["Calliphoridae", "Sarcophagidae", "Muscidae", "Fanniidae"]

with open(sys.argv[1], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["familia_consulta", "organismo", "accession", "longitud_pb", "localidad", "fecha_coleccion", "envio"])
    for fam in familias:
        term = '"%s"[Organism] AND Bolivia[All Fields] AND %s' % (fam, COI)
        h = Entrez.esearch(db="nucleotide", term=term, retmax=150)
        r = Entrez.read(h)
        h.close()
        ids = r["IdList"]
        print(fam, "- candidatos devueltos por la busqueda:", r["Count"])
        time.sleep(0.4)
        if not ids:
            continue
        h = Entrez.efetch(db="nucleotide", id=",".join(ids), rettype="gb", retmode="text")
        n = 0
        for rec in SeqIO.parse(h, "gb"):
            src = next((ft for ft in rec.features if ft.type == "source"), None)
            q = src.qualifiers if src else {}
            loc = (q.get("geo_loc_name") or q.get("country") or [""])[0]
            if not loc.startswith("Bolivia"):
                continue
            envio = ""
            for ref in rec.annotations.get("references", []):
                if "Submitted" in ref.journal:
                    envio = ref.journal[:70]
                    break
            org = rec.annotations.get("organism", "")
            w.writerow([fam, org, rec.id, len(rec), loc, q.get("collection_date", [""])[0], envio])
            n += 1
        h.close()
        print(fam, "- con localidad Bolivia confirmada:", n)
        time.sleep(0.4)

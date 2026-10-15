#!/usr/bin/env python3
import csv, sys, time, os
from Bio import Entrez, SeqIO

Entrez.email = os.environ["NCBI_EMAIL"]
COI = '(COI[Gene] OR COX1[Gene] OR "cytochrome c oxidase subunit I"[Title] OR "cytochrome oxidase subunit I"[Title])'

taxa = [l.strip() for l in open(sys.argv[1]) if l.strip()]
with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["taxon", "accession", "longitud_pb", "pais", "fecha_coleccion", "fecha_modificacion", "envio"])
    for t in taxa:
        h = Entrez.esearch(db="nucleotide", term='"%s"[Organism] AND %s' % (t, COI), retmax=60)
        lista = Entrez.read(h)["IdList"]
        h.close()
        time.sleep(0.4)
        if not lista:
            continue
        h = Entrez.efetch(db="nucleotide", id=",".join(lista), rettype="gb", retmode="text")
        for rec in SeqIO.parse(h, "gb"):
            src = next((ft for ft in rec.features if ft.type == "source"), None)
            q = src.qualifiers if src else {}
            envio = ""
            for ref in rec.annotations.get("references", []):
                if "Submitted" in ref.journal:
                    envio = ref.journal[:70]
                    break
            w.writerow([t, rec.id, len(rec), (q.get("geo_loc_name") or q.get("country") or [""])[0], q.get("collection_date", [""])[0], rec.annotations.get("date", ""), envio])
        h.close()
        time.sleep(0.4)

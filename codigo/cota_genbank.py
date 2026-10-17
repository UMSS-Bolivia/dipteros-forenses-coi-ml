import os, sys, time
import pandas as pd
from Bio import Entrez

Entrez.email = os.environ["NCBI_EMAIL"]
Entrez.tool = "cota_genbank"

bold = pd.read_csv("datos/intermedio/bold_registros_crudos.csv",
                   usecols=["genus", "insdc_acs"], low_memory=False)
en_bold = set(bold["insdc_acs"].dropna().astype(str).str.split(".").str[0].str.upper())
generos = sorted(bold["genus"].dropna().unique())

COI = ('(COI[All Fields] OR COX1[All Fields] OR "cytochrome c oxidase subunit I"[All Fields] '
       'OR "cytochrome oxidase subunit I"[All Fields])')


def accesiones(consulta):
    for _ in range(5):
        try:
            h = Entrez.esearch(db="nuccore", term=consulta, usehistory="y", retmax=0)
            r = Entrez.read(h); h.close()
            n = int(r["Count"])
            if n == 0:
                return set()
            web, key = r["WebEnv"], r["QueryKey"]
            salida = []
            for ini in range(0, n, 2000):
                h = Entrez.efetch(db="nuccore", rettype="acc", retmode="text",
                                  retstart=ini, retmax=2000, webenv=web, query_key=key)
                salida += [x.strip() for x in h.read().splitlines() if x.strip()]
                h.close()
                time.sleep(0.4)
            return {a.split(".")[0].upper() for a in salida}
        except Exception as e:
            print("reintento:", consulta[:40], e, file=sys.stderr)
            time.sleep(5)
    raise SystemExit("falló la consulta: " + consulta)


filas = []
for g in generos:
    base = f"{g}[Organism] AND {COI}"
    todo = accesiones(base)
    barras = accesiones(base + " AND 500:1600[SLEN]")
    filas.append({"genero": g,
                  "genbank_coi": len(todo),
                  "ya_en_bold": len(todo & en_bold),
                  "no_en_bold": len(todo - en_bold),
                  "genbank_500_1600": len(barras),
                  "no_en_bold_500_1600": len(barras - en_bold)})
    print(filas[-1], flush=True)

t = pd.DataFrame(filas).set_index("genero")
t.loc["TOTAL"] = t.sum()
print(t.to_string())
t.to_csv("resultados/cota_genbank.csv")

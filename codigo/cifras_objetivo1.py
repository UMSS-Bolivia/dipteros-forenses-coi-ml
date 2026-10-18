#!/usr/bin/env python3
import glob, json, os
import pandas as pd
from pandas.errors import EmptyDataError

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)

t = pd.read_csv("datos/fuente/estructurado/tabla_brecha_v2.csv")
t["genero"] = t["nombre_ncbi"].str.split().str[0]
g = t.groupby("genero").agg(
    genomas=("genomas_ncbi_genero", "max"),
    en_la_paz=("departamentos", lambda s: s.str.contains("La Paz").any()),
    bold_bolivia=("bold_bolivia_genero", "max")).reset_index()
print("=== 1. Géneros de la lista maestra ===")
print("géneros distintos:", len(g))
print("sin genoma en NCBI (%d): %s" % ((g.genomas == 0).sum(), ", ".join(g.loc[g.genomas == 0, "genero"])))
print("con genoma de otra especie del género (%d): %s" % ((g.genomas > 0).sum(), ", ".join(g.loc[g.genomas > 0, "genero"])))
lp = g[g.en_la_paz]
print("géneros de La Paz: %d | sin genoma: %d (%s)" % (len(lp), (lp.genomas == 0).sum(), ", ".join(lp.loc[lp.genomas == 0, "genero"])))
print("géneros con COI boliviano en BOLD:", ", ".join(g.loc[g.bold_bolivia > 0, "genero"]) or "ninguno")
sp = t[t["rango"] == "especie"]
print("especies de la lista: %d | con genoma propio: %s" % (len(sp), ", ".join(sp.loc[sp["genomas_ncbi_especie"] > 0, "nombre_ncbi"]) or "ninguna"))
print("filas con BOLD sin respuesta:", int((t["coi_boliviano_bold"] == "sin respuesta").sum()))

print("\n=== 2. COI de Bolivia en BOLD (cuatro familias) ===")
partes = []
for f in sorted(glob.glob("datos/fuente/original/bolivia_*.tsv")):
    try:
        d = pd.read_csv(f, sep="\t", low_memory=False)
    except EmptyDataError:
        print(os.path.basename(f), "-> 0 registros")
        continue
    d["familia_consulta"] = os.path.basename(f)[8:-4]
    partes.append(d)
b = pd.concat(partes, ignore_index=True)
print("registros:", len(b))
print(b["province/state"].fillna("sin dato").value_counts().to_string())
print("instituciones:", dict(b["inst"].fillna("sin dato").value_counts()))
print("años de colecta:", pd.to_datetime(b["collection_date_start"], errors="coerce").dt.year.agg(["min", "max"]).tolist())
print("con acceso INSDC (también en GenBank): %d de %d" % (b["insdc_acs"].notna().sum(), len(b)))

print("\n=== 3. Fannia en BOLD ===")
j = json.load(open("datos/fuente/original/bold_resumen/tax_genus_Fannia.json"))
c, tot = j["country/ocean"], j["counts"]["specimens"]
con_pais = sum(c.values())
sur = ["Argentina", "Brazil", "Colombia", "Ecuador", "Peru", "Suriname", "Chile", "Bolivia", "Venezuela", "Paraguay", "Uruguay", "Guyana"]
cuk = c.get("Canada", 0) + c.get("United Kingdom", 0)
sa = sum(c.get(p, 0) for p in sur)
print("registros: %d | con país: %d | países: %d" % (tot, con_pais, len(c)))
print("Canadá + Reino Unido: %d (%.1f%% del total; %.1f%% de los que tienen país)" % (cuk, 100 * cuk / tot, 100 * cuk / con_pais))
print("Sudamérica: %d (%.1f%% del total)" % (sa, 100 * sa / tot))

print("\n=== 4. Taxones con pocos registros (descarga directa de BOLD) ===")
for f in sorted(glob.glob("datos/fuente/original/global_*.tsv")):
    try:
        d = pd.read_csv(f, sep="\t", low_memory=False)
    except EmptyDataError:
        continue
    pais = d["country/ocean"].fillna("sin dato").value_counts()
    print("%s | registros: %d | COI-5P: %d | países: %s" % (os.path.basename(f)[7:-4], len(d), int((d["marker_code"] == "COI-5P").sum()), dict(pais)))

print("\n=== 5. Calidad de los genomas ===")
print(pd.read_csv("datos/fuente/estructurado/metricas_agregado.csv").to_string(index=False))

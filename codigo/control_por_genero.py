"""Control de duplicados y de coherencia taxonómica desglosado por género
(apartado 4.2.2, Objetivo Específico 2).

Entrada : datos/procesados/bold_coi_modelado_final.csv.gz
Salida  : resultados_objetivo2/control_por_genero.csv
"""
import sys
from pathlib import Path

import pandas as pd

RUTA = Path(sys.argv[1] if len(sys.argv) > 1
            else "datos/procesados/bold_coi_modelado_final.csv.gz")
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2
              else "resultados_objetivo2/control_por_genero.csv")
SALIDA.parent.mkdir(parents=True, exist_ok=True)

d = pd.read_csv(RUTA, low_memory=False)
d["_sec"] = d["secuencia"].str.upper()
formal = d["especie_formal"].notna() & (d["especie_formal"].astype(str).str.strip() != "")
f = d[formal]

# Copias exactas por género
t = d.groupby("genus").agg(registros=("_sec", "size"),
                           secuencias=("_sec", "nunique"))
t["copias_pct"] = (100 * (1 - t["secuencias"] / t["registros"])).round(1)

# Secuencias compartidas por dos o más especies formales
por_sec = f.groupby("_sec").agg(especies=("especie_formal", "nunique"),
                                genero=("genus", "first"),
                                registros=("record_id", "size"))
comp = por_sec[por_sec["especies"] > 1]
t["sec_compartidas"] = comp.groupby("genero").size()
t["reg_en_sec_compartidas"] = comp.groupby("genero")["registros"].sum()

# BIN con más de una especie formal y especies repartidas en más de un BIN
fb = f[f["bin_uri"].notna()]
bins = fb.groupby("bin_uri").agg(especies=("especie_formal", "nunique"),
                                 genero=("genus", "first"))
bins_mult = bins[bins["especies"] > 1]
t["bin_varias_especies"] = bins_mult.groupby("genero").size()
esp = fb.groupby("especie_formal").agg(bins=("bin_uri", "nunique"),
                                       genero=("genus", "first"))
esp_mult = esp[esp["bins"] > 1]
t["especies_en_varios_bin"] = esp_mult.groupby("genero").size()
t["sin_bin"] = d[d["bin_uri"].isna()].groupby("genus").size()

t = t.fillna(0).astype({c: int for c in ("sec_compartidas", "reg_en_sec_compartidas",
                                         "bin_varias_especies", "especies_en_varios_bin",
                                         "sin_bin")})
t = t.sort_values("registros", ascending=False)
t.loc["TOTAL"] = [t["registros"].sum(), len(d["_sec"].unique()),
                  round(100 * (1 - d["_sec"].nunique() / len(d)), 1),
                  len(comp), int(comp["registros"].sum()), len(bins_mult),
                  len(esp_mult), int(d["bin_uri"].isna().sum())]
t = t.astype({c: int for c in t.columns if c != "copias_pct"})
t.to_csv(SALIDA)
print(t.to_string())
print("\nControl con los valores del apartado 3.5.4 y 3.5.5:")
print("  registros", len(d), "(66 782) | con especie formal", int(formal.sum()), "(47 347)")
print("  secuencias distintas", d["_sec"].nunique(), "(28 913)")
print("  secuencias compartidas entre especies", len(comp), "(58) | registros",
      int(comp["registros"].sum()), "(1 030)")
print("  BIN con más de una especie formal", len(bins_mult), "(96)")
print("  especies formales en más de un BIN", len(esp_mult), "(137)")
print("  registros sin BIN", int(d["bin_uri"].isna().sum()), "(812)")

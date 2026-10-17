"""Control de coherencia taxonómica y de BIN sobre el conjunto final (3.5.4).
Ejecutar desde la raíz del repositorio."""
import pandas as pd

ENTRADA = "datos/procesados/bold_coi_modelado_final.csv.gz"
REGEX = r"^[A-Z][a-z]+ [a-z][a-z-]+$"

d = pd.read_csv(ENTRADA, low_memory=False,
                usecols=["record_id", "bin_uri", "genus", "species"])
d["formal"] = d["species"].fillna("").str.match(REGEX)
n = len(d)

res = {}
res["registros"] = n
res["con_especie_formal"] = int(d["formal"].sum())
res["solo_genero"] = int((~d["formal"]).sum())
res["sin_especie"] = int(d["species"].isna().sum())
res["nombre_no_formal"] = int((~d["formal"] & d["species"].notna()).sum())
res["nombres_no_formales_distintos"] = int(
    d.loc[~d["formal"] & d["species"].notna(), "species"].nunique())

# Coherencia género-especie: el primer término de la especie debe ser el género
f = d[d["formal"]]
res["discordancias_genero_especie"] = int(
    (f["species"].str.split().str[0] != f["genus"]).sum())

# BIN
res["bins_distintos"] = int(d["bin_uri"].nunique())
res["registros_sin_bin"] = int(d["bin_uri"].isna().sum())
b = d.dropna(subset=["bin_uri"])
g = b.groupby("bin_uri")["genus"].nunique()
res["bins_con_mas_de_un_genero"] = int((g > 1).sum())

sp = b[b["formal"]].groupby("bin_uri")["species"].nunique()
res["bins_con_mas_de_una_especie_formal"] = int((sp > 1).sum())
disc = (b[b["formal"] & b["bin_uri"].isin(sp[sp > 1].index)]
        .groupby("bin_uri")
        .agg(genero=("genus", "first"),
             especies=("species", lambda s: "; ".join(sorted(s.unique()))),
             n_especies=("species", "nunique"),
             registros=("record_id", "count"))
        .sort_values("registros", ascending=False))
disc.to_csv("resultados_objetivo2/bins_discordantes.csv")

# Especies formales repartidas en más de un BIN
bs = b[b["formal"]].groupby("species")["bin_uri"].nunique()
res["especies_en_mas_de_un_bin"] = int((bs > 1).sum())

pd.Series(res).to_csv("resultados_objetivo2/control_bins.csv", header=["valor"])
for k, v in res.items():
    print(f"{k}: {v}")
print("\nTop BIN con varias especies formales:")
print(disc.head(10).to_string())

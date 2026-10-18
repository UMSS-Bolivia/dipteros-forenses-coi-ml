import pandas as pd

UMBRAL = 0.9
REGEX = r"^[A-Z][a-z]+ [a-z][a-z-]+$"

m = pd.read_csv("pentaho/salida/bold_coi_modelado.csv.gz", low_memory=False)
columnas = list(m.columns)
if "secuencia" not in m.columns:
    sec = pd.read_csv("pentaho/salida/bold_coi_limpio.csv.gz",
                      usecols=["record_id", "secuencia"], low_memory=False)
    m = m.merge(sec, on="record_id", how="left")
m["seq"] = m["secuencia"].str.upper()

ng = m.groupby("seq")["genus"].transform("nunique")
conf = m[ng > 1].copy()
cnt = conf.groupby(["seq", "genus"]).size().rename("n").reset_index()
cnt["prop"] = cnt["n"] / cnt.groupby("seq")["n"].transform("sum")
mayor = cnt.loc[cnt["prop"] >= UMBRAL, ["seq", "genus"]].assign(conservar=True)
conf = conf.merge(mayor, on=["seq", "genus"], how="left")
excl = conf[conf["conservar"].isna()]

cols_rep = ["record_id", "genus", "species", "bin_uri", "insdc_acs", "country/ocean"]
excl[cols_rep].to_csv("resultados_objetivo2/registros_excluidos_multigenero.csv", index=False)
print("secuencias en conflicto:", conf["seq"].nunique())
print("registros excluidos:", len(excl))
print(excl[cols_rep].to_string(index=False))

fin = m[~m["record_id"].isin(excl["record_id"])]
fin[columnas].to_csv("datos/procesados/bold_coi_modelado_final.csv.gz", index=False)
print("modelado antes:", len(m), "| final:", len(fin))

def resumen(df):
    f = df["species"].fillna("").str.match(REGEX)
    r = df[f].groupby("genus").agg(especies=("species", "nunique"), con_especie=("species", "size"))
    return f.sum(), r

fa, _ = resumen(m)
fb, r = resumen(fin)
print("registros con especie formal antes / después:", fa, "/", fb)
print("géneros:", fin["genus"].nunique(), "| géneros que cumplen el criterio:",
      int(((r.especies >= 3) & (r.con_especie >= 100)).sum()))
print(r.sort_values("especies").head(4))

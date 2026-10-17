import pandas as pd

d = pd.read_csv("datos/intermedio/bold_coi_modelado.csv", usecols=["record_id", "bin_uri", "genus", "especie_formal"], low_memory=False)
print("sin BIN:", int(d["bin_uri"].isna().sum()), "de", len(d))
b = d.dropna(subset=["bin_uri"])
n = b.groupby("bin_uri")["genus"].nunique()
disc = n[n > 1].index
print("BINs totales:", b["bin_uri"].nunique(), "| BINs con más de un género:", len(disc))
x = b[b["bin_uri"].isin(disc)]
t = x.groupby(["bin_uri", "genus"]).size().rename("registros").reset_index()
t["es_mayoritario"] = t["registros"] == t.groupby("bin_uri")["registros"].transform("max")
print("registros en el género minoritario de un BIN discordante:", int(t.loc[~t["es_mayoritario"], "registros"].sum()))
t.to_csv("resultados/bins_discordantes.csv", index=False)

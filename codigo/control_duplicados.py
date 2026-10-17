"""Control de duplicados sobre el conjunto modelado final.

Ejecutar desde la raiz del repositorio:  python codigo/control_duplicados.py
"""
import hashlib
import pandas as pd

REGEX = r"^[A-Z][a-z]+ [a-z][a-z-]+$"
d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", low_memory=False)
n = len(d)
d["seq"] = d["secuencia"].str.upper()
filas = [("registros evaluados", n)]

for col in ["record_id", "processid", "insdc_acs"]:
    filas.append((f"{col}: valores repetidos", int(d[col].dropna().duplicated().sum())))
filas.append(("insdc_acs: registros sin accesion", int(d["insdc_acs"].isna().sum())))

vc = d["seq"].value_counts()
rep = vc[vc > 1]
filas += [
    ("secuencias distintas", int(len(vc))),
    ("registros redundantes (copias exactas)", int(n - len(vc))),
    ("porcentaje redundante", round(100 * (n - len(vc)) / n, 1)),
    ("secuencias que aparecen una sola vez", int((vc == 1).sum())),
    ("secuencias repetidas (2 o mas registros)", int(len(rep))),
    ("registros en secuencias repetidas", int(rep.sum())),
    ("tamano del grupo mas grande", int(vc.max())),
    ("mediana del tamano de grupo (repetidas)", float(rep.median())),
]

d["formal"] = d["species"].fillna("").str.match(REGEX)
f = d[d["formal"]]
esp = f.groupby("seq")["species"].nunique()
comp = esp[esp > 1]
filas += [
    ("secuencias identicas en 2+ especies formales", int(len(comp))),
    ("registros con esas secuencias", int(f["seq"].isin(comp.index).sum())),
    ("secuencias identicas en 2+ generos", int((d.groupby("seq")["genus"].nunique() > 1).sum())),
    ("secuencias identicas en 2+ BIN",
     int((d.dropna(subset=["bin_uri"]).groupby("seq")["bin_uri"].nunique() > 1).sum())),
]

res = pd.DataFrame(filas, columns=["control", "valor"])
print(res.to_string(index=False))
res.to_csv("resultados_objetivo2/control_duplicados.csv", index=False)

c = f[f["seq"].isin(comp.index)].copy()
c["id_seq"] = c["seq"].map(lambda s: hashlib.md5(s.encode()).hexdigest()[:10])
tab = (c.groupby("id_seq")
        .agg(genero=("genus", "first"), n_registros=("record_id", "size"),
             especies=("species", lambda x: "; ".join(sorted(set(x)))))
        .reset_index().sort_values("n_registros", ascending=False))
tab.to_csv("resultados_objetivo2/secuencias_compartidas_entre_especies.csv", index=False)
print()
print(tab.head(10).to_string(index=False))
print()
print("grupos mas grandes:")
for s, k in vc.head(5).items():
    sub = d[d["seq"] == s]
    esp_m = sub["species"].mode().iat[0] if sub["species"].notna().any() else "(solo genero)"
    print(k, sub["genus"].mode().iat[0], esp_m)

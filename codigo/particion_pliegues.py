"""Partición en 5 pliegues por grupos (Objetivo 3). Ejecutar desde la raíz, después de particion_grupos.py.

Cada grupo completo va a un solo pliegue. Se prueban 100 semillas y se elige la que deja menos
celdas género x pliegue vacías y, a igualdad, la de tamaños de pliegue más parejos.
La semilla no se elige con ningún resultado de modelos.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

REGEX = r"^[A-Z][a-z]+ [a-z][a-z-]+$"
K = 5
SEMILLAS = range(100)

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz",
                usecols=["record_id", "bin_uri", "genus", "species", "secuencia"], low_memory=False)
d["secuencia"] = d["secuencia"].str.upper()
g = pd.read_csv("resultados_objetivo3/grupos_registros.csv")
assert (d["record_id"].values == g["record_id"].values).all(), "orden distinto entre datos y grupos"
d["grupo"] = g["grupo"].values
d["esp_formal"] = d["species"].where(d["species"].fillna("").str.match(REGEX))

y, grupos = d["genus"].values, d["grupo"].values
filas, mejor = [], None
for s in SEMILLAS:
    pl = np.empty(len(d), dtype=int)
    for k, (_, te) in enumerate(StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=s)
                                .split(np.zeros(len(d)), y, grupos)):
        pl[te] = k
    tab = pd.crosstab(d["genus"], pl).reindex(columns=range(K), fill_value=0)
    vacias = int((tab == 0).sum().sum())
    desv = float(np.abs(np.bincount(pl, minlength=K) / len(d) - 1 / K).max())
    filas.append((s, vacias, round(desv, 8)))
    if mejor is None or (vacias, desv) < mejor[0]:
        mejor = ((vacias, desv), s, pl)

pd.DataFrame(filas, columns=["semilla", "celdas_vacias", "desv_max_tamano"]).to_csv(
    "resultados_objetivo3/seleccion_semilla.csv", index=False)
(_, desv), semilla, d["pliegue"] = mejor[0], mejor[1], mejor[2]

d[["record_id", "genus", "grupo", "pliegue"]].to_csv("resultados_objetivo3/particion_pliegues.csv", index=False)
tab = pd.crosstab(d["genus"], d["pliegue"]).reindex(columns=range(K), fill_value=0)
tab.to_csv("resultados_objetivo3/pliegues_por_genero.csv")

print("semilla elegida:", semilla, "| celdas género x pliegue vacías:", mejor[0][0],
      "| desviación máxima del tamaño (de 20 %):", round(desv * 100, 1), "puntos")
print("mínimo posible de celdas vacías (géneros con menos de 5 grupos):",
      int(sum(max(0, K - n) for n in d.groupby("genus")["grupo"].nunique())))
print("\nRegistros de prueba por género y pliegue:")
print(tab.assign(total=tab.sum(axis=1)).sort_values("total", ascending=False).to_string())
res = d.groupby("pliegue").agg(registros=("record_id", "size"), grupos=("grupo", "nunique"),
                               generos=("genus", "nunique"), especies_formales=("esp_formal", "nunique"))
res["pct"] = (res["registros"] / len(d) * 100).round(1)
print("\nPliegues:"); print(res.to_string())

print("\n=== verificación de que nada se comparte entre pliegues (esperado 0) ===")
print("grupos en más de un pliegue:", int((d.groupby("grupo")["pliegue"].nunique() > 1).sum()))
print("especies formales en más de un pliegue:", int((d.dropna(subset=["esp_formal"]).groupby("esp_formal")["pliegue"].nunique() > 1).sum()))
print("BIN en más de un pliegue:", int((d.dropna(subset=["bin_uri"]).groupby("bin_uri")["pliegue"].nunique() > 1).sum()))
print("secuencias idénticas en más de un pliegue:", int((d.groupby("secuencia")["pliegue"].nunique() > 1).sum()))
print("registros sin pliegue:", int(d["pliegue"].isna().sum()), "| record_id repetidos:", int(d["record_id"].duplicated().sum()))

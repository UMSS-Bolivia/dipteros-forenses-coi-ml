"""Grupos de independencia para la partición del Objetivo 3. Ejecutar desde la raíz.

Dos registros pertenecen al mismo grupo si comparten especie formal, BIN o secuencia
idéntica, directa o indirectamente (componentes conectados del grafo de registros).
Salidas en resultados_objetivo3/: grupos_registros.csv, grupos_resumen.csv, grupos_por_genero.csv
"""
import os
import numpy as np
import pandas as pd

REGEX = r"^[A-Z][a-z]+ [a-z][a-z-]+$"
os.makedirs("resultados_objetivo3", exist_ok=True)

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz",
                usecols=["record_id", "bin_uri", "genus", "species", "secuencia"], low_memory=False)
d["secuencia"] = d["secuencia"].str.upper()   # igual que control_duplicados.py
n = len(d)
d["esp_formal"] = d["species"].where(d["species"].fillna("").str.match(REGEX))

parent = list(range(n))
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

for col in ["esp_formal", "bin_uri", "secuencia"]:
    primero = {}
    for i, v in enumerate(d[col].tolist()):
        if pd.isna(v):
            continue
        if v in primero:
            a, b = find(i), find(primero[v])
            if a != b:
                parent[b] = a
        else:
            primero[v] = i

d["raiz"] = [find(i) for i in range(n)]
orden = d.groupby("raiz").size().sort_values(ascending=False, kind="stable")
ids = {r: f"G{k + 1:05d}" for k, r in enumerate(orden.index)}
d["grupo"] = d["raiz"].map(ids)

res = d.groupby("grupo").agg(genero=("genus", "first"), generos=("genus", "nunique"),
                             registros=("record_id", "size"), especies_formales=("esp_formal", "nunique"),
                             bins=("bin_uri", "nunique")).reset_index()
res.to_csv("resultados_objetivo3/grupos_resumen.csv", index=False)
d[["record_id", "genus", "grupo"]].to_csv("resultados_objetivo3/grupos_registros.csv", index=False)

pg = res.groupby("genero").agg(grupos=("grupo", "size"), registros=("registros", "sum"),
                               mayor_grupo=("registros", "max"),
                               grupos_con_especie=("especies_formales", lambda s: int((s > 0).sum()))).reset_index()
pg["pct_mayor_grupo"] = (pg["mayor_grupo"] / pg["registros"] * 100).round(1)
pg = pg.sort_values("registros", ascending=False)
pg.to_csv("resultados_objetivo3/grupos_por_genero.csv", index=False)

print("registros:", n, "| secuencias distintas:", d["secuencia"].nunique(), "(3.5.3: 28913)")
print("grupos:", len(res), "| grupos de 1 registro:", int((res["registros"] == 1).sum()))
print("grupos con más de un género (esperado 0):", int((res["generos"] > 1).sum()))
print("grupos con ≥2 especies formales (unidas por BIN o secuencia):", int((res["especies_formales"] >= 2).sum()))
print("tamaño de grupo, percentiles 50/90/99/max:", [int(res["registros"].quantile(q)) for q in (.5, .9, .99)], int(res["registros"].max()))
print("\n10 grupos más grandes:")
print(res.head(10).to_string(index=False))
print("\nGrupos por género:")
print(pg.to_string(index=False))

"""Tabla 5-4 del Anexo 5: diez grupos con más errores de BLAST y error de cada método en ellos.
Ejecutar desde la raíz. Usa solo la rejilla definitiva (excluye los archivos *_rejilla1).
"""
import glob
import os
import pandas as pd

part = pd.read_csv("resultados_objetivo3/particion_pliegues.csv", dtype={"record_id": str})[["record_id", "grupo", "pliegue"]]
d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", low_memory=False,
                usecols=["record_id", "genus", "species"]).merge(part, on="record_id")
b = pd.read_csv("resultados_objetivo4/pred_blast.csv", dtype={"record_id": str}).drop(columns="pliegue").merge(part, on="record_id")
b["error"] = b["genero_real"] != b["genero_predicho"]
top = b[b["error"]].groupby("grupo").size().sort_values(ascending=False).head(10)
reg = b.groupby("grupo").size()

nombres = {"svm_dnabert2": "SVM DNABERT-2", "svm_k4": "SVM k=4", "svm_nt50m": "SVM NT50M",
           "rf_k4": "RF k=4", "svm_k3": "SVM k=3", "rf_k3": "RF k=3"}
filas = {"BLAST": b.groupby("grupo")["error"].mean() * 100}
for k, n in nombres.items():
    p = pd.read_csv(f"resultados_objetivo3/pred_{k}.csv", dtype={"record_id": str}).merge(part[["record_id", "grupo"]], on="record_id")
    filas[n] = (p["genero_real"] != p["genero_predicho"]).groupby(p["grupo"]).mean() * 100

c = lambda v, dd=1: f"{v:.{dd}f}".replace(".", ",")
print("Grupo | Especie principal | Género real / predicho (BLAST) | Registros | Errores BLAST | " + " | ".join(filas) + "  (% de error)")
for g, ne in top.items():
    x = d[d["grupo"] == g]
    esp = x["species"].value_counts().index[0]
    pred = b[(b["grupo"] == g) & b["error"]]["genero_predicho"].mode()[0]
    print(f"{g} | {esp} | {x["genus"].mode()[0]} / {pred} | {reg[g]:,} | {ne} | ".replace(",", " ")
          + " | ".join(c(filas[k][g]) for k in filas))
pd.DataFrame(filas).loc[top.index].round(1).to_csv("resultados_objetivo4/anexo5_tabla_5-4.csv")

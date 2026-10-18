"""Descripción de las matrices de k-mers (3.5.6). Ejecutar desde la raíz."""
import os
import numpy as np
import pandas as pd

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz",
                usecols=["record_id", "largo", "prop_no_acgt"], low_memory=False)
z = np.load("datos/procesados/kmers_k3_k4.npz", allow_pickle=True)
res = {"registros": len(d),
       "largo_min": int(d.largo.min()), "largo_mediana": float(d.largo.median()),
       "largo_max": int(d.largo.max()),
       "secuencias_con_alguna_base_no_ACGT": int((d.prop_no_acgt > 0).sum())}
for k in (3, 4):
    v = d.largo - k + 1
    X = z[f"X{k}"]
    res[f"ventanas_k{k}_min"] = int(v.min())
    res[f"ventanas_k{k}_mediana"] = float(v.median())
    res[f"variables_k{k}"] = X.shape[1]
    res[f"porcentaje_ceros_k{k}"] = round(float((X == 0).mean() * 100), 2)
    res[f"variables_constantes_k{k}"] = int((X.std(axis=0) == 0).sum())
    res[f"frecuencia_max_k{k}"] = round(float(X.max()), 4)
    res[f"ejemplo_variables_k{k}"] = " ".join(z[f"cols{k}"][:4].tolist())
res["tamano_npz_MB"] = round(os.path.getsize("datos/procesados/kmers_k3_k4.npz") / 1e6, 1)
pd.Series(res).to_csv("resultados_objetivo2/resumen_kmers.csv", header=["valor"])
for a, b in res.items():
    print(f"{a}: {b}")

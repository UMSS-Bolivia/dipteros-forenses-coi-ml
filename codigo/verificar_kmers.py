"""Verificación independiente de las frecuencias de k-mers (3.5.6).
Recalcula con otro método (cadenas de texto y diccionarios) una muestra de
secuencias y la compara con la matriz guardada. Ejecutar desde la raíz."""
import itertools
import numpy as np
import pandas as pd
from collections import Counter

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz",
                usecols=["record_id", "secuencia"], low_memory=False)
z = np.load("datos/procesados/kmers_k3_k4.npz", allow_pickle=True)
meta = pd.read_csv("datos/procesados/metadatos_modelado.csv.gz", usecols=["record_id"])

COMP = str.maketrans("ACGT", "TGCA")
def canon(w):
    return min(w, w.translate(COMP)[::-1])

res = {"registros": len(d)}
res["orden_record_id_matriz"] = bool((z["record_id"] == d["record_id"].astype(str).values).all())
res["orden_record_id_metadatos"] = bool((meta["record_id"].values == d["record_id"].values).all())

rng = np.random.default_rng(42)
idx = rng.choice(len(d), size=500, replace=False)
for k, X, cols in [(3, z["X3"], z["cols3"]), (4, z["X4"], z["cols4"])]:
    teoricos = {canon("".join(p)) for p in itertools.product("ACGT", repeat=k)}
    res[f"variables_k{k}"] = X.shape[1]
    res[f"variables_k{k}_teoricas"] = len(teoricos)
    res[f"nombres_k{k}_coinciden"] = set(cols.tolist()) == teoricos
    res[f"filas_suman_1_k{k}"] = bool(np.allclose(X.sum(axis=1), 1, atol=1e-4))
    res[f"nan_k{k}"] = int(np.isnan(X).sum())
    pos = {c: i for i, c in enumerate(cols.tolist())}
    maxdif = 0.0
    for i in idx:
        s = d.loc[i, "secuencia"].upper()
        cnt = Counter(canon(s[j:j + k]) for j in range(len(s) - k + 1)
                      if set(s[j:j + k]) <= set("ACGT"))
        tot = sum(cnt.values())
        v = np.zeros(len(cols))
        for w, c in cnt.items():
            v[pos[w]] = c / tot
        maxdif = max(maxdif, float(np.abs(v - X[i]).max()))
    res[f"dif_maxima_k{k}_muestra_500"] = maxdif

pd.Series(res).to_csv("resultados_objetivo2/verificacion_kmers.csv", header=["valor"])
for k_, v_ in res.items():
    print(f"{k_}: {v_}")

import time
import numpy as np
import pandas as pd

ENTRADA = "datos/intermedio/bold_coi_modelado_final.csv"
SALIDA_NPZ = "datos/intermedio/kmers_k3_k4.npz"
SALIDA_META = "datos/intermedio/metadatos_modelado.csv"

CODIGO = np.full(256, 255, dtype=np.uint8)
for i, base in enumerate(b"ACGT"):
    CODIGO[base] = i

def mapa_canonico(k):
    n = 4 ** k
    canon = np.zeros(n, dtype=np.int64)
    for kid in range(n):
        dig = [(kid // 4 ** (k - 1 - j)) % 4 for j in range(k)]
        rc = [3 - x for x in reversed(dig)]
        rid = sum(x * 4 ** (k - 1 - j) for j, x in enumerate(rc))
        canon[kid] = min(kid, rid)
    unicos = np.unique(canon)
    col = {int(c): i for i, c in enumerate(unicos)}
    cmap = np.array([col[int(c)] for c in canon], dtype=np.int64)
    nombres = ["".join("ACGT"[(int(c) // 4 ** (k - 1 - j)) % 4] for j in range(k)) for c in unicos]
    return cmap, nombres

def frecuencias(cod, k, cmap, ncol):
    n = len(cod) - k + 1
    if n <= 0:
        return np.zeros(ncol)
    ventana = np.zeros(n, dtype=np.int64)
    valido = np.ones(n, dtype=bool)
    for j in range(k):
        c = cod[j:j + n]
        valido &= c < 4
        ventana = ventana * 4 + np.where(c < 4, c, 0)
    ids = ventana[valido]
    if len(ids) == 0:
        return np.zeros(ncol)
    cuentas = np.bincount(cmap[ids], minlength=ncol)
    return cuentas / cuentas.sum()

d = pd.read_csv(ENTRADA, low_memory=False)
cmap3, nom3 = mapa_canonico(3)
cmap4, nom4 = mapa_canonico(4)
print("variables k=3:", len(nom3), "| k=4:", len(nom4))
X3 = np.zeros((len(d), len(nom3)), dtype=np.float32)
X4 = np.zeros((len(d), len(nom4)), dtype=np.float32)
t0 = time.time()
for i, s in enumerate(d["secuencia"].str.upper().values):
    cod = CODIGO[np.frombuffer(s.encode("ascii"), dtype=np.uint8)]
    X3[i] = frecuencias(cod, 3, cmap3, len(nom3))
    X4[i] = frecuencias(cod, 4, cmap4, len(nom4))
    if (i + 1) % 10000 == 0:
        print(i + 1, "secuencias,", round(time.time() - t0), "s")

np.savez_compressed(SALIDA_NPZ, X3=X3, X4=X4, cols3=np.array(nom3), cols4=np.array(nom4), record_id=d["record_id"].astype(str).values)
meta = d[["record_id", "processid", "bin_uri", "genus", "species", "especie_formal", "nivel_asignacion", "country/ocean", "province/state", "largo"]]
meta.to_csv(SALIDA_META, index=False)
print("X3:", X3.shape, "| X4:", X4.shape)
print("filas que suman 1 (k=3):", bool(np.allclose(X3.sum(axis=1), 1, atol=1e-4)), "| (k=4):", bool(np.allclose(X4.sum(axis=1), 1, atol=1e-4)))
print("valores NaN:", int(np.isnan(X3).sum() + np.isnan(X4).sum()))

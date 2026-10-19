"""Registros por género del conjunto de datos del Objetivo 3 (apartado 3.6.2). Ejecutar desde la raíz."""
import numpy as np
import pandas as pd

FAMILIA = {
    "Calliphora": "Calliphoridae", "Chrysomya": "Calliphoridae", "Cochliomyia": "Calliphoridae",
    "Hemilucilia": "Calliphoridae", "Fannia": "Fanniidae", "Hydrotaea": "Muscidae",
    "Morellia": "Muscidae", "Musca": "Muscidae", "Muscina": "Muscidae", "Phaonia": "Muscidae",
    "Stomoxys": "Muscidae", "Boettcheria": "Sarcophagidae", "Sarcophaga": "Sarcophagidae",
    "Tricharaea": "Sarcophagidae",
}

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", usecols=["record_id", "genus"], low_memory=False)
z = np.load("datos/procesados/kmers_k3_k4.npz", allow_pickle=True)
assert z["X3"].shape[0] == z["X4"].shape[0] == len(d), "distinto número de filas"
assert (d["record_id"].astype(str).values == z["record_id"].astype(str)).all(), "orden distinto entre datos y matrices"

t = (d.groupby("genus").size().rename("registros").reset_index()
       .rename(columns={"genus": "genero"}).sort_values("registros", ascending=False))
t["familia"] = t["genero"].map(FAMILIA)
assert t["familia"].notna().all(), "género sin familia"
t["pct"] = (100 * t["registros"] / len(d)).round(1)
t = t[["genero", "familia", "registros", "pct"]].reset_index(drop=True)

p = pd.read_csv("resultados_objetivo3/pliegues_por_genero.csv", index_col=0)
c = t.set_index("genero")["registros"]
assert (p.sum(axis=1).reindex(c.index) == c).all(), "no coincide con la partición en pliegues"

total = pd.DataFrame([{"genero": "Total", "familia": "", "registros": len(d), "pct": 100.0}])
t = pd.concat([t, total], ignore_index=True)
t.to_csv("resultados_objetivo3/registros_por_genero.csv", index=False)
print(t.to_string(index=False))
print(f"géneros: {len(c)} | desbalance: {c.max()} / {c.min()} = {c.max() / c.min():.1f} a 1")

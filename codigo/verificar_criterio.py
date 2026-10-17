"""Verifica el criterio de inclusión (Pentaho 02 y 03) recalculándolo en Python,
repite el cálculo sobre el conjunto final y la sensibilidad a los umbrales.
Ejecutar desde la raíz del repositorio."""
import pandas as pd

LIMPIO = "pentaho/salida/bold_coi_limpio.csv.gz"
USO = ["record_id", "genus", "especie_formal"]

def criterio(df, esp=3, reg=100):
    g = (df.groupby("genus")
           .agg(registros=("record_id", "size"),
                con_especie=("especie_formal", "count"),
                especies=("especie_formal", "nunique"))
           .reset_index())
    g["cumple"] = ((g.especies >= esp) & (g.con_especie >= reg)).map({True: "si", False: "no"})
    return g

d = pd.read_csv(LIMPIO, usecols=USO, low_memory=False)
py = criterio(d)

# 1) Tabla de criterio: Python frente a Pentaho 02
pt = pd.read_csv("pentaho/salida/criterio_inclusion.csv").fillna({"especies": 0})
pt["especies"] = pt["especies"].astype(int)
m = py.merge(pt, on="genus", suffixes=("_py", "_pt"), how="outer")
res = {"generos_python": len(py), "generos_pentaho": len(pt)}
for c in ["registros", "con_especie", "especies", "cumple"]:
    res[f"coincide_{c}"] = bool((m[f"{c}_py"] == m[f"{c}_pt"]).all())

# 2) Registros modelables y fuera de alcance: Python frente a Pentaho 03
incl = set(py.loc[py.cumple == "si", "genus"])
ids_py = set(d.loc[d.genus.isin(incl), "record_id"])
ids_mod = set(pd.read_csv("pentaho/salida/bold_coi_modelado.csv.gz", usecols=["record_id"])["record_id"])
ids_fuera = set(pd.read_csv("pentaho/salida/bold_coi_fuera_alcance.csv", usecols=["record_id"])["record_id"])
res["generos_incluidos"] = len(incl)
res["modelado_python"] = len(ids_py)
res["modelado_pentaho"] = len(ids_mod)
res["modelado_mismos_ids"] = ids_py == ids_mod
res["fuera_alcance_python"] = len(set(d["record_id"]) - ids_py)
res["fuera_alcance_pentaho"] = len(ids_fuera)
res["fuera_mismos_ids"] = (set(d["record_id"]) - ids_py) == ids_fuera
pd.Series(res).to_csv("resultados_objetivo2/verificacion_criterio.csv", header=["valor"])
for k, v in res.items():
    print(f"{k}: {v}")

# 3) Sensibilidad a los umbrales (conjunto de Pentaho, previo a la exclusión de 3.5.4)
filas = []
for esp, reg in [(2, 50), (3, 100), (3, 200), (5, 100), (5, 200)]:
    c = criterio(d, esp, reg)
    ok = c[c.cumple == "si"]
    filas.append({"min_especies": esp, "min_registros": reg,
                  "generos": len(ok), "registros": int(ok.registros.sum())})
sens = pd.DataFrame(filas)
sens.to_csv("resultados_objetivo2/sensibilidad_criterio.csv", index=False)
print("\nSensibilidad:\n", sens.to_string(index=False))

# 4) Criterio recalculado sobre el conjunto final (66 782), tras la exclusión de 3.5.4
fin = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", usecols=USO, low_memory=False)
cf = criterio(fin)
cf.to_csv("resultados_objetivo2/criterio_inclusion_final.csv", index=False)
dif = cf.merge(py, on="genus", suffixes=("_final", "_pent"))
dif = dif[(dif.registros_final != dif.registros_pent) | (dif.con_especie_final != dif.con_especie_pent) | (dif.especies_final != dif.especies_pent)]
print("\nGéneros que cambian tras la exclusión:\n", dif.to_string(index=False))
print("\nGéneros en el conjunto final:", len(cf), "| todos cumplen:", bool((cf.cumple == "si").all()),
      "| registros:", int(cf.registros.sum()))

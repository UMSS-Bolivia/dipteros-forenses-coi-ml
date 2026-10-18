"""Tabla por género de la depuración de calidad (3.5.2). Ejecutar desde la raíz."""
import pandas as pd

lim = pd.read_csv("pentaho/salida/bold_coi_limpio.csv.gz", usecols=["genus"], low_memory=False)
des = pd.read_csv("pentaho/salida/bold_coi_descartados.csv", usecols=["genus", "resultado_calidad"], low_memory=False)
t = pd.DataFrame({"retenidos": lim.groupby("genus").size()})
t = t.join(des.groupby(["genus", "resultado_calidad"]).size().unstack(fill_value=0), how="outer").fillna(0).astype(int)
for c in ["largo<500", "no_ACGT>1%"]:
    if c not in t:
        t[c] = 0
t["evaluados"] = t["retenidos"] + t["largo<500"] + t["no_ACGT>1%"]
t["pct_retenido"] = (t["retenidos"] / t["evaluados"] * 100).round(1)
t = t[["retenidos", "largo<500", "no_ACGT>1%", "evaluados", "pct_retenido"]].reset_index()
tot = {"genus": "TOTAL"}
for c in ["retenidos", "largo<500", "no_ACGT>1%", "evaluados"]:
    tot[c] = int(t[c].sum())
tot["pct_retenido"] = round(tot["retenidos"] / tot["evaluados"] * 100, 1)
t = pd.concat([t, pd.DataFrame([tot])], ignore_index=True)
t.to_csv("resultados_objetivo2/tabla_depuracion_por_genero.csv", index=False)
print(t.to_string(index=False))

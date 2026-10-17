"""Verifica la transformacion 01 de Pentaho recalculando la depuracion en Python.

Ejecutar desde la raiz del repositorio:  python codigo/verificar_depuracion.py
"""
import pandas as pd

LARGO_MIN = 500
PROP_NO_ACGT_MAX = 0.01

crudos = pd.read_csv("pentaho/entrada/bold_registros_crudos.csv.gz",
                     usecols=["record_id", "marker_code", "nuc"], low_memory=False)
coi = crudos[crudos["marker_code"] == "COI-5P"]
sin_sec = coi[coi["nuc"].isna()]
c = coi[coi["nuc"].notna()].copy()

s = c["nuc"].str.replace("-", "", regex=False).str.upper()
largo = s.str.len()
prop = (largo - s.str.count("[ACGT]")) / largo
c["causa"] = "ok"
c.loc[largo < LARGO_MIN, "causa"] = "largo<500"
c.loc[(largo >= LARGO_MIN) & (prop > PROP_NO_ACGT_MAX), "causa"] = "no_ACGT>1%"

limpio = pd.read_csv("pentaho/salida/bold_coi_limpio.csv.gz", usecols=["record_id"])
desc = pd.read_csv("pentaho/salida/bold_coi_descartados.csv",
                   usecols=["record_id", "resultado_calidad"])

py_ok = set(c.loc[c["causa"] == "ok", "record_id"])
py_desc = c.loc[c["causa"] != "ok", ["record_id", "causa"]]
pe_ok = set(limpio["record_id"])

union = py_desc.merge(desc, on="record_id", how="outer", indicator=True)
misma_causa = (union["_merge"] == "both") & (union["causa"] == union["resultado_calidad"])

filas = [
    ("registros crudos", len(crudos), ""),
    ("COI-5P", len(coi), ""),
    ("COI-5P sin secuencia", len(sin_sec), ""),
    ("COI-5P con secuencia", len(c), ""),
    ("retenidos (Python)", len(py_ok), ""),
    ("retenidos (Pentaho)", len(pe_ok), ""),
    ("descartados (Python)", len(py_desc), ""),
    ("descartados (Pentaho)", len(desc), ""),
    ("retenidos: mismos record_id", py_ok == pe_ok, ""),
    ("descartados: mismos record_id y misma causa", bool(misma_causa.all()), ""),
    ("sin secuencia presentes en alguna salida de Pentaho",
     int(sin_sec["record_id"].isin(pe_ok | set(desc["record_id"])).sum()), ""),
]
res = pd.DataFrame(filas, columns=["control", "valor", "nota"]).drop(columns="nota")
print(res.to_string(index=False))
print()
print(py_desc["causa"].value_counts().to_string())
res.to_csv("resultados_objetivo2/verificacion_depuracion.csv", index=False)

"""Secuencias idénticas asignadas a más de un género (3.5.4). Ejecutar desde la raíz."""
import pandas as pd

COLS = ["record_id", "genus", "species", "identification_rank", "bin_uri",
        "insdc_acs", "country/ocean", "largo"]
m = pd.read_csv("pentaho/salida/bold_coi_modelado.csv.gz", usecols=COLS + ["secuencia"], low_memory=False)
m["seq"] = m["secuencia"].str.upper()
c = m[m.groupby("seq")["genus"].transform("nunique") > 1].copy()
c["id_seq"] = c.groupby("seq").ngroup() + 1
c = c.sort_values(["id_seq", "genus", "record_id"])
c[["id_seq"] + COLS].to_csv("resultados_objetivo2/secuencias_multigenero.csv", index=False)
print("secuencias en conflicto:", c["id_seq"].nunique(), "| registros:", len(c))
print(c.groupby(["id_seq", "genus"]).size().to_string())

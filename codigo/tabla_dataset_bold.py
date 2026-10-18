"""Tabla por género de los registros descargados de BOLD (3.5.1). Ejecutar desde la raíz."""
import pandas as pd

REGEX = r"^[A-Z][a-z]+ [a-z][a-z-]+$"
d = pd.read_csv("pentaho/entrada/bold_registros_crudos.csv.gz", low_memory=False)
coi = d[d["marker_code"] == "COI-5P"].copy()
con_sec = coi["nuc"].fillna("").str.replace("-", "", regex=False).str.len() > 0
formal = coi["species"].fillna("").str.match(REGEX)
t = pd.DataFrame({
    "registros_total": d.groupby("genus").size(),
    "coi5p": coi.groupby("genus").size(),
    "coi5p_con_secuencia": coi[con_sec].groupby("genus").size(),
    "coi5p_especie_formal": coi[formal].groupby("genus").size(),
    "especies_formales": coi[formal].groupby("genus")["species"].nunique(),
}).fillna(0).astype(int)
t.insert(0, "familia", d.groupby("genus")["family"].first())
t = t.reset_index().sort_values(["familia", "genus"])
tot = {"genus": "TOTAL", "familia": ""}
for c in ["registros_total", "coi5p", "coi5p_con_secuencia", "coi5p_especie_formal"]:
    tot[c] = int(t[c].sum())
tot["especies_formales"] = int(coi[formal]["species"].nunique())
t = pd.concat([t, pd.DataFrame([tot])], ignore_index=True)
t.to_csv("resultados_objetivo2/tabla_dataset_bold.csv", index=False)
print(t.to_string(index=False))

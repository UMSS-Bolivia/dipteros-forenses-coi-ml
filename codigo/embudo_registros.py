"""Embudo de registros: de la descarga al conjunto final. Ejecutar desde la raíz."""
import pandas as pd

raw = pd.read_csv("pentaho/entrada/bold_registros_crudos.csv.gz",
                  usecols=["record_id", "marker_code", "nuc"], low_memory=False)
coi = raw[raw.marker_code == "COI-5P"]
sec = coi[coi.nuc.fillna("").str.replace("-", "", regex=False).str.len() > 0]
n = lambda f, **kw: len(pd.read_csv(f, usecols=["record_id"], low_memory=False))
filas = [
    ("Registros descargados (todos los marcadores)", len(raw)),
    ("Registros con COI-5P", len(coi)),
    ("COI-5P con secuencia", len(sec)),
    ("Tras el control de calidad (3.5.2)", n("pentaho/salida/bold_coi_limpio.csv.gz")),
    ("Géneros incluidos (3.5.5)", n("pentaho/salida/bold_coi_modelado.csv.gz")),
    ("Tras excluir conflictos de género (3.5.4)", n("datos/procesados/bold_coi_modelado_final.csv.gz")),
]
t = pd.DataFrame(filas, columns=["etapa", "registros"])
t["perdidos"] = (-t.registros.diff()).fillna(0).astype(int)
t.loc[len(t)] = ["Fuera de alcance (aparte, 3.5.5)", n("pentaho/salida/bold_coi_fuera_alcance.csv"), 0]
t.to_csv("resultados_objetivo2/embudo_registros.csv", index=False)
print(t.to_string(index=False))

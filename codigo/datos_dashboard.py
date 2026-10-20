"""Datos del dashboard del Objetivo 4. Ejecutar desde la raíz.

Reúne en un solo JSON los resultados del Objetivo 4 (comparación, pruebas pareadas, estratos de
identidad), las métricas por género y la tabla de brecha del Objetivo 1 cruzada con el modelo,
más los contornos de los departamentos. No calcula inferencia nueva: lee los CSV ya generados.
"""
import json
import os
import unicodedata
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
                             precision_recall_fscore_support)

R4 = "resultados_objetivo4"
SIN_HIT = "sin_asignacion"
RUTAS = {
    "RF k=3": "resultados_objetivo3/pred_rf_k3.csv",
    "RF k=4": "resultados_objetivo3/pred_rf_k4.csv",
    "SVM k=3": "resultados_objetivo3/pred_svm_k3.csv",
    "SVM k=4": "resultados_objetivo3/pred_svm_k4.csv",
    "SVM NT50M": "resultados_objetivo3/pred_svm_nt50m.csv",
    "SVM DNABERT-2": "resultados_objetivo3/pred_svm_dnabert2.csv",
    "BLAST": f"{R4}/pred_blast.csv",
}
SENS = f"{R4}/pred_blast_sin_GBDP0769.csv"
ESCENARIOS = ["completo", "sin_G00001"]

p = pd.read_csv("resultados_objetivo3/particion_pliegues.csv", dtype={"record_id": str})
labs = sorted(p["genus"].unique())
mascara = {"completo": np.ones(len(p), bool), "sin_G00001": (p["grupo"] != "G00001").values}


def pred(ruta):
    x = (pd.read_csv(ruta, usecols=["record_id", "genero_real", "genero_predicho"], dtype={"record_id": str})
           .set_index("record_id").loc[p["record_id"]])
    assert (x["genero_real"].values == p["genus"].values).all(), ruta
    return x["genero_predicho"].values


def por_genero(y, yp):
    pr, rc, f1, n = precision_recall_fscore_support(y, yp, labels=labs, zero_division=0)
    return [{"genero": g, "registros": int(a), "recall": round(float(b), 4), "precision": round(float(c), 4),
             "f1": round(float(d), 4)} for g, a, b, c, d in zip(labs, n, rc, pr, f1)]


preds = {m: pred(r) for m, r in RUTAS.items()}
y = p["genus"].values
genero = {esc: {m: por_genero(y[mk], preds[m][mk]) for m in RUTAS} for esc, mk in mascara.items()}

cm = pd.read_csv(f"{R4}/comparacion_metodos.csv")
resumen = {}
for esc in ESCENARIOS:
    t = cm[cm.escenario == esc]
    resumen[esc] = [{"metodo": r.metodo,
                     "f1": r.f1_macro, "f1_lo": r.f1_macro_ic_inf, "f1_hi": r.f1_macro_ic_sup,
                     "bal": r.exactitud_balanceada, "bal_lo": r.exactitud_balanceada_ic_inf,
                     "bal_hi": r.exactitud_balanceada_ic_sup,
                     "acc": r.exactitud, "acc_lo": r.exactitud_ic_inf, "acc_hi": r.exactitud_ic_sup}
                    for r in t.itertuples()]

cp = pd.read_csv(f"{R4}/comparaciones_pareadas.csv")
pares = {esc: [{"A": r.A, "B": r.B, "tipo": r.tipo, "dif": r.dif_f1_macro, "lo": r.ic_inf, "hi": r.ic_sup,
                "p": r.p_remuestreo, "p_holm": r.p_remuestreo_holm,
                "pw": r.p_wilcoxon, "pw_holm": r.p_wilcoxon_holm}
               for r in cp[cp.escenario == esc].itertuples()] for esc in ESCENARIOS}

ei = pd.read_csv(f"{R4}/estratos_identidad.csv")
ed = pd.read_csv(f"{R4}/estratos_identidad_diferencias.csv")
estratos = {}
for esc in ESCENARIOS:
    lista = []
    for et in pd.unique(ei[ei.escenario == esc]["estrato"]):
        t = ei[(ei.escenario == esc) & (ei.estrato == et)]
        filas = []
        for r in t.itertuples():
            d = ed[(ed.escenario == esc) & (ed.estrato == et) & (ed.metodo == r.metodo) & (ed.metrica == "exactitud")]
            fila = {"metodo": r.metodo, "acc": r.exactitud, "acc_lo": r.exactitud_ic_inf, "acc_hi": r.exactitud_ic_sup,
                    "bal": r.exactitud_balanceada, "bal_lo": r.exactitud_balanceada_ic_inf,
                    "bal_hi": r.exactitud_balanceada_ic_sup, "dif": None, "dif_lo": None, "dif_hi": None,
                    "dif_bal": None, "dif_bal_lo": None, "dif_bal_hi": None, "p_bal": None, "p_holm_bal": None}
            if len(d):
                fila.update(dif=d.iloc[0].dif_vs_BLAST, dif_lo=d.iloc[0].ic_inf, dif_hi=d.iloc[0].ic_sup)
            db = ed[(ed.escenario == esc) & (ed.estrato == et) & (ed.metodo == r.metodo) & (ed.metrica == "exactitud_balanceada")]
            if len(db):
                fila.update(dif_bal=db.iloc[0].dif_vs_BLAST, dif_bal_lo=db.iloc[0].ic_inf, dif_bal_hi=db.iloc[0].ic_sup,
                            p_bal=db.iloc[0].p_remuestreo, p_holm_bal=db.iloc[0].p_holm)
            filas.append(fila)
        lista.append({"estrato": et, "registros": int(t.iloc[0].registros), "grupos": int(t.iloc[0].grupos),
                      "generos": int(t.iloc[0].generos), "metodos": filas})
    estratos[esc] = lista

sens = None
if os.path.exists(SENS):
    ps = pred(SENS)
    sens = {"f1": round(float(f1_score(y, ps, labels=labs, average="macro", zero_division=0)), 4),
            "bal": round(float(balanced_accuracy_score(y, ps)), 4),
            "acc": round(float(accuracy_score(y, ps)), 4)}


# ---- tabla de brecha cruzada con el modelo ----
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()
    return {"beni": "el beni"}.get(s, s)


geo = json.load(open("datos/fuente/mapa/bolivia_departamentos.geojson", encoding="utf-8"))
deptos = {norm(f["properties"]["nombre"]): f["properties"]["nombre"] for f in geo["features"]}
tb = pd.read_csv("datos/fuente/estructurado/tabla_brecha_v2.csv")
gen = {m: {r["genero"]: r for r in genero["completo"][m]} for m in ["BLAST", "SVM DNABERT-2"]}
brecha = []
for r in tb.itertuples():
    g = r.taxon_fuente.split()[0]
    en = g in labs
    deps = [deptos[norm(d)] for d in str(r.departamentos).split(";")]
    fila = {"taxon": r.taxon_fuente, "rango": r.rango, "familia": r.familia, "fuentes": r.fuentes, "departamentos": deps, "genero": g,
            "en_modelo": en, "coi_genero": r.bold_coi5p_genero, "bolivia_genero": r.bold_bolivia_genero,
            "coi_especie": r.bold_coi5p_especie, "bolivia_especie": r.bold_bolivia_especie,
            "genbank_especie": r.genbank_coi_especie, "genomica": r.situacion_genomica,
            "coi_bolivia": r.coi_boliviano_bold,
            "registros_modelo": gen["BLAST"][g]["registros"] if en else None,
            "blast_recall": gen["BLAST"][g]["recall"] if en else None,
            "blast_f1": gen["BLAST"][g]["f1"] if en else None,
            "dnabert2_recall": gen["SVM DNABERT-2"][g]["recall"] if en else None,
            "dnabert2_f1": gen["SVM DNABERT-2"][g]["f1"] if en else None}
    brecha.append(fila)
departamentos = []
for nombre in sorted(deptos.values()):
    ts = [b for b in brecha if nombre in b["departamentos"]]
    departamentos.append({"nombre": nombre, "n_taxa": len(ts), "n_en_modelo": sum(b["en_modelo"] for b in ts),
                          "n_fuera": sum(not b["en_modelo"] for b in ts),
                          "n_con_coi_bolivia": sum(str(b["coi_bolivia"]).startswith("sí") for b in ts)})

mod = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz",
                  usecols=["record_id", "genus", "species", "bin_uri", "country/ocean", "province/state"], low_memory=False)
bo = mod[mod["country/ocean"].astype(str).str.contains("Bolivia", case=False)]
bolivia_registros = [{"record_id": r["record_id"], "genero": r["genus"],
                      "especie": None if pd.isna(r["species"]) else r["species"],
                      "bin": None if pd.isna(r["bin_uri"]) else r["bin_uri"],
                      "departamento": deptos.get(norm(r["province/state"]), r["province/state"])}
                     for r in bo.to_dict("records")]
datos = {"meta": {"n_registros": int(len(p)), "n_grupos": int(p["grupo"].nunique()), "generos": labs,
                  "bootstrap": 2000, "semilla": 2026},
         "metodos": list(RUTAS), "resumen": resumen, "pares": pares, "estratos": estratos, "genero": genero,
         "sensibilidad_blast": sens, "bolivia_registros": bolivia_registros, "brecha": brecha, "departamentos": departamentos, "mapa": geo}


def limpiar(o):
    if isinstance(o, dict):
        return {k: limpiar(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpiar(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else float(o)
    return o


salida = f"{R4}/dashboard_datos.json"
with open(salida, "w", encoding="utf-8") as fh:
    json.dump(limpiar(datos), fh, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
print(f"{salida}: {os.path.getsize(salida) / 1024:.0f} KB")
print("taxones en la tabla de brecha:", len(brecha), "| con género en el modelo:", sum(b["en_modelo"] for b in brecha),
      "| fuera del modelo:", sum(not b["en_modelo"] for b in brecha))
print("géneros fuera del modelo:", sorted({b["genero"] for b in brecha if not b["en_modelo"]}))
print("por departamento:", {d["nombre"]: (d["n_taxa"], d["n_en_modelo"], d["n_con_coi_bolivia"])
                            for d in departamentos if d["n_taxa"]})
print("sensibilidad BLAST sin GBDP0769:", sens if sens else "no disponible todavía")
print("registros de Bolivia en el modelado:", len(bolivia_registros),
      [(b["genero"], b["departamento"]) for b in bolivia_registros])

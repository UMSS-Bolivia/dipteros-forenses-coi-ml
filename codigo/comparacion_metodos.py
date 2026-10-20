"""Comparación de métodos con intervalos y pruebas pareadas (Objetivo 4). Ejecutar desde la raíz.

Decisiones fijadas en resultados_objetivo4/plan_analisis.md. Remuestreo de los grupos con
reemplazo (las mismas remuestras para todos los métodos). En cada remuestra, los promedios
macro usan solo los géneros con al menos un registro real en esa remuestra.
"""
import itertools
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

SEMILLA, B = 2026, 2000
SIN_HIT = "sin_asignacion"
RUTAS = {
    "RF k=3": "resultados_objetivo3/pred_rf_k3.csv",
    "RF k=4": "resultados_objetivo3/pred_rf_k4.csv",
    "SVM k=3": "resultados_objetivo3/pred_svm_k3.csv",
    "SVM k=4": "resultados_objetivo3/pred_svm_k4.csv",
    "SVM NT50M": "resultados_objetivo3/pred_svm_nt50m.csv",
    "SVM DNABERT-2": "resultados_objetivo3/pred_svm_dnabert2.csv",
    "BLAST": "resultados_objetivo4/pred_blast.csv",
}

p = pd.read_csv("resultados_objetivo3/particion_pliegues.csv", dtype={"record_id": str})
labs = sorted(p["genus"].unique()); K = len(labs); idx = {g: i for i, g in enumerate(labs)}
grupos = sorted(p["grupo"].unique()); G = len(grupos); gidx = {g: i for i, g in enumerate(grupos)}
gi = p["grupo"].map(gidx).values; yi = p["genus"].map(idx).values


def matrices(ruta):
    x = (pd.read_csv(ruta, usecols=["record_id", "genero_real", "genero_predicho"], dtype={"record_id": str})
           .set_index("record_id").loc[p["record_id"]])
    assert (x["genero_real"].values == p["genus"].values).all(), ruta
    pr = x["genero_predicho"].map(lambda v: idx.get(v, K if v == SIN_HIT else -1)).values
    assert (pr >= 0).all(), ruta
    C = np.zeros((G, K, K + 1))
    np.add.at(C, (gi, yi, pr), 1)
    return C


def metricas(CM):
    tp = np.diagonal(CM[..., :K], axis1=-2, axis2=-1)
    fila = CM.sum(-1)
    col = CM[..., :K].sum(-2)
    pres = fila > 0
    f1 = np.divide(2 * tp, fila + col, out=np.zeros_like(tp), where=(fila + col) > 0)
    rec = np.divide(tp, fila, out=np.zeros_like(tp), where=pres)
    n = pres.sum(-1)
    return ({"f1_macro": (f1 * pres).sum(-1) / n, "exactitud_balanceada": (rec * pres).sum(-1) / n,
             "exactitud": tp.sum(-1) / fila.sum(-1)}, f1, pres)


def holm(pv):
    pv = np.asarray(pv, float); o = np.argsort(pv); m = len(pv); aj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * pv[i]); aj[i] = min(1.0, run)
    return aj


def analizar(escenario, activo, Cs):
    rng = np.random.default_rng(SEMILLA)
    act = np.where(activo)[0]
    W = np.zeros((B, G))
    for b in range(B):
        W[b] = np.bincount(rng.choice(act, size=len(act)), minlength=G)
    filas, boot, f1g = [], {}, {}
    for nombre, C in Cs.items():
        m0, f10, pres0 = metricas(C[act].sum(0))
        mb, _, presb = metricas(np.tensordot(W, C, axes=(1, 0)))
        boot[nombre], f1g[nombre] = mb, f10
        fila = {"escenario": escenario, "metodo": nombre}
        for k in m0:
            lo, hi = np.percentile(mb[k], [2.5, 97.5])
            fila[k] = round(float(m0[k]), 4); fila[k + "_ic_inf"] = round(float(lo), 4)
            fila[k + "_ic_sup"] = round(float(hi), 4)
        filas.append(fila)
    print(f"[{escenario}] grupos activos: {len(act)} | géneros presentes: {int(pres0.sum())} | "
          f"remuestras con algún género ausente: {int((~presb).any(-1).sum())} de {B}")
    pares = []
    for a, b_ in itertools.combinations(Cs, 2):
        d = boot[a]["f1_macro"] - boot[b_]["f1_macro"]
        pv = min(1.0, 2 * min((d <= 0).sum() + 1, (d >= 0).sum() + 1) / (B + 1))
        dif = (f1g[a] - f1g[b_])[pres0]
        try:
            pw = float(wilcoxon(dif, zero_method="wilcox").pvalue)
        except ValueError:
            pw = 1.0
        lo, hi = np.percentile(d, [2.5, 97.5])
        conf = {a, b_} == {"SVM NT50M", "BLAST"}
        pares.append({"escenario": escenario, "A": a, "B": b_, "tipo": "confirmatoria" if conf else "exploratoria",
                      "dif_f1_macro": round(float(boot[a]["f1_macro"].mean() * 0 + (
                          metricas(Cs[a][act].sum(0))[0]["f1_macro"] - metricas(Cs[b_][act].sum(0))[0]["f1_macro"])), 4),
                      "ic_inf": round(float(lo), 4), "ic_sup": round(float(hi), 4),
                      "p_remuestreo": round(pv, 4), "p_wilcoxon": round(pw, 4)})
    df = pd.DataFrame(pares)
    df["p_remuestreo_holm"] = np.nan; df["p_wilcoxon_holm"] = np.nan
    ex = df["tipo"] == "exploratoria"
    df.loc[ex, "p_remuestreo_holm"] = np.round(holm(df.loc[ex, "p_remuestreo"].values), 4)
    df.loc[ex, "p_wilcoxon_holm"] = np.round(holm(df.loc[ex, "p_wilcoxon"].values), 4)
    return pd.DataFrame(filas), df


Cs = {n: matrices(r) for n, r in RUTAS.items()}
res, par = [], []
for esc, activo in [("completo", np.ones(G, bool)), ("sin_G00001", np.array([g != "G00001" for g in grupos]))]:
    a, b = analizar(esc, activo, Cs); res.append(a); par.append(b)
res, par = pd.concat(res), pd.concat(par)
res.to_csv("resultados_objetivo4/comparacion_metodos.csv", index=False)
par.to_csv("resultados_objetivo4/comparaciones_pareadas.csv", index=False)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
for esc in ["completo", "sin_G00001"]:
    print(f"\n=== {esc}: métricas con IC 95 % ===")
    t = res[res.escenario == esc]
    print(t[["metodo", "f1_macro", "f1_macro_ic_inf", "f1_macro_ic_sup", "exactitud_balanceada",
             "exactitud_balanceada_ic_inf", "exactitud_balanceada_ic_sup", "exactitud"]].to_string(index=False))
    print(f"\n=== {esc}: diferencias pareadas de F1 macro (A - B) ===")
    print(par[par.escenario == esc].drop(columns="escenario").to_string(index=False))

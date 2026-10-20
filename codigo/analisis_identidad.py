"""Desempeño por estrato de identidad del mejor hit de BLAST contra el entrenamiento (Objetivo 4).

Ejecutar desde la raíz. Decisiones fijadas en resultados_objetivo4/plan_analisis.md.
Remuestreo de grupos como en comparacion_metodos.py (semilla 2026, 2000 remuestras).
En cada estrato se compara cada modelo con BLAST en la exactitud balanceada (diferencia, IC 95 %
y valor p del remuestreo), con ajuste de Holm sobre los 30 valores p de cada escenario.
"""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import pandas as pd

SEMILLA, B = 2026, 2000
SIN_HIT = "sin_asignacion"
ESTRATOS = [(0, 90, "<90"), (90, 95, "90-95"), (95, 98, "95-98"), (98, 99, "98-99"), (99, 101, ">=99")]
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

bl = (pd.read_csv("resultados_objetivo4/pred_blast.csv", dtype={"record_id": str})
        .set_index("record_id").loc[p["record_id"]])
ident = bl["pident_mejor"].values
assert not np.isnan(ident).any()
est = np.full(len(p), -1)
for s, (lo, hi, _) in enumerate(ESTRATOS):
    est[(ident >= lo) & (ident < hi)] = s
assert (est >= 0).all()
S = len(ESTRATOS)


def matrices(ruta):
    x = (pd.read_csv(ruta, usecols=["record_id", "genero_real", "genero_predicho"], dtype={"record_id": str})
           .set_index("record_id").loc[p["record_id"]])
    assert (x["genero_real"].values == p["genus"].values).all(), ruta
    pr = x["genero_predicho"].map(lambda v: idx.get(v, K if v == SIN_HIT else -1)).values
    assert (pr >= 0).all(), ruta
    C = np.zeros((S, G, K, K + 1))
    np.add.at(C, (est, gi, yi, pr), 1)
    return C


def metricas(CM):
    tp = np.diagonal(CM[..., :K], axis1=-2, axis2=-1)
    fila = CM.sum(-1); pres = fila > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        rec = np.where(pres, tp / fila, 0.0)
        n = pres.sum(-1)
        return {"exactitud": tp.sum(-1) / fila.sum(-1), "exactitud_balanceada": (rec * pres).sum(-1) / n}, pres


def ic(v):
    v = v[~np.isnan(v)]
    return (tuple(np.percentile(v, [2.5, 97.5])) if len(v) else (np.nan, np.nan)), len(v)


def holm(pv):
    pv = np.asarray(pv, float); o = np.argsort(pv); m = len(pv); aj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * pv[i]); aj[i] = min(1.0, run)
    return aj


def fmt(v, lo, hi):
    return f"{v:.3f} ({lo:.3f}-{hi:.3f})"


def pfmt(v):
    return "≤0,001" if v <= 0.0011 else f"{v:.3f}"


def analizar(escenario, activo, Cs):
    rng = np.random.default_rng(SEMILLA)
    act = np.where(activo)[0]
    W = np.zeros((B, G))
    for b in range(B):
        W[b] = np.bincount(rng.choice(act, size=len(act)), minlength=G)
    filas, boot, punto, info = [], {}, {}, {}
    for nombre, C in Cs.items():
        for s, (_, _, et) in enumerate(ESTRATOS):
            Cn = C[s]; Cf = Cn[act].sum(0)
            m0, pres0 = metricas(Cf)
            mb, _ = metricas(np.tensordot(W, Cn, axes=(1, 0)))
            boot[(nombre, s)], punto[(nombre, s)] = mb, m0
            info[s] = (int(Cf.sum()), int((Cn[act].sum((1, 2)) > 0).sum()), int(pres0.sum()))
            fila = {"escenario": escenario, "estrato": et, "metodo": nombre,
                    "registros": info[s][0], "grupos": info[s][1], "generos": info[s][2]}
            for k in m0:
                (lo, hi), nv = ic(mb[k])
                fila[k] = round(float(m0[k]), 4); fila[k + "_ic_inf"] = round(float(lo), 4)
                fila[k + "_ic_sup"] = round(float(hi), 4)
            fila["remuestras_validas"] = nv
            filas.append(fila)
    difs = []
    for s, (_, _, et) in enumerate(ESTRATOS):
        for nombre in Cs:
            if nombre == "BLAST":
                continue
            for k in ["exactitud", "exactitud_balanceada"]:
                d = boot[(nombre, s)][k] - boot[("BLAST", s)][k]
                (lo, hi), nv = ic(d)
                fila = {"escenario": escenario, "estrato": et, "metodo": nombre, "metrica": k,
                        "dif_vs_BLAST": round(float(punto[(nombre, s)][k] - punto[("BLAST", s)][k]), 4),
                        "ic_inf": round(float(lo), 4), "ic_sup": round(float(hi), 4),
                        "p_remuestreo": np.nan, "p_holm": np.nan}
                if k == "exactitud_balanceada":
                    dv = d[~np.isnan(d)]
                    fila["p_remuestreo"] = round(min(1.0, 2 * min((dv <= 0).sum() + 1, (dv >= 0).sum() + 1) / (len(dv) + 1)), 4)
                difs.append(fila)
    res, dif = pd.DataFrame(filas), pd.DataFrame(difs)
    m = dif["metrica"] == "exactitud_balanceada"
    dif.loc[m, "p_holm"] = np.round(holm(dif.loc[m, "p_remuestreo"].values), 4)
    for s, (_, _, et) in enumerate(ESTRATOS):
        print(f"\n--- [{escenario}] identidad {et} %: {info[s][0]} registros, {info[s][1]} grupos, {info[s][2]} géneros ---")
        print(f"{'método':14s} {'exactitud (IC)':24s} {'exact. balanceada (IC)':26s} {'dif. exact. (IC)':26s} {'dif. exact. balanceada (IC)':28s} p / p Holm")
        for nombre in Cs:
            r = res[(res.estrato == et) & (res.metodo == nombre)].iloc[0]
            linea = (f"{nombre:14s} {fmt(r.exactitud, r.exactitud_ic_inf, r.exactitud_ic_sup):24s} "
                     f"{fmt(r.exactitud_balanceada, r.exactitud_balanceada_ic_inf, r.exactitud_balanceada_ic_sup):26s} ")
            if nombre != "BLAST":
                q = dif[(dif.estrato == et) & (dif.metodo == nombre) & (dif.metrica == "exactitud")].iloc[0]
                z = dif[(dif.estrato == et) & (dif.metodo == nombre) & (dif.metrica == "exactitud_balanceada")].iloc[0]
                linea += (f"{fmt(q.dif_vs_BLAST, q.ic_inf, q.ic_sup):26s} {fmt(z.dif_vs_BLAST, z.ic_inf, z.ic_sup):28s} "
                          f"{pfmt(z.p_remuestreo)} / {pfmt(z.p_holm)}")
            print(linea)
    return res, dif


todas = {n: matrices(r) for n, r in RUTAS.items()}
res, dif = [], []
for esc, activo in [("completo", np.ones(G, bool)), ("sin_G00001", np.array([g != "G00001" for g in grupos]))]:
    a, b = analizar(esc, activo, todas); res.append(a); dif.append(b)
pd.concat(res).to_csv("resultados_objetivo4/estratos_identidad.csv", index=False)
pd.concat(dif).to_csv("resultados_objetivo4/estratos_identidad_diferencias.csv", index=False)

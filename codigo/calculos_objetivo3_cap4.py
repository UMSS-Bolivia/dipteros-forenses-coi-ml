"""Cifras del apartado 4.3 (Objetivo Específico 3) a partir de las predicciones.

Entradas : resultados_objetivo3/pred_<modelo>.csv y pred_<modelo>_rejilla1.csv
           (record_id, pliegue, genero_real, genero_predicho)
           resultados_objetivo3/metricas_genero_<modelo>.csv   (solo para verificar)
Salidas  : resultados_objetivo3/cap4_metricas_globales.csv
           resultados_objetivo3/cap4_metricas_por_genero.csv   (formato largo)
           resultados_objetivo3/cap4_metricas_por_pliegue.csv
           resultados_objetivo3/cap4_recall_genero_pliegue.csv
           resultados_objetivo3/cap4_confusiones_principales.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
                             precision_recall_fscore_support)

warnings.filterwarnings("ignore")
R = Path(sys.argv[1] if len(sys.argv) > 1 else ".") / "resultados_objetivo3"
MODELOS = ["rf_k3", "rf_k4", "svm_k3", "svm_k4", "svm_nt50m", "svm_dnabert2"]
pd.set_option("display.width", 250, "display.max_columns", 30)


def leer(m, sufijo=""):
    return pd.read_csv(R / f"pred_{m}{sufijo}.csv")


def globales(p):
    y, h = p["genero_real"], p["genero_predicho"]
    etq = sorted(set(y) | set(h))
    return (accuracy_score(y, h), balanced_accuracy_score(y, h),
            f1_score(y, h, labels=etq, average="macro", zero_division=0))


glob, largo, pliegue, rec_gp, conf = [], [], [], [], []
for m in MODELOS:
    p = leer(m)
    a, b, f = globales(p)
    a1, b1, f1r = globales(leer(m, "_rejilla1"))
    etq = sorted(p["genero_real"].unique())
    pr, rc, f1, _ = precision_recall_fscore_support(
        p["genero_real"], p["genero_predicho"], labels=etq, zero_division=0)
    n = p["genero_real"].value_counts()
    t = pd.DataFrame({"modelo": m, "genero": etq, "registros": [n[g] for g in etq],
                      "recall": rc, "precision": pr, "f1": f1})
    largo.append(t)
    csv = pd.read_csv(R / f"metricas_genero_{m}.csv").set_index("genero")
    dif = max(abs(csv.loc[etq, "recall"].values - rc.round(3)).max(),
              abs(csv.loc[etq, "f1"].values - f1.round(3)).max())
    glob.append({"modelo": m, "registros": len(p), "exactitud": a, "exactitud_balanceada": b,
                 "f1_macro": f, "f1_macro_rejilla1": f1r, "dif_f1_def_menos_rej1": f - f1r,
                 "generos_f1_ge_090": int((f1 >= 0.90).sum()),
                 "generos_recall_lt_050": int((rc < 0.50).sum()),
                 "max_dif_vs_csv_metricas_genero": round(float(dif), 4)})
    for k, q in p.groupby("pliegue"):
        y, h = q["genero_real"], q["genero_predicho"]
        pres = sorted(y.unique())
        _, rcq, _, sq = precision_recall_fscore_support(y, h, labels=pres, zero_division=0)
        pliegue.append({"modelo": m, "pliegue": k, "registros": len(q),
                        "generos_presentes": len(pres),
                        "exactitud": accuracy_score(y, h),
                        "exactitud_balanceada": balanced_accuracy_score(y, h),
                        "f1_macro_presentes": f1_score(y, h, labels=pres, average="macro", zero_division=0)})
        for g, r_, s_ in zip(pres, rcq, sq):
            rec_gp.append({"modelo": m, "pliegue": k, "genero": g, "registros": int(s_), "recall": r_})
    err = p[p["genero_real"] != p["genero_predicho"]]
    c = (err.groupby(["genero_real", "genero_predicho"]).size().sort_values(ascending=False)
         .head(10).reset_index(name="registros"))
    c.insert(0, "modelo", m)
    c["pct_de_los_errores"] = (100 * c["registros"] / len(err)).round(1)
    conf.append(c)

G = pd.DataFrame(glob).sort_values("f1_macro", ascending=False).reset_index(drop=True)
G.insert(1, "orden", G.index + 1)
L, P = pd.concat(largo), pd.DataFrame(pliegue)
RG, C = pd.DataFrame(rec_gp), pd.concat(conf)
G.to_csv(R / "cap4_metricas_globales.csv", index=False)
L.to_csv(R / "cap4_metricas_por_genero.csv", index=False)
P.to_csv(R / "cap4_metricas_por_pliegue.csv", index=False)
RG.to_csv(R / "cap4_recall_genero_pliegue.csv", index=False)
C.to_csv(R / "cap4_confusiones_principales.csv", index=False)

print("\n=== 1. Métricas globales (predicciones de los 5 pliegues reunidas) ===")
print(G.round(4).to_string(index=False))
mejor = G.loc[0, "modelo"]
print("\n=== 2. F1 por género, por modelo ===")
print(L.pivot(index="genero", columns="modelo", values="f1")[MODELOS].round(3).to_string())
print("\n=== 3. Recall por género, por modelo ===")
print(L.pivot(index="genero", columns="modelo", values="recall")[MODELOS].round(3).to_string())
print("\n=== 4. Por pliegue: exactitud, balanceada, F1 macro (géneros presentes) ===")
for col in ("exactitud", "exactitud_balanceada", "f1_macro_presentes"):
    print("\n", col)
    print(P.pivot(index="modelo", columns="pliegue", values=col).loc[MODELOS].round(3).to_string())
print("\nRegistros y géneros presentes por pliegue:")
print(P[P["modelo"] == mejor][["pliegue", "registros", "generos_presentes"]].to_string(index=False))
print(f"\n=== 5. Recall por género y pliegue, modelo con mayor F1 macro ({mejor}) ===")
print(RG[RG["modelo"] == mejor].pivot(index="genero", columns="pliegue", values="recall").round(3).to_string())
print("\n=== 6. Diez confusiones más frecuentes por modelo ===")
for m in MODELOS:
    print("\n", m)
    print(C[C["modelo"] == m].drop(columns="modelo").to_string(index=False))
print("\nArchivos guardados en", R)

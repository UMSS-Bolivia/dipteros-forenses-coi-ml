"""Verificación de las métricas del Objetivo 4 contra scikit-learn. Ejecutar desde la raíz."""
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
RUTAS = {
    "RF k=3": "resultados_objetivo3/pred_rf_k3.csv", "RF k=4": "resultados_objetivo3/pred_rf_k4.csv",
    "SVM k=3": "resultados_objetivo3/pred_svm_k3.csv", "SVM k=4": "resultados_objetivo3/pred_svm_k4.csv",
    "SVM NT50M": "resultados_objetivo3/pred_svm_nt50m.csv", "SVM DNABERT-2": "resultados_objetivo3/pred_svm_dnabert2.csv",
    "BLAST": "resultados_objetivo4/pred_blast.csv"}
c = pd.read_csv("resultados_objetivo4/comparacion_metodos.csv")
c = c[c.escenario == "completo"].set_index("metodo")
for n, r in RUTAS.items():
    x = pd.read_csv(r, usecols=["genero_real", "genero_predicho"])
    labs = sorted(x.genero_real.unique())
    sk = {"f1_macro": f1_score(x.genero_real, x.genero_predicho, labels=labs, average="macro", zero_division=0),
          "exactitud_balanceada": balanced_accuracy_score(x.genero_real, x.genero_predicho),
          "exactitud": accuracy_score(x.genero_real, x.genero_predicho)}
    d = max(abs(sk[k] - c.loc[n, k]) for k in sk)
    print(f"{n:14s} sklearn F1 {sk['f1_macro']:.4f} | bal {sk['exactitud_balanceada']:.4f} | exact {sk['exactitud']:.4f} | dif. máx. {d:.6f}", "OK" if d < 1e-4 else "REVISAR")

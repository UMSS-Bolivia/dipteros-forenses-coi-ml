"""SVM sobre embeddings de un modelo de ADN preentrenado (Objetivo 3). Ejecutar desde la raíz.

Uso: python codigo/entrenar_embeddings.py {nt50m|dnabert2}
Misma partición por grupos y misma búsqueda interna por grupos que entrenar_kmers.py; el escalado
se ajusta dentro de cada entrenamiento y el desbalance se maneja con pesos de clase.
"""
import sys, time, warnings
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

warnings.filterwarnings("ignore")
nombre = sys.argv[1]
assert nombre in ("nt50m", "dnabert2")
z = np.load(f"datos/procesados/embeddings_{nombre}.npz")
X, rid = z["X"], z["record_id"].astype(str)
p = pd.read_csv("resultados_objetivo3/particion_pliegues.csv")
assert (rid == p["record_id"].astype(str).values).all(), "orden distinto entre embeddings y partición"
y, g, pl = p["genus"].values, p["grupo"].values, p["pliegue"].values
nvar = X.shape[1]

base = make_pipeline(StandardScaler(), SVC(kernel="rbf", class_weight="balanced"))
rejilla = {"svc__C": [1, 10], "svc__gamma": [f / nvar for f in (0.1, 0.3, 1)]}

pred = np.empty(len(y), dtype=object)
filas = []
for f in range(5):
    t0 = time.time()
    tr, te = np.where(pl != f)[0], np.where(pl == f)[0]
    cv = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42).split(X[tr], y[tr], g[tr]))
    gs = GridSearchCV(base, rejilla, scoring="f1_macro", cv=cv, n_jobs=2, refit=True)
    gs.fit(X[tr], y[tr])
    pred[te] = gs.predict(X[te])
    filas.append({"pliegue": f, **gs.best_params_, "f1_macro_interno": round(gs.best_score_, 4),
                  "minutos": round((time.time() - t0) / 60, 1)})
    print(f"[svm {nombre}] pliegue {f}: {gs.best_params_} | F1 macro interno {gs.best_score_:.3f} | "
          f"{(time.time()-t0)/60:.1f} min", flush=True)

pd.DataFrame(filas).to_csv(f"resultados_objetivo3/params_svm_{nombre}.csv", index=False)
pd.DataFrame({"record_id": rid, "pliegue": pl, "genero_real": y, "genero_predicho": pred}).to_csv(
    f"resultados_objetivo3/pred_svm_{nombre}.csv", index=False)

labs = sorted(set(y))
pr, rc, f1, n = precision_recall_fscore_support(y, pred, labels=labs, zero_division=0)
tab = pd.DataFrame({"genero": labs, "registros": n, "recall": rc.round(3), "precision": pr.round(3), "f1": f1.round(3)})
tab.to_csv(f"resultados_objetivo3/metricas_genero_svm_{nombre}.csv", index=False)
print(f"\n=== svm {nombre}: predicciones de los 5 pliegues juntas ===")
print("exactitud:", round(accuracy_score(y, pred), 3), "| exactitud balanceada:", round(balanced_accuracy_score(y, pred), 3),
      "| F1 macro:", round(f1_score(y, pred, average="macro", zero_division=0), 3))
print(tab.to_string(index=False))

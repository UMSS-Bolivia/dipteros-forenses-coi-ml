"""RF o SVM sobre frecuencias de k-mers con la partición por grupos (Objetivo 3).

Uso (desde la raíz):  python codigo/entrenar_kmers.py {rf|svm} {3|4}
Para cada pliegue como prueba, los hiperparámetros se eligen con validación cruzada interna por
grupos usando SOLO el entrenamiento; el escalado (SVM) se ajusta dentro de cada ajuste.
El desbalance se maneja con pesos de clase dentro del entrenamiento (sin sobremuestreo).
"""
import sys, time, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from obj3_comun import cargar

warnings.filterwarnings("ignore")
modelo, k = sys.argv[1], int(sys.argv[2])
assert modelo in ("rf", "svm") and k in (3, 4)
X, y, g, pl, rid = cargar(k)
nvar = X.shape[1]

if modelo == "rf":
    base = RandomForestClassifier(n_estimators=300, class_weight="balanced_subsample", n_jobs=-1, random_state=42)
    rejilla = {"max_features": ["sqrt", 0.3], "min_samples_leaf": [1, 3, 10, 30]}
    n_jobs_gs = 1
else:
    base = make_pipeline(StandardScaler(), SVC(kernel="rbf", class_weight="balanced"))
    rejilla = {"svc__C": [0.1, 1, 10, 100], "svc__gamma": [f / nvar for f in (0.03, 0.1, 0.3, 1)]}
    n_jobs_gs = 3

pred = np.empty(len(y), dtype=object)
filas = []
for f in range(5):
    t0 = time.time()
    tr, te = np.where(pl != f)[0], np.where(pl == f)[0]
    cv = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42).split(X[tr], y[tr], g[tr]))
    gs = GridSearchCV(base, rejilla, scoring="f1_macro", cv=cv, n_jobs=n_jobs_gs, refit=True)
    gs.fit(X[tr], y[tr])
    pred[te] = gs.predict(X[te])
    filas.append({"pliegue": f, **gs.best_params_, "f1_macro_interno": round(gs.best_score_, 4),
                  "minutos": round((time.time() - t0) / 60, 1)})
    print(f"[{modelo} k={k}] pliegue {f}: {gs.best_params_} | F1 macro interno {gs.best_score_:.3f} | "
          f"{(time.time()-t0)/60:.1f} min", flush=True)

pd.DataFrame(filas).to_csv(f"resultados_objetivo3/params_{modelo}_k{k}.csv", index=False)
pd.DataFrame({"record_id": rid, "pliegue": pl, "genero_real": y, "genero_predicho": pred}).to_csv(
    f"resultados_objetivo3/pred_{modelo}_k{k}.csv", index=False)

labs = sorted(set(y))
p, r, f1, n = precision_recall_fscore_support(y, pred, labels=labs, zero_division=0)
tab = pd.DataFrame({"genero": labs, "registros": n, "recall": r.round(3), "precision": p.round(3), "f1": f1.round(3)})
tab.to_csv(f"resultados_objetivo3/metricas_genero_{modelo}_k{k}.csv", index=False)
print(f"\n=== {modelo} k={k}: predicciones de los 5 pliegues juntas ===")
print("exactitud:", round(accuracy_score(y, pred), 3), "| exactitud balanceada:", round(balanced_accuracy_score(y, pred), 3),
      "| F1 macro:", round(f1_score(y, pred, average="macro", zero_division=0), 3))
print(tab.to_string(index=False))

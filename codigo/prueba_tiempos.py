"""Prueba de tiempos de RF y SVM con el pliegue 0 como prueba (Objetivo 3). Ejecutar desde la raíz."""
import time, warnings
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, LinearSVC
from obj3_comun import cargar

warnings.filterwarnings("ignore")
rng = np.random.default_rng(42)

def evaluar(yte, pred):
    labs = np.unique(yte)
    return round(balanced_accuracy_score(yte, pred), 3), round(f1_score(yte, pred, labels=labs, average="macro", zero_division=0), 3)

for k in (3, 4):
    X, y, g, pl, _ = cargar(k)
    tr, te = pl != 0, pl == 0
    print(f"\n===== k = {k} | entrenamiento {tr.sum()} | prueba {te.sum()} =====")

    t0 = time.time()
    rf = RandomForestClassifier(n_estimators=200, class_weight="balanced_subsample", n_jobs=-1, random_state=42)
    rf.fit(X[tr], y[tr]); t1 = time.time()
    pred = rf.predict(X[te]); t2 = time.time()
    print(f"RF 200 árboles: ajuste {t1-t0:.1f} s, predicción {t2-t1:.1f} s | (bal. acc., F1 macro) = {evaluar(y[te], pred)}")

    if k == 4:
        t0 = time.time()
        lin = make_pipeline(StandardScaler(), LinearSVC(class_weight="balanced", max_iter=2000, random_state=42))
        lin.fit(X[tr], y[tr]); t1 = time.time()
        pred = lin.predict(X[te])
        print(f"SVM lineal (todo el entrenamiento): ajuste {t1-t0:.1f} s | (bal. acc., F1 macro) = {evaluar(y[te], pred)}")

        idx_tr, idx_te = np.where(tr)[0], np.where(te)[0]
        sub_te = rng.choice(idx_te, 3000, replace=False)
        tiempos = []
        for n in (4000, 8000, 16000):
            sub = rng.choice(idx_tr, n, replace=False)
            t0 = time.time()
            m = make_pipeline(StandardScaler(), SVC(kernel="rbf", C=1, gamma="scale", class_weight="balanced"))
            m.fit(X[sub], y[sub]); t1 = time.time()
            m.predict(X[sub_te]); t2 = time.time()
            tiempos.append((n, t1 - t0, t2 - t1))
            print(f"SVM RBF con {n} registros: ajuste {t1-t0:.1f} s, predicción de 3000: {t2-t1:.1f} s")
        (n1, a1, _), (n2, a2, _) = tiempos[-2], tiempos[-1]
        b = np.log(a2 / a1) / np.log(n2 / n1)
        est = a2 * (tr.sum() / n2) ** b
        print(f"exponente de crecimiento ≈ {b:.2f} | ajuste estimado con {tr.sum()} registros: {est/60:.0f} min "
              f"(un solo ajuste, sin buscar hiperparámetros)")

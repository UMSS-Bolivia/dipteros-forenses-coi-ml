"""Tabla del Anexo 5: las 20 comparaciones exploratorias, en los dos escenarios. Ejecutar desde la raíz.

Entrada : resultados_objetivo4/comparaciones_pareadas.csv
Salidas : resultados_objetivo4/anexo5_comparaciones_exploratorias.csv
          e impresión en formato de tabla (columnas separadas por « | ») con decimales en coma.
"""
import pandas as pd

P = pd.read_csv("resultados_objetivo4/comparaciones_pareadas.csv")
X = P[P["tipo"] != "confirmatoria"].copy()
X = X[["escenario", "A", "B", "dif_f1_macro", "ic_inf", "ic_sup", "p_remuestreo", "p_remuestreo_holm", "p_wilcoxon_holm"]]
X.to_csv("resultados_objetivo4/anexo5_comparaciones_exploratorias.csv", index=False)


def c(v, d=4):
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


for esc in ("completo", "sin_G00001"):
    q = X[X["escenario"] == esc]
    print(f"\n=== Escenario {esc} ({len(q)} comparaciones) ===")
    print("Comparación (A − B) | Diferencia | IC 95 % | p remuestreo | p Holm (remuestreo) | p Holm (Wilcoxon)")
    for r in q.itertuples():
        print(f"{r.A} − {r.B} | {c(r.dif_f1_macro)} | {c(r.ic_inf)} a {c(r.ic_sup)} | {c(r.p_remuestreo, 3)} | "
              f"{c(r.p_remuestreo_holm)} | {c(r.p_wilcoxon_holm)}")

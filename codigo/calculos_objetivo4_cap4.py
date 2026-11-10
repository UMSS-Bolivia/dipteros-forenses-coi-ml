"""Cálculos derivados para el apartado 4.4 (Objetivo Específico 4). Ejecutar desde la raíz.

Imprime cada valor que el texto de 4.4 cita y que no está tal cual en un CSV:
  1. métricas globales de BLAST recalculadas (control contra comparacion_metodos.csv);
  2. participación de G00001 y de los diez grupos con más errores en los errores de BLAST;
  3. errores fuera de G00001, por grupo;
  4. participación de cada estrato de identidad en los errores;
  5. cambio de F1 macro de cada método al excluir G00001;
  6. BLAST sin el registro GBDP0769-06.COI-5P: métricas globales, cambios de predicción y géneros afectados.
No modifica ningún resultado; solo imprime.
"""
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_recall_fscore_support

REG = "GBDP0769-06.COI-5P"
G1 = "G00001"
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)


def coma(x, d=4):
    return f"{x:.{d}f}".replace(".", ",")


def metricas(df):
    etiquetas = sorted(df["genero_real"].unique())
    y, p = df["genero_real"], df["genero_predicho"]
    return (accuracy_score(y, p), balanced_accuracy_score(y, p),
            f1_score(y, p, labels=etiquetas, average="macro", zero_division=0))


part = pd.read_csv("resultados_objetivo3/particion_pliegues.csv", dtype={"record_id": str})[["record_id", "grupo"]]
b = pd.read_csv("resultados_objetivo4/pred_blast.csv", dtype={"record_id": str}).merge(part, on="record_id")
s = pd.read_csv("resultados_objetivo4/pred_blast_sin_GBDP0769.csv", dtype={"record_id": str}).merge(part, on="record_id")
for d in (b, s):
    d["error"] = d["genero_real"] != d["genero_predicho"]
    d["estrato"] = pd.cut(d["pident_mejor"], [0, 90, 95, 98, 99, 101], right=False,
                          labels=["<90", "90-95", "95-98", "98-99", ">=99"])
C = pd.read_csv("resultados_objetivo4/comparacion_metodos.csv")

print("=== 1. Métricas globales de BLAST recalculadas (accuracy, exactitud balanceada, F1 macro) ===")
for nombre, d in (("BLAST completo", b), ("BLAST sin G00001", b[b["grupo"] != G1]),
                  ("BLAST sin GBDP0769 completo", s), ("BLAST sin GBDP0769 y sin G00001", s[s["grupo"] != G1])):
    a, ba, f = metricas(d)
    print(f"{nombre:34s} n={len(d):6d} errores={int(d['error'].sum()):5d} acc={coma(a)} bal={coma(ba)} F1={coma(f)}")
print("Control contra comparacion_metodos.csv (BLAST):")
print(C[C["metodo"] == "BLAST"].to_string(index=False))

print("\n=== 2. Participación de G00001 y de los diez grupos con más errores ===")
e = b[b["error"]]
tot = len(e)
por_grupo = e.groupby("grupo").size().sort_values(ascending=False)
tam = b.groupby("grupo").size()
n_g1, tam_g1 = int(por_grupo.get(G1, 0)), int(tam[G1])
print(f"errores totales: {tot} | de G00001: {n_g1} ({coma(100 * n_g1 / tot, 1)} %) | registros de G00001: {tam_g1} "
      f"| error dentro de G00001: {coma(100 * n_g1 / tam_g1, 1)} %")
top10 = por_grupo.head(10)
print(f"suma de los diez grupos con más errores: {int(top10.sum())} ({coma(100 * top10.sum() / tot, 1)} % de los errores)")
fuera = tot - n_g1
print(f"errores fuera de G00001: {fuera} ({coma(100 * fuera / tot, 1)} %) en {b[b['grupo'] != G1]['grupo'].nunique()} grupos")
print(f"registros fuera de G00001: {len(b) - tam_g1} | tasa de error fuera de G00001: {coma(100 * fuera / (len(b) - tam_g1), 2)} %")
print(f"grupos con al menos un error: {por_grupo.size} de {tam.size}")

print("\n=== 3. Los diez grupos con más errores: tamaño del grupo y fracción de sus registros mal asignados ===")
t3 = pd.DataFrame({"errores": top10, "registros_grupo": tam.loc[top10.index]})
t3["pct_del_grupo"] = (100 * t3["errores"] / t3["registros_grupo"]).round(1)
t3["pct_de_los_errores"] = (100 * t3["errores"] / tot).round(1)
t3["genero_real"] = [b[b["grupo"] == g]["genero_real"].mode()[0] for g in t3.index]
t3["genero_predicho"] = [e[e["grupo"] == g]["genero_predicho"].mode()[0] for g in t3.index]
print(t3.to_string())

print("\n=== 4. Estratos de identidad: participación en los errores ===")
t4 = b.groupby("estrato", observed=True).agg(registros=("error", "size"), errores=("error", "sum"))
t4["pct_error"] = (100 * t4["errores"] / t4["registros"]).round(2)
t4["pct_de_todos_los_errores"] = (100 * t4["errores"] / tot).round(1)
t4["errores_G00001"] = b[b["grupo"] == G1].groupby("estrato", observed=True)["error"].sum()
t4["errores_G00001"] = t4["errores_G00001"].fillna(0).astype(int)
t4["errores_sin_G00001"] = t4["errores"] - t4["errores_G00001"]
t4["registros_sin_G00001"] = b[b["grupo"] != G1].groupby("estrato", observed=True).size()
t4["pct_error_sin_G00001"] = (100 * t4["errores_sin_G00001"] / t4["registros_sin_G00001"]).round(2)
print(t4.to_string())

print("\n=== 5. Cambio de F1 macro al excluir G00001 (comparacion_metodos.csv) ===")
w = C.pivot(index="metodo", columns="escenario", values="f1_macro")
w["cambio"] = w["sin_G00001"] - w["completo"]
print(w.round(4).to_string())
mod = w.drop(index="BLAST")
print(f"modelos: cambio mínimo {coma(mod['cambio'].min())} | máximo {coma(mod['cambio'].max())}")
print(f"BLAST: {coma(w.loc['BLAST', 'completo'])} -> {coma(w.loc['BLAST', 'sin_G00001'])} (cambio {coma(w.loc['BLAST', 'cambio'])})")

print(f"\n=== 6. BLAST sin el registro {REG} ===")
m = b[["record_id", "genero_real", "genero_predicho", "grupo", "error"]].merge(
    s[["record_id", "genero_predicho", "error"]], on="record_id", suffixes=("", "_sin"))
cam = m[m["genero_predicho"] != m["genero_predicho_sin"]]
print(f"errores: {int(m['error'].sum())} -> {int(m['error_sin'].sum())} | predicciones que cambian: {len(cam)} "
      f"| de ellas en G00001: {int((cam['grupo'] == G1).sum())} | fuera de G00001: {int((cam['grupo'] != G1).sum())}")
print("Errores que desaparecen:", int((m["error"] & ~m["error_sin"]).sum()),
      "| errores que aparecen:", int((~m["error"] & m["error_sin"]).sum()))
print("Cambios por par (predicho antes -> después):")
print(cam.groupby(["genero_predicho", "genero_predicho_sin"]).size().sort_values(ascending=False).head(5).to_string())
print("\nPrecisión, exhaustividad y F1 por género (con GBDP | sin GBDP), géneros con diferencia:")
gen = sorted(b["genero_real"].unique())
pa = precision_recall_fscore_support(b["genero_real"], b["genero_predicho"], labels=gen, zero_division=0)
ps = precision_recall_fscore_support(s["genero_real"], s["genero_predicho"], labels=gen, zero_division=0)
t6 = pd.DataFrame({"prec_con": pa[0], "prec_sin": ps[0], "rec_con": pa[1], "rec_sin": ps[1],
                   "f1_con": pa[2], "f1_sin": ps[2], "registros": pa[3]}, index=gen)
t6["dif_f1"] = t6["f1_sin"] - t6["f1_con"]
print(t6[t6["dif_f1"].abs() > 1e-9].round(4).to_string())
print("\nGéneros sin cambio:", ", ".join(t6.index[t6["dif_f1"].abs() <= 1e-9]))

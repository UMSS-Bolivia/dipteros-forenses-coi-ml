"""Tablas 5-2 y 5-3 del Anexo 5 (estratos de identidad). Ejecutar desde la raíz.

Entradas : resultados_objetivo4/estratos_identidad.csv, estratos_identidad_diferencias.csv
Salidas  : resultados_objetivo4/anexo5_tabla_5-2.csv, anexo5_tabla_5-3.csv e impresión con decimales en coma.
"""
import pandas as pd

EST = ["<90", "90-95", "95-98", "98-99", ">=99"]
ORD = ["BLAST", "SVM DNABERT-2", "SVM k=4", "SVM NT50M", "RF k=4", "SVM k=3", "RF k=3"]
c = lambda v, d=4: f"{v:.{d}f}".replace(".", ",").replace("-", "−")
E = pd.read_csv("resultados_objetivo4/estratos_identidad.csv")
D = pd.read_csv("resultados_objetivo4/estratos_identidad_diferencias.csv")
D = D[D["metrica"] == "exactitud_balanceada"]

T2 = E.pivot(index=["escenario", "metodo"], columns="estrato", values="exactitud_balanceada")[EST]
T2.to_csv("resultados_objetivo4/anexo5_tabla_5-2.csv")
D.to_csv("resultados_objetivo4/anexo5_tabla_5-3.csv", index=False)

print("=== Tabla 5-2 ===")
for esc in ("completo", "sin_G00001"):
    n = E[(E["escenario"] == esc) & (E["metodo"] == "BLAST")].set_index("estrato").loc[EST, "registros"]
    print(f"\nEscenario {esc}")
    print("Método | " + " | ".join(f"{e.replace('>=', '≥')} % (n = {int(n[e]):,})".replace(",", " ") for e in EST))
    for m in ORD:
        print(m + " | " + " | ".join(c(T2.loc[(esc, m), e]) for e in EST))

print("\n=== Tabla 5-3 ===")
for esc in ("completo", "sin_G00001"):
    print(f"\nEscenario {esc}")
    print("Estrato | Modelo | Diferencia con BLAST | IC 95 % | p remuestreo | p Holm")
    for e in EST:
        for m in ORD[1:]:
            r = D[(D["escenario"] == esc) & (D["estrato"] == e) & (D["metodo"] == m)].iloc[0]
            print(f"{e.replace('>=', '≥')} | {m} | {c(r.dif_vs_BLAST)} | {c(r.ic_inf)} a {c(r.ic_sup)} | {c(r.p_remuestreo, 3)} | {c(r.p_holm, 3)}")

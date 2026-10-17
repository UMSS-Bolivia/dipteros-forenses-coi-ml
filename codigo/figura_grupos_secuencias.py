"""Figura 3-5 6: distribución del tamaño de los grupos de secuencias idénticas.
Ejecutar desde la raíz del repositorio."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz",
                low_memory=False, usecols=["secuencia"])
t = d["secuencia"].str.upper().value_counts()
cortes = [0, 1, 2, 5, 10, 50, 100, t.max()]
et = ["1", "2", "3-5", "6-10", "11-50", "51-100", ">100"]
g = pd.cut(t, cortes, labels=et)
sec = g.value_counts().reindex(et)
reg = t.groupby(g, observed=False).sum().reindex(et)
print(pd.DataFrame({"secuencias": sec, "registros": reg}))

fig, ax = plt.subplots(1, 2, figsize=(9, 3.5))
ax[0].bar(et, sec.values, color="#4a6fa5")
ax[0].set_title("Secuencias")
ax[1].bar(et, reg.values, color="#a56a4a")
ax[1].set_title("Registros")
for a in ax:
    a.set_xlabel("Tamaño del grupo (registros por secuencia)")
    a.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.savefig("resultados_objetivo2/figura_grupos_secuencias.png", dpi=200)

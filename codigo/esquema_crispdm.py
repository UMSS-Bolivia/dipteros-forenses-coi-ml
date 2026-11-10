"""Figura 2-3 2: fases de CRISP-DM y su adaptacion en este trabajo.
Uso: python esquema_crispdm.py [carpeta_de_salida]
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

salida = Path(sys.argv[1] if len(sys.argv) > 1 else "figuras_marco_teorico")
salida.mkdir(parents=True, exist_ok=True)

ARRIBA = ["Comprensión\ndel negocio", "Comprensión\nde los datos",
          "Preparación\nde los datos", "Modelado", "Evaluación"]
ABAJO = ["1. Comprensión del\nproblema y de los datos\n(Objetivo 1)",
         "2. Preparación de\nlos datos: pipeline ETL\n(Objetivo 2)",
         "3. Modelado a nivel\nde género\n(Objetivo 3)",
         "4. Evaluación y presentación\nde resultados\n(Objetivo 4)"]
# fase de abajo -> fases de CRISP-DM de arriba (indices)
VINCULOS = {0: [0, 1], 1: [2], 2: [3], 3: [4]}

fig, ax = plt.subplots(figsize=(11, 5))
ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")

ancho_a, alto = 2.0, 1.1
xs_a = [0.2 + i * 2.35 for i in range(5)]
y_a, y_b = 4.3, 0.6
centros_a = []
for i, (x, t) in enumerate(zip(xs_a, ARRIBA)):
    ax.add_patch(FancyBboxPatch((x, y_a), ancho_a, alto, boxstyle="round,pad=0.03",
                 fc="#dbe7f3", ec="#1f4e79", lw=1.5))
    ax.text(x + ancho_a / 2, y_a + alto / 2, t, ha="center", va="center", fontsize=9)
    centros_a.append(x + ancho_a / 2)

ancho_b = 2.6
xs_b = [0.4 + i * 2.95 for i in range(4)]
centros_b = []
for x, t in zip(xs_b, ABAJO):
    ax.add_patch(FancyBboxPatch((x, y_b), ancho_b, 1.4, boxstyle="round,pad=0.03",
                 fc="#e2efda", ec="#375623", lw=1.5))
    ax.text(x + ancho_b / 2, y_b + 0.7, t, ha="center", va="center", fontsize=9)
    centros_b.append(x + ancho_b / 2)

for j, destinos in VINCULOS.items():
    for i in destinos:
        ax.plot([centros_b[j], centros_a[i]], [y_b + 1.43, y_a - 0.03],
                color="#555555", lw=1.2)

ax.text(6, 5.85, "Fases del modelo CRISP-DM utilizadas", ha="center", fontsize=11, weight="bold")
ax.text(6, 0.15, "Fases adaptadas en este trabajo", ha="center", fontsize=11, weight="bold")

fig.savefig(salida / "Figura_2-3_2_crispdm.png", dpi=200, bbox_inches="tight")
print("Guardada:", salida / "Figura_2-3_2_crispdm.png")

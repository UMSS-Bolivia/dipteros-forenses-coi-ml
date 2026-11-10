"""Figura 4-2 1 del apartado 4.2.1 (Objetivo Específico 2).

Entradas : resultados_objetivo2/tabla_depuracion_por_genero.csv
           pentaho/salida/bold_coi_limpio.csv.gz  (columna "largo")
Salidas  : figuras/figura_4-2_1.png (300 dpi)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

RUTA_TABLA = Path(sys.argv[1] if len(sys.argv) > 1
                  else "resultados_objetivo2/tabla_depuracion_por_genero.csv")
RUTA_LIMPIO = Path(sys.argv[2] if len(sys.argv) > 2
                   else "pentaho/salida/bold_coi_limpio.csv.gz")
SALIDA = Path(sys.argv[3] if len(sys.argv) > 3 else "figuras")
SALIDA.mkdir(parents=True, exist_ok=True)

AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#8a8982"
TINTA, TINTA_2, REJILLA = "#0b0b0b", "#52514e", "#dcdbd6"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": TINTA_2, "axes.labelcolor": TINTA,
    "xtick.color": TINTA_2, "ytick.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False,
})


def coma(x, dec=1):
    """Número con coma decimal."""
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def estilo_eje(ax, eje):
    ax.set_axisbelow(True)
    ax.grid(axis=eje, color=REJILLA, linewidth=0.6)
    ax.tick_params(length=0)


# --- datos ------------------------------------------------------------------
largos = pd.read_csv(RUTA_LIMPIO, usecols=["largo"])["largo"]
t = pd.read_csv(RUTA_TABLA)
t = t[t["genus"] != "TOTAL"].copy()
t["pct_largo"] = 100 * t["largo<500"] / t["evaluados"]
t["pct_acgt"] = 100 * t["no_ACGT>1%"] / t["evaluados"]
t["pct_desc"] = t["pct_largo"] + t["pct_acgt"]
t = t.sort_values("pct_desc", ascending=False).reset_index(drop=True)

# --- figura -------------------------------------------------------------------
fig, (a, b) = plt.subplots(
    2, 1, figsize=(8.0, 8.4), gridspec_kw={"height_ratios": [1, 2.3], "hspace": 0.38})

# (a) histograma de los largos retenidos, eje vertical logarítmico
bordes = np.arange(500, 1550, 10)
a.hist(largos, bins=bordes, color=GRIS, edgecolor="white", linewidth=0.3)
a.set_yscale("log")
a.set_xlim(490, 1560)
lim = a.get_ylim()
marcas = [v for v in (1, 10, 100, 1000, 10000, 100000) if lim[0] <= v <= lim[1]]
a.set_yticks(marcas)
a.set_yticklabels([coma(v, 0) for v in marcas])
a.axvline(500, color=TINTA, linestyle="--", linewidth=1)
a.axvline(largos.median(), color=NARANJA, linestyle="--", linewidth=1)
rotulo = a.get_xaxis_transform()
a.text(500, 1.03, "500 pb", transform=rotulo, fontsize=8, color=TINTA,
       ha="left", va="bottom")
a.text(largos.median() + 8, 1.03, f"Mediana: {coma(largos.median(), 0)} pb",
       transform=rotulo, fontsize=8, color=TINTA, ha="left", va="bottom")
a.set_xlabel("Largo de la secuencia retenida (pb)")
a.set_ylabel("Registros (escala logarítmica)")
a.text(-0.09, 1.12, "a", transform=a.transAxes, fontsize=11, fontweight="bold")
estilo_eje(a, "y")

# (b) porcentaje descartado por género, separado por causa
y = np.arange(len(t))
b.barh(y, t["pct_largo"], color=AZUL, height=0.66)
b.barh(y, t["pct_acgt"], left=t["pct_largo"], color=NARANJA, height=0.66)
for i, v in enumerate(t["pct_desc"]):
    b.text(v + 0.15, i, coma(v), va="center", color=TINTA, fontsize=8)
b.set_yticks(y)
b.set_yticklabels(t["genus"], style="italic")
b.invert_yaxis()
b.set_xlim(0, t["pct_desc"].max() * 1.12)
b.set_xlabel("Registros descartados (% de los evaluados de cada género)")
b.text(-0.09, 1.02, "b", transform=b.transAxes, fontsize=11, fontweight="bold")
b.legend(handles=[Patch(color=AZUL, label="Largo menor de 500 pb"),
                  Patch(color=NARANJA, label="Más de 1 % de bases no ACGT")],
         loc="lower right", frameon=False)
estilo_eje(b, "x")

fig.savefig(SALIDA / "figura_4-2_1.png", dpi=300, bbox_inches="tight",
            facecolor="white")
plt.close(fig)
print("Figura guardada en", (SALIDA / "figura_4-2_1.png").resolve())
print("Largos retenidos: n =", len(largos), "| mínimo", largos.min(),
      "| mediana", largos.median(), "| máximo", largos.max())
print(t[["genus", "evaluados", "pct_largo", "pct_acgt", "pct_desc"]]
      .round(2).to_string(index=False))

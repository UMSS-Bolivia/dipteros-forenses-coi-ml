"""Figuras 4-1 1 y 4-1 2 del apartado 4.1 (Objetivo Específico 1).

Entradas : datos/fuente/estructurado/tabla_brecha_v2.csv y las métricas de la
           Tabla 3-11 (valores incluidos abajo, tomados de metricas_ensamblajes.py).
Salidas  : figuras/figura_4-1_1.png y figuras/figura_4-1_2.png (300 dpi).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

RUTA_TABLA = Path(sys.argv[1] if len(sys.argv) > 1
                  else "datos/fuente/estructurado/tabla_brecha_v2.csv")
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "figuras")
SALIDA.mkdir(parents=True, exist_ok=True)

AZUL, NARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA_2, REJILLA = "#0b0b0b", "#52514e", "#dcdbd6"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": TINTA_2, "axes.labelcolor": TINTA,
    "xtick.color": TINTA_2, "ytick.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False,
})


def coma(x, dec=2):
    """Número con coma decimal."""
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",") if dec else \
        f"{x:,.0f}".replace(",", " ")


def estilo_eje(ax, eje="x"):
    ax.set_axisbelow(True)
    ax.grid(axis=eje, color=REJILLA, linewidth=0.6)
    ax.tick_params(length=0)


# ---------------------------------------------------------------- Figura 4-1 1
genomas = pd.DataFrame({
    "especie": ["Calliphora vomitoria", "Sarcophaga peregrina", "Lucilia cuprina",
                "Musca domestica", "Aldrichina grahami"],
    "n50_mb": [130.62, 105.45, 71.02, 12.46, 1.93],
    "huecos_pct": [0.0046, 0.0820, 0.4852, 12.1300, 0.0000],
})
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.4), sharey=True,
                             gridspec_kw={"wspace": 0.08})
y = range(len(genomas))
a1.barh(y, genomas.n50_mb, color=AZUL, height=0.6)
a2.barh(y, genomas.huecos_pct, color=AZUL, height=0.6)
for i, (n, h) in enumerate(zip(genomas.n50_mb, genomas.huecos_pct)):
    a1.text(n + 2, i, coma(n), va="center", color=TINTA, fontsize=8.5)
    a2.text(h + 0.25, i, coma(h, 4) if h < 1 else coma(h), va="center",
            color=TINTA, fontsize=8.5)
a1.set_yticks(list(y))
a1.set_yticklabels(genomas.especie, style="italic")
a1.invert_yaxis()
a1.set_xlim(0, 160)
a2.set_xlim(0, 15.5)
a1.set_xlabel("N50 (Mb)")
a2.set_xlabel("Huecos (bases N, % del genoma)")
estilo_eje(a1); estilo_eje(a2)
a2.spines["left"].set_visible(False)
fig.savefig(SALIDA / "figura_4-1_1.png", dpi=300, bbox_inches="tight",
            facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- Figura 4-1 2
d = pd.read_csv(RUTA_TABLA)
d["genero"] = d["nombre_ncbi"].str.split().str[0]
d["prioridad"] = (d["rango"] != "genero").astype(int)      # filas de género primero
g = (d.sort_values("prioridad").drop_duplicates("genero")
       [["genero", "genbank_coi_genero", "bold_coi5p_genero", "situacion_genomica"]]
       .copy())
g["sin_genoma"] = g["situacion_genomica"].str.startswith("sin genoma")
g = g.sort_values("bold_coi5p_genero", ascending=False).reset_index(drop=True)

fig, (b1, b2) = plt.subplots(1, 2, figsize=(8.0, 6.6), sharey=True,
                             gridspec_kw={"wspace": 0.08})
for ax, col, titulo in ((b1, "genbank_coi_genero", "COI en GenBank"),
                        (b2, "bold_coi5p_genero", "COI-5P en BOLD")):
    for i, fila in g.iterrows():
        color = NARANJA if fila.sin_genoma else AZUL
        ax.barh(i, max(fila[col] - 1, 0.0), left=1, color="white" if fila.sin_genoma else color,
                edgecolor=color, linewidth=1.0, height=0.68,
                hatch="////" if fila.sin_genoma else None)
        ax.text(fila[col] * 1.12, i, coma(fila[col], 0), va="center",
                color=TINTA, fontsize=7.5)
    ax.set_xscale("log")
    ax.set_xlim(1, 90000)
    ax.set_xticks([1, 10, 100, 1000, 10000])
    ax.set_xticklabels(["1", "10", "100", "1 000", "10 000"])
    ax.set_xlabel("Número de registros (escala logarítmica)")
    ax.set_title(titulo, loc="left", fontsize=9.5, color=TINTA)
    estilo_eje(ax)
b1.set_yticks(range(len(g)))
b1.set_yticklabels(g.genero, style="italic")
b1.invert_yaxis()
b2.spines["left"].set_visible(False)
fig.legend(handles=[
    Patch(facecolor="white", edgecolor=NARANJA, hatch="////",
          label="Sin genoma en el género"),
    Patch(facecolor=AZUL, edgecolor=AZUL,
          label="Genoma de otra especie del género")],
    loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.savefig(SALIDA / "figura_4-1_2.png", dpi=300, bbox_inches="tight",
            facecolor="white")
plt.close(fig)
print("Figuras guardadas en", SALIDA.resolve())
print(g.to_string(index=False))

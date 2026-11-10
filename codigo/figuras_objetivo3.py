"""Figuras 4-3 1 a 4-3 4 del Capítulo 4 (Objetivo Específico 3).

Entradas : resultados_objetivo3/cap4_metricas_globales.csv
           resultados_objetivo3/cap4_metricas_por_genero.csv
           resultados_objetivo3/cap4_metricas_por_pliegue.csv
           resultados_objetivo3/cap4_recall_genero_pliegue.csv
           (los genera codigo/calculos_objetivo3_cap4.py)
Salidas  : figuras/figura_4-3_1.png  métricas globales de los seis modelos
           figuras/figura_4-3_2.png  F1 por género y modelo (mapa de calor)
           figuras/figura_4-3_3.png  desempeño por pliegue
           figuras/figura_4-3_4.png  recall por género y pliegue del mejor modelo
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

R = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
D = R / "resultados_objetivo3"
SALIDA = R / "figuras"
SALIDA.mkdir(parents=True, exist_ok=True)
AZUL, NARANJA, AZUL_CL, AZUL_OSC = "#2a78d6", "#eb6834", "#a9c6ec", "#0d3b73"
TINTA, TINTA_2, REJILLA = "#0b0b0b", "#52514e", "#dcdbd6"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": TINTA_2, "axes.labelcolor": TINTA,
    "xtick.color": TINTA_2, "ytick.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False,
})
NOMBRES = {"svm_dnabert2": "SVM · DNABERT-2", "svm_k4": "SVM · k = 4", "svm_nt50m": "SVM · NT50M",
           "rf_k4": "RF · k = 4", "svm_k3": "SVM · k = 3", "rf_k3": "RF · k = 3"}


COMA = FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ","))


def num(x, dec=3):
    return f"{x:.{dec}f}".replace(".", ",")


G = pd.read_csv(D / "cap4_metricas_globales.csv").sort_values("f1_macro", ascending=False)
orden = list(G["modelo"])

# ------------------------------------------------------------ Figura 4-3 1
fig, ax = plt.subplots(figsize=(8.0, 4.2))
series = [("exactitud", "Exactitud", AZUL_CL), ("exactitud_balanceada", "Exactitud balanceada", AZUL),
          ("f1_macro", "F1 macro", AZUL_OSC)]
alto = 0.25
for j, (col, nom, color) in enumerate(series):
    for i, (_, f) in enumerate(G.iterrows()):
        yy = i + (j - 1) * alto
        ax.barh(yy, f[col], height=alto * 0.92, color=color)
        extra = max(f[col], f["f1_macro_rejilla1"]) if col == "f1_macro" else f[col]
        ax.text(extra + 0.014, yy, num(f[col], 4), va="center", fontsize=7.3, color=TINTA)
for i, (_, f) in enumerate(G.iterrows()):
    ax.plot(f["f1_macro_rejilla1"], i + alto, marker="D", color=NARANJA, markersize=4.5, zorder=3)
ax.set_yticks(range(len(G)))
ax.set_yticklabels([NOMBRES[m] for m in G["modelo"]])
ax.invert_yaxis()
ax.set_xlim(0, 1.12)
ax.xaxis.set_major_formatter(COMA)
ax.set_xlabel("Valor de la métrica")
ax.set_axisbelow(True)
ax.grid(axis="x", color=REJILLA, linewidth=0.6)
ax.tick_params(length=0)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in series] +
          [Line2D([], [], marker="D", color=NARANJA, linestyle="", markersize=5)],
          labels=[n for _, n, _ in series] + ["F1 macro con la rejilla exploratoria"],
          loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.45, -0.28), fontsize=8)
fig.savefig(SALIDA / "figura_4-3_1.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-3 2
L = pd.read_csv(D / "cap4_metricas_por_genero.csv")
reg = L[L["modelo"] == orden[0]].set_index("genero")["registros"].sort_values(ascending=False)
M = L.pivot(index="genero", columns="modelo", values="f1").loc[reg.index, orden]
cmap = LinearSegmentedColormap.from_list("az", ["#f3f7fc", AZUL_CL, AZUL, AZUL_OSC])
fig, ax = plt.subplots(figsize=(7.6, 6.0))
im = ax.imshow(M.values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M.values[i, j]
        ax.text(j, i, num(v), ha="center", va="center", fontsize=8,
                color="white" if v > 0.55 else TINTA)
ax.set_xticks(range(len(orden)))
ax.set_xticklabels([NOMBRES[m] for m in orden], rotation=25, ha="right")
ax.set_yticks(range(len(M)))
ax.set_yticklabels([f"{g}  ({reg[g]:,})".replace(",", " ") for g in M.index])
for t in ax.get_yticklabels():
    t.set_style("italic")
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
cb.set_label("F1 por género")
cb.outline.set_visible(False)
ax.set_title("Géneros ordenados por número de registros (entre paréntesis)", loc="left", fontsize=8.5, color=TINTA_2)
fig.savefig(SALIDA / "figura_4-3_2.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-3 3
P = pd.read_csv(D / "cap4_metricas_por_pliegue.csv")
colores = {"svm_dnabert2": AZUL_OSC, "svm_k4": NARANJA, "svm_nt50m": "#2f9e6f",
           "rf_k4": "#7a5bc7", "svm_k3": "#8a8a85", "rf_k3": "#c9a227"}
fig, (a, b) = plt.subplots(1, 2, figsize=(9.2, 3.8), gridspec_kw={"wspace": 0.28})
for ax, col, titulo in ((a, "f1_macro_presentes", "a) F1 macro (géneros presentes en el pliegue)"),
                        (b, "exactitud", "b) Exactitud")):
    for m in orden:
        q = P[P["modelo"] == m].sort_values("pliegue")
        ax.plot(q["pliegue"], q[col], marker="o", markersize=4, linewidth=2.2 if m == orden[0] else 1.4,
                color=colores[m], label=NOMBRES[m])
    ax.set_xticks(range(5))
    ax.set_xticklabels([f"{k}" for k in range(5)])
    ax.set_xlabel("Pliegue")
    ax.set_title(titulo, loc="left", fontsize=9, color=TINTA)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=REJILLA, linewidth=0.6)
    ax.tick_params(length=0)
a.set_ylim(0.4, 0.9)
b.set_ylim(0.75, 1.0)
a.set_ylabel("F1 macro")
b.set_ylabel("Exactitud")
a.annotate("Pliegue 0: 13 géneros (sin Cochliomyia)", xy=(-0.15, 0.885), fontsize=7.5, color=TINTA_2, va="top")
a.yaxis.set_major_formatter(COMA)
b.yaxis.set_major_formatter(COMA)
fig.legend(*a.get_legend_handles_labels(), loc="lower center", ncol=6, frameon=False,
           bbox_to_anchor=(0.5, -0.08), fontsize=8)
fig.savefig(SALIDA / "figura_4-3_3.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-3 4
RG = pd.read_csv(D / "cap4_recall_genero_pliegue.csv")
mejor = orden[0]
H = RG[RG["modelo"] == mejor].pivot(index="genero", columns="pliegue", values="recall").reindex(reg.index)
fig, ax = plt.subplots(figsize=(6.4, 5.6))
masc = np.ma.masked_invalid(H.values)
cm = cmap.copy()
cm.set_bad("#e8e7e2")
im = ax.imshow(masc, cmap=cm, vmin=0, vmax=1, aspect="auto")
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        v = H.values[i, j]
        if np.isnan(v):
            ax.text(j, i, "sin registros", ha="center", va="center", fontsize=7, color=TINTA_2)
        else:
            ax.text(j, i, num(v), ha="center", va="center", fontsize=8, color="white" if v > 0.55 else TINTA)
ax.set_xticks(range(H.shape[1]))
ax.set_xticklabels([f"Pliegue {c}" for c in H.columns])
ax.set_yticks(range(len(H)))
ax.set_yticklabels(H.index)
for t in ax.get_yticklabels():
    t.set_style("italic")
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
cb.set_label("Recall")
cb.outline.set_visible(False)
ax.set_title(f"Modelo: {NOMBRES[mejor]}", loc="left", fontsize=8.5, color=TINTA_2)
fig.savefig(SALIDA / "figura_4-3_4.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Figuras guardadas en", SALIDA.resolve())

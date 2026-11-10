"""Figuras 4-4 1 a 4-4 5 del Capítulo 4 (Objetivo Específico 4).

Entradas : resultados_objetivo4/comparacion_metodos.csv
           resultados_objetivo4/comparaciones_pareadas.csv
           resultados_objetivo4/estratos_identidad.csv
           resultados_objetivo4/log_diagnostico_errores_blast.txt
           resultados_objetivo4/metricas_genero_blast.csv
           resultados_objetivo4/metricas_genero_blast_sin_GBDP0769.csv
           resultados_objetivo3/cap4_metricas_por_genero.csv
Salidas  : figuras/figura_4-4_1.png  F1 macro con IC 95 %, dos escenarios
           figuras/figura_4-4_2.png  diferencia de F1 macro de cada modelo con BLAST
           figuras/figura_4-4_3.png  exactitud balanceada por estrato de identidad
           figuras/figura_4-4_4.png  errores de BLAST por grupo y por estrato
           figuras/figura_4-4_5.png  F1 por género: BLAST y los seis modelos
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

R = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
D4, D3 = R / "resultados_objetivo4", R / "resultados_objetivo3"
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
NOM = {"BLAST": "BLAST", "SVM DNABERT-2": "SVM · DNABERT-2", "SVM k=4": "SVM · k = 4",
       "SVM NT50M": "SVM · NT50M", "RF k=4": "RF · k = 4", "SVM k=3": "SVM · k = 3",
       "RF k=3": "RF · k = 3"}
ORDEN = list(NOM)
ESC = {"completo": "Completo", "sin_G00001": "Sin el grupo G00001"}
COL = {"BLAST": NARANJA, "SVM DNABERT-2": AZUL_OSC, "SVM k=4": "#2a78d6", "SVM NT50M": "#2f9e6f",
       "RF k=4": "#7a5bc7", "SVM k=3": "#8a8a85", "RF k=3": "#c9a227"}
COMA2 = FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ","))


def num(x, dec=3):
    return f"{x:.{dec}f}".replace(".", ",")


def estilo(ax, eje="x"):
    ax.set_axisbelow(True)
    ax.grid(axis=eje, color=REJILLA, linewidth=0.6)
    ax.tick_params(length=0)


# ------------------------------------------------------------ Figura 4-4 1
C = pd.read_csv(D4 / "comparacion_metodos.csv")
fig, ax = plt.subplots(figsize=(8.4, 4.2))
for j, (esc, color, dy) in enumerate((("completo", AZUL_OSC, -0.16), ("sin_G00001", NARANJA, 0.16))):
    for i, m in enumerate(ORDEN):
        f = C[(C["escenario"] == esc) & (C["metodo"] == m)].iloc[0]
        ax.errorbar(f["f1_macro"], i + dy, xerr=[[f["f1_macro"] - f["f1_macro_ic_inf"]],
                    [f["f1_macro_ic_sup"] - f["f1_macro"]]], fmt="o", color=color, markersize=5,
                    capsize=3, linewidth=1.4)
        ax.text(1.03 + 0.085 * j, i + dy, num(f["f1_macro"], 4), va="center", fontsize=7.6,
                color=color, ha="left")
ax.text(1.03, -0.85, "Completo", fontsize=7.8, color=AZUL_OSC, fontweight="bold", va="center")
ax.text(1.115, -0.85, "Sin G00001", fontsize=7.8, color=NARANJA, fontweight="bold", va="center")
ax.set_yticks(range(len(ORDEN)))
ax.set_yticklabels([NOM[m] for m in ORDEN])
ax.invert_yaxis()
ax.set_ylim(len(ORDEN) - 0.5, -1.15)
ax.set_xlim(0.40, 1.0)
ax.xaxis.set_major_formatter(COMA2)
ax.set_xlabel("F1 macro (punto) e intervalo de confianza de 95 %")
estilo(ax)
ax.legend(handles=[Line2D([], [], marker="o", color=AZUL_OSC, linestyle="-"),
                   Line2D([], [], marker="o", color=NARANJA, linestyle="-")],
          labels=["Escenario completo", "Sin el grupo G00001"], loc="lower center",
          ncol=2, frameon=False, bbox_to_anchor=(0.4, -0.27))
fig.savefig(SALIDA / "figura_4-4_1.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-4 2
Pp = pd.read_csv(D4 / "comparaciones_pareadas.csv")
modelos = [m for m in ORDEN if m != "BLAST"]
fig, ejes = plt.subplots(1, 2, figsize=(9.2, 3.9), sharey=True, gridspec_kw={"wspace": 0.08})
for ax, esc in zip(ejes, ESC):
    q = Pp[(Pp["escenario"] == esc) & (Pp["B"] == "BLAST")].set_index("A")
    for i, m in enumerate(modelos):
        f = q.loc[m]
        conf = f["tipo"] == "confirmatoria"
        p = f["p_remuestreo"] if conf else f["p_remuestreo_holm"]
        sig = p < 0.05
        ax.plot([f["ic_inf"], f["ic_sup"]], [i, i], color=NARANJA if conf else TINTA_2, linewidth=1.6)
        ax.plot(f["dif_f1_macro"], i, marker="D" if conf else "o", markersize=7,
                color=NARANJA if conf else AZUL_OSC, markerfacecolor=(NARANJA if conf else AZUL_OSC) if sig else "white",
                markeredgewidth=1.6, zorder=3)
        ax.text(0.27, i, num(f["dif_f1_macro"], 4).replace("-", "−"), va="center", ha="right", fontsize=7.8, color=TINTA)
    ax.axvline(0, color=TINTA, linewidth=1)
    ax.set_xlim(-0.55, 0.28)
    ax.set_xticks([-0.5, -0.4, -0.3, -0.2, -0.1, 0.0])
    ax.spines["bottom"].set_bounds(-0.55, 0.05)
    ax.set_title(ESC[esc], loc="left", fontsize=9.5, color=TINTA)
    ax.set_xlabel("Diferencia de F1 macro (modelo − BLAST)")
    ax.xaxis.set_major_formatter(COMA2)
    estilo(ax)
ejes[0].set_yticks(range(len(modelos)))
ejes[0].set_yticklabels([NOM[m] for m in modelos])
ejes[0].invert_yaxis()
ejes[1].spines["left"].set_visible(False)
fig.legend(handles=[Line2D([], [], marker="o", color=AZUL_OSC, linestyle="", markersize=7),
                    Line2D([], [], marker="o", color=AZUL_OSC, markerfacecolor="white", linestyle="", markersize=7),
                    Line2D([], [], marker="D", color=NARANJA, linestyle="", markersize=7)],
           labels=["Exploratoria, significativa (p de Holm < 0,05)", "Exploratoria, no significativa",
                   "Confirmatoria (SVM NT50M), p < 0,05 sin ajuste"],
           loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.1), fontsize=8)
fig.savefig(SALIDA / "figura_4-4_2.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-4 3
E = pd.read_csv(D4 / "estratos_identidad.csv")
estratos = ["<90", "90-95", "95-98", "98-99", ">=99"]
fig, ejes = plt.subplots(1, 2, figsize=(9.4, 4.0), sharey=True, gridspec_kw={"wspace": 0.08})
for ax, esc in zip(ejes, ESC):
    q = E[E["escenario"] == esc]
    for m in ORDEN:
        s = q[q["metodo"] == m].set_index("estrato").loc[estratos]
        ax.plot(range(5), s["exactitud_balanceada"], marker="o", markersize=4,
                linewidth=2.6 if m == "BLAST" else 1.3, color=COL[m], label=NOM[m],
                zorder=3 if m == "BLAST" else 2)
    n = q[q["metodo"] == "BLAST"].set_index("estrato").loc[estratos, "registros"]
    ax.set_xticks(range(5))
    ax.set_xticklabels([f"{e.replace('>=', '≥')} %\n{f'{int(v):,}'.replace(',', ' ')}" for e, v in zip(estratos, n)], fontsize=8)
    ax.set_title(ESC[esc], loc="left", fontsize=9.5, color=TINTA)
    ax.set_xlabel("Identidad del mejor alineamiento (debajo, registros)")
    ax.set_ylim(0.15, 1.02)
    ax.yaxis.set_major_formatter(COMA2)
    estilo(ax, "y")
ejes[0].set_ylabel("Exactitud balanceada")
ejes[1].spines["left"].set_visible(False)
fig.legend(*ejes[0].get_legend_handles_labels(), loc="lower center", ncol=7, frameon=False,
           bbox_to_anchor=(0.5, -0.1), fontsize=8)
fig.savefig(SALIDA / "figura_4-4_3.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-4 4
log = (D4 / "log_diagnostico_errores_blast.txt").read_text(encoding="utf-8")
grupos = [m.groups() for m in re.finditer(
    r"^(G\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s*$", log, flags=re.M)]
G = pd.DataFrame(grupos, columns=["grupo", "errores", "real", "predicho", "pliegue", "registros", "pct"])
G[["errores", "pliegue", "registros"]] = G[["errores", "pliegue", "registros"]].astype(int)
est = [m.groups() for m in re.finditer(
    r"^(<90|90-95|95-98|98-99|>=99)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+(\d+)\s*$", log, flags=re.M)]
S = pd.DataFrame(est, columns=["estrato", "registros", "errores", "pct_error", "err_g1"])
S[["registros", "errores", "err_g1"]] = S[["registros", "errores", "err_g1"]].astype(int)
S["pct_error"] = S["pct_error"].astype(float)
fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 4.1), gridspec_kw={"wspace": 0.55, "width_ratios": [1.15, 1]})
y = range(len(G))
a.barh(list(y), G["errores"], color=[NARANJA if g == "G00001" else AZUL for g in G["grupo"]], height=0.64)
for i, f in G.iterrows():
    a.text(f["errores"] * 1.12, i, f"{f['errores']:,}".replace(",", " "),
           va="center", fontsize=7.6, color=TINTA)
a.set_xscale("log")
a.set_xlim(10, 40000)
a.set_xticks([10, 100, 1000, 10000])
a.set_xticklabels(["10", "100", "1 000", "10 000"])
a.set_yticks(list(y))
a.set_yticklabels([f"{r.grupo} · {r.real} / {r.predicho}" for r in G.itertuples()], fontsize=8)
a.invert_yaxis()
a.set_xlabel("Errores de BLAST (escala logarítmica)")
a.set_title("a) Diez grupos con más errores\n(grupo · género real / predicho)", loc="left", fontsize=9.5, color=TINTA)
estilo(a)
x = range(len(S))
b.bar(x, S["err_g1"], color=NARANJA, width=0.62, label="Grupo G00001")
b.bar(x, S["errores"] - S["err_g1"], bottom=S["err_g1"], color=AZUL, width=0.62, label="Otros grupos")
for i, f in S.iterrows():
    b.text(i, f["errores"] + 60, f"{str(f['pct_error']).replace('.', ',')} %", ha="center", fontsize=7.8, color=TINTA)
b.set_xticks(list(x))
b.set_xticklabels([e.replace(">=", "≥") for e in S["estrato"]], fontsize=8)
b.set_xlabel("Identidad del mejor alineamiento (%)")
b.set_ylabel("Errores de BLAST")
b.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", " ")))
b.set_title("b) Errores por estrato (sobre cada barra, % de error)", loc="left", fontsize=9.5, color=TINTA)
b.legend(frameon=False, fontsize=8, loc="upper right")
b.set_ylim(0, S["errores"].max() * 1.25)
estilo(b, "y")
fig.savefig(SALIDA / "figura_4-4_4.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-4 5
mg = pd.read_csv(D3 / "cap4_metricas_por_genero.csv")
reg = mg[mg["modelo"] == "svm_dnabert2"].set_index("genero")["registros"].sort_values(ascending=False)
b1 = pd.read_csv(D4 / "metricas_genero_blast.csv").set_index("genero")["f1"]
b2 = pd.read_csv(D4 / "metricas_genero_blast_sin_GBDP0769.csv").set_index("genero")["f1"]
cols = {"BLAST": b1, "BLAST sin\nGBDP": b2}
for k, nombre in (("svm_dnabert2", "SVM · DNABERT-2"), ("svm_k4", "SVM · k = 4"), ("svm_nt50m", "SVM · NT50M"),
                  ("rf_k4", "RF · k = 4"), ("svm_k3", "SVM · k = 3"), ("rf_k3", "RF · k = 3")):
    cols[nombre] = mg[mg["modelo"] == k].set_index("genero")["f1"]
M = pd.DataFrame(cols).loc[reg.index]
cmap = LinearSegmentedColormap.from_list("az", ["#f3f7fc", AZUL_CL, AZUL, AZUL_OSC])
fig, ax = plt.subplots(figsize=(8.4, 6.0))
im = ax.imshow(M.values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M.values[i, j]
        ax.text(j, i, num(v), ha="center", va="center", fontsize=7.8, color="white" if v > 0.55 else TINTA)
ax.axvline(1.5, color="white", linewidth=3)
ax.set_xticks(range(M.shape[1]))
ax.set_xticklabels(M.columns, rotation=25, ha="right")
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
fig.savefig(SALIDA / "figura_4-4_5.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Figuras guardadas en", SALIDA.resolve())

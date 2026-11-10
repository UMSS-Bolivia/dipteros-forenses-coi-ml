"""Figuras 4-2 2, 4-2 3 y 4-2 4 del Capítulo 4 (Objetivo Específico 2).

Entradas : resultados_objetivo2/control_por_genero.csv
           resultados_objetivo2/criterio_inclusion_python.csv
           resultados_objetivo2/embudo_registros.csv
           datos/procesados/bold_coi_modelado_final.csv.gz  (columna country/ocean)
Salidas  : figuras/figura_4-2_2.png  control de duplicados y etiquetado por género
           figuras/figura_4-2_3.png  criterio de inclusión de los 24 géneros
           figuras/figura_4-2_4.png  embudo de registros y países de origen
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

R = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SALIDA = R / "figuras"
SALIDA.mkdir(parents=True, exist_ok=True)
AZUL, NARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA_2, REJILLA = "#0b0b0b", "#52514e", "#dcdbd6"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": TINTA_2, "axes.labelcolor": TINTA,
    "xtick.color": TINTA_2, "ytick.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False,
})


def num(x, dec=0):
    """Número con coma decimal y espacio de miles."""
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def estilo(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=REJILLA, linewidth=0.6)
    ax.tick_params(length=0)


# ------------------------------------------------------------ Figura 4-2 2
c = pd.read_csv(R / "resultados_objetivo2/control_por_genero.csv", index_col=0)
c = c.drop("TOTAL").sort_values("registros", ascending=False)
c["sin_bin_pct"] = 100 * c["sin_bin"] / c["registros"]
paneles = [("copias_pct", "a) Copias exactas (% de los registros)", 1),
           ("reg_en_sec_compartidas", "b) Registros en secuencias compartidas\nentre especies (n)", 0),
           ("sin_bin_pct", "c) Registros sin BIN (% del género)", 1)]
fig, ejes = plt.subplots(1, 3, figsize=(9.2, 4.6), sharey=True, gridspec_kw={"wspace": 0.12})
y = range(len(c))
for ax, (col, titulo, dec) in zip(ejes, paneles):
    ax.barh(list(y), c[col], color=AZUL, height=0.66)
    tope = c[col].max()
    for i, v in enumerate(c[col]):
        ax.text(v + tope * 0.015, i, num(v, dec), va="center", fontsize=7.5, color=TINTA)
    ax.set_xlim(0, tope * 1.2)
    ax.set_title(titulo, loc="left", fontsize=9, color=TINTA)
    estilo(ax)
ejes[0].set_yticks(list(y))
ejes[0].set_yticklabels(c.index, style="italic")
ejes[0].invert_yaxis()
for ax in ejes[1:]:
    ax.spines["left"].set_visible(False)
fig.savefig(SALIDA / "figura_4-2_2.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-2 3
k = pd.read_csv(R / "resultados_objetivo2/criterio_inclusion_python.csv")
k = k.sort_values(["cumple", "registros"], ascending=[False, False]).reset_index(drop=True)
fig, (a, b) = plt.subplots(1, 2, figsize=(8.6, 6.4), sharey=True, gridspec_kw={"wspace": 0.1})
for ax, col, titulo, umbral, txt in (
        (a, "con_especie", "a) Registros con especie formal", 100, "mínimo 100"),
        (b, "especies", "b) Especies formales", 3, "mínimo 3")):
    for i, f in k.iterrows():
        ok = f["cumple"]
        ax.barh(i, f[col], color=AZUL if ok else "white", edgecolor=AZUL if ok else NARANJA,
                hatch=None if ok else "////", linewidth=1.0, height=0.68)
        ax.text(55000 if col == "con_especie" else 3600, i, num(f[col]),
                va="center", ha="right", fontsize=7.5, color=TINTA)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(0, 60000 if col == "con_especie" else 4000)
    ax.set_xticks([0, 1, 10, 100, 1000] + ([10000] if col == "con_especie" else []))
    ax.set_xticklabels(["0", "1", "10", "100", "1 000"] + (["10 000"] if col == "con_especie" else []))
    ax.spines["bottom"].set_bounds(0, 55000 if col == "con_especie" else 3600)
    ax.axvline(umbral, color=TINTA, linestyle="--", linewidth=1)
    ax.text(umbral * 1.1, -0.9, txt, fontsize=7.5, color=TINTA, va="bottom")
    ax.set_title(titulo, loc="left", fontsize=9.5, color=TINTA, pad=14)
    ax.set_xlabel("Escala logarítmica (con 0)")
    estilo(ax)
a.set_yticks(range(len(k)))
a.set_yticklabels(k["genus"], style="italic")
a.invert_yaxis()
b.spines["left"].set_visible(False)
fig.legend(handles=[Patch(facecolor=AZUL, edgecolor=AZUL, label="Cumple el criterio"),
                    Patch(facecolor="white", edgecolor=NARANJA, hatch="////", label="No cumple")],
           loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.savefig(SALIDA / "figura_4-2_3.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------ Figura 4-2 4
e = pd.read_csv(R / "resultados_objetivo2/embudo_registros.csv")
e = e[~e["etapa"].str.startswith("Fuera de alcance")].reset_index(drop=True)
etiquetas = ["Registros descargados\n(todos los marcadores)", "Registros con COI-5P",
             "COI-5P con secuencia", "Tras el control de calidad", "Géneros incluidos",
             "Tras excluir conflictos\nde género"]
m = pd.read_csv(R / "datos/procesados/bold_coi_modelado_final.csv.gz",
                usecols=["country/ocean"], low_memory=False)["country/ocean"]
ES = {"Canada": "Canadá", "United Kingdom": "Reino Unido", "Pakistan": "Pakistán",
      "United States": "Estados Unidos", "Bangladesh": "Bangladés", "South Africa": "Sudáfrica",
      "Germany": "Alemania", "Australia": "Australia", "Brazil": "Brasil", "Guinea": "Guinea"}
pais = m.value_counts().head(10)
n = len(m)
fig, (a, b) = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw={"wspace": 0.75, "width_ratios": [1.1, 1]})
for i, f in e.iterrows():
    a.barh(i, f["registros"], color=AZUL, height=0.62)
    perd = f"  (−{num(f['perdidos'])})" if f["perdidos"] > 0 else ""
    a.text(f["registros"] + 800, i, num(f["registros"]) + perd, va="center", fontsize=8, color=TINTA)
a.set_yticks(range(len(e)))
a.set_yticklabels(etiquetas[:len(e)])
a.invert_yaxis()
a.set_xlim(0, 100000)
a.set_xticks([0, 25000, 50000, 75000])
a.set_xticklabels(["0", "25 000", "50 000", "75 000"])
a.set_title("a) Registros por etapa (entre paréntesis, los perdidos)", loc="left", fontsize=9, color=TINTA)
a.set_xlabel("Registros")
estilo(a)
b.barh(range(len(pais)), 100 * pais.values / n, color=AZUL, height=0.62)
for i, v in enumerate(pais.values):
    b.text(100 * v / n + 0.4, i, f"{num(v)} ({num(100 * v / n, 1)} %)", va="center", fontsize=7.5, color=TINTA)
b.set_yticks(range(len(pais)))
b.set_yticklabels([ES.get(p, p) for p in pais.index])
b.invert_yaxis()
b.set_xlim(0, 45)
b.set_xlabel("% de los registros de la matriz final")
b.set_title("b) Diez países con más registros", loc="left", fontsize=9, color=TINTA)
estilo(b)
bol = int((m == "Bolivia").sum())
b.text(44.5, len(pais) - 0.2, f"Bolivia: {bol} registros", ha="right", va="bottom",
       fontsize=8, color=NARANJA, fontweight="bold")
fig.savefig(SALIDA / "figura_4-2_4.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Figuras guardadas en", SALIDA.resolve())

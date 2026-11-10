"""
ejemplo_kmeros.py
Ejemplo didáctico de la Figura 2-3 1: conteo y frecuencia de k-meros
en una secuencia corta inventada (no corresponde a ningún espécimen).

Uso:
    python codigo/ejemplo_kmeros.py [CARPETA_SALIDA]
Imprime la tabla de conteos y frecuencias, y guarda la figura en PNG.
"""
import sys
from collections import Counter
from pathlib import Path
from itertools import product

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SECUENCIA = "ATGCGATGCA"   # secuencia inventada, solo para ilustrar
K = 3
SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
SALIDA.mkdir(parents=True, exist_ok=True)

n = len(SECUENCIA)
ventanas = n - K + 1
palabras = [SECUENCIA[i:i + K] for i in range(ventanas)]
conteos = Counter(palabras)
todas = ["".join(p) for p in product("ACGT", repeat=K)]

print(f"Secuencia: {SECUENCIA}  (n = {n}, k = {K})")
print(f"Ventanas = n - k + 1 = {ventanas}")
print(f"Palabras posibles r^k = {len(todas)}")
print(f"{'k-mero':<8}{'conteo':>8}{'frecuencia':>12}")
for p in sorted(conteos):
    print(f"{p:<8}{conteos[p]:>8}{conteos[p] / ventanas:>12.4f}")
print(f"Suma de frecuencias = {sum(conteos[p] / ventanas for p in conteos):.4f}")
print(f"k-meros posibles con conteo cero: {len(todas) - len(conteos)}")

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [1.1, 1]})

# a) ventana deslizante
a1.set_xlim(-0.5, n + 3.5)
a1.set_ylim(-0.5, ventanas + 1.2)
a1.axis("off")
a1.set_title("a) Ventana deslizante de k = %d" % K, fontsize=11)
for i, b in enumerate(SECUENCIA):
    a1.text(i + 0.5, ventanas + 0.4, b, ha="center", va="center", fontsize=12, family="monospace")
for v in range(ventanas):
    y = ventanas - 1 - v
    a1.add_patch(plt.Rectangle((v, y + 0.15), K, 0.7, fill=False, lw=1.4, ec="#1f4e79"))
    a1.text(v + K / 2, y + 0.5, palabras[v], ha="center", va="center", fontsize=11, family="monospace", color="#1f4e79")
    a1.text(n + 0.4, y + 0.5, f"ventana {v + 1}", ha="left", va="center", fontsize=9, color="#555555")

# b) frecuencias
orden = sorted(conteos)
a2.bar(orden, [conteos[p] / ventanas for p in orden], color="#1f4e79")
a2.set_title("b) Frecuencia relativa de cada k-mero observado", fontsize=11)
a2.set_ylabel("Frecuencia relativa")
a2.set_xlabel("k-mero")
a2.tick_params(axis="x", rotation=45)
for lab in a2.get_xticklabels():
    lab.set_family("monospace")
a2.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
destino = SALIDA / "Figura_2-3_1_kmeros.png"
fig.savefig(destino, dpi=200)
print(f"Figura guardada en: {destino}")

"""Valores derivados del apartado 4.2.3 (géneros incluidos y matriz final).

Entradas : resultados_objetivo2/criterio_inclusion_python.csv
           datos/procesados/bold_coi_modelado_final.csv.gz
Salida   : resultados_objetivo2/calculos_derivados_423.csv
"""
import sys
from pathlib import Path
import pandas as pd

R = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
c = pd.read_csv(R / "resultados_objetivo2/criterio_inclusion_python.csv")
m = pd.read_csv(R / "datos/procesados/bold_coi_modelado_final.csv.gz",
                usecols=["genus", "country/ocean"], low_memory=False)
f = []


def reg(desc, valor, formula):
    f.append({"descripcion": desc, "valor": valor, "formula": formula})


tot = int(c["registros"].sum())
si, no = c[c["cumple"]], c[~c["cumple"]]
reg("Registros evaluados por el criterio (24 géneros)", tot, "suma de registros")
reg("Géneros que cumplen", len(si), "cumple = True")
reg("Géneros que no cumplen", len(no), "cumple = False")
reg("Registros de los géneros que cumplen", int(si["registros"].sum()), "suma")
reg("% de los registros evaluados en géneros que cumplen",
    round(100 * si["registros"].sum() / tot, 1), "suma cumplen / total * 100")
reg("Registros de los géneros que no cumplen", int(no["registros"].sum()), "suma")
reg("% de los registros evaluados en géneros que no cumplen",
    round(100 * no["registros"].sum() / tot, 1), "suma no cumplen / total * 100")
a = no[no["especies"] < 3]
b = no[(no["especies"] >= 3) & (no["con_especie"] < 100)]
reg("No cumplen por tener menos de 3 especies formales: " + ", ".join(a["genus"]), len(a), "especies < 3")
reg("No cumplen por tener <100 registros con especie (con >=3 especies): " + ", ".join(b["genus"]),
    len(b), "especies >= 3 y con_especie < 100")
reg("Géneros incluidos con menos registros con especie: " + ", ".join(
    f"{g} ({n})" for g, n in zip(*[si.sort_values("con_especie").head(3)[k] for k in ("genus", "con_especie")])),
    "", "3 menores con_especie entre los que cumplen")
fin = m["genus"].value_counts()
reg("Registros finales (matriz)", int(fin.sum()), "filas del conjunto modelado")
d = si.set_index("genus")["registros"].sub(fin, fill_value=0)
d = d[d != 0].astype(int)
reg("Géneros con diferencia entre criterio y matriz final: " + ", ".join(f"{g} ({v})" for g, v in d.items()),
    int(d.sum()), "registros(criterio) - registros(final) por género")
reg("Género mayor / menor en la matriz final", f"{fin.idxmax()} {fin.max()} / {fin.idxmin()} {fin.min()}",
    "max y min de registros por género")
reg("% de la matriz en los tres géneros mayores (" + ", ".join(fin.head(3).index) + ")",
    round(100 * fin.head(3).sum() / fin.sum(), 1), "suma 3 mayores / total * 100")
reg("Razón entre el género mayor y el menor", round(fin.max() / fin.min(), 1), "max / min")
p = m["country/ocean"].fillna("sin dato").value_counts()
n = len(m)
reg("Países distintos (sin contar 'sin dato')", int((p.index != "sin dato").sum()), "valores distintos")
reg("Registros sin país", int(p.get("sin dato", 0)), "country/ocean vacío")
pc = p.drop("sin dato", errors="ignore")
for k, v in pc.head(5).items():
    reg(f"Registros de {k}", int(v), "conteo")
    reg(f"% de la matriz en {k}", round(100 * v / n, 1), "conteo / total * 100")
reg("% de la matriz en los cinco primeros", round(100 * pc.head(5).sum() / n, 1), "suma 5 países mayores / total * 100")
reg("Registros de Bolivia", int(p.get("Bolivia", 0)), "country/ocean = Bolivia")
for gen, v in m[m["country/ocean"] == "Bolivia"]["genus"].value_counts().items():
    reg(f"Bolivia: registros de {gen}", int(v), "conteo")
out = pd.DataFrame(f)
out.to_csv(R / "resultados_objetivo2/calculos_derivados_423.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 120)
print(out.to_string(index=False))

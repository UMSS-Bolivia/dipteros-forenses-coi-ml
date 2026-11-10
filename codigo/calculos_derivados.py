"""Valores derivados que se citan en los apartados 4.1 y 4.2 (Capítulo 4).

Cada valor se calcula aquí a partir de los archivos de resultados, con su
fórmula, para que ninguna cifra del texto dependa de un cálculo manual.

Entradas : datos/fuente/estructurado/tabla_brecha_v2.csv
           datos/**/bolivia_*.tsv
           resultados_objetivo2/tabla_depuracion_por_genero.csv
           resultados_objetivo2/control_por_genero.csv
           pentaho/salida/bold_coi_limpio.csv.gz
           datos/procesados/bold_coi_modelado_final.csv.gz
Salidas  : resultados_objetivo2/calculos_derivados_capitulo4.csv
           resultados_objetivo2/control_por_genero_derivados.csv
"""
import glob
import os
import sys
import traceback
from pathlib import Path

import pandas as pd

R = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
filas = []


def reg(apartado, descripcion, valor, formula):
    filas.append({"apartado": apartado, "descripcion": descripcion,
                  "valor": valor, "formula": formula})


def pct(a, b, dec=1):
    return round(100 * a / b, dec)


def bloque(nombre, funcion):
    try:
        funcion()
    except Exception as e:                       # un bloque que falla no detiene los demás
        print(f"[{nombre}] NO SE CALCULÓ: {type(e).__name__}: {e}")
        traceback.print_exc(limit=1)


# ------------------------------------------------------------------ 4.1.2 y 4.1.3
def brecha():
    d = pd.read_csv(R / "datos/fuente/estructurado/tabla_brecha_v2.csv")
    d["genero"] = d["nombre_ncbi"].str.split().str[0]
    d["prio"] = (d["rango"] != "genero").astype(int)
    g = d.sort_values("prio").drop_duplicates("genero").copy()
    n = len(g)
    reg("4.1.2", "Géneros distintos", n, "géneros únicos de nombre_ncbi")
    tot = int(g["bold_coi5p_genero"].sum())
    reg("4.1.2", "Registros COI-5P de BOLD en los géneros", tot, "suma de bold_coi5p_genero")
    top = g.sort_values("bold_coi5p_genero", ascending=False).head(4)
    reg("4.1.2", "Cuatro géneros con más COI-5P: " + ", ".join(top["genero"]),
        int(top["bold_coi5p_genero"].sum()), "suma de los 4 mayores")
    reg("4.1.2", "% de los COI-5P en esos cuatro géneros",
        pct(top["bold_coi5p_genero"].sum(), tot), "suma 4 mayores / total * 100")
    men = g[g["bold_coi5p_genero"] < 100].sort_values("bold_coi5p_genero")
    reg("4.1.2", "Géneros con menos de 100 COI-5P: " + ", ".join(
        f"{a} ({b})" for a, b in zip(men["genero"], men["bold_coi5p_genero"])),
        len(men), "conteo de bold_coi5p_genero < 100")
    reg("4.1.2", "De ellos, con genoma en NCBI",
        int((men["genomas_ncbi_genero"] > 0).sum()), "genomas_ncbi_genero > 0")
    reg("4.1.2", "Géneros con más COI-5P en BOLD que COI en GenBank",
        int((g["bold_coi5p_genero"] > g["genbank_coi_genero"]).sum()),
        "bold_coi5p_genero > genbank_coi_genero")
    reg("4.1.2", "Géneros con más COI en GenBank que COI-5P en BOLD: " + ", ".join(
        g.loc[g["genbank_coi_genero"] > g["bold_coi5p_genero"], "genero"]),
        int((g["genbank_coi_genero"] > g["bold_coi5p_genero"]).sum()),
        "genbank_coi_genero > bold_coi5p_genero")
    reg("4.1.2", "Países en BOLD: mínimo", int(g["bold_paises_genero"].min()),
        "mínimo de bold_paises_genero")
    reg("4.1.2", "Países en BOLD: máximo", int(g["bold_paises_genero"].max()),
        "máximo de bold_paises_genero")
    reg("4.1.2", "Géneros con 6 países o menos",
        int((g["bold_paises_genero"] <= 6).sum()), "bold_paises_genero <= 6")
    sin = g["situacion_genomica"].str.startswith("sin genoma")
    reg("4.1.2", "Géneros sin genoma en NCBI", int(sin.sum()), "situacion_genomica = sin genoma")
    reg("4.1.2", "Géneros con genoma de otra especie del género", int((~sin).sum()),
        "situacion_genomica distinta de sin genoma")
    con = g[~sin]
    reg("4.1.2", "Genomas NCBI por género con genoma: mínimo / máximo",
        f"{int(con['genomas_ncbi_genero'].min())} / {int(con['genomas_ncbi_genero'].max())}",
        "min y max de genomas_ncbi_genero entre géneros con genoma")
    e = d[d["rango"] == "especie"]
    reg("4.1.2", "Especies en la lista", len(e), "filas con rango = especie")
    reg("4.1.2", "Especies con 100 o más COI-5P en BOLD",
        int((e["bold_coi5p_especie"] >= 100).sum()), "bold_coi5p_especie >= 100")
    otras = e[e["bold_coi5p_especie"] < 100]["bold_coi5p_especie"]
    reg("4.1.2", "COI-5P de las demás especies: mínimo / máximo",
        f"{int(otras.min())} / {int(otras.max())}", "min y max entre las especies con < 100")
    bol = g[g["bold_bolivia_genero"] > 0]
    reg("4.1.3", "Géneros con COI boliviano en BOLD: " + ", ".join(
        f"{a} ({int(b)})" for a, b in zip(bol["genero"], bol["bold_bolivia_genero"])),
        len(bol), "bold_bolivia_genero > 0")
    reg("4.1.3", "Géneros sin COI boliviano", n - len(bol), "n géneros - géneros con COI boliviano")
    reg("4.1.3", "Especies con COI boliviano", int((e["bold_bolivia_especie"] > 0).sum()),
        "bold_bolivia_especie > 0")
    lp = d[d["departamentos"].str.contains("La Paz")]
    ch = d[d["departamentos"].str.contains("Chuquisaca")]
    reg("4.1.3", "Taxones de La Paz", len(lp), "filas con La Paz en departamentos")
    reg("4.1.3", "Taxones de Chuquisaca", len(ch), "filas con Chuquisaca en departamentos")
    reg("4.1.3", "Géneros distintos de La Paz", lp["genero"].nunique(), "géneros únicos en La Paz")
    sg = g[g["genero"].isin(lp["genero"]) & g["situacion_genomica"].str.startswith("sin genoma")]
    reg("4.1.3", "Géneros de La Paz sin genoma: " + ", ".join(sg["genero"]), len(sg),
        "géneros de La Paz con situacion_genomica = sin genoma")
    reg("4.1.3", "Rango de COI-5P de esos géneros",
        f"{int(sg['bold_coi5p_genero'].min())} a {int(sg['bold_coi5p_genero'].max())}",
        "min y max de bold_coi5p_genero")


def bolivia():
    fs = [f for f in glob.glob(str(R / "datos/**/bolivia_*.tsv"), recursive=True)
          if os.path.getsize(f) > 5]
    d = pd.concat([pd.read_csv(f, sep="\t", low_memory=False) for f in fs], ignore_index=True)
    n = len(d)
    reg("4.1.3", "Registros COI de Bolivia en BOLD (4 familias)", n, "filas de bolivia_*.tsv")
    prov = d["province/state"].fillna("sin dato").value_counts()
    for k, v in prov.items():
        reg("4.1.3", f"Provincia {k}", int(v), "conteo de province/state")
        reg("4.1.3", f"% de los registros bolivianos en {k}", pct(v, n), f"{v}/{n}*100")
    g = d["genus"]
    reg("4.1.3", "Identificados hasta género", int(g.notna().sum()), "genus no vacío")
    reg("4.1.3", "Solo hasta familia", int(g.isna().sum()), "genus vacío")
    inst = [c for c in d.columns if "institution" in c.lower()]
    if inst:
        vc = d[inst[0]].fillna("sin dato").value_counts()
        for k, v in vc.items():
            reg("4.1.3", f"Institución: {k}", int(v), f"conteo de {inst[0]}")
            reg("4.1.3", f"% en {k}", pct(v, n), f"{v}/{n}*100")


# ------------------------------------------------------------------ 4.2.1
def depuracion():
    t = pd.read_csv(R / "resultados_objetivo2/tabla_depuracion_por_genero.csv")
    tot = t[t["genus"] == "TOTAL"].iloc[0]
    g = t[t["genus"] != "TOTAL"]
    desc = int(tot["largo<500"] + tot["no_ACGT>1%"])
    reg("4.2.1", "Registros descartados", desc, "largo<500 + no_ACGT>1% del total")
    reg("4.2.1", "% de los evaluados descartado", pct(desc, tot["evaluados"]), "descartados/evaluados*100")
    reg("4.2.1", "% de los descartes debido al largo", pct(tot["largo<500"], desc),
        "largo<500 / descartados * 100")
    dos = g[g["genus"].isin(["Sarcophaga", "Calliphora"])]
    reg("4.2.1", "Descartes por largo de Sarcophaga + Calliphora", int(dos["largo<500"].sum()),
        "suma de largo<500")
    reg("4.2.1", "% de los descartes por largo que aportan esos dos géneros",
        pct(dos["largo<500"].sum(), tot["largo<500"]), "suma / largo<500 total * 100")
    resto = g[~g["genus"].isin(["Sarcophaga", "Calliphora"])]
    reg("4.2.1", "Retención mínima en los demás géneros (%)", float(resto["pct_retenido"].min()),
        "mínimo de pct_retenido sin esos dos géneros")
    con = g[g["no_ACGT>1%"] > 0]
    reg("4.2.1", "Géneros con descartes por bases no ACGT", len(con), "no_ACGT>1% > 0")
    reg("4.2.1", "Géneros sin descartes por bases no ACGT", len(g) - len(con), "no_ACGT>1% = 0")
    top4 = g.sort_values("no_ACGT>1%", ascending=False).head(4)
    reg("4.2.1", "Cuatro géneros con más descartes no ACGT: " + ", ".join(
        f"{a} ({b})" for a, b in zip(top4["genus"], top4["no_ACGT>1%"])),
        int(top4["no_ACGT>1%"].sum()), "suma de los 4 mayores")
    try:
        l = pd.read_csv(R / "pentaho/salida/bold_coi_limpio.csv.gz", usecols=["largo"])["largo"]
        for q in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99):
            reg("4.2.1", f"Largo retenido, percentil {int(q*100)}", float(l.quantile(q)),
                "cuantil de largo en bold_coi_limpio")
        reg("4.2.1", "Largo retenido: mínimo / máximo", f"{int(l.min())} / {int(l.max())}", "min y max")
        reg("4.2.1", "Registros con largo >= percentil 99", int((l >= l.quantile(.99)).sum()),
            "conteo de largo >= P99")
    except Exception as e:
        print("[4.2.1 largos] NO SE CALCULÓ:", e)


# ------------------------------------------------------------------ 4.2.2
def control():
    c = pd.read_csv(R / "resultados_objetivo2/control_por_genero.csv", index_col=0)
    tot = c.loc["TOTAL"]
    g = c.drop("TOTAL").copy()
    g["sin_bin_pct"] = (100 * g["sin_bin"] / g["registros"]).round(1)
    g["pct_de_reg_en_sec_compartidas"] = (100 * g["reg_en_sec_compartidas"] / tot["reg_en_sec_compartidas"]).round(1)
    g["pct_de_bin_varias_especies"] = (100 * g["bin_varias_especies"] / tot["bin_varias_especies"]).round(1)
    g["pct_de_especies_en_varios_bin"] = (100 * g["especies_en_varios_bin"] / tot["especies_en_varios_bin"]).round(1)
    g.to_csv(R / "resultados_objetivo2/control_por_genero_derivados.csv")
    print(g[["sin_bin", "sin_bin_pct", "pct_de_reg_en_sec_compartidas",
             "pct_de_bin_varias_especies", "pct_de_especies_en_varios_bin"]].to_string())
    reg("4.2.2", "% de registros sin BIN (total)", pct(tot["sin_bin"], tot["registros"]),
        "sin_bin / registros * 100")
    for gen in g.sort_values("sin_bin_pct", ascending=False).head(4).index:
        reg("4.2.2", f"% de registros sin BIN en {gen}", float(g.loc[gen, "sin_bin_pct"]),
            "sin_bin / registros del género * 100")
    dos = g.loc[["Calliphora", "Chrysomya"]]
    reg("4.2.2", "Registros en secuencias compartidas: Calliphora + Chrysomya",
        int(dos["reg_en_sec_compartidas"].sum()), "suma")
    reg("4.2.2", "% de los registros en secuencias compartidas que aportan esos dos géneros",
        pct(dos["reg_en_sec_compartidas"].sum(), tot["reg_en_sec_compartidas"]),
        "suma / total * 100")
    reg("4.2.2", "% de los BIN con varias especies que están en Sarcophaga",
        float(g.loc["Sarcophaga", "pct_de_bin_varias_especies"]),
        "bin_varias_especies de Sarcophaga / total * 100")
    reg("4.2.2", "% de las especies en más de un BIN que están en Sarcophaga",
        float(g.loc["Sarcophaga", "pct_de_especies_en_varios_bin"]),
        "especies_en_varios_bin de Sarcophaga / total * 100")
    reg("4.2.2", "Copias exactas: mínimo y máximo por género (%)",
        f"{g['copias_pct'].min()} ({g['copias_pct'].idxmin()}) / {g['copias_pct'].max()} ({g['copias_pct'].idxmax()})",
        "min y max de copias_pct")
    try:
        d = pd.read_csv(R / "datos/procesados/bold_coi_modelado_final.csv.gz",
                        usecols=["secuencia"], low_memory=False)
        s = d["secuencia"].str.upper().value_counts()
        n = len(d)
        reg("4.2.2", "Secuencias que aparecen una sola vez", int((s == 1).sum()), "conteo de secuencias con 1 registro")
        reg("4.2.2", "% de registros con secuencia única", pct((s == 1).sum(), n), "únicas / registros * 100")
        rep = s[s > 1]
        reg("4.2.2", "Secuencias repetidas", len(rep), "secuencias con más de 1 registro")
        reg("4.2.2", "Registros cubiertos por secuencias repetidas", int(rep.sum()), "suma de repeticiones")
        reg("4.2.2", "% de registros cubiertos por secuencias repetidas", pct(rep.sum(), n), "suma / registros * 100")
        reg("4.2.2", "Grupo idéntico mayor (registros)", int(s.max()), "máximo de repeticiones")
        reg("4.2.2", "Cinco grupos idénticos mayores (registros)", int(s.head(5).sum()), "suma de los 5 mayores")
        reg("4.2.2", "% que representan los cinco mayores", pct(s.head(5).sum(), n), "suma / registros * 100")
    except Exception as e:
        print("[4.2.2 secuencias] NO SE CALCULÓ:", e)


for nombre, fn in (("4.1 brecha", brecha), ("4.1 bolivia", bolivia),
                   ("4.2.1", depuracion), ("4.2.2", control)):
    bloque(nombre, fn)

out = pd.DataFrame(filas)
salida = R / "resultados_objetivo2/calculos_derivados_capitulo4.csv"
out.to_csv(salida, index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 110)
print("\n", out.to_string(index=False))
print("\nGuardado en", salida)

#!/usr/bin/env python3
import glob, json, os
import pandas as pd
from pandas.errors import EmptyDataError

D = "anexos/anexo1_evidencia_objetivo1"
SIN_PAIS = ["Unrecoverable", "Unspecified country"]

def leer(f):
    try:
        return pd.read_csv(f, sep="\t", low_memory=False)
    except EmptyDataError:
        return None

proc = pd.read_csv(os.path.join(D, "procedencia_genomas.csv"))
proc.columns = ["Especie", "Repositorio", "Accesión", "Ensamblaje", "Depositante", "BioProject", "Fecha", "Referencia"]

inv = pd.read_csv("resultados/inventario_archivos_originales.csv")

m = pd.read_csv(os.path.join(D, "metricas_agregado.csv"))
genes = {"Aldrichina grahami": 12823, "Calliphora vomitoria": 14665, "Lucilia cuprina": 13927, "Musca domestica": 17481}
busco = {"Aldrichina grahami": "99,2 % (1.645 de 1.658)"}
cal = pd.DataFrame({
    "Especie": m["especie"],
    "Secuencias nucleares": m["num_secuencias_nucleares"],
    "Longitud total (Mb)": (m["longitud_total_nuclear"] / 1e6).round(2),
    "N50 (Mb)": (m["n50"] / 1e6).round(2),
    "L50": m["l50"],
    "GC (%)": m["gc_pct"],
    "Bases N (%)": m["gaps_pct"].round(2),
    "Genes codificantes": m["especie"].map(genes).apply(lambda v: "sin anotación pública" if pd.isna(v) else int(v)),
    "BUSCO": m["especie"].map(busco).fillna("no disponible"),
})
contigs = pd.read_csv(os.path.join(D, "metricas_contigs.csv"))

lm = pd.read_csv("resultados/lista_maestra_taxones.csv")
lm.columns = ["Taxón en la fuente", "Rango", "Nombre en NCBI", "Familia", "Departamento", "Fuente", "Identificación"]

b = pd.read_csv(os.path.join(D, "tabla_brecha_v2.csv"))
brecha = pd.DataFrame({
    "Taxón": b["nombre_ncbi"], "Departamentos": b["departamentos"],
    "Genomas NCBI (género)": b["genomas_ncbi_genero"], "Genomas NCBI (especie)": b["genomas_ncbi_especie"],
    "COI GenBank (especie)": b["genbank_coi_especie"],
    "BOLD (género)": b["bold_total_genero"], "BOLD (especie)": b["bold_total_especie"],
    "Países BOLD (género)": b["bold_paises_genero"], "BOLD Bolivia (género)": b["bold_bolivia_genero"],
    "Situación genómica": b["situacion_genomica"], "COI boliviano": b["coi_boliviano_bold"]})

partes = []
for f in sorted(glob.glob(os.path.join(D, "bolivia_*.tsv"))):
    d = leer(f)
    if d is not None:
        d["Familia consultada"] = os.path.basename(f)[8:-4]
        partes.append(d)
bol = pd.concat(partes, ignore_index=True)
bol["Departamento"] = bol["province/state"].fillna("sin dato")
bol["Género"] = bol["genus"].fillna("sin asignar")
por_dep = bol.groupby(["Familia consultada", "Departamento"]).size().unstack(fill_value=0).reset_index()
por_gen = bol.groupby(["Familia consultada", "Género"]).size().rename("Registros").reset_index()
cols = [c for c in ["processid", "family", "genus", "species", "country/ocean", "province/state", "inst",
                    "collection_date_start", "insdc_acs", "bin_uri"] if c in bol.columns]
det = bol[cols]

j = json.load(open(os.path.join(D, "bold_resumen", "tax_genus_Fannia.json")))
fa = pd.Series(j["country/ocean"]).rename("Registros").sort_values(ascending=False).reset_index()
fa.columns = ["País", "Registros"]
fa["% del total"] = (100 * fa["Registros"] / j["counts"]["specimens"]).round(1)

filas = []
for f in sorted(glob.glob(os.path.join(D, "global_*.tsv"))):
    d = leer(f)
    if d is None:
        continue
    p = d["country/ocean"].dropna()
    p = p[~p.isin(SIN_PAIS)]
    filas.append({"Taxón": os.path.basename(f)[7:-4].replace("_", " "), "Registros": len(d),
                  "COI-5P": int((d["marker_code"] == "COI-5P").sum()), "Países (n)": p.nunique(),
                  "Países (registros)": "; ".join("%s (%d)" % (k, v) for k, v in p.value_counts().items())})
peq = pd.DataFrame(filas)

notas = pd.DataFrame({"Nota": [
    "N50 y L50 se calcularon sobre las secuencias de cada archivo (contigs o scaffolds según el ensamblaje); no equivalen al N50 de contigs que informa NCBI.",
    "Se excluyeron de las métricas nucleares los genomas mitocondriales: C. vomitoria (16.152 pb) y M. domestica (16.108 pb).",
    "Genes codificantes: genes con biotype=protein_coding en el GFF (C. vomitoria, L. cuprina y M. domestica). En A. grahami el archivo contiene solo genes codificantes (Meng et al., 2019). El total de genes, incluidos los no codificantes, es 63.932.",
    "BUSCO solo está disponible para A. grahami (Meng et al., 2019; BUSCO 3.0.1, linaje insecta_odb9); no se ejecutó para las demás especies.",
    "Los conteos de GenBank son un mínimo: el filtro por nombre del gen (COI/COX1, citocromo c oxidasa subunidad I) puede omitir registros.",
    "Consultas a GenBank y BOLD (API del portal v5) realizadas el 14/10/2026; versiones de las herramientas en LEEME.txt.",
    "Se descartó la descarga masiva en TSV de BOLD: el archivo mezcla bloques de 10.000 registros con distinto número de columnas. Los conteos usan el endpoint de resumen y descargas de un solo bloque.",
    "Lista de Chuquisaca (Machicado-Ocampo et al., 2025): verificación contra el PDF [PENDIENTE].",
    "Cochabamba (Chávez Abasto et al., 2008) y Potosí (Acho, 2014): sin lista de taxones; texto completo no accesible."]})

hojas = {"F1-1 Procedencia": proc, "F1-2 Inventario": inv, "F1-4 Calidad": cal, "F1-5 Contigs": contigs,
         "F1-6 Bolivia por depto": por_dep, "F1-6 Bolivia por genero": por_gen, "F1-6 Bolivia registros": det,
         "F1-7 Lista maestra": lm, "F1-7 Brecha": brecha, "F1-7 Brecha completa": b,
         "Fannia por pais": fa, "Taxones pequenos": peq, "Notas": notas}
salida = os.path.join(D, "Anexo1_tablas.xlsx")
with pd.ExcelWriter(salida, engine="openpyxl") as w:
    for nombre, df in hojas.items():
        df.to_excel(w, sheet_name=nombre, index=False)
        ws = w.sheets[nombre]
        for col in ws.columns:
            largo = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
            ws.column_dimensions[col[0].column_letter].width = min(largo + 2, 60)
print("Listo:", os.path.abspath(salida))

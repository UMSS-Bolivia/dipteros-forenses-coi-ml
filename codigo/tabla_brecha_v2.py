#!/usr/bin/env python3
import json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
import pandas as pd
from Bio import Entrez

Entrez.email = os.environ["NCBI_EMAIL"]
BASE = "https://portal.boldsystems.org/api"
COI = '(COI[Gene] OR COX1[Gene] OR "cytochrome c oxidase subunit I"[Title] OR "cytochrome oxidase subunit I"[Title])'
TAXID = {"Sarcophaga": "7384", "Musca": "7369"}
ALT = {"Sarconesia splendida": "Chlorobrachycoma splendida"}
SIN_PAIS = {"Unrecoverable", "Unspecified country"}
VACIO = {"total": None, "coi5p": None, "paises": None}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "monografia-dipteros/1.0"})
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code != 503 or intento == 3:
                raise
            time.sleep(20)

def bold(query):
    url = (BASE + "/summary?query=" + urllib.parse.quote(query, safe=":;/")
           + "&fields=" + urllib.parse.quote("specimens,marker_code,country/ocean", safe=","))
    try:
        d = json.loads(get(url))
    except urllib.error.HTTPError as e:
        print("AVISO: BOLD respondió", e.code, "para", query)
        return dict(VACIO)
    time.sleep(0.3)
    paises = [p for p in d.get("country/ocean", {}) if p not in SIN_PAIS]
    return {"total": d.get("counts", {}).get("specimens", 0),
            "coi5p": d.get("marker_code", {}).get("COI-5P", 0),
            "paises": len(paises)}

def genomas(nombre):
    r = subprocess.run(["datasets", "summary", "genome", "taxon", TAXID.get(nombre, nombre), "--as-json-lines"],
                       capture_output=True, text=True)
    return len([l for l in r.stdout.splitlines() if l.strip()])

def genbank(term):
    h = Entrez.esearch(db="nucleotide", term=term, retmax=0)
    n = int(Entrez.read(h)["Count"])
    h.close()
    time.sleep(0.4)
    return n

lista = pd.read_csv(sys.argv[1])
agr = lista.groupby("nombre_ncbi", sort=False).agg(
    taxon=("taxon_fuente", "first"), rango=("rango", "first"), familia=("familia", "first"),
    departamentos=("departamento", lambda s: "; ".join(sorted(set(s)))),
    fuentes=("fuente", lambda s: "; ".join(sorted(set(s))))).reset_index()

filas = []
for _, r in agr.iterrows():
    nombre, rango = r["nombre_ncbi"], r["rango"]
    genero = nombre.split()[0]
    es_esp = rango == "especie"
    bg = bold("tax:genus:%s" % genero)
    bgb = bold("tax:genus:%s;geo:country/ocean:Bolivia" % genero)
    be, beb = dict(VACIO), dict(VACIO)
    if es_esp:
        be = bold("tax:species:%s" % nombre)
        if not be["total"] and nombre in ALT:
            be = bold("tax:species:%s" % ALT[nombre])
        beb = bold("tax:species:%s;geo:country/ocean:Bolivia" % nombre)
    g_gen = genomas(genero)
    g_esp = genomas(nombre) if es_esp else None
    gb_gen = genbank('"%s"[Organism] AND %s' % (genero, COI))
    gb_esp = genbank('"%s"[Organism] AND %s' % (nombre, COI)) if es_esp else None
    if es_esp and g_esp:
        situacion = "genoma de la especie"
    elif g_gen:
        situacion = "genoma de otra especie del género"
    else:
        situacion = "sin genoma en el género"
    n_bol = beb["total"] if es_esp else bgb["total"]
    boliviano = "sin respuesta" if n_bol is None else ("sí (%d)" % n_bol if n_bol else "ninguno")
    filas.append({
        "taxon_fuente": r["taxon"], "nombre_ncbi": nombre, "rango": rango, "familia": r["familia"],
        "departamentos": r["departamentos"], "fuentes": r["fuentes"],
        "genomas_ncbi_genero": g_gen, "genomas_ncbi_especie": g_esp,
        "genbank_coi_genero": gb_gen, "genbank_coi_especie": gb_esp,
        "bold_total_genero": bg["total"], "bold_coi5p_genero": bg["coi5p"], "bold_paises_genero": bg["paises"],
        "bold_bolivia_genero": bgb["total"],
        "bold_total_especie": be["total"], "bold_coi5p_especie": be["coi5p"], "bold_bolivia_especie": beb["total"],
        "situacion_genomica": situacion, "coi_boliviano_bold": boliviano})
    print(nombre, "listo")

res = pd.DataFrame(filas)
os.makedirs("resultados", exist_ok=True)
res.to_csv("resultados/tabla_brecha_v2.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
print(res[["nombre_ncbi", "departamentos", "genomas_ncbi_genero", "genomas_ncbi_especie",
           "genbank_coi_especie", "bold_total_genero", "bold_total_especie", "bold_paises_genero",
           "bold_bolivia_genero", "situacion_genomica", "coi_boliviano_bold"]].to_string(index=False))

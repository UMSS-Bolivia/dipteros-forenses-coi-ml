#!/usr/bin/env python3
import io, json, os, sys, time, urllib.error, urllib.parse, urllib.request
import pandas as pd

BASE = "https://portal.boldsystems.org/api"
SALIDA = sys.argv[1]
os.makedirs(SALIDA, exist_ok=True)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "monografia-dipteros/1.0"})
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code != 503 or intento == 3:
                raise
            time.sleep(20)

def descargar(query):
    q = urllib.parse.quote(query, safe=":;/")
    resp = json.loads(get(BASE + "/query?query=" + q + "&extent=full"))
    qid = resp.get("query_id")
    if not qid:
        raise RuntimeError("Respuesta inesperada: " + str(resp)[:300])
    txt = get(BASE + "/documents/" + qid + "/download?format=tsv")
    if not txt.strip():
        return pd.DataFrame()
    if not txt.strip():
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(txt), sep="\t", low_memory=False)

def col(df, *cands):
    for c in cands:
        if c in df.columns:
            return c
    for c in df.columns:
        if any(k in c.lower() for k in cands):
            return c
    return None

consultas = {}
for fam in ["Calliphoridae", "Sarcophagidae", "Muscidae", "Fanniidae"]:
    consultas["bolivia_" + fam] = "tax:family:%s;geo:country/ocean:Bolivia" % fam
for tx, rango in [("Sarconesia", "genus"), ("Compsomyiops", "genus"), ("Sarconesiopsis", "genus"),
                  ("Microcerella", "genus"), ("Calliphora nigribasis", "species")]:
    consultas["global_" + tx.replace(" ", "_")] = "tax:%s:%s" % (rango, tx)

for nombre, q in consultas.items():
    try:
        df = descargar(q)
    except Exception as e:
        print(nombre, "-> ERROR:", e)
        continue
    df.to_csv(os.path.join(SALIDA, nombre + ".tsv"), sep="\t", index=False)
    print("=" * 60)
    print(nombre, "| registros:", len(df))
    if len(df) == 0:
        continue
    c_sp, c_pa, c_mk = col(df, "species"), col(df, "country/ocean", "country"), col(df, "marker_code")
    if nombre.startswith("bolivia_") and c_sp:
        print(df.groupby(c_sp, dropna=False).size().sort_values(ascending=False).head(25).to_string())
    if nombre.startswith("global_") and c_pa:
        print(df.groupby(c_pa, dropna=False).size().sort_values(ascending=False).to_string())
    if c_mk:
        print("marcadores:", df[c_mk].value_counts().head(5).to_dict())

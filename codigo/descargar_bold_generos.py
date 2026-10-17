import json, os, time, urllib.parse, urllib.request
import pandas as pd

BASE = "https://portal.boldsystems.org/api"
SAL = "datos/raw/bold_coi"
os.makedirs(SAL, exist_ok=True)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "monografia-dipteros/1.0"})
    for intento in range(6):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            print("   reintento", intento + 1, "->", e)
            if intento == 5:
                raise
            time.sleep(20)

def leer(txt):
    try:
        datos = json.loads(txt)
        return datos if isinstance(datos, list) else [datos]
    except json.JSONDecodeError:
        return [json.loads(l) for l in txt.splitlines() if l.strip()]

tabla = pd.read_csv("resultados/tabla_brecha_v2.csv")
tabla["genero"] = tabla["nombre_ncbi"].str.split().str[0]
esperado = tabla.groupby("genero")["bold_total_genero"].max()
print("Géneros a descargar:", len(esperado))

filas = []
for genero in sorted(esperado.index):
    ruta = os.path.join(SAL, genero + ".json")
    if not (os.path.exists(ruta) and os.path.getsize(ruta) > 0):
        print("Descargando", genero, "...")
        q = urllib.parse.quote("tax:genus:" + genero, safe=":;/")
        qid = json.loads(get(BASE + "/query?query=" + q + "&extent=full"))["query_id"]
        txt = get(BASE + "/documents/" + qid + "/download?format=json")
        with open(ruta, "w") as f:
            f.write(txt)
    regs = leer(open(ruta).read())
    df = pd.DataFrame(regs)
    n5 = int((df["marker_code"] == "COI-5P").sum()) if "marker_code" in df else 0
    filas.append({"genero": genero, "filas_descargadas": len(df),
                  "total_bold_esperado": int(esperado[genero]),
                  "coi5p_descargados": n5})
    print(genero, len(df), "esperado", int(esperado[genero]), "COI-5P", n5)

res = pd.DataFrame(filas)
res["coincide"] = res["filas_descargadas"] == res["total_bold_esperado"]
res.to_csv("resultados/descarga_bold_resumen.csv", index=False)
print(res.to_string(index=False))

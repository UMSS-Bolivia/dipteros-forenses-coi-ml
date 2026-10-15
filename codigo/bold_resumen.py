#!/usr/bin/env python3
import os, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://portal.boldsystems.org/api"
SALIDA = sys.argv[1]
os.makedirs(SALIDA, exist_ok=True)

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

consultas = ["tax:genus:Sarconesia", "tax:genus:Fannia", "tax:species:Musca domestica", "tax:genus:Phaonia"]
campos = "specimens,marker_code,country/ocean"
for i, q in enumerate(consultas):
    url = BASE + "/summary?query=" + urllib.parse.quote(q, safe=":;/") + "&fields=" + urllib.parse.quote(campos, safe=",")
    txt = get(url)
    nombre = q.replace(":", "_").replace(" ", "_")
    open(os.path.join(SALIDA, nombre + ".json"), "w").write(txt)
    print("=" * 60)
    print(q, "| bytes:", len(txt))
    print(txt[:1500] if i < 2 else "(guardado)")

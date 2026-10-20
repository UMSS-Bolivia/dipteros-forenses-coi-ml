"""Prepara el mapa de departamentos de Bolivia para el dashboard (Objetivo 4). Ejecutar desde la raíz.

Fuente: Natural Earth, capa ne_10m_admin_1_states_provinces (dominio público),
https://www.naturalearthdata.com/ . Se descarga una vez, se filtra Bolivia, se simplifican
los contornos (Douglas-Peucker, 0,01 grados) y se guarda un archivo pequeño en el repositorio.
"""
import json
import os
import urllib.request
import numpy as np

URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
       "ne_10m_admin_1_states_provinces.geojson")
SALIDA = "datos/fuente/mapa/bolivia_departamentos.geojson"
TOL = 0.01


def simplificar(pts, tol):
    n = len(pts)
    keep = np.zeros(n, bool); keep[0] = keep[-1] = True
    pila = [(0, n - 1)]
    while pila:
        i, j = pila.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        seg = b - a; L = float(np.hypot(*seg)); v = pts[i + 1:j] - a
        d = np.abs(seg[0] * v[:, 1] - seg[1] * v[:, 0]) / L if L > 0 else np.hypot(v[:, 0], v[:, 1])
        k = int(np.argmax(d))
        if d[k] > tol:
            m = i + 1 + k; keep[m] = True
            pila += [(i, m), (m, j)]
    return pts[keep]


print("Descargando Natural Earth (unos 40 MB)...")
g = json.loads(urllib.request.urlopen(URL, timeout=600).read())
bo = [f for f in g["features"] if f["properties"].get("iso_a2") == "BO"]
assert len(bo) == 9, f"se esperaban 9 departamentos y hay {len(bo)}"

salida = []
for f in bo:
    geo = f["geometry"]
    polis = [geo["coordinates"]] if geo["type"] == "Polygon" else geo["coordinates"]
    nuevos = []
    for poli in polis:
        anillos = []
        for anillo in poli:
            s = simplificar(np.array(anillo, float), TOL)
            if len(s) >= 4:
                anillos.append([[round(float(x), 3), round(float(y), 3)] for x, y in s])
        if anillos:
            nuevos.append(anillos)
    salida.append({"type": "Feature",
                   "properties": {"nombre": f["properties"]["name"], "iso": f["properties"]["iso_3166_2"]},
                   "geometry": {"type": "MultiPolygon", "coordinates": nuevos}})

os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
with open(SALIDA, "w", encoding="utf-8") as fh:
    json.dump({"type": "FeatureCollection", "features": salida}, fh, ensure_ascii=False, separators=(",", ":"))
puntos = sum(len(a) for s in salida for p in s["geometry"]["coordinates"] for a in p)
print("departamentos:", sorted(s["properties"]["nombre"] for s in salida))
print(f"puntos: {puntos} | tamaño: {os.path.getsize(SALIDA) / 1024:.0f} KB | guardado en {SALIDA}")

"""Construye el dashboard del Objetivo 4 como un solo archivo HTML sin dependencias externas.

Ejecutar desde la raíz, después de codigo/datos_dashboard.py. Lee la plantilla
codigo/dashboard_plantilla.html y le incorpora resultados_objetivo4/dashboard_datos.json.
"""
import json
import os

DATOS = "resultados_objetivo4/dashboard_datos.json"
PLANTILLA = "codigo/dashboard_plantilla.html"
SALIDA = "resultados_objetivo4/dashboard_objetivo4.html"
MARCA = "/*DATOS*/"

datos = json.load(open(DATOS, encoding="utf-8"))
texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = open(PLANTILLA, encoding="utf-8").read()
assert html.count(MARCA) == 1, "la plantilla debe contener la marca de datos una sola vez"
with open(SALIDA, "w", encoding="utf-8") as f:
    f.write(html.replace(MARCA, texto))
print(f"{SALIDA}: {os.path.getsize(SALIDA) / 1024:.0f} KB")

"""Composición de G00001 y de los grupos con más errores de BLAST, y desempeño de los modelos en ellos (4.4.5).
Ejecutar desde la raíz. Solo imprime; no modifica resultados.
"""
import glob
import os
import pandas as pd

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 100)
G1 = "G00001"

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", low_memory=False)
col_pais = [c for c in d.columns if "country" in c.lower() or "pais" in c.lower()]
print("columnas de país detectadas:", col_pais)
part = pd.read_csv("resultados_objetivo3/particion_pliegues.csv", dtype={"record_id": str})[["record_id", "grupo", "pliegue"]]
d = d.merge(part, on="record_id")
b = pd.read_csv("resultados_objetivo4/pred_blast.csv", dtype={"record_id": str}).drop(columns="pliegue").merge(part, on="record_id")
b["error"] = b["genero_real"] != b["genero_predicho"]

top = b[b["error"]].groupby("grupo").size().sort_values(ascending=False).head(10).index.tolist()

print("\n=== A. Composición de los diez grupos con más errores de BLAST ===")
for g in top:
    x = d[d["grupo"] == g]
    print(f"\n{g}: {len(x)} registros | género {x['genus'].mode()[0]} | pliegue {x['pliegue'].iloc[0]} | "
          f"especies: {x['species'].nunique()} | BIN: {x['bin_uri'].nunique()}")
    print("  especies (hasta 6):", x["species"].value_counts(dropna=False).head(6).to_dict())
    print("  BIN (hasta 4):", x["bin_uri"].value_counts(dropna=False).head(4).to_dict())
    for c in col_pais:
        print(f"  {c} (hasta 4):", x[c].value_counts(dropna=False).head(4).to_dict())

print(f"\n=== B. {G1} completo ===")
x = d[d["grupo"] == G1]
print(x["species"].value_counts(dropna=False).to_string())
print("BIN:", x["bin_uri"].value_counts(dropna=False).to_dict())
print("registros de Stomoxys en todo el conjunto:", int((d["genus"] == "Stomoxys").sum()),
      "| en G00001:", len(x), "| en otros grupos:", int(((d["genus"] == "Stomoxys") & (d["grupo"] != G1)).sum()))

print(f"\n=== C. BLAST en {G1}: identidad del mejor alineamiento y empates ===")
y = b[b["grupo"] == G1]
print(y["pident_mejor"].describe().round(3).to_string())
print("registros con empate de géneros en el mejor hit:", int((y["generos_empatados"] > 1).sum()))
print("género predicho:", y["genero_predicho"].value_counts().to_dict())

print("\n=== D. Modelos: error por grupo (porcentaje de registros del grupo mal asignados) ===")
filas = {"BLAST": b.groupby("grupo")["error"].mean() * 100}
for f in sorted(glob.glob("resultados_objetivo3/pred_*.csv")):
    p = pd.read_csv(f, dtype={"record_id": str}).merge(part[["record_id", "grupo"]], on="record_id")
    p["error"] = p["genero_real"] != p["genero_predicho"]
    nombre = os.path.basename(f).replace("pred_", "").replace(".csv", "")
    filas[nombre] = p.groupby("grupo")["error"].mean() * 100
    print(f"archivo {os.path.basename(f)}: {len(p)} registros, errores totales {int(p['error'].sum())}, "
          f"en {G1}: {int(p[p['grupo'] == G1]['error'].sum())}")
T = pd.DataFrame(filas).loc[top].round(1)
print(T.to_string())

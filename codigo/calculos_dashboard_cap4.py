"""Cifras de la brecha de datos y de Bolivia para 4.4.6. Ejecutar desde la raíz. Solo imprime."""
import json
import pandas as pd

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 100)
d = json.load(open("resultados_objetivo4/dashboard_datos.json", encoding="utf-8"))

print("=== Registros de Bolivia en la matriz ===")
print(pd.DataFrame(d["bolivia_registros"]).to_string(index=False))

B = pd.DataFrame(d["brecha"])
print("\n=== Brecha: columnas ===", B.columns.tolist())
print("taxones registrados para Bolivia:", len(B))
print("por rango:", B["rango"].value_counts().to_dict())
print("por familia:", B["familia"].value_counts().to_dict())
print("en_modelo:", B["en_modelo"].value_counts().to_dict())
for c in B.columns:
    if c not in ("taxon", "rango", "familia", "fuentes", "departamentos", "genero", "en_modelo"):
        print(f"{c}:", B[c].value_counts(dropna=False).head(8).to_dict())
print("\nTaxones fuera del modelo:")
print(B[~B["en_modelo"]][["taxon", "rango", "familia", "genero", "departamentos"]].to_string(index=False))
print("\nTaxones dentro del modelo:")
print(B[B["en_modelo"]][["taxon", "rango", "familia", "genero", "departamentos"]].to_string(index=False))
print("\nGéneros del modelo con al menos un taxón registrado en Bolivia:", sorted(B[B["en_modelo"]]["genero"].dropna().unique()))
print("Géneros fuera del modelo:", sorted(B[~B["en_modelo"]]["genero"].dropna().unique()))

print("\n=== Departamentos ===")
D = pd.DataFrame(d["departamentos"])
print(D.to_string(index=False))
print("totales: n_con_coi_bolivia =", int(D["n_con_coi_bolivia"].sum()))

import glob, json, os
import pandas as pd

COLS = ["record_id", "processid", "bin_uri", "family", "genus", "species",
        "identification_rank", "marker_code", "country/ocean", "province/state",
        "insdc_acs", "nuc_basecount", "nuc"]

def leer(txt):
    try:
        d = json.loads(txt)
        return d if isinstance(d, list) else [d]
    except json.JSONDecodeError:
        return [json.loads(l) for l in txt.splitlines() if l.strip()]

partes = []
for ruta in sorted(glob.glob("datos/fuente/original/bold_coi/*.json")):
    df = pd.DataFrame(leer(open(ruta).read())).reindex(columns=COLS)
    df["archivo_genero"] = os.path.basename(ruta).replace(".json", "")
    partes.append(df)
todo = pd.concat(partes, ignore_index=True)
todo.to_csv("pentaho/entrada/bold_registros_crudos.csv", index=False)

print("Filas totales:", len(todo))
print(todo["marker_code"].value_counts(dropna=False).head(6))
print("record_id duplicados:", int(todo["record_id"].duplicated().sum()))
print("sin secuencia (nuc vacío):", int(todo["nuc"].isna().sum()))
c5 = todo[todo["marker_code"] == "COI-5P"]
print("COI-5P con especie asignada:", int(c5["species"].notna().sum()), "de", len(c5))
print("COI-5P con insdc_acs (también en GenBank):", int(c5["insdc_acs"].notna().sum()))

brecha = pd.read_csv("datos/fuente/estructurado/tabla_brecha_v2.csv")
brecha["genero"] = brecha["nombre_ncbi"].str.split().str[0]
esp = brecha.groupby("genero")["bold_coi5p_genero"].max()
real = c5.groupby("archivo_genero").size()
comp = pd.DataFrame({"coi5p_14oct": esp, "coi5p_descarga": real})
comp["diferencia"] = comp["coi5p_descarga"] - comp["coi5p_14oct"]
print(comp[comp["diferencia"] != 0].to_string())
print("Suma COI-5P:", int(real.sum()))

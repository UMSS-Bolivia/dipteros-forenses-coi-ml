"""Une las matrices de k-mers con los metadatos (etiqueta = género), muestra
unas filas de ejemplo y guarda la distribución por género. Ejecutar desde la raíz."""
import numpy as np
import pandas as pd

z = np.load("datos/procesados/kmers_k3_k4.npz", allow_pickle=True)
m = pd.read_csv("datos/procesados/metadatos_modelado.csv.gz",
                usecols=["record_id", "genus", "especie_formal", "largo"])
X4 = pd.DataFrame(z["X4"], columns=z["cols4"])
t = pd.concat([m, X4], axis=1)
print("Tabla (registros x columnas):", t.shape, "| etiqueta: genus")

ej = (t[t.genus.isin(["Calliphora", "Fannia", "Musca", "Sarcophaga", "Stomoxys"])]
        .groupby("genus").head(1)[["record_id", "genus", "largo", "AAAA", "AAAC", "AAAG", "AAAT"]])
ej.round(4).to_csv("resultados_objetivo2/ejemplo_tabla_caracteristicas.csv", index=False)
print(ej.round(4).to_string(index=False))

dist = (m.genus.value_counts().rename_axis("genus").reset_index(name="registros"))
dist["porcentaje"] = (dist.registros / len(m) * 100).round(1)
dist.to_csv("resultados_objetivo2/registros_por_genero_final.csv", index=False)
print("\n", dist.to_string(index=False))

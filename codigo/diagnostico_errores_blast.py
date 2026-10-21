"""Diagnóstico de los errores de BLAST (Objetivo 4). Ejecutar desde la raíz.

Reproduce las cifras de la adición del 20 de octubre del plan de análisis: errores de BLAST por par de
géneros, por grupo y por estrato de identidad, y los alineamientos del registro GBDP0769-06.COI-5P.
No modifica ningún resultado; solo imprime tablas.
"""
import subprocess
import tempfile
import pandas as pd

REGISTRO = "GBDP0769-06.COI-5P"
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)

p = pd.read_csv("resultados_objetivo3/particion_pliegues.csv", dtype={"record_id": str})[["record_id", "grupo", "pliegue"]]
d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", low_memory=False,
                usecols=["record_id", "genus", "species", "bin_uri", "secuencia"])
b = (pd.read_csv("resultados_objetivo4/pred_blast.csv", dtype={"record_id": str})
       .drop(columns="pliegue").merge(p, on="record_id"))
s = pd.read_csv("resultados_objetivo4/pred_blast_sin_GBDP0769.csv", dtype={"record_id": str})
b["error"] = b["genero_real"] != b["genero_predicho"]
s["error"] = s["genero_real"] != s["genero_predicho"]
e = b[b["error"]]

print("=== 1. Errores de BLAST (análisis principal) ===")
print("registros:", len(b), "| errores:", len(e), "| sin asignación:", int((b["genero_predicho"] == "sin_asignacion").sum()))
print("\nPares género real -> género predicho con más errores:")
print(e.groupby(["genero_real", "genero_predicho"]).size().sort_values(ascending=False).head(10).rename("errores").to_string())

print("\n=== 2. Grupos con más errores ===")
g = e.groupby("grupo").agg(errores=("error", "size"), genero_real=("genero_real", lambda x: x.mode()[0]),
                           genero_predicho=("genero_predicho", lambda x: x.mode()[0]), pliegue=("pliegue", "first"))
g = g.join(b.groupby("grupo").size().rename("registros_del_grupo")).sort_values("errores", ascending=False).head(10)
g["pct_de_los_errores"] = (100 * g["errores"] / len(e)).round(1)
print(g.to_string())

print("\n=== 3. Errores por estrato de identidad del mejor hit ===")
b["estrato"] = pd.cut(b["pident_mejor"], [0, 90, 95, 98, 99, 101], right=False,
                      labels=["<90", "90-95", "95-98", "98-99", ">=99"])
t = b.groupby("estrato", observed=True).agg(registros=("error", "size"), errores=("error", "sum"))
t["pct_error"] = (100 * t["errores"] / t["registros"]).round(2)
t["errores_G00001"] = b[b["grupo"] == "G00001"].groupby("estrato", observed=True)["error"].sum()
t["errores_G00001"] = t["errores_G00001"].fillna(0).astype(int)
print(t.to_string())

print("\n=== 4. Errores con identidad >= 99 % por par de géneros ===")
c = (e[e["pident_mejor"] >= 99].groupby(["genero_real", "genero_predicho"])
       .agg(errores=("error", "size"), grupos=("grupo", "nunique")).sort_values("errores", ascending=False).head(10))
print(c.to_string())

print(f"\n=== 5. Registro {REGISTRO} ===")
r = d[d["record_id"] == REGISTRO].iloc[0]
fila = b[b["record_id"] == REGISTRO].iloc[0]
print("género:", r["genus"], "| especie:", r["species"], "| BIN:", r["bin_uri"],
      "| grupo:", fila["grupo"], "| pliegue:", fila["pliegue"], "| longitud:", len(str(r["secuencia"])))
ref = d[d["record_id"] != REGISTRO]
with tempfile.TemporaryDirectory() as tmp:
    with open(f"{tmp}/ref.fa", "w") as f:
        for rid, seq in zip(ref["record_id"], ref["secuencia"].str.upper()):
            f.write(f">{rid}\n{seq}\n")
    with open(f"{tmp}/q.fa", "w") as f:
        f.write(f">{r['record_id']}\n{str(r['secuencia']).upper()}\n")
    subprocess.run(["makeblastdb", "-in", f"{tmp}/ref.fa", "-dbtype", "nucl", "-out", f"{tmp}/db"],
                   check=True, capture_output=True)
    subprocess.run(["blastn", "-task", "blastn", "-query", f"{tmp}/q.fa", "-db", f"{tmp}/db", "-evalue", "1e-5",
                    "-max_target_seqs", "500", "-max_hsps", "1", "-num_threads", "4",
                    "-outfmt", "6 sseqid pident length qcovs bitscore evalue", "-out", f"{tmp}/h.tsv"], check=True)
    h = pd.read_csv(f"{tmp}/h.tsv", sep="\t", names=["sseqid", "pident", "length", "qcovs", "bitscore", "evalue"])
h = h.merge(d[["record_id", "genus", "species"]], left_on="sseqid", right_on="record_id")
print("alineamientos devueltos contra el resto de los registros:", len(h),
      "| identidad mínima y máxima:", h["pident"].min().round(1), h["pident"].max().round(1))
print(h.groupby(["genus", "species"], dropna=False).size().sort_values(ascending=False).head(5).rename("alineamientos").to_string())

print("\n=== 6. Sensibilidad: BLAST sin el registro en la base de referencia ===")
print("errores en el análisis principal:", int(b["error"].sum()), "| sin el registro:", int(s["error"].sum()))
m = b.merge(s[["record_id", "genero_predicho"]], on="record_id", suffixes=("", "_sin"))
print("predicciones que cambiaron:", int((m["genero_predicho"] != m["genero_predicho_sin"]).sum()),
      "| de ellas, en el grupo G00001:", int(((m["genero_predicho"] != m["genero_predicho_sin"]) & (m["grupo"] == "G00001")).sum()))
fr = m[m["record_id"] == REGISTRO].iloc[0]
print(f"predicción del propio {REGISTRO} (género real {fr['genero_real']}): principal = {fr['genero_predicho']}, sin el registro = {fr['genero_predicho_sin']}")

"""Línea base BLAST por pliegue (Objetivo 4). Ejecutar desde la raíz.

Para cada pliegue de la partición del Objetivo 3 se construye una base de datos con SOLO los
registros de entrenamiento y se consultan los registros de prueba. Decisiones fijadas en
resultados_objetivo4/plan_analisis.md.
"""
import os, subprocess, tempfile, time
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
                             precision_recall_fscore_support)

HILOS, EVALUE, MAX_HITS = 10, "1e-5", "100"
SIN_HIT = "sin_asignacion"

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz",
                usecols=["record_id", "genus", "secuencia"], low_memory=False)
p = pd.read_csv("resultados_objetivo3/particion_pliegues.csv")
assert (d["record_id"].astype(str).values == p["record_id"].astype(str).values).all(), "orden distinto"
assert (d["genus"].values == p["genus"].values).all(), "géneros distintos"
d["secuencia"] = d["secuencia"].str.upper()
d["pliegue"] = p["pliegue"].values
genero = dict(zip(d["record_id"], d["genus"]))
labs = sorted(d["genus"].unique())

print(subprocess.run(["blastn", "-version"], capture_output=True, text=True).stdout.splitlines()[0])
os.makedirs("resultados_objetivo4", exist_ok=True)


def escribir_fasta(df, ruta):
    with open(ruta, "w") as f:
        for rid, seq in zip(df["record_id"], df["secuencia"]):
            f.write(f">{rid}\n{seq}\n")


salidas = []
for f in range(5):
    t0 = time.time()
    tr, te = d[d["pliegue"] != f], d[d["pliegue"] == f]
    with tempfile.TemporaryDirectory() as tmp:
        escribir_fasta(tr, f"{tmp}/train.fa")
        escribir_fasta(te, f"{tmp}/test.fa")
        subprocess.run(["makeblastdb", "-in", f"{tmp}/train.fa", "-dbtype", "nucl", "-out", f"{tmp}/db"],
                       check=True, capture_output=True)
        subprocess.run(["blastn", "-task", "blastn", "-query", f"{tmp}/test.fa", "-db", f"{tmp}/db",
                        "-evalue", EVALUE, "-max_target_seqs", MAX_HITS, "-max_hsps", "1",
                        "-num_threads", str(HILOS),
                        "-outfmt", "6 qseqid sseqid pident length qcovs bitscore evalue",
                        "-out", f"{tmp}/hits.tsv"], check=True)
        h = pd.read_csv(f"{tmp}/hits.tsv", sep="\t",
                        names=["qseqid", "sseqid", "pident", "length", "qcovs", "bitscore", "evalue"])
    h["genero_hit"] = h["sseqid"].map(genero)
    mx = h.groupby("qseqid")["bitscore"].transform("max")
    top = h[h["bitscore"] == mx]
    cnt = (top.groupby(["qseqid", "genero_hit"]).size().rename("n").reset_index()
              .sort_values(["qseqid", "n", "genero_hit"], ascending=[True, False, True]))
    ngen = cnt.groupby("qseqid")["genero_hit"].nunique().rename("generos_empatados")
    mejor = cnt.groupby("qseqid").head(1).set_index("qseqid")["genero_hit"].rename("genero_predicho")
    info = top.groupby("qseqid").agg(pident_mejor=("pident", "max"), qcovs_mejor=("qcovs", "max"),
                                     bitscore_mejor=("bitscore", "max"), hits_empatados=("sseqid", "size"))
    r = te[["record_id", "pliegue", "genus"]].rename(columns={"genus": "genero_real"}).set_index("record_id")
    r = r.join(mejor).join(info).join(ngen)
    r["genero_predicho"] = r["genero_predicho"].fillna(SIN_HIT)
    salidas.append(r.reset_index())
    print(f"pliegue {f}: {len(te)} consultas | sin hit: {int((r['genero_predicho'] == SIN_HIT).sum())} | "
          f"{(time.time() - t0) / 60:.1f} min", flush=True)

res = pd.concat(salidas).set_index("record_id").loc[d["record_id"]].reset_index()
res.to_csv("resultados_objetivo4/pred_blast.csv", index=False)

y, pred = res["genero_real"].values, res["genero_predicho"].values
pr, rc, f1, n = precision_recall_fscore_support(y, pred, labels=labs, zero_division=0)
tab = pd.DataFrame({"genero": labs, "registros": n, "recall": rc.round(3), "precision": pr.round(3), "f1": f1.round(3)})
tab.to_csv("resultados_objetivo4/metricas_genero_blast.csv", index=False)

print("\n=== BLAST: predicciones de los 5 pliegues juntas ===")
print("exactitud:", round(accuracy_score(y, pred), 3), "| exactitud balanceada:",
      round(balanced_accuracy_score(y, pred), 3), "| F1 macro:",
      round(f1_score(y, pred, labels=labs, average="macro", zero_division=0), 3))
print("registros sin hit:", int((pred == SIN_HIT).sum()),
      "| con hits empatados de más de un género:", int((res["generos_empatados"] > 1).sum()))
print("identidad del mejor hit, percentiles 5/25/50/75/95:",
      res["pident_mejor"].quantile([.05, .25, .5, .75, .95]).round(1).tolist())
print(tab.to_string(index=False))

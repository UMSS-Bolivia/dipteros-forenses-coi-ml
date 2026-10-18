"""Embeddings de un modelo de ADN preentrenado (Objetivo 3). Ejecutar desde la raíz.

Uso: python codigo/extraer_embeddings.py {nt50m|dnabert2}
Embedding de cada secuencia = promedio de los estados ocultos de la última capa sobre los tokens de
ADN (sin tokens especiales ni de relleno). Las secuencias van en mayúsculas.
Guarda por bloques en datos/procesados/embeddings_tmp_<modelo>/ y se puede reanudar.
"""
import json, os, sys, time, types
import numpy as np
import pandas as pd
import torch
import transformers
from transformers import AutoModel, AutoModelForMaskedLM, AutoTokenizer

nombre = sys.argv[1]
MODELOS = {
    "nt50m": ("InstaDeepAI/nucleotide-transformer-v2-50m-multi-species", AutoModelForMaskedLM, 1000),
    "dnabert2": ("zhihan1996/DNABERT-2-117M", AutoModel, 512),
}
repo, clase, maxlen = MODELOS[nombre]
torch.set_num_threads(10)
BATCH, BLOQUE = 16, 2000
tmp = f"datos/procesados/embeddings_tmp_{nombre}"
os.makedirs(tmp, exist_ok=True)

if nombre == "dnabert2":   # sin GPU: módulo vacío para que use la atención normal de PyTorch
    sys.modules.setdefault("triton", types.ModuleType("triton"))
try:
    from huggingface_hub import HfApi
    sha = HfApi().model_info(repo).sha
except Exception as e:
    sha = None
    print("no se pudo fijar la revisión:", type(e).__name__)

tok = AutoTokenizer.from_pretrained(repo, trust_remote_code=True, revision=sha)
mod = clase.from_pretrained(repo, trust_remote_code=True, revision=sha).eval()
especiales = torch.tensor(tok.all_special_ids)

d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", usecols=["record_id", "secuencia"], low_memory=False)
seqs = d["secuencia"].str.upper().tolist()
n = len(seqs)
orden = np.argsort([len(s) for s in seqs], kind="stable")   # secuencias parecidas en largo: menos relleno
truncadas = 0

def embeber(lote):
    global truncadas
    enc = tok(lote, return_tensors="pt", padding=True, truncation=True, max_length=maxlen)
    truncadas += int((enc["attention_mask"].sum(1) >= maxlen).sum())
    with torch.no_grad():
        if nombre == "nt50m":
            h = mod(**enc, output_hidden_states=True).hidden_states[-1]
        else:
            h = mod(enc["input_ids"], attention_mask=enc["attention_mask"])[0]
    m = (enc["attention_mask"].bool() & ~torch.isin(enc["input_ids"], especiales)).unsqueeze(-1).to(h.dtype)
    return ((h * m).sum(1) / m.sum(1)).numpy().astype(np.float32)

t0 = time.time()
for b, ini in enumerate(range(0, n, BLOQUE)):
    ruta = f"{tmp}/bloque_{b:03d}.npy"
    if os.path.exists(ruta):
        continue
    idx = orden[ini:ini + BLOQUE]
    E = np.vstack([embeber([seqs[i] for i in idx[j:j + BATCH]]) for j in range(0, len(idx), BATCH)])
    np.save(ruta, E)
    hechos = min(ini + BLOQUE, n)
    print(f"[{nombre}] {hechos}/{n} | {(time.time()-t0)/60:.1f} min", flush=True)

E = np.vstack([np.load(f"{tmp}/bloque_{b:03d}.npy") for b in range((n + BLOQUE - 1) // BLOQUE)])
X = np.zeros_like(E)
X[orden] = E
assert not np.isnan(X).any() and X.shape[0] == n
np.savez(f"datos/procesados/embeddings_{nombre}.npz", X=X, record_id=np.array(d["record_id"].astype(str).tolist()))
json.dump({"modelo": nombre, "repo": repo, "revision": sha, "dimension": int(X.shape[1]),
           "transformers": transformers.__version__, "torch": torch.__version__, "max_tokens": maxlen,
           "secuencias_truncadas": truncadas, "pooling": "promedio de la última capa sin tokens especiales"},
          open(f"datos/procesados/embeddings_{nombre}_info.json", "w"), indent=2)
print(f"[{nombre}] listo: {X.shape} | truncadas: {truncadas}", flush=True)

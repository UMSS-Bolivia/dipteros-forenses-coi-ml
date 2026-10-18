"""Prueba de carga y tiempos de dos modelos de ADN preentrenados (Objetivo 3). Ejecutar desde la raíz."""
import sys, time, types
import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoModelForMaskedLM, AutoTokenizer

torch.set_num_threads(12)
N_TOTAL = 66782
d = pd.read_csv("datos/procesados/bold_coi_modelado_final.csv.gz", usecols=["record_id", "secuencia"], nrows=200)
seqs = d["secuencia"].str.upper().sample(32, random_state=42).tolist()   # siempre en mayúsculas

MODELOS = {
    "nt50m": ("InstaDeepAI/nucleotide-transformer-v2-50m-multi-species", AutoModelForMaskedLM),
    "dnabert2": ("zhihan1996/DNABERT-2-117M", AutoModel),
}
for nombre, (repo, clase) in [(n, v) for n, v in MODELOS.items() if len(sys.argv) < 2 or n in sys.argv[1:]]:
    print(f"\n===== {nombre}: {repo} =====", flush=True)
    try:
        if nombre == "dnabert2":   # sin GPU: módulo vacío para que use la atención normal de PyTorch
            sys.modules.setdefault("triton", types.ModuleType("triton"))
        tok = AutoTokenizer.from_pretrained(repo, trust_remote_code=True)
        mod = clase.from_pretrained(repo, trust_remote_code=True).eval()
        print("parámetros (millones):", round(sum(p.numel() for p in mod.parameters()) / 1e6, 1), flush=True)
        t0, embs, ntok = time.time(), [], []
        for i in range(0, len(seqs), 8):
            enc = tok(seqs[i:i + 8], return_tensors="pt", padding=True, truncation=True, max_length=512)
            ntok += enc["attention_mask"].sum(1).tolist()
            with torch.no_grad():
                if nombre == "nt50m":
                    h = mod(**enc, output_hidden_states=True).hidden_states[-1]
                else:
                    h = mod(enc["input_ids"], attention_mask=enc["attention_mask"])[0]
            m = enc["attention_mask"].unsqueeze(-1).to(h.dtype)
            embs.append(((h * m).sum(1) / m.sum(1)).numpy())
        seg = time.time() - t0
        E = np.vstack(embs)
        print(f"embedding: {E.shape} | tokens por secuencia (media): {np.mean(ntok):.0f} | NaN: {int(np.isnan(E).sum())}")
        print(f"{seg:.1f} s para 32 secuencias = {seg/32:.2f} s/secuencia | estimado para {N_TOTAL}: {seg/32*N_TOTAL/3600:.1f} horas", flush=True)
    except Exception as e:
        print("FALLA:", type(e).__name__, str(e)[:400])

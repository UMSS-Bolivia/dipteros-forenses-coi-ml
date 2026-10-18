"""Carga común de matrices, etiquetas, grupos y pliegues del Objetivo 3."""
import numpy as np
import pandas as pd

def cargar(k):
    z = np.load("datos/procesados/kmers_k3_k4.npz", allow_pickle=True)
    X, rid = z[f"X{k}"], z["record_id"].astype(str)
    p = pd.read_csv("resultados_objetivo3/particion_pliegues.csv")
    assert (rid == p["record_id"].astype(str).values).all(), "orden distinto entre matriz y partición"
    return X, p["genus"].values, p["grupo"].values, p["pliegue"].values, rid

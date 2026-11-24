"""Demostración breve para el video: python demo.py (sin volver a entrenar)."""
import json
from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parent
p=json.loads((root/"results/parameters.json").read_text())
print("MODELO OCULTO DE MARKOV - SERVICIO WEB")
print("Estados: Normal, Degradado, Crítico\n")
for name in ["pi","A","B"]:
    print(name, "=",p["E1_base"][name],"\n")
df=pd.read_csv(root/"data/sequences.csv")
print("Primeros 15 minutos del escenario E2, réplica 0:")
print(df[(df.scenario=="E2_persistencia")&(df.rep==0)].head(15)[
    ["t","latency_ms","errors_100","symbol","state","Viterbi"]].to_string(index=False))
s=pd.read_csv(root/"results/summary.csv")
print("\nExactitud de Viterbi (50 réplicas por escenario):")
print(s[(s.method=="Viterbi")&(s.metric=="accuracy")][
    ["scenario","mean","std","ci_low","ci_high"]].to_string(index=False))
print("\nGráficos disponibles en figures/. Datos sintéticos: no son mediciones de producción.")

"""Recalcula las métricas exportadas y, opcionalmente, compara una repetición."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.experiment import metrics, describe, scenarios


def main(root, replay=None):
    data=pd.read_csv(root/"data/sequences.csv")
    scores=pd.read_csv(root/"results/metrics.csv")
    assert len(data)==4*50*1440
    checks=0
    for (case,rep),df in data.groupby(["scenario","rep"]):
        for method in ["Viterbi","Filtrado","Sin_memoria","Viterbi_base_fijo"]:
            actual,_=metrics(df.state.to_numpy(),df[method].to_numpy())
            saved=scores[(scores.scenario==case)&(scores.rep==rep)&(scores.method==method)].iloc[0]
            for key,value in actual.items():
                np.testing.assert_allclose(value,saved[key],rtol=0,atol=1e-10)
                checks+=1
    cols=["accuracy","macro_f1","critical_recall","critical_fpr","accuracy_first30"]
    recalculated=describe(scores,["scenario","method"],cols)
    saved=pd.read_csv(root/"results/summary.csv")
    idx=["scenario","method","metric"]
    pd.testing.assert_frame_equal(recalculated.set_index(idx).sort_index(),saved.set_index(idx).sort_index(),
                                  check_exact=False,rtol=1e-9,atol=1e-10)
    # Los símbolos guardados deben corresponder a las observaciones numéricas.
    symbol=2*np.digitize(data.latency_ms,[200,600])+(data.errors_100>=3).astype(int)
    np.testing.assert_array_equal(symbol,data.symbol)
    for case in scenarios(): case.model().validate()
    hist=pd.read_csv(root/"results/baum_welch_history.csv")
    for _,df in hist.groupby("restart"): assert np.all(np.diff(df.loglik)>=-1e-7)
    design=json.loads((root/"results/design.json").read_text())
    assert set(design["test_seeds"]).isdisjoint(design["training_seeds"])
    comparison=[]
    if replay:
        files=sorted(list((root/"data").glob("*.csv"))+list((root/"results").glob("*.csv")))
        files += [root/"results"/f for f in ("parameters.json","learned_model.json","design.json")]
        for path in files:
            other=replay/path.relative_to(root)
            a=hashlib.sha256(path.read_bytes()).hexdigest()
            b=hashlib.sha256(other.read_bytes()).hexdigest()
            assert a==b, str(path)
            comparison.append({"file":str(path.relative_to(root)),"sha256":a,"identical":True})
    result={"status":"PASS","rows":len(data),"individual_metric_checks":checks,
            "recomputed_summary":True,"symbol_consistency":True,"em_non_decreasing":True,
            "training_test_seeds_disjoint":True,"replay_comparison":comparison,
            "note":"La igualdad de bytes fue comprobada en este entorno; no certifica otros sistemas."}
    (root/"results/validation.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="replay_comparison"},indent=2))
    print("Archivos idénticos en repetición:",len(comparison))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--compare",type=Path)
    args=p.parse_args();main(args.root,args.compare)

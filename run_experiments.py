"""Ejecute: python run_experiments.py --output ."""
import argparse
import json
import platform
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import scipy
import matplotlib
from src.hmm import HMM, forward, viterbi, stationary, baum_welch
from src.experiment import scenarios, simulate, metrics, describe

SEED = 20261106
REPS = 50
LENGTH = 1440


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def model_dict(m):
    return {"pi": m.pi.tolist(), "A": m.A.tolist(), "B": m.B.tolist()}


def run(out):
    for directory in ("data", "results", "figures"):
        (out/directory).mkdir(parents=True, exist_ok=True)
    cases = scenarios()
    base = cases[0].model()
    frames, rows, diagnostics, confusion_rows = [], [], [], []
    print("Simulando 4 escenarios, 50 réplicas y 1440 minutos...", flush=True)
    for sc in cases:
        model = sc.model()
        print(sc.name, flush=True)
        prior = stationary(model.A)
        for rep in range(REPS):
            df = simulate(sc, LENGTH, SEED+rep)
            obs, z = df.symbol.to_numpy(), df.state.to_numpy()
            ll, alpha, _ = forward(obs, model)
            preds = {"Viterbi": viterbi(obs, model)[0],
                     "Filtrado": alpha.argmax(1),
                     "Sin_memoria": (prior[:, None]*model.B[:, obs]).argmax(0),
                     "Viterbi_base_fijo": viterbi(obs, base)[0]}
            for name, pred in preds.items():
                met, cm = metrics(z, pred)
                rows.append({"scenario": sc.name, "rep": rep, "seed": SEED+rep,
                             "method": name} | met)
                df[name] = pred
                for i in range(3):
                    for j in range(3):
                        confusion_rows.append({"scenario":sc.name,"rep":rep,"method":name,
                                               "true":i,"predicted":j,"count":int(cm[i,j])})
            diagnostics.append({"scenario":sc.name,"rep":rep,
                 "latency_mean_ms":df.latency_ms.mean(), "error_rate":df.errors_100.mean()/100,
                 "critical_fraction":(z==2).mean(),"critical_first30":(z[:30]==2).mean(),
                 "transitions":int(np.sum(z[1:]!=z[:-1])),"nll_per_minute":-ll/LENGTH})
            df.insert(0, "rep", rep)
            df.insert(0, "scenario", sc.name)
            frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    data.to_csv(out/"data/sequences.csv", index=False, float_format="%.12g")
    score = pd.DataFrame(rows)
    score.to_csv(out/"results/metrics.csv", index=False, float_format="%.12g")
    measure_cols = ["accuracy", "macro_f1", "critical_recall", "critical_fpr", "accuracy_first30"]
    summary = describe(score, ["scenario", "method"], measure_cols)
    summary.to_csv(out/"results/summary.csv", index=False, float_format="%.12g")
    diag = pd.DataFrame(diagnostics)
    diag.to_csv(out/"results/process_metrics.csv", index=False, float_format="%.12g")
    describe(diag, ["scenario"], list(diag.columns[2:])).to_csv(
        out/"results/process_summary.csv", index=False, float_format="%.12g")
    pd.DataFrame(confusion_rows).to_csv(out/"results/confusion.csv", index=False)
    # Comparación pareada en las MISMAS secuencias; no IC de minutos correlacionados.
    paired = []
    for sc in cases:
        sub = score[score.scenario == sc.name]
        for other in ("Filtrado", "Sin_memoria", "Viterbi_base_fijo"):
            for rep in range(REPS):
                p = sub[sub.rep == rep].set_index("method")
                paired.append({"scenario":sc.name,"comparison":"Viterbi - "+other,"rep":rep,
                               "delta_accuracy":p.loc["Viterbi","accuracy"]-p.loc[other,"accuracy"],
                               "delta_f1":p.loc["Viterbi","macro_f1"]-p.loc[other,"macro_f1"]})
    paired = pd.DataFrame(paired)
    paired.to_csv(out/"results/paired_differences.csv", index=False, float_format="%.12g")
    describe(paired,["scenario","comparison"],["delta_accuracy","delta_f1"]).to_csv(
        out/"results/paired_summary.csv",index=False,float_format="%.12g")
    configs = {sc.name: model_dict(sc.model()) | {"latency_medians_ms":sc.medians.tolist(),
                  "log_sigmas":sc.sigmas.tolist(),"error_probabilities":sc.error_p.tolist(),
                  "stationary":stationary(sc.A).tolist(),"mean_dwell_minutes":(1/(1-np.diag(sc.A))).tolist()}
               for sc in cases}
    write_json(out/"results/parameters.json", configs)
    write_json(out/"results/design.json", {"base_seed":SEED,"replications":REPS,"length":LENGTH,
        "test_seeds":[SEED+r for r in range(REPS)],"training_seeds":[900000+i for i in range(8)],
        "initialization_seeds":[700000+i for i in range(3)],"training_length":600,
        "rng":"NumPy default_rng PCG64; SeedSequence.spawn(3)","requests_per_minute":100,
        "latency_cutoffs_ms":[200,600],"error_cutoff_count":3,
        "paired_scenarios":"Misma semilla por réplica; flujos separados estado/latencia/errores"})
    base_frames = [f for f in frames if f.scenario.iloc[0] == "E1_base"]
    sensitivity = []
    print("Evaluando sensibilidad de matrices y prior...", flush=True)
    for kind in ("A", "B"):
        for eps in (0., .1, .25, .5, .75, 1.):
            a = (1-eps)*base.A+eps/3 if kind == "A" else base.A
            b = (1-eps)*base.B+eps/6 if kind == "B" else base.B
            mod = HMM(base.pi, a, b).validate()
            for rep, df in enumerate(base_frames):
                met, _ = metrics(df.state.to_numpy(), viterbi(df.symbol.to_numpy(),mod)[0])
                sensitivity.append({"parameter":kind,"epsilon":eps,"rep":rep} | met)
    sensitivity = pd.DataFrame(sensitivity)
    sensitivity.to_csv(out/"results/sensitivity.csv",index=False,float_format="%.12g")
    describe(sensitivity,["parameter","epsilon"],measure_cols).to_csv(
        out/"results/sensitivity_summary.csv",index=False,float_format="%.12g")
    priors = {"base":base.pi,"uniforme":np.ones(3)/3,"critico":np.array([.05,.15,.8])}
    pi_rows = []
    for name, prior in priors.items():
        for rep, df in enumerate(base_frames):
            obs = df.symbol.to_numpy()
            pred = forward(obs,HMM(prior,base.A,base.B))[1].argmax(1)
            met,_ = metrics(df.state.to_numpy(),pred)
            met["accuracy_first5"] = float(np.mean(df.state.to_numpy()[:5]==pred[:5]))
            pi_rows.append({"prior":name,"rep":rep} | met)
    pi_df = pd.DataFrame(pi_rows)
    pi_df.to_csv(out/"results/prior_sensitivity.csv",index=False,float_format="%.12g")
    describe(pi_df,["prior"],measure_cols+["accuracy_first5"]).to_csv(
        out/"results/prior_summary.csv",index=False,float_format="%.12g")
    print("Ajustando Baum-Welch: 8 secuencias independientes, 3 reinicios...",flush=True)
    train = [simulate(cases[0],600,900000+i) for i in range(8)]
    pd.concat([d.assign(sequence=i,seed=900000+i) for i,d in enumerate(train)],ignore_index=True).to_csv(
        out/"data/training_sequences.csv",index=False,float_format="%.12g")
    obs_train = [d.symbol.to_numpy() for d in train]
    trained, histories, restart_info = [], [], []
    for restart in range(3):
        rng = np.random.default_rng(700000+restart)
        init = HMM(rng.dirichlet(np.ones(3)),
                   np.array([rng.dirichlet(np.ones(3)+8*np.eye(3)[i]) for i in range(3)]),
                   rng.dirichlet(np.ones(6),size=3))
        fitted, hist = baum_welch(obs_train,init,max_iter=60,tol=1e-5)
        trained.append(fitted)
        restart_info.append({"restart":restart,"final_ll":hist[-1],"iterations":len(hist)-1,
                             "stopped_by_tolerance":len(hist)-1<60 or hist[-1]-hist[-2]<1e-5})
        histories.extend({"restart":restart,"iteration":i,"loglik":v} for i,v in enumerate(hist))
        print(f"Reinicio {restart}: LL={hist[-1]:.3f}, iteraciones={len(hist)-1}",flush=True)
    chosen = int(np.argmax([r["final_ll"] for r in restart_info]))
    fitted = trained[chosen]
    write_json(out/"results/learned_model.json",model_dict(fitted)|{"selected_restart":chosen,
                  "restarts":restart_info,"ordering":"Expected symbol index, ascending"})
    pd.DataFrame(histories).to_csv(out/"results/baum_welch_history.csv",index=False,float_format="%.12g")
    learned_rows, learned_predictions = [], []
    for rep, df in enumerate(base_frames):
        obs = df.symbol.to_numpy()
        pred = viterbi(obs,fitted)[0]
        met,_ = metrics(df.state.to_numpy(),pred)
        learned_rows.append({"method":"Baum_Welch","rep":rep,
                            "nll_per_minute":-forward(obs,fitted)[0]/LENGTH} | met)
        learned_predictions.append(pd.DataFrame({"rep":rep,"t":df.t.to_numpy(),"prediction":pred}))
    learned_df = pd.DataFrame(learned_rows)
    learned_df.to_csv(out/"results/learned_metrics.csv",index=False,float_format="%.12g")
    pd.concat(learned_predictions).to_csv(out/"results/learned_predictions.csv",index=False)
    describe(learned_df,["method"],measure_cols+["nll_per_minute"]).to_csv(
        out/"results/learned_summary.csv",index=False,float_format="%.12g")
    write_json(out/"results/environment.json",{"python":sys.version,"platform":platform.platform(),
        "numpy":np.__version__,"pandas":pd.__version__,"matplotlib":matplotlib.__version__,
        "scipy":scipy.__version__,"execution_date_local":datetime.now(ZoneInfo("America/Bogota")).date().isoformat(),
        "timezone":"America/Bogota"})
    from src.plots import make_plots
    make_plots(out)
    print(summary[(summary.method=="Viterbi") & (summary.metric=="accuracy")].to_string(index=False))
    print("Resultados guardados en",out.resolve(),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("."))
    args = parser.parse_args()
    run(args.output)

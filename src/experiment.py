"""Generación, evaluación y resúmenes; la unidad estadística es una réplica."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.stats import norm, binom, t as student_t
from .hmm import HMM

STATES = ["Normal", "Degradado", "Crítico"]
SYMBOLS = ["baja/pocos", "baja/muchos", "media/pocos", "media/muchos", "alta/pocos", "alta/muchos"]
BASE_A = np.array([[.96, .035, .005], [.15, .80, .05], [.05, .20, .75]])
STRESS_A = np.array([[.88, .10, .02], [.05, .85, .10], [.02, .08, .90]])
BASE_PI = np.array([.90, .08, .02])


@dataclass
class Scenario:
    name: str
    pi: np.ndarray
    A: np.ndarray
    medians: np.ndarray
    sigmas: np.ndarray
    error_p: np.ndarray

    def model(self):
        # P(L < x) = Phi((ln(x)-ln(mediana))/sigma).
        cdf = norm.cdf((np.log([200., 600.])[None, :] - np.log(self.medians)[:, None])
                      / self.sigmas[:, None])
        lp = np.diff(np.c_[np.zeros(3), cdf, np.ones(3)], axis=1)
        ep = binom.cdf(2, 100, self.error_p)
        B = (lp[:, :, None] * np.c_[ep, 1-ep][:, None, :]).reshape(3, 6)
        return HMM(self.pi.copy(), self.A.copy(), B).validate()


def scenarios():
    med, sig, ep = np.array([100., 300., 900.]), np.array([.4, .45, .5]), np.array([.005, .03, .12])
    return [Scenario("E1_base", BASE_PI, BASE_A, med, sig, ep),
            Scenario("E2_persistencia", BASE_PI, STRESS_A, med, sig, ep),
            Scenario("E3_solapamiento", BASE_PI, BASE_A, np.array([140., 240., 400.]),
                     np.full(3, .65), np.array([.015, .03, .06])),
            Scenario("E4_inicio_critico", np.array([.05, .15, .80]), BASE_A, med, sig, ep)]


def simulate(sc, length, seed):
    # Flujos separados: modificar pi o A no altera la cantidad de números de emisión.
    streams = np.random.SeedSequence(seed).spawn(3)
    rng_state, rng_latency, rng_errors = [np.random.default_rng(s) for s in streams]
    u = rng_state.random(length)
    z = np.empty(length, dtype=int)
    z[0] = np.searchsorted(np.cumsum(sc.pi), u[0], side="right")
    for j in range(1, length):
        z[j] = np.searchsorted(np.cumsum(sc.A[z[j-1]]), u[j], side="right")
    latency = rng_latency.lognormal(np.log(sc.medians[z]), sc.sigmas[z])
    errors = rng_errors.binomial(100, sc.error_p[z])
    obs = 2*np.digitize(latency, [200., 600.]) + (errors >= 3).astype(int)
    return pd.DataFrame({"t": np.arange(length), "state": z, "latency_ms": latency,
                         "errors_100": errors, "symbol": obs})


def metrics(truth, pred):
    confusion = np.zeros((3, 3), dtype=int)
    np.add.at(confusion, (truth, pred), 1)
    tp = np.diag(confusion)
    denom = confusion.sum(0) + confusion.sum(1)
    f1 = np.divide(2*tp, denom, out=np.zeros(3), where=denom > 0)
    critical = confusion[2].sum()
    noncritical = confusion[:2].sum()
    return {"accuracy": float(np.mean(truth == pred)), "macro_f1": float(f1.mean()),
            "critical_recall": float(tp[2]/critical) if critical else np.nan,
            "critical_fpr": float(confusion[:2, 2].sum()/noncritical) if noncritical else np.nan,
            "accuracy_first30": float(np.mean(truth[:30] == pred[:30]))}, confusion


def describe(df, groups, values):
    rows = []
    for keys, group in df.groupby(groups, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        for value in values:
            x = group[value].dropna().to_numpy()
            n = len(x)
            sd = x.std(ddof=1) if n > 1 else np.nan
            half = student_t.ppf(.975, n-1)*sd/np.sqrt(n) if n > 1 else np.nan
            rows.append(dict(zip(groups, keys)) | {"metric": value, "n": n, "mean": x.mean(),
                         "std": sd, "min": x.min(), "max": x.max(),
                         "ci_low": x.mean()-half, "ci_high": x.mean()+half})
    return pd.DataFrame(rows)

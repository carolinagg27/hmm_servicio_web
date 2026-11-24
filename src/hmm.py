"""HMM categórico de primer orden: algoritmos explícitos sin hmmlearn."""
from dataclasses import dataclass
import numpy as np


@dataclass
class HMM:
    pi: np.ndarray
    A: np.ndarray
    B: np.ndarray

    def validate(self):
        k = len(self.pi)
        if self.A.shape != (k, k) or self.B.shape[0] != k:
            raise ValueError("Dimensiones incompatibles")
        for p in (self.pi, self.A, self.B):
            if not np.all(np.isfinite(p)) or np.any(p < 0):
                raise ValueError("Probabilidades inválidas")
            if not np.allclose(p.sum(axis=-1), 1, atol=1e-12, rtol=0):
                raise ValueError("Las probabilidades deben sumar uno")
        return self


def forward(obs, model):
    """Filtrado causal escalado y log P(O|lambda); evita subdesbordamiento."""
    obs = np.asarray(obs, dtype=int)
    if len(obs) == 0 or np.any(obs < 0) or np.any(obs >= model.B.shape[1]):
        raise ValueError("Secuencia vacía o símbolos inválidos")
    alpha = np.empty((len(obs), len(model.pi)))
    scales = np.empty(len(obs))
    alpha[0] = model.pi * model.B[:, obs[0]]
    scales[0] = alpha[0].sum()
    if scales[0] <= 0:
        raise ValueError("Secuencia imposible bajo el modelo")
    alpha[0] /= scales[0]
    for t in range(1, len(obs)):
        alpha[t] = (alpha[t-1] @ model.A) * model.B[:, obs[t]]
        scales[t] = alpha[t].sum()
        if scales[t] <= 0:
            raise ValueError("Secuencia imposible bajo el modelo")
        alpha[t] /= scales[t]
    return float(np.log(scales).sum()), alpha, scales


def backward(obs, model, scales):
    beta = np.ones((len(obs), len(model.pi)))
    for t in range(len(obs)-2, -1, -1):
        beta[t] = model.A @ (model.B[:, obs[t+1]] * beta[t+1]) / scales[t+1]
    return beta


def viterbi(obs, model):
    """Ruta conjunta más probable; utiliza toda la secuencia (retrospectivo)."""
    with np.errstate(divide="ignore"):
        lp, la, lb = np.log(model.pi), np.log(model.A), np.log(model.B)
    delta = lp + lb[:, obs[0]]
    back = np.zeros((len(obs), len(lp)), dtype=int)
    for t in range(1, len(obs)):
        candidates = delta[:, None] + la
        back[t] = candidates.argmax(axis=0)
        delta = candidates.max(axis=0) + lb[:, obs[t]]
    path = np.empty(len(obs), dtype=int)
    path[-1] = delta.argmax()
    for t in range(len(obs)-2, -1, -1):
        path[t] = back[t+1, path[t+1]]
    return path, float(delta.max())


def stationary(A):
    """Distribución estacionaria de una matriz irreducible."""
    k = len(A)
    return np.linalg.lstsq(np.vstack([A.T-np.eye(k), np.ones(k)]),
                           np.r_[np.zeros(k), 1.], rcond=None)[0]


def baum_welch(sequences, initial, max_iter=60, tol=1e-5):
    """EM multissecuencia. No crea transiciones entre secuencias independientes.

    Se usan inicializaciones positivas. Solo hay un suelo numérico de 1e-12;
    no se emplean etiquetas reales ni datos de prueba para ajustar parámetros.
    """
    model = initial.validate()
    k, m = model.B.shape
    history = [sum(forward(o, model)[0] for o in sequences)]
    for _ in range(max_iter):
        pi_count, a_count, b_count = np.zeros(k), np.zeros((k, k)), np.zeros((k, m))
        for obs in sequences:
            _, alpha, c = forward(obs, model)
            beta = backward(obs, model, c)
            gamma = alpha * beta
            gamma /= gamma.sum(axis=1, keepdims=True)
            pi_count += gamma[0]
            xi = (alpha[:-1, :, None] * model.A[None, :, :]
                  * (model.B[:, obs[1:]].T * beta[1:])[:, None, :])
            xi /= xi.sum(axis=(1, 2), keepdims=True)
            a_count += xi.sum(axis=0)
            for symbol in range(m):
                b_count[:, symbol] += gamma[np.asarray(obs) == symbol].sum(axis=0)
        def norm(x):
            x = np.maximum(x, 1e-12)
            return x / x.sum(axis=-1, keepdims=True)
        candidate = HMM(norm(pi_count), norm(a_count), norm(b_count)).validate()
        ll = sum(forward(o, candidate)[0] for o in sequences)
        if ll < history[-1] - 1e-7:
            raise ArithmeticError("La verosimilitud EM disminuyó")
        improvement = ll - history[-1]
        model = candidate
        history.append(ll)
        if improvement < tol:
            break
    # Identificación semántica por severidad observable, sin mirar estados reales.
    order = np.argsort(model.B @ np.arange(m))
    model = HMM(model.pi[order], model.A[np.ix_(order, order)], model.B[order]).validate()
    return model, history

import itertools
import unittest
import numpy as np
from src.hmm import HMM, forward, backward, viterbi, baum_welch
from src.experiment import scenarios, simulate


class TestHMM(unittest.TestCase):
    def test_exact_enumeration(self):
        m=HMM(np.array([.6,.4]),np.array([[.7,.3],[.2,.8]]),np.array([[.8,.2],[.1,.9]])).validate()
        obs=np.array([0,1,1,0])
        probabilities=[]
        paths=list(itertools.product(range(2),repeat=4))
        for z in paths:
            p=m.pi[z[0]]*m.B[z[0],obs[0]]
            for i in range(1,4): p*=m.A[z[i-1],z[i]]*m.B[z[i],obs[i]]
            probabilities.append(p)
        ll,alpha,c=forward(obs,m)
        pred,score=viterbi(obs,m)
        self.assertAlmostEqual(np.exp(ll),sum(probabilities),places=13)
        np.testing.assert_array_equal(pred,paths[np.argmax(probabilities)])
        self.assertAlmostEqual(np.exp(score),max(probabilities),places=13)
        gamma=alpha*backward(obs,m,c)
        for t in range(4):
            for k in range(2):
                exact=sum(p for p,z in zip(probabilities,paths) if z[t]==k)/sum(probabilities)
                self.assertAlmostEqual(gamma[t,k],exact,places=12)

    def test_valid_parameters_and_seed(self):
        for sc in scenarios(): sc.model().validate()
        a=simulate(scenarios()[0],100,12)
        b=simulate(scenarios()[0],100,12)
        self.assertTrue(a.equals(b))
        self.assertFalse(a.equals(simulate(scenarios()[0],100,13)))
        with self.assertRaises(ValueError):
            HMM(np.ones(3),np.eye(3),np.ones((3,6))/6).validate()

    def test_empirical_emissions(self):
        # Control independiente de la fórmula analítica B.
        rng=np.random.default_rng(444)
        for sc in [scenarios()[0],scenarios()[2]]:
            for state in range(3):
                L=rng.lognormal(np.log(sc.medians[state]),sc.sigmas[state],100000)
                K=rng.binomial(100,sc.error_p[state],100000)
                symbols=2*np.digitize(L,[200,600])+(K>=3)
                observed=np.bincount(symbols,minlength=6)/len(symbols)
                np.testing.assert_allclose(observed,sc.model().B[state],atol=.007,rtol=0)

    def test_em_monotonic(self):
        sc=scenarios()[0]
        obs=[simulate(sc,200,i).symbol.to_numpy() for i in range(3)]
        initial=HMM(np.ones(3)/3,.8*np.eye(3)+.2/3,
                    np.random.default_rng(9).dirichlet(np.ones(6),size=3))
        fit,history=baum_welch(obs,initial,max_iter=12)
        fit.validate()
        self.assertTrue(np.all(np.diff(history)>=-1e-7))


if __name__=="__main__": unittest.main()

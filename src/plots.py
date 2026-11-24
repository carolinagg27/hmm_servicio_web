"""Figuras reproducibles: PNG a 300 dpi y PDF vectorial."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]


def make_plots(root):
    root = Path(root)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,
                        "axes.spines.right":False,"savefig.dpi":300,"pdf.fonttype":42})
    def save(fig, name):
        fig.savefig(root/"figures"/(name+".png"),dpi=300,bbox_inches="tight")
        fig.savefig(root/"figures"/(name+".pdf"),bbox_inches="tight")
        plt.close(fig)
    summary = pd.read_csv(root/"results/summary.csv")
    fig, axes = plt.subplots(1,2,figsize=(10,3.8),layout="constrained")
    for ax,metric,title in zip(axes,["accuracy","macro_f1"],["Exactitud","F1 macro"]):
        for i,method in enumerate(["Viterbi","Filtrado","Sin_memoria","Viterbi_base_fijo"]):
            sub=summary[(summary.method==method)&(summary.metric==metric)]
            x=np.arange(4)+(i-1.5)*.16
            ax.errorbar(x,sub["mean"],yerr=[sub["mean"]-sub.ci_low,sub.ci_high-sub["mean"]],
                        fmt="o",capsize=3,color=COLORS[i],label=method.replace("_"," "),markersize=4)
        ax.set_xticks(range(4),["E1\nBase","E2\nPersistencia","E3\nSolapamiento","E4\nInicio crítico"])
        ax.set_ylabel(title)
        ax.set_ylim(.25,1.01)
        ax.grid(axis="y",alpha=.2)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="outside lower center",ncol=4,fontsize=9)
    save(fig,"01_comparacion")
    df=pd.read_csv(root/"data/sequences.csv")
    sub=df[(df.scenario=="E2_persistencia")&(df.rep==0)&(df.t<300)]
    fig,axes=plt.subplots(3,1,figsize=(9,5.8),sharex=True,layout="constrained")
    axes[0].plot(sub.t,sub.latency_ms,color=COLORS[0],lw=.8)
    axes[0].axhline(200,color="gray",ls=":",lw=.8)
    axes[0].axhline(600,color="gray",ls=":",lw=.8)
    axes[0].set_ylabel("Latencia (ms)")
    axes[1].plot(sub.t,sub.errors_100,color=COLORS[1],lw=.8)
    axes[1].axhline(3,color="gray",ls=":",lw=.8)
    axes[1].set_ylabel("Errores / 100")
    axes[2].step(sub.t,sub.state,where="post",label="Estado real",lw=2,color="black",alpha=.6)
    axes[2].step(sub.t,sub.Viterbi,where="post",label="Viterbi",lw=1,color=COLORS[0],ls="--")
    axes[2].set_yticks([0,1,2],["Normal","Degradado","Crítico"])
    axes[2].set_xlabel("Minuto (E2, réplica 0, primeros 300 minutos)")
    axes[2].legend(loc="upper left",fontsize=8,ncol=2)
    for ax in axes: ax.grid(alpha=.2)
    save(fig,"02_secuencia")
    sen=pd.read_csv(root/"results/sensitivity_summary.csv")
    fig,ax=plt.subplots(figsize=(7,3.8),layout="constrained")
    for i,kind in enumerate(["A","B"]):
        q=sen[(sen.parameter==kind)&(sen.metric=="accuracy")]
        ax.plot(q.epsilon,q["mean"],"o-",color=COLORS[i],label=f"Perturbar {kind}")
        ax.fill_between(q.epsilon,q.ci_low,q.ci_high,color=COLORS[i],alpha=.15)
    ax.set(xlabel="ε en Mε = (1 − ε) M + ε U",ylabel="Exactitud de Viterbi",ylim=(0,1))
    ax.legend(); ax.grid(alpha=.2)
    save(fig,"03_sensibilidad")
    hist=pd.read_csv(root/"results/baum_welch_history.csv")
    fig,ax=plt.subplots(figsize=(7,3.5),layout="constrained")
    for i,q in hist.groupby("restart"):
        ax.plot(q.iteration,q.loglik,label=f"Reinicio {i}",color=COLORS[i])
    ax.set(xlabel="Iteración EM",ylabel="Log verosimilitud de entrenamiento")
    ax.legend(); ax.grid(alpha=.2)
    save(fig,"04_baum_welch")
    # Diagrama exacto del procedimiento, generado por código, sin IA de imágenes.
    fig,ax=plt.subplots(figsize=(8,2.25),layout="constrained")
    ax.set_xlim(0,10); ax.set_ylim(0,4); ax.axis("off")
    nodes=[(1.6,3,"Definir π, A y\ndistribuciones"),(5,3,"Simular estados,\nlatencia y errores"),
           (8.4,3,"Discretizar y\ncalcular B"),(8.4,1,"Inferir estados\ny comparar"),
           (5,1,"Repetir 50 veces\npor escenario"),(1.6,1,"Calcular IC y\nexportar CSV")]
    for x,y,label in nodes:
        ax.text(x,y,label,ha="center",va="center",bbox=dict(boxstyle="round,pad=.6",fc="#edf3f8",ec="#44647a"))
    for start,end in [((2.95,3),(3.65,3)),((6.35,3),(7.05,3)),((8.4,2.5),(8.4,1.5)),
                      ((7.05,1),(6.35,1)),((3.65,1),(2.95,1))]:
        ax.annotate("",xy=end,xytext=start,arrowprops={"arrowstyle":"->","color":"#44647a"})
    save(fig,"05_flujo")

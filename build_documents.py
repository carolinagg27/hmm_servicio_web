"""Construye artículo y guion desde los CSV ejecutados. Dependencia: python-docx.

Las ecuaciones se renderizan con Matplotlib para conservar la notación al abrir
el documento en Word o LibreOffice; sus fuentes LaTeX están en este archivo.
"""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"docs"
OUT.mkdir(exist_ok=True)
(OUT/"assets").mkdir(exist_ok=True)
SUM=pd.read_csv(ROOT/"results/summary.csv")
PROC=pd.read_csv(ROOT/"results/process_summary.csv")
LEARN=pd.read_csv(ROOT/"results/learned_summary.csv")
PARAM=json.loads((ROOT/"results/parameters.json").read_text())
LEARNED=json.loads((ROOT/"results/learned_model.json").read_text())
SOURCES=json.loads((ROOT/"references/sources.json").read_text())
CLAIMS=[]


def number(x,n=2): return f"{x:.{n}f}".replace(".",",")
def row(case,metric="accuracy",method="Viterbi"):
    return SUM[(SUM.scenario==case)&(SUM.metric==metric)&(SUM.method==method)].iloc[0]
def val(case,metric="accuracy",method="Viterbi",stat="mean",percent=True,n=2):
    r=row(case,metric,method); x=r[stat]*(100 if percent else 1)
    s=number(x,n)
    CLAIMS.append({"scenario":case,"metric":metric,"method":method,"stat":stat,
                   "percent":percent,"decimals":n,"formatted":s})
    return s
def pro(case,metric,percent=False,n=2):
    x=PROC[(PROC.scenario==case)&(PROC.metric==metric)].iloc[0]["mean"]
    return number(x*(100 if percent else 1),n)


def setup():
    d=Document()
    sec=d.sections[0]
    sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.top_margin=sec.bottom_margin=Inches(.75)
    sec.left_margin=sec.right_margin=Inches(.95)
    sec.header_distance=sec.footer_distance=Inches(.35)
    for name in ["Normal","Title","Subtitle","Heading 1","Heading 2","Caption"]:
        st=d.styles[name]
        st.font.name="Times New Roman";st.font.color.rgb=RGBColor(0,0,0)
        st.paragraph_format.line_spacing=1.5
        st.paragraph_format.space_after=Pt(3)
        for element in list(st.element.iter()):
            if element.tag==qn("w:pBdr"):
                element.getparent().remove(element)
            elif element.tag==qn("w:rFonts"):
                for key in list(element.attrib):
                    if "theme" in key.lower(): del element.attrib[key]
                for key in ["ascii","hAnsi","eastAsia","cs"]:element.set(qn("w:"+key),"Times New Roman")
    d.styles["Normal"].font.size=Pt(11)
    d.styles["Normal"].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    d.styles["Title"].font.size=Pt(16)
    d.styles["Title"].font.bold=True
    d.styles["Title"].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
    d.styles["Heading 1"].font.size=Pt(13)
    d.styles["Heading 2"].font.size=Pt(11.5)
    d.styles["Caption"].font.size=Pt(9)
    for name in ["Heading 1","Heading 2"]:
        d.styles[name].paragraph_format.space_before=Pt(6)
        d.styles[name].paragraph_format.keep_with_next=True
    footer=sec.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=footer.add_run();field=OxmlElement("w:fldSimple");field.set(qn("w:instr"),"PAGE");r._r.addnext(field)
    d.core_properties.author="Danny Stiven Agudelo Vásquez"
    d.core_properties.subject="Simulación de Ingeniería de Software"
    return d


def p(d,text,style=None):
    return d.add_paragraph(text,style)
def h(d,text,level=1):d.add_heading(text,level)
def new(d,title):
    q=d.add_heading(title,1)
    q.paragraph_format.page_break_before=True
def caption(d,text):
    q=p(d,text,"Caption");q.paragraph_format.keep_with_next=True
    return q
def table(d,headers,rows,widths=None,font=9.5):
    tb=d.add_table(rows=1,cols=len(headers));tb.autofit=False
    if widths:
        for col,w in zip(tb.columns,widths):col.width=Inches(w)
    for c,v in zip(tb.rows[0].cells,headers):c.text=str(v)
    for row_ in rows:
        for c,v in zip(tb.add_row().cells,row_):c.text=str(v)
    for i,r in enumerate(tb.rows):
        trpr=r._tr.get_or_add_trPr()
        cant=OxmlElement("w:cantSplit");trpr.append(cant)
        if i==0:
            repeat=OxmlElement("w:tblHeader");trpr.append(repeat)
        for j,c in enumerate(r.cells):
            if widths:c.width=Inches(widths[j])
            pr=c._tc.get_or_add_tcPr()
            margins=OxmlElement("w:tcMar")
            for edge in ["top","left","bottom","right"]:
                x=OxmlElement("w:"+edge);x.set(qn("w:w"),"65");x.set(qn("w:type"),"dxa");margins.append(x)
            pr.append(margins)
            borders=OxmlElement("w:tcBorders")
            for edge in ["top","left","bottom","right"]:
                x=OxmlElement("w:"+edge);x.set(qn("w:val"),"single");x.set(qn("w:sz"),"4");x.set(qn("w:color"),"D9D9D9");borders.append(x)
            pr.append(borders)
            sh=OxmlElement("w:shd");sh.set(qn("w:fill"),"DCE6F0" if i==0 else ("F4F6F8" if i%2==0 else "FFFFFF"));pr.append(sh)
            for q in c.paragraphs:
                q.paragraph_format.space_after=Pt(0)
                q.paragraph_format.line_spacing=1.5
                q.alignment=WD_ALIGN_PARAGRAPH.LEFT
                for run in q.runs:
                    run.font.name="Times New Roman";run.font.size=Pt(font);run.bold=i==0
    blank=p(d,"")
    blank.paragraph_format.space_after=Pt(0)
    blank.paragraph_format.line_spacing=Pt(2)
    blank.add_run(" ").font.size=Pt(1)
    return tb


def figure(d,name,width=6.4):
    q=d.add_paragraph();q.paragraph_format.space_after=Pt(2)
    q.alignment=WD_ALIGN_PARAGRAPH.CENTER
    q.add_run().add_picture(str(ROOT/"figures"/name),width=Inches(width))
def equation(d,latex,name):
    # Ecuación legible a 300 dpi, con tamaño físico derivado del lienzo.
    fig=plt.figure(figsize=(10,.5));fig.text(.01,.5,"$"+latex+"$",fontsize=12,va="center")
    path=OUT/"assets"/(name+".png")
    fig.savefig(path,dpi=300,bbox_inches="tight",pad_inches=.035,transparent=True);plt.close(fig)
    w=Image.open(path).width/300
    q=d.add_paragraph();q.alignment=WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after=Pt(3)
    q.add_run().add_picture(str(path),width=Inches(min(w,6.5)))


def article():
    d=setup()
    d.core_properties.title="Inferencia del estado operativo de un servicio web mediante un modelo oculto de Markov"
    p(d,d.core_properties.title,"Title")
    q=p(d,"Danny Stiven Agudelo Vásquez · Ingeniería de Sistemas\nSimulación de Ingeniería de Software · 6 de noviembre de 2026")
    q.alignment=WD_ALIGN_PARAGRAPH.CENTER
    h(d,"Resumen")
    abstract=("La latencia y los errores de un servicio web no revelan de manera inequívoca su condición operativa. "
    "Este estudio evalúa un modelo oculto de Markov de tres estados, normal, degradado y crítico, mediante un experimento sintético reproducible. "
    "Se generan latencias lognormales y conteos binomiales de errores; su discretización produce seis símbolos y una matriz de emisión calculada analíticamente. "
    "Se implementan Forward escalado, Viterbi y Baum-Welch en Python. Se comparan cuatro escenarios con 50 réplicas de 1440 minutos cada uno, "
    "incluyendo cambios de transición, solapamiento de emisiones y distribución inicial. Se evalúan exactitud, F1 macro, sensibilidad al estado crítico "
    "y falsas alarmas, con intervalos de confianza entre réplicas. "
    f"La exactitud media de Viterbi es {val('E1_base')} % en el escenario base y {val('E3_solapamiento')} % con mayor solapamiento. "
    f"En este último, conservar las emisiones originales reduce la exactitud a {val('E3_solapamiento',method='Viterbi_base_fijo')} %. "
    "Un ajuste sin etiquetas obtiene resultados cercanos al modelo conocido en datos de prueba independientes. Dos ejecuciones reproducen exactamente los CSV científicos. "
    "El aporte consiste en un banco experimental auditable que relaciona supuestos probabilísticos, inferencia temporal e incertidumbre estadística. "
    "Los resultados describen el simulador y no demuestran eficacia en producción; requieren validación externa con telemetría real.")
    assert 150<=len(abstract.split())<=250
    p(d,abstract)
    p(d,"Palabras clave: modelo oculto de Markov; simulación estocástica; observabilidad; detección de anomalías; reproducibilidad.")
    h(d,"1 Introducción")
    p(d,"Un aumento aislado de latencia puede corresponder a variación normal, mientras una sucesión de errores puede indicar deterioro persistente. "
      "La tarea consiste en inferir una condición operativa no observada directamente, sin confundir una medición ruidosa con el estado del sistema. "
      "La diversidad de detectores y los sesgos de evaluación descritos en [1]–[3] justifican estudiar primero una solución transparente y contrastable.")
    p(d,"El objetivo general es construir y evaluar un HMM reproducible. Los objetivos específicos son formular sus probabilidades, implementar inferencia y aprendizaje, "
      "cuantificar variación entre escenarios y examinar sensibilidad. El alcance es un servicio agregado, con muestreo por minuto y datos sintéticos; "
      "no incluye localización causal, predicción de incidentes futuros ni decisiones automáticas de recuperación.")

    # Página 2
    new(d,"2 Estado del arte")
    p(d,"Se realizó una revisión dirigida de publicaciones entre el 6 de noviembre de 2021 y el 6 de noviembre de 2026. "
      "Las búsquedas combinaron time series anomaly detection, software reliability, hidden Markov model y microservices. "
      "Se priorizaron actas, editoriales y versiones de autores con identificadores verificables. Se seleccionaron diez trabajos de 2022–2025 "
      "por su relación con modelado temporal, evaluación reproducible o monitoreo de software. No se presenta esta selección como una revisión sistemática exhaustiva.")
    p(d,"Anomaly Transformer [4], TranAD [5] y DCdetector [6] ilustran modelos de representación temporal complejos. "
      "TimeEval [7] aporta infraestructura de evaluación; TimeSeriesBench [8] introduce exigencias de uso industrial. "
      "Nezha [9] estudia causas de fallos con varias fuentes de observabilidad y Wang et al. [10] organizan las familias recientes de métodos. "
      "La tabla 1 sintetiza la utilidad de estos antecedentes para el diseño del experimento.")
    caption(d,"Tabla 1. Comparación de publicaciones recientes, parte 1 de 2.")
    table(d,["Trabajo y año","Enfoque o evidencia","Implicación para este estudio"],
          [[s["short"]+"\n"+str(s["year"]),s["method"],s["contribution"]] for s in SOURCES[:5]],
          [1.15,2.55,2.9],font=10)
    p(d,"La literatura no permite atribuir una ventaja universal a un detector. Los resultados dependen de la definición de anomalía, "
      "la composición de los datos y las métricas. Por ello, el experimento compara métodos sobre las mismas secuencias y conserva "
      "los errores de clasificación por minuto, sin transformar un acierto aislado en la detección completa de un episodio.")

    # Página 3
    new(d,"2 Estado del arte y alcance del aporte")
    caption(d,"Tabla 1. Comparación de publicaciones recientes, parte 2 de 2.")
    table(d,["Trabajo y año","Enfoque o evidencia","Implicación para este estudio"],
          [[s["short"]+"\n"+str(s["year"]),s["method"],s["contribution"]] for s in SOURCES[5:10]],
          [1.15,2.55,2.9],font=10)
    h(d,"2.1 Vacío delimitado",2)
    p(d,"La oportunidad que aborda este trabajo es metodológica y didáctica: disponer de un caso pequeño donde se conozca la verdad latente "
      "y pueda seguirse toda la cadena desde las distribuciones generadoras hasta los intervalos de confianza. Los antecedentes seleccionados "
      "no constituyen por sí mismos ese experimento concreto de tres estados, seis símbolos y perturbaciones controladas. "
      "Esto no prueba que el problema nunca haya sido investigado ni que el algoritmo propuesto sea nuevo.")
    p(d,"Existe un antecedente directo fuera de la ventana reciente: Samir y Pahl [11] emplean un HMM jerárquico en clústeres de contenedores. "
      "Su inclusión evita presentar la aplicación de Markov al monitoreo como una originalidad absoluta. Aquí se reduce el alcance a un HMM "
      "categórico interpretable, con experimentos que un estudiante puede ejecutar y revisar sin infraestructura distribuida.")
    h(d,"2.2 Verificación bibliográfica",2)
    p(d,"Las referencias recientes se verificaron mediante fuentes editoriales, actas oficiales o registros de los autores; las rutas y el nivel de acceso "
      "se documentan en references/sources.json. Algunas páginas bloquearon la apertura directa y se contrastaron con sus PDF o registros indexados. "
      "No se contó con acceso autenticado a Scopus, Web of Science ni IEEE Xplore; por tanto, no se certifican indexación individual, cuartiles ni revisión íntegra "
      "de todos los textos. Las fuentes [11] y [12] son antecedentes históricos adicionales y no integran el mínimo de diez publicaciones recientes.")

    # Página 4
    new(d,"3 Marco teórico")
    h(d,"3.1 Probabilidad y variables observadas",2)
    p(d,"Una distribución asigna probabilidades a resultados posibles. En este caso, la distribución categórica permite sortear un estado; "
      "la binomial describe el número de errores en un conjunto de solicitudes y la lognormal representa una latencia positiva con asimetría a la derecha. "
      "Estas familias constituyen supuestos de diseño, no ajustes a mediciones de un proveedor. Sus parámetros se eligen para separar niveles operativos "
      "y luego se alteran deliberadamente para estudiar condiciones menos favorables.")
    equation(d,r"Z_0\sim\mathrm{Cat}(\pi),\quad Z_t\mid Z_{t-1}=i\sim\mathrm{Cat}(A_{i,:})","eq_states")
    equation(d,r"\ln L_t\mid Z_t=i\sim\mathcal{N}(\ln m_i,\sigma_i^2),\quad K_t\mid Z_t=i\sim\mathrm{Bin}(100,p_i)","eq_emissions")
    p(d,"L representa una solicitud de sondeo por minuto, no la media ni el percentil 95 de cien solicitudes. K cuenta errores en otras cien "
      "solicitudes del mismo intervalo. Se supone independencia entre el sondeo y el conteo una vez conocido el estado. "
      "La mediana de L es m y su esperanza es m exp(σ²/2); la media y varianza de K son 100p y 100p(1−p). "
      "La diferencia entre mediana y media es relevante para interpretar los promedios de latencia exportados.")
    h(d,"3.2 Estados ocultos y propiedad de Markov",2)
    p(d,"El estado Z es una condición latente definida por el régimen generador. Una observación alta no obliga a clasificar el estado como crítico: "
      "las distribuciones se superponen. El símbolo O se obtiene de L y K y es el único dato que recibe el HMM. "
      "Las etiquetas reales se conservan exclusivamente para evaluar el simulador, no para inferir estados ni ajustar Baum-Welch.")
    equation(d,r"P(Z_t=j\mid Z_{t-1}=i,Z_{t-2},\ldots)=P(Z_t=j\mid Z_{t-1}=i)=a_{ij}","eq_markov")
    p(d,"El modelo es homogéneo: A y B permanecen constantes dentro de cada escenario. Las emisiones son independientes entre minutos "
      "condicionadas a la trayectoria de estados. La duración de un estado sigue una distribución geométrica, con esperanza 1/(1−aᵢᵢ). "
      "No se fija una duración mínima superior a un intervalo ni memoria explícita de cuánto tiempo lleva degradado el servicio. Estas restricciones facilitan "
      "la interpretación, pero pueden ser inadecuadas para incidentes con recuperación programada o cargas estacionales.")

    # Página 5
    new(d,"3 Marco teórico de los algoritmos")
    p(d,"La estructura clásica del HMM y sus tres tareas de evaluación, decodificación y aprendizaje se desarrollan en [12]. "
      "Las siguientes ecuaciones fijan la notación de la implementación. Para T observaciones se emplean índices de 0 a T−1.")
    equation(d,r"P(z,o\mid\lambda)=\pi_{z_0}b_{z_0,o_0}\prod_{t=1}^{T-1}a_{z_{t-1},z_t}b_{z_t,o_t},\quad\lambda=(\pi,A,B)","eq_joint")
    h(d,"3.3 Forward y filtrado causal",2)
    equation(d,r"\alpha_0(j)=\pi_j b_{j,o_0},\quad\alpha_t(j)=b_{j,o_t}\sum_i\alpha_{t-1}(i)a_{ij}","eq_forward")
    p(d,"Forward suma las probabilidades de las rutas compatibles y evalúa la verosimilitud de las observaciones. En el código se normaliza "
      "cada vector por un factor c; la log verosimilitud es la suma de log(c). Así se evita multiplicar cantidades que terminarían redondeadas a cero. "
      "El vector normalizado representa P(Zₜ|O₀:ₜ); tomar su máximo produce una decisión causal que solo utiliza información disponible hasta ese minuto.")
    h(d,"3.4 Viterbi",2)
    equation(d,r"\delta_t(j)=\log b_{j,o_t}+\max_i\{\delta_{t-1}(i)+\log a_{ij}\}","eq_viterbi")
    p(d,"Viterbi reemplaza la suma por un máximo, guarda predecesores y reconstruye la ruta conjunta más probable. "
      "Se inicializa con log(π) + log(B para la primera observación). La ruta usa observaciones posteriores al instante que clasifica, "
      "por lo que se evalúa como análisis retrospectivo. Maximizar la probabilidad de toda una ruta no garantiza maximizar "
      "el número de minutos correctos ni el recall de episodios críticos. Forward y Viterbi requieren tiempo O(T·|S|²).")
    h(d,"3.5 Baum Welch",2)
    equation(d,r"a'_{ij}=\frac{\sum_r\sum_{t=0}^{T_r-2}\xi^{(r)}_t(i,j)}{\sum_r\sum_{t=0}^{T_r-2}\gamma^{(r)}_t(i)},\quad b'_{jk}=\frac{\sum_r\sum_t\gamma^{(r)}_t(j)\,\mathbf{1}(o^{(r)}_t=k)}{\sum_r\sum_t\gamma^{(r)}_t(j)}","eq_bw")
    p(d,"El paso E calcula γ, probabilidad posterior de cada estado, y ξ, probabilidad posterior de cada transición, mediante Forward y Backward. "
      "El paso M normaliza esos conteos esperados; π se actualiza promediando γ del inicio de cada secuencia. "
      "El proceso aumenta o mantiene la verosimilitud, pero puede alcanzar óptimos locales. Por eso se comparan tres inicializaciones "
      "y se conserva la de mayor verosimilitud de entrenamiento. No se agregan transiciones entre secuencias independientes.")

    # Página 6
    new(d,"4 Metodología y formulación del modelo")
    h(d,"4.1 Conjuntos y discretización",2)
    p(d,"Se define S = {Normal, Degradado, Crítico}, codificado como {0, 1, 2}. V = {v₀, …, v₅} combina tres bandas de latencia "
      "y dos bandas de errores. Baja significa L < 200 ms; media, 200 ≤ L < 600 ms; alta, L ≥ 600 ms. Pocos errores significa K ≤ 2 "
      "y muchos errores, K ≥ 3. El orden es baja/pocos, baja/muchos, media/pocos, media/muchos, alta/pocos y alta/muchos. "
      "Los cortes son elecciones pedagógicas previas al experimento, no acuerdos de nivel de servicio universales.")
    caption(d,"Tabla 2. Parámetros generadores base por estado.")
    table(d,["Estado","Mediana L en ms","σ del logaritmo","p de error"],
          [["Normal","100","0,40","0,005"],["Degradado","300","0,45","0,030"],["Crítico","900","0,50","0,120"]],
          [1.5,1.7,1.7,1.7],font=10)
    p(d,"La distribución inicial es π = (0,90; 0,08; 0,02). Favorece un arranque sano, sin excluir arranques adversos. "
      "La matriz A permite recuperación, empeoramiento y saltos directos poco frecuentes. Sus filas indican el estado actual y sus columnas el siguiente.")
    caption(d,"Tabla 3. Matriz de transición A del escenario base.")
    table(d,["Desde / hacia","Normal","Degradado","Crítico"],
          [[name]+[number(v,3) for v in r] for name,r in zip(["Normal","Degradado","Crítico"],PARAM["E1_base"]["A"])],[1.8,1.6,1.6,1.6],font=10)
    caption(d,"Tabla 4. Matriz de emisión B base con columnas ordenadas como V.")
    table(d,["Estado","v₀","v₁","v₂","v₃","v₄","v₅"],
          [[name]+[f"{v:.4g}" for v in r] for name,r in zip(["Normal","Degradado","Crítico"],PARAM["E1_base"]["B"])],
          [1.05,.925,.925,.925,.925,.925,.925],font=9)
    p(d,"B no se asigna por intuición ni se estima con los datos de prueba: se deriva de las distribuciones. "
      "Para cada estado, la probabilidad de una banda de latencia se multiplica por la de la banda de errores. "
      "El cálculo usa diferencias de la CDF lognormal y la CDF binomial. Las tablas redondean; el programa conserva precisión de coma flotante.")

    # Página 7
    new(d,"4 Metodología y diseño experimental")
    equation(d,r"b_{i,(\ell,e)}=[F_i(u_\ell)-F_i(l_\ell)]\,P(K_t\in E_e\mid Z_t=i)","eq_b")
    p(d,"Las bandas particionan los dominios de L y K. Por ello B es no negativa y cada fila suma uno. "
      "El código comprueba finitud, no negatividad y sumas de π, A y B con tolerancia absoluta 10⁻¹². "
      "La matriz base implica permanencias esperadas de 25, 5 y 4 minutos. Su distribución estacionaria es "
      "(0,76190; 0,18571; 0,05238); π describe el comienzo y no debe confundirse con esta ocupación a largo plazo.")
    caption(d,"Tabla 5. Cuatro escenarios y factores modificados.")
    table(d,["Escenario","Cambio respecto a E1","Propósito"],[
      ["E1 Base","A, π y emisiones base","Referencia controlada"],
      ["E2 Persistencia","Solo A cambia según tabla 6","Mayor ocupación y duración del estado crítico"],
      ["E3 Solapamiento","m = (140, 240, 400), σ = (0,65, 0,65, 0,65), p = (0,015, 0,030, 0,060)","Menor separación entre emisiones"],
      ["E4 Inicio crítico","Solo π cambia a (0,05; 0,15; 0,80)","Efecto transitorio de las condiciones iniciales"]],
      [1.25,3.45,1.9],font=9.5)
    caption(d,"Tabla 6. A del escenario E2 con filas y columnas Normal, Degradado y Crítico.")
    table(d,["Desde / hacia","Normal","Degradado","Crítico"],
          [[name]+[number(v,2) for v in r] for name,r in zip(["Normal","Degradado","Crítico"],PARAM["E2_persistencia"]["A"])],
          [1.8,1.6,1.6,1.6],font=10)
    p(d,"Cada escenario contiene 50 trayectorias de 1440 minutos: 288 000 observaciones de prueba en total. "
      "No se elimina un calentamiento porque interesa observar el arranque. La semilla de la réplica r es 20261106 + r, con r entre 0 y 49. "
      "Se reutiliza por escenario y se separan flujos para estados, latencia y errores mediante SeedSequence. Las réplicas son independientes "
      "dentro de cada escenario; entre escenarios hay un acoplamiento deliberado por números aleatorios comunes. E1 y E3 comparten exactamente "
      "la trayectoria latente y solo difieren en las emisiones.")

    # Página 8
    new(d,"4 Procedimiento y análisis estadístico")
    caption(d,"Figura 1. Fases ejecutadas del experimento.")
    figure(d,"05_flujo.png",6.1)
    h(d,"4.2 Pseudocódigo y comparadores",2)
    code=("PARA cada escenario y réplica r\n"
          "  Crear tres flujos aleatorios con semilla 20261106 + r\n"
          "  Sortear Z[0] con π y Z[t] con la fila A[Z[t−1]]\n"
          "  Generar L[t] y K[t]; discretizar en O[t]\n"
          "  Ejecutar Forward, Viterbi y clasificador sin memoria\n"
          "  Ejecutar Viterbi con parámetros base fijos\n"
          "  Comparar predicciones con Z; guardar CSV\n"
          "FIN; resumir métricas entre 50 réplicas y dibujar figuras")
    q=p(d,code);q.paragraph_format.line_spacing=1.5;q.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for r in q.runs:r.font.name="Consolas";r.font.size=Pt(9)
    p(d,"Los modelos conocidos usan los parámetros generadores de cada escenario y constituyen una referencia favorable, de tipo oráculo. "
      "El clasificador sin memoria elige el máximo de qⱼbⱼₒ, donde q es la distribución estacionaria de A. "
      "El filtrado emplea el pasado disponible; Viterbi utiliza toda la secuencia. El comparador base fijo conserva π, A y B de E1 "
      "en los cuatro escenarios y permite medir desajuste de especificación.")
    h(d,"4.3 Métricas e incertidumbre",2)
    p(d,"Se calculan exactitud, F1 macro de las tres clases, recall crítico y tasa de falsos positivos críticos. F1 por clase es "
      "2TP/(2TP+FP+FN); F1 macro es su promedio. Recall crítico divide críticos detectados entre críticos reales. "
      "La tasa de falsos positivos divide predicciones críticas erróneas entre minutos realmente no críticos. "
      "Un denominador inexistente en recall produce un valor ausente; una clase sin soporte de F1 recibe cero. Se exporta el número efectivo de réplicas.")
    equation(d,r"IC_{95\%}(\bar{x})=\bar{x}\pm t_{0.975,49}\frac{s}{\sqrt{50}},\quad t_{0.975,49}=2.0096","eq_ci")
    p(d,"La unidad de análisis es la trayectoria completa, no cada minuto correlacionado. Se informa media, desviación estándar muestral, "
      "mínimo, máximo e IC de la media. Las diferencias de métodos se calculan por réplica antes de resumirlas. "
      "Los IC t son aproximados y marginales, sin ajuste por comparaciones múltiples; se interpretan de forma exploratoria, "
      "no como intervalos de predicción de una futura trayectoria.")

    # Página 9
    new(d,"5 Resultados de la simulación")
    caption(d,"Tabla 7. Exactitud de Viterbi en porcentaje, 50 réplicas por escenario.")
    table(d,["Escenario","Media","DE","Mínimo","Máximo","IC 95 % de la media"],
          [[case.split("_")[0]]+[val(case,stat=s) for s in ["mean","std","min","max"]]+[
              val(case,stat="ci_low")+"–"+val(case,stat="ci_high")] for case in PARAM],
          [1.05,.8,.8,.85,.85,2.25],font=10)
    caption(d,"Figura 2. Comparación de métodos con IC 95 % entre réplicas.")
    figure(d,"01_comparacion.png")
    p(d,f"En E1, Viterbi obtiene {val('E1_base')} % de exactitud, frente a {val('E1_base',method='Filtrado')} % del filtrado "
      f"y {val('E1_base',method='Sin_memoria')} % del clasificador sin memoria. La diferencia pareada frente a este último es "
      "4,67 puntos porcentuales, con IC 95 % de 4,48 a 4,85 puntos. El resultado evidencia utilidad de la dependencia temporal "
      "dentro del proceso generador estudiado; no establece superioridad frente a detectores neuronales que no fueron ejecutados.")
    p(d,f"La exactitud de E2 es {val('E2_persistencia')} %, inferior a E1, pero su F1 macro es {val('E2_persistencia','macro_f1',percent=False,n=3)}, "
      f"mayor que {val('E1_base','macro_f1',percent=False,n=3)}. La composición de clases cambia y desaconseja juzgar los escenarios "
      "con una sola métrica. En E3, la menor separación entre emisiones reduce tanto la exactitud como F1 macro. "
      "Las tablas detalladas para todos los métodos y métricas están en results/summary.csv.")
    p(d,"La etiqueta Viterbi en las figuras corresponde al modelo con parámetros conocidos del escenario. "
      "Viterbi base fijo es el modelo desajustado; en E1 ambos coinciden por construcción. Los símbolos de algunos IC "
      "se superponen porque las diferencias son pequeñas, no porque se hayan eliminado réplicas.")

    # Página 10
    new(d,"5 Secuencias y comportamiento del servicio")
    caption(d,"Figura 3. Fragmento predeterminado de E2, réplica 0, minutos 0 a 299.")
    figure(d,"02_secuencia.png",6.05)
    caption(d,"Tabla 8. Medias entre réplicas de las características del proceso.")
    table(d,["Escenario","Latencia media ms","Errores %","Tiempo crítico %"],
          [[c.split("_")[0],pro(c,"latency_mean_ms"),pro(c,"error_rate",True),pro(c,"critical_fraction",True)] for c in PARAM],
          [1.05,2,1.65,1.9],font=9.5)
    p(d,"La figura muestra oscilaciones de las observaciones dentro de un mismo estado y diferencias puntuales entre trayectoria real "
      "e inferida. Se eligió de antemano la primera réplica, sin buscar el caso visualmente más favorable. "
      "Los estados degradado y crítico pueden compartir latencias medias; el historial y los errores aportan información adicional.")
    p(d,f"E2 aumenta la ocupación crítica de {pro('E1_base','critical_fraction',True)} % a {pro('E2_persistencia','critical_fraction',True)} %. "
      "La probabilidad estacionaria crítica prevista en E2 es 41,14 %, compatible con la variación entre trayectorias. "
      "No significa que un servicio real pase esa proporción de tiempo caído: es una consecuencia de la matriz de estrés seleccionada. "
      "El escenario base tampoco pretende describir un objetivo de disponibilidad comercial.")

    # Página 11
    new(d,"5 Sensibilidad a las emisiones y las condiciones iniciales")
    caption(d,"Figura 4. Perturbación aislada de matrices del decodificador sobre las mismas secuencias E1.")
    figure(d,"03_sensibilidad.png",6.15)
    p(d,"Se aplica Mε = (1−ε)M + εU, donde M es A o B y U tiene filas uniformes de tres o seis elementos. "
      "Los valores de ε son 0; 0,10; 0,25; 0,50; 0,75 y 1. Los datos generados no cambian. "
      "Esta prueba mide sensibilidad a parámetros erróneos del decodificador, mientras E2 y E3 modifican el propio proceso. "
      "Con ε = 0,50, perturbar A produce 96,17 % de exactitud y perturbar B produce 91,00 %. "
      "Cuando B es uniforme, las observaciones dejan de distinguir estados y la exactitud queda en 76,60 % por el predominio de Normal.")
    p(d,f"En E3, usar B adaptada al escenario da {val('E3_solapamiento')} % de exactitud; mantener el modelo base da "
      f"{val('E3_solapamiento',method='Viterbi_base_fijo')} %. La diferencia pareada es 18,04 puntos, con IC 95 % de 17,10 a 18,97. "
      f"Incluso con parámetros conocidos, el recall crítico es solo {val('E3_solapamiento','critical_recall')} %. "
      "La inferencia temporal no puede reconstruir información que las emisiones apenas distinguen. E3 modifica conjuntamente mediana, "
      "dispersión y probabilidad de error; esta comparación no identifica la contribución causal individual de cada componente.")
    h(d,"5.1 Separación del efecto inicial",2)
    p(d,"El arranque crítico E4 eleva el tiempo crítico durante los primeros 30 minutos de 4,47 % a 18,33 %, "
      "pero la ocupación de todo el día cambia de 5,04 % a 5,33 %. En otra prueba se conservan los datos E1 y se cambia "
      "solo el prior del filtrado: la exactitud de los primeros cinco minutos pasa de 96,80 % con π base a 93,60 % con π crítico; "
      "para el día completo pasa de 95,36 % a 95,35 %. La evidencia indica un efecto principalmente transitorio en esta configuración. "
      "No demuestra insensibilidad general: trayectorias breves, emisiones poco informativas o cadenas casi absorbentes podrían depender mucho más del arranque.")

    # Página 12
    new(d,"5 Aprendizaje de parámetros sin etiquetas")
    p(d,"Baum-Welch se ajustó con ocho secuencias adicionales de 600 minutos, semillas 900000–900007. "
      "Las semillas de inicialización fueron 700000–700002. No se emplearon estados reales para entrenar ni resultados de prueba "
      "para seleccionar el reinicio. Al final, las clases se ordenaron por el valor esperado del índice del símbolo, de menor a mayor severidad. "
      "Esta convención resuelve la permutación de etiquetas bajo el orden supuesto, pero no garantiza una semántica operativa universal.")
    caption(d,"Figura 5. Evolución de la log verosimilitud en tres reinicios de Baum-Welch.")
    figure(d,"04_baum_welch.png",5.9)
    caption(d,"Tabla 9. Modelo aprendido y oráculo evaluados en las mismas 50 secuencias E1.")
    lr=LEARN.set_index("metric")
    table(d,["Modelo","Exactitud % e IC 95 %","F1 macro","Recall crítico %"],[
      ["Parámetros conocidos",val("E1_base")+" ["+val("E1_base",stat="ci_low")+"; "+val("E1_base",stat="ci_high")+"]",
       val("E1_base","macro_f1",percent=False,n=3),val("E1_base","critical_recall")],
      ["Baum-Welch",number(lr.loc["accuracy","mean"]*100)+" ["+number(lr.loc["accuracy","ci_low"]*100)+"; "+number(lr.loc["accuracy","ci_high"]*100)+"]",
       number(lr.loc["macro_f1","mean"],3),number(lr.loc["critical_recall","mean"]*100)]],
      [1.5,2.8,1.1,1.2],font=9.5)
    p(d,"El reinicio 2 obtuvo la mayor log verosimilitud de entrenamiento, −3012,226720. Los tres reinicios "
      "alcanzaron el límite de 60 iteraciones sin satisfacer la tolerancia absoluta de mejora de 10⁻⁵. "
      "Las curvas fueron no decrecientes, pero no se afirma convergencia estricta ni optimalidad global. "
      "Las matrices completas y el historial por iteración se entregan en los archivos JSON y CSV.")
    p(d,"Las ocho secuencias de entrenamiento comenzaron en Normal, de modo que el π estimado quedó prácticamente concentrado "
      "en ese estado. Esto muestra la debilidad de estimar probabilidades iniciales con pocos comienzos, incluso cuando hay miles de minutos. "
      "Los IC de la tabla reflejan variación de prueba condicionada a un único ajuste seleccionado; no incluyen incertidumbre "
      "por nuevos conjuntos de entrenamiento. Una evaluación de esa variación exigiría repetir también todo el entrenamiento.")

    # Página 13
    new(d,"6 Discusión")
    h(d,"6.1 Interpretación y contraste con la literatura",2)
    p(d,"Los resultados apoyan la conveniencia de modelar persistencia cuando el proceso contiene regímenes que duran varios minutos. "
      "Esta observación es compatible con el interés por relaciones temporales de [4]–[6], aunque el experimento no compara arquitecturas "
      "ni reproduce sus benchmarks. La elección de una línea base sencilla y el énfasis en protocolos comparables siguen las preocupaciones "
      "metodológicas de [1]–[3] y [7]. No es válido comparar directamente los porcentajes de este simulador con los reportados en esos trabajos.")
    p(d,"Los resultados desajustados de E3 ilustran por qué un despliegue debe vigilar cambios de distribución, una preocupación abordada "
      "desde escenarios industriales en [8]. Sin embargo, conocer B nueva en una simulación es mucho más fácil que estimarla en producción. "
      "Asimismo, clasificar el estado de un servicio no identifica si el fallo proviene de CPU, red, base de datos o código. "
      "El análisis multimodal de [9] tiene un objetivo distinto. La taxonomía de [10] ayuda a ubicar estas diferencias de tarea y de información disponible.")
    p(d,f"En E1, Viterbi tiene recall crítico de {val('E1_base','critical_recall')} % y falsos positivos críticos de "
      f"{val('E1_base','critical_fpr')} %. El filtrado alcanza {val('E1_base','critical_recall',method='Filtrado')} % "
      f"y {val('E1_base','critical_fpr',method='Filtrado')} %, respectivamente. "
      "La mayor exactitud retrospectiva no equivale a mejor sensibilidad para todas las alarmas. Una política operativa debe ponderar "
      "el costo de omitir un incidente frente al costo de una falsa alerta; no basta con elegir el mayor porcentaje global.")
    h(d,"6.2 Validez interna y reproducibilidad",2)
    p(d,"La validación incluye enumeración exhaustiva de un HMM pequeño para comprobar Forward y Viterbi, contraste de posteriores "
      "Forward–Backward y comprobación Monte Carlo independiente de B. Se validaron 4000 métricas individuales recalculadas "
      "desde las predicciones exportadas, sus resúmenes, la discretización y la separación de semillas. Dos ejecuciones completas "
      "produjeron 20 archivos científicos CSV/JSON idénticos mediante SHA-256. La evidencia está en results/validation.json y los registros de ejecución.")
    h(d,"6.3 Limitaciones y validez externa",2)
    p(d,"El generador comparte familia matemática con el oráculo, lo que favorece su ajuste. No hay telemetría real, pérdida de observaciones, "
      "estacionalidad, tráfico variable ni dependencia residual entre errores y latencia. La discretización descarta magnitudes dentro de las bandas. "
      "Las duraciones geométricas y la homogeneidad temporal simplifican las averías. No se midieron latencia de alerta por episodio, calibración "
      "de probabilidades ni costo de ejecución en producción. Los IC son aproximaciones t sobre 50 réplicas y no garantizan cobertura bajo otras distribuciones.")
    p(d,"La reproducción exacta se comprobó en Linux con Python 3.12.14 y versiones fijadas. "
      "No se probó una instalación limpia en Windows. Otros entornos pueden introducir diferencias numéricas. "
      "El paquete está preparado para GitHub, pero no se publicó en una cuenta remota.")

    # Página 14
    new(d,"7 Conclusiones y trabajo futuro")
    p(d,"Se construyó una implementación pequeña y verificable de simulación, inferencia y aprendizaje HMM. "
      "El resultado central es condicional: las emisiones informativas y una estructura temporal apropiada permiten reconstruir "
      "estados con alta exactitud en el simulador; el solapamiento y la especificación errónea reducen esa capacidad, especialmente "
      "para la clase crítica. El aporte es un protocolo experimental y un conjunto de artefactos auditables, no un algoritmo nuevo ni "
      "una demostración de calidad editorial Q1.")
    h(d,"7.1 P1 Cómo se representa el problema mediante un HMM",2)
    p(d,"Los tres estados operativos forman la cadena latente Z. π representa la incertidumbre sobre el comienzo; A expresa las probabilidades "
      "de permanencia, deterioro y recuperación; B conecta cada estado con seis observaciones de latencia y errores. "
      "El estado no se determina mediante un umbral único: se infiere probabilísticamente de una secuencia. Forward permite filtrar con "
      "información causal y Viterbi recuperar una trayectoria retrospectiva. Baum-Welch muestra cómo estimar parámetros sin etiquetas de estado.")
    h(d,"7.2 P2 Cómo influyen los parámetros y las distribuciones",2)
    p(d,"A modifica las duraciones y la ocupación: la proporción crítica media subió de 5,04 % en E1 a 40,35 % en E2. "
      "Las medianas, dispersiones y probabilidades de error determinan B y la separabilidad. En E3, la exactitud pasó de 97,31 % "
      "a 86,95 % respecto a E1, mientras el recall crítico quedó en 49,17 %. Conservar el modelo base en E3 redujo la exactitud a 68,92 %. "
      "Estos resultados distinguen dificultad intrínseca de observación y error de especificación del decodificador.")
    h(d,"7.3 P3 Qué tan reproducible y sensible es el modelo",2)
    p(d,"La reproducción fue exacta para los 20 archivos científicos comparados, usando las mismas semillas, versiones y entorno. "
      "La sensibilidad depende del componente alterado. Un prior adverso afectó principalmente los primeros minutos; la perturbación "
      "de B tuvo mayor impacto que la de A en la rejilla estudiada. Esto no implica robustez universal ni permite extrapolar a otro servicio. "
      "El código, las matrices, las semillas, los CSV y las pruebas permiten revisar cada conclusión sin depender del texto del artículo.")
    h(d,"7.4 Trabajo futuro",2)
    p(d,"La siguiente etapa debe recoger telemetría real y definir estados con criterios operativos externos al simulador. "
      "Conviene evaluar nuevas jornadas en orden temporal, ajustar umbrales solo con entrenamiento y medir demora de detección por episodio. "
      "También se propone repetir conjuntos completos de entrenamiento, estudiar dependencia entre variables y probar emisiones continuas "
      "o duraciones semimarkovianas. Cada extensión debería compararse con la implementación actual para justificar su complejidad.")

    new(d,"Referencias")
    for s in SOURCES[:6]:p(d,f"[{s['id']}] {s['reference']}")
    new(d,"Referencias continuadas")
    for s in SOURCES[6:]:p(d,f"[{s['id']}] {s['reference']}")
    p(d,"Fecha de consulta de fuentes web: 6 de noviembre de 2026. Los enlaces de consulta y las restricciones de verificación "
      "se registran en references/sources.json y references/verification.md.")
    new(d,"Anexo A Parámetros y ejemplos auditables")
    caption(d,"Tabla A1. Matriz B de E3, con el mismo orden de símbolos de la tabla 4.")
    table(d,["Estado","v₀","v₁","v₂","v₃","v₄","v₅"],
          [[n]+[number(v,5) for v in r] for n,r in zip(["Normal","Degradado","Crítico"],PARAM["E3_solapamiento"]["B"])],
          [1.05,.925,.925,.925,.925,.925,.925],font=9)
    caption(d,"Tabla A2. Primeros doce minutos de E2, réplica 0. N = normal, D = degradado, C = crítico.")
    seq=pd.read_csv(ROOT/"data/sequences.csv")
    example=seq[(seq.scenario=="E2_persistencia")&(seq.rep==0)].head(12)
    table(d,["Minuto","Latencia ms","Errores","Símbolo","Real","Viterbi"],
          [[int(r.t),number(r.latency_ms,1),int(r.errors_100),int(r.symbol),"NDC"[int(r.state)],"NDC"[int(r.Viterbi)]] for r in example.itertuples()],
          [.8,1.5,1,1,.95,1.35],font=9.5)
    p(d,"Cada fila de data/sequences.csv conserva escenario, réplica, minuto, estado real, observaciones y predicciones. "
      "Los 4800 minutos de entrenamiento se guardan por separado. No se usa información de prueba para escoger el mejor reinicio.")
    new(d,"Anexo B Evidencias y trazabilidad de la entrega")
    table(d,["Criterio de evaluación","Evidencia principal"],[
      ["Comprensión HMM · 20 puntos","Sección 3; src/hmm.py; pruebas por enumeración"],
      ["Problema y pertinencia · 15 puntos","Secciones 1, 2 y 6; alcance y vacío delimitado"],
      ["Probabilidades · 15 puntos","Sección 4; tablas 2–6; parameters.json; prueba de emisiones"],
      ["Respuestas y formato · 10 puntos","Sección 7, P1–P3; artículo carta e interlineado 1,5"],
      ["Simulación verificable · 20 puntos","CSV, cinco figuras a 300 dpi, pruebas y validation.json"],
      ["Video · 10 puntos","Guion de 2:50 con pantalla y narración; grabación pendiente del estudiante"],
      ["Repositorio · 10 puntos","README, requirements, código, datos y comandos de reproducción"]],
      [2.35,4.25],font=10)
    p(d,"Reproducción desde la raíz: crear un entorno Python 3.12, instalar requirements.txt, ejecutar las pruebas con "
      "python -m unittest discover -s tests -v y luego python run_experiments.py. Validar con python validate_results.py. "
      "Para comparar una nueva ejecución sin sobrescribir la entrega: python run_experiments.py --output replay; "
      "python validate_results.py --compare replay. El README contiene instrucciones de Windows y Linux/macOS.")
    p(d,"Comprobaciones realizadas: ejecución completa en dos ocasiones, cuatro pruebas automatizadas, validación de matrices y símbolos, "
      "recomputación de 4000 métricas y comparación SHA-256 de veinte archivos. El documento se genera desde los CSV; "
      "docs/claims.json registra las cifras insertadas mediante consulta a summary.csv. No se certifica indexación individual "
      "en bases de pago ni desempeño sobre datos reales. El entregable del video es el guion solicitado; no se incluye una grabación MP4.")
    d.save(OUT/"Articulo_HMM.docx")
    (OUT/"claims.json").write_text(json.dumps(CLAIMS,ensure_ascii=False,indent=2),encoding="utf-8")
    text="\n".join(q.text for q in d.paragraphs)
    (OUT/"Articulo_texto.txt").write_text(text,encoding="utf-8")
    print("Resumen:",len(abstract.split()),"palabras; párrafos:",len(text.split()),"palabras (sin tablas).")


def script():
    d=setup();d.core_properties.title="Guion de sustentación del modelo oculto de Markov"
    p(d,d.core_properties.title,"Title")
    p(d,"Duración prevista 2:50 · Español · MP4 · 1920 × 1080 · Horizontal 16:9")
    p(d,"Preparación: abrir README, src/hmm.py, results/parameters.json y las figuras 01, 02 y 03. "
      "Ejecutar demo.py para mostrar resultados existentes; la simulación completa se debe ejecutar y validar antes de grabar. "
      "Grabar pantalla y voz, o añadir la narración posteriormente. Ensayar para no superar 3:00; no se afirma una duración de voz medida.")
    segments=[
      ("0:00–0:12","Gancho","Mostrar figura 02, con el cursor sobre un pico de latencia.",
       "¿Un pico de latencia significa que un servicio web está fallando? No siempre. Este proyecto utiliza el historial de latencia y errores para inferir una condición que no observamos directamente."),
      ("0:12–0:32","Problema y motivación","Mostrar título del proyecto y los tres nombres de estados en README.",
       "El problema consiste en distinguir un servicio normal, degradado o crítico. Una lectura aislada puede confundirnos, porque los estados generan observaciones que se superponen. El objetivo fue construir una solución sencilla, reproducible y capaz de cuantificar esa incertidumbre."),
      ("0:32–1:00","Modelo y matrices","Mostrar π, A y B en parameters.json; ampliar filas para que sean legibles.",
       "Usé un modelo oculto de Markov con tres estados y seis símbolos de observación. Pi representa el estado inicial; A describe permanencia, deterioro y recuperación; B relaciona cada estado con las observaciones. Simulé latencias lognormales y errores binomiales. Después los agrupé en tres bandas de latencia y dos bandas de errores. Todas las probabilidades son válidas y cada fila suma uno."),
      ("1:00–1:27","Método y simulación","Mostrar funciones forward y viterbi brevemente; ejecutar python demo.py.",
       "Implementé Forward para inferencia en línea, Viterbi para reconstruir la trayectoria y Baum-Welch para aprender parámetros sin etiquetas. Ejecuté cuatro escenarios con cincuenta repeticiones de mil cuatrocientos cuarenta minutos: base, mayor persistencia crítica, observaciones solapadas y arranque crítico. Las semillas están fijadas y el entrenamiento está separado de la prueba."),
      ("1:27–2:00","Resultados cuantitativos","Mostrar figura 01 y después figura 03; resaltar E1 y E3.",
       f"En el escenario base, Viterbi logró {val('E1_base')} por ciento de exactitud, frente a {val('E1_base',method='Sin_memoria')} del método sin memoria. "
       f"Con más solapamiento, la exactitud bajó a {val('E3_solapamiento')} por ciento y el reconocimiento del estado crítico quedó en {val('E3_solapamiento','critical_recall')} por ciento. "
       f"Si además se conservan las probabilidades originales, la exactitud cae a {val('E3_solapamiento',method='Viterbi_base_fijo')} por ciento. "
       "Los gráficos muestran intervalos de confianza del noventa y cinco por ciento entre repeticiones."),
      ("2:00–2:27","Aporte y límites","Mostrar validation.json, README y la curva de Baum-Welch si hay tiempo.",
       "El aporte es un experimento auditable que conecta matrices, simulación y resultados. Dos ejecuciones completas produjeron veinte archivos científicos idénticos. Sin embargo, estos son datos sintéticos. Viterbi utiliza información futura y no debe confundirse con una alarma en tiempo real. Además, Baum-Welch llegó al límite de iteraciones sin cumplir todavía la tolerancia estricta de convergencia."),
      ("2:27–2:50","Conclusión","Volver a figura 01; cerrar mostrando la carpeta del proyecto.",
       "Concluyo que la memoria temporal ayuda, pero su eficacia depende de la separación entre observaciones y de probabilidades bien especificadas. Cambiar el estado inicial afectó sobre todo el comienzo de la secuencia. El siguiente paso es validar con telemetría real y medir el tiempo de detección de los incidentes. El código y los datos permiten reproducir todo el análisis.")
    ]
    for i,(time,title,screen,voice) in enumerate(segments):
        if i in [3,5]:d.add_page_break()
        h(d,f"{time}  {title}",2)
        p(d,"Pantalla: "+screen)
        p(d,"Narración: "+voice)
    words=sum(len(s[3].split()) for s in segments)
    p(d,f"Control de duración: {words} palabras de narración; aproximadamente {words/ (170/60):.0f} palabras por minuto para 2:50. "
      "Las transiciones y pausas están incluidas en los tiempos previstos. El tiempo real depende de la lectura y debe confirmarse en el ensayo.")
    d.save(OUT/"Guion_sustentacion.docx")
    md="# Guion de sustentación\n\nMP4 · 1920 × 1080 · 16:9 · Duración objetivo 2:50, máximo 3:00.\n\n"
    for time,title,screen,voice in segments:md+=f"## {time} — {title}\n\n**Pantalla:** {screen}\n\n{voice}\n\n"
    md+=f"Narración: {words} palabras. Ensayar duración antes de exportar. El MP4 debe grabarlo el estudiante.\n"
    (OUT/"Guion_sustentacion.md").write_text(md,encoding="utf-8")
    print("Guion:",words,"palabras")


if __name__=="__main__":article();script()

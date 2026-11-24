# Registro de verificación bibliográfica

Consulta: 6 de noviembre de 2026, hora de Colombia. Revisión dirigida para una actividad académica; no es una revisión sistemática ni acredita un cuartil editorial.

## Estrategia y criterios

Se buscaron trabajos sobre detección de anomalías en series temporales, telemetría de servicios y microservicios, evaluación reproducible, modelos de Markov y sesgos de las métricas. Las búsquedas combinaron términos como `time series anomaly detection benchmark 2022 2023 2024`, `HMM microservices anomaly detection`, `rigorous evaluation anomaly detection` y los títulos de los artículos seleccionados. Se priorizaron actas oficiales, páginas editoriales, repositorios y versiones de los autores.

Se incluyeron diez publicaciones de 2022–2025, dentro de los cinco años anteriores a la consulta. Se añadieron dos antecedentes de 2020 y 1989, expresamente excluidos del conteo reciente. La fecha de publicación usada es la de la versión final en revista o congreso.

El contraste con la literatura es conceptual y metodológico. No se ejecutaron sus implementaciones ni se compararon sus cifras de desempeño con las de este simulador, porque las tareas y los conjuntos de datos son diferentes.

## Fuentes y alcance de comprobación

### [1] Schmidl et al. [1] · 2022

S. Schmidl, P. Wenig y T. Papenbrock, “Anomaly Detection in Time Series: A Comprehensive Evaluation,” Proceedings of the VLDB Endowment, vol. 15, no. 9, pp. 1779–1797, 2022, doi: 10.14778/3538598.3538602.

Fuente: https://www.vldb.org/pvldb/vol15/p1779-wenig.pdf

Comprobación realizada: PDF editorial: título, autores, año, DOI y contenido.

Aspecto utilizado: Evaluación de 71 algoritmos en 976 series. La selección depende de los datos; motiva comparar una línea base.

### [2] Kim et al. [2] · 2022

S. Kim, K. Choi, H.-S. Choi, B. Lee y S. Yoon, “Towards a Rigorous Evaluation of Time-Series Anomaly Detection,” Proceedings of the AAAI Conference on Artificial Intelligence, vol. 36, no. 7, pp. 7194–7201, 2022, doi: 10.1609/aaai.v36i7.20680.

Fuente: https://cdn.aaai.org/ojs/20680/20680-13-24693-1-2-20220628.pdf

Comprobación realizada: PDF oficial y ficha editorial indexada; la apertura directa de la ficha mostró bloqueo.

Aspecto utilizado: Análisis del ajuste de puntos en evaluación. Evitar inflar resultados al corregir segmentos completos.

### [3] Liu y Paparrizos [3] · 2024

Q. Liu y J. Paparrizos, “The Elephant in the Room: Towards A Reliable Time-Series Anomaly Detection Benchmark,” Advances in Neural Information Processing Systems, vol. 37, pp. 108231–108261, 2024, doi: 10.52202/079017-3437.

Fuente: https://proceedings.neurips.cc/paper_files/paper/2024/hash/c3f3c690b7a99fba16d0efd35cb83b2c-Abstract-Datasets_and_Benchmarks_Track.html

Comprobación realizada: Actas oficiales y página de publicaciones del autor; resumen y metadatos.

Aspecto utilizado: TSB-AD y evaluación uniforme de detectores. Contrastar métodos simples y controlar sesgos de evaluación.

### [4] Xu et al. [4] · 2022

J. Xu, H. Wu, J. Wang y M. Long, “Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy,” en International Conference on Learning Representations, 2022. [En línea]. Disponible: https://openreview.net/forum?id=LzQQ89U1qm_

Fuente: https://ise.thss.tsinghua.edu.cn/~mlong/doc/anomaly-transformer-iclr22.pdf

Comprobación realizada: PDF de los autores con identificación de ICLR 2022; OpenReview exigió verificación del navegador.

Aspecto utilizado: Atención y discrepancia de asociaciones temporales. Antecedente de modelado temporal; aquí se elige un HMM pequeño.

### [5] Tuli et al. [5] · 2022

S. Tuli, G. Casale y N. R. Jennings, “TranAD: Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data,” Proceedings of the VLDB Endowment, vol. 15, no. 6, pp. 1201–1214, 2022, doi: 10.14778/3514061.3514067.

Fuente: https://www.vldb.org/pvldb/vol15/p1201-tuli.pdf

Comprobación realizada: PDF editorial: título, autores, año, DOI y contenido.

Aspecto utilizado: Transformer multivariante con autoacondicionamiento. Contextualiza la detección en telemetría industrial compleja.

### [6] Yang et al. [6] · 2023

Y. Yang, C. Zhang, T. Zhou, Q. Wen y L. Sun, “DCdetector: Dual Attention Contrastive Representation Learning for Time Series Anomaly Detection,” en Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining, pp. 3033–3045, 2023, doi: 10.1145/3580305.3599295.

Fuente: https://arxiv.org/abs/2306.10347

Comprobación realizada: Registro arXiv de autores, resumen, DOI editorial y aceptación KDD; páginas en repositorio oficial de autores.

Aspecto utilizado: Atención dual y aprendizaje contrastivo. La representación determina la separación de anomalías.

### [7] Wenig et al. [7] · 2022

P. Wenig, S. Schmidl y T. Papenbrock, “TimeEval: A Benchmarking Toolkit for Time Series Anomaly Detection Algorithms,” Proceedings of the VLDB Endowment, vol. 15, no. 12, pp. 3678–3681, 2022, doi: 10.14778/3554821.3554873.

Fuente: https://www.vldb.org/pvldb/vol15/p3678-schmidl.pdf

Comprobación realizada: PDF editorial recuperado en búsqueda y sitio oficial del proyecto con entrada bibliográfica.

Aspecto utilizado: Herramienta de evaluación y generación sintética. Motiva configuraciones explícitas y artefactos ejecutables.

### [8] Si et al. [8] · 2024

H. Si et al., “TimeSeriesBench: An Industrial-Grade Benchmark for Time Series Anomaly Detection Models,” en IEEE 35th International Symposium on Software Reliability Engineering, pp. 61–72, 2024, doi: 10.1109/ISSRE62328.2024.00017.

Fuente: https://arxiv.org/abs/2402.10802

Comprobación realizada: Registro de autores en arXiv con aceptación ISSRE y resumen; DOI y páginas contrastados con DBLP. Sin acceso autenticado a IEEE Xplore.

Aspecto utilizado: Benchmark industrial y series no vistas. Exige considerar cambios de distribución y despliegue.

### [9] Yu et al. [9] · 2023

G. Yu, P. Chen, Y. Li, H. Chen, X. Li y Z. Zheng, “Nezha: Interpretable Fine-Grained Root Causes Analysis for Microservices on Multi-modal Observability Data,” en Proceedings of the 31st ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering, 2023, doi: 10.1145/3611643.3616249.

Fuente: https://2023.esec-fse.org/details/fse-2023-research-papers/8/-Remote-Nezha-Interpretable-Fine-Grained-Root-Causes-Analysis-for-Microservices-on-

Comprobación realizada: Programa oficial, autores y resumen; DOI en PDF del grupo AIOps Nankai recuperado por búsqueda.

Aspecto utilizado: Métricas, trazas y logs para localizar causas. Delimita el alcance: clasificar estado no identifica la causa.

### [10] Wang et al. [10] · 2025

F. Wang, Y. Jiang, R. Zhang, A. Wei, J. Xie y X. Pang, “A Survey of Deep Anomaly Detection in Multivariate Time Series: Taxonomy, Applications, and Directions,” Sensors, vol. 25, no. 1, art. 190, 2025, doi: 10.3390/s25010190.

Fuente: https://www.mdpi.com/1424-8220/25/1/190

Comprobación realizada: Ficha editorial y texto de PMC recuperados en búsqueda; apertura directa bloqueada por 429/captcha. Metadatos coinciden con PubMed.

Aspecto utilizado: Revisión de paradigmas, modelos y datasets. Ubica dependencias temporales y entre variables como retos.

### [11] Samir y Pahl [11] · 2020

A. Samir y C. Pahl, “Detecting and Localizing Anomalies in Container Clusters Using Markov Models,” Electronics, vol. 9, no. 1, art. 64, 2020, doi: 10.3390/electronics9010064.

Fuente: https://www.mdpi.com/2079-9292/9/1/64

Comprobación realizada: Fuente editorial recuperada por búsqueda con resumen y metadatos.

Aspecto utilizado: HMM jerárquico para clústeres de contenedores. Antecedente directo histórico; no cuenta entre los diez recientes.

### [12] Rabiner [12] · 1989

L. R. Rabiner, “A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition,” Proceedings of the IEEE, vol. 77, no. 2, pp. 257–286, 1989, doi: 10.1109/5.18626.

Fuente: https://www.fceia.unr.edu.ar/prodivoz/Rabiner_1989.pdf

Comprobación realizada: PDF del artículo preservado por una universidad; autores, revista, fecha, paginación y algoritmos.

Aspecto utilizado: Fundamentación clásica de algoritmos HMM. Fuente fundacional; no cuenta entre los diez recientes.

## Verificaciones no realizadas

- No hubo acceso autenticado a Scopus, Web of Science o IEEE Xplore; no se certifica la indexación individual ni el cuartil de cada publicación.
- No se afirma lectura íntegra de los diez textos: algunas contribuciones se contrastaron mediante resúmenes, metadatos, fuentes editoriales indexadas y versiones de autores, como indica cada registro.
- Los bloqueos de apertura directa se documentan arriba. Una respuesta de bloqueo no se presenta como lectura del documento.
- No se realizó un estudio de campo ni validación con telemetría real; las referencias motivan decisiones y delimitan el alcance, pero no validan los valores sintéticos de las matrices.
- El vacío propuesto es una oportunidad acotada de integración didáctica y auditabilidad; no demuestra ausencia absoluta de trabajos similares.

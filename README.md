# Inferencia del estado operativo de un servicio web mediante un HMM

Proyecto académico de **Simulación de Ingeniería de Software**. Un modelo oculto de Markov infiere estados **Normal, Degradado y Crítico** a partir de latencia y errores sintéticos. Implementa Forward escalado, filtrado causal, Viterbi en logaritmos y Baum-Welch sin `hmmlearn`.

Los resultados describen un simulador, no un servicio real. Viterbi es retrospectivo; el filtrado es causal. El modelo conocido de cada escenario es una referencia de tipo oráculo. El ajuste aprendido usa datos independientes.

## Entregables

- `docs/Articulo_HMM.docx`: artículo académico, 14 páginas de contenido más 2 de referencias y 2 de anexos; carta, interlineado 1,5. Paginación verificada en la exportación de revisión.
- `docs/Guion_sustentacion.docx` y `.md`: guion con pantalla y narración, objetivo 2:50, para grabar MP4 1080p horizontal.
- `src/`, `run_experiments.py`: simulador y algoritmos.
- `data/`: todas las secuencias de prueba y entrenamiento en CSV.
- `results/`: estadísticas, modelos, matrices, semillas, entorno y registros de validación.
- `figures/`: cinco figuras en PNG de 300 dpi y PDF vectorial.
- `references/`: 10 publicaciones de 2022–2025, 2 antecedentes históricos y registro de verificación.

## Instalación y ejecución en Windows

Instalar Python 3.12 y abrir PowerShell en esta carpeta. No es necesario activar el entorno:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe run_experiments.py
.venv\Scripts\python.exe validate_results.py
.venv\Scripts\python.exe demo.py
```

`run_experiments.py` vuelve a generar datos y figuras en las carpetas actuales. Para conservar la entrega y comparar una nueva ejecución:

```powershell
.venv\Scripts\python.exe run_experiments.py --output replay
.venv\Scripts\python.exe validate_results.py --compare replay
```

## Instalación en Linux o macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python run_experiments.py
.venv/bin/python validate_results.py
.venv/bin/python demo.py
```

La primera instalación requiere internet. Tras instalar, los experimentos no usan servicios externos, GPU ni datos descargados. La prueba se realizó en Linux con Python 3.12.14; no se ejecutó una instalación limpia en Windows. El tiempo depende del equipo; la fase más lenta es Baum-Welch. `demo.py` muestra los resultados guardados de inmediato y es apropiado para la grabación.

## Modelo y supuestos

Cada minuto contiene una latencia de sondeo `L` y un conteo `K` de errores entre otras 100 solicitudes. Son independientes dado el estado oculto. `L` es lognormal con medianas `[100, 300, 900]` ms y desviaciones del logaritmo `[0.40, 0.45, 0.50]`. `K` es binomial con probabilidades `[0.005, 0.030, 0.120]`.

```text
pi = [0.90, 0.08, 0.02]
A = [[0.960, 0.035, 0.005],
     [0.150, 0.800, 0.050],
     [0.050, 0.200, 0.750]]
```

Las filas de A son el estado actual; las columnas son el siguiente. `B` se calcula **analíticamente**, no se elige arbitrariamente: producto de probabilidades de banda de latencia y banda de errores. Se comprueban sumas iguales a uno con tolerancia absoluta de `1e-12`.

| Símbolo | Latencia | Errores K de 100 |
|---|---|---|
| 0 | L < 200 ms | K ≤ 2 |
| 1 | L < 200 ms | K ≥ 3 |
| 2 | 200 ≤ L < 600 ms | K ≤ 2 |
| 3 | 200 ≤ L < 600 ms | K ≥ 3 |
| 4 | L ≥ 600 ms | K ≤ 2 |
| 5 | L ≥ 600 ms | K ≥ 3 |

## Diseño experimental

Se ejecutan 4 escenarios × 50 réplicas × 1440 minutos = **288 000 observaciones de prueba**. No se descarta calentamiento. Los parámetros se encuentran en `results/parameters.json`.

| Escenario | Factor modificado |
|---|---|
| E1 Base | Configuración de referencia |
| E2 Persistencia | Solo A: mayor ocupación y permanencia crítica |
| E3 Solapamiento | Medianas, dispersiones y probabilidades de error |
| E4 Inicio crítico | Solo pi: `[0.05, 0.15, 0.80]` |

Semillas de prueba: `20261106 + r`, con `r = 0,…,49`. Cada réplica usa tres flujos PCG64 creados con `SeedSequence.spawn(3)`. Las mismas semillas se emplean entre escenarios para acoplar las comparaciones. E1 y E3 tienen los mismos estados reales, pero distintas emisiones.

Comparadores: Viterbi con parámetros conocidos; filtrado Forward; MAP sin memoria con prior estacionario; Viterbi con parámetros base fijos. Se evalúan sobre las mismas secuencias. Además se perturba A o B del decodificador hacia matrices uniformes con epsilon `0, 0.1, 0.25, 0.5, 0.75, 1`, conservando los datos E1. El efecto del prior del filtrado se estudia por separado.

Baum-Welch usa 8 secuencias independientes de 600 minutos, semillas `900000…900007`; inicializaciones `700000…700002`; máximo 60 iteraciones y tolerancia absoluta `1e-5`. Se selecciona el reinicio con mayor verosimilitud de entrenamiento, nunca por el conjunto de prueba. Las clases aprendidas se ordenan por el índice esperado del símbolo. Los tres reinicios alcanzaron 60 iteraciones sin cumplir todavía la tolerancia estricta. Sus curvas son no decrecientes. Las 8 secuencias comenzaron en Normal, lo que limita la estimación de pi.

## Resultados principales de la ejecución incluida

| Escenario | Exactitud Viterbi | IC 95 % de la media | F1 macro | Recall crítico |
|---|---:|---:|---:|---:|
| E1 | 97,31 % | 97,17–97,46 % | 0,929 | 81,82 % |
| E2 | 95,05 % | 94,82–95,28 % | 0,952 | 94,58 % |
| E3 | 86,95 % | 86,28–87,62 % | 0,707 | 49,17 % |
| E4 | 97,28 % | 97,13–97,43 % | 0,931 | 82,43 % |

Los resúmenes usan desviación estándar **muestral** y un intervalo t de Student sobre 50 trayectorias independientes por escenario, no sobre minutos correlacionados. Son IC de la media, no intervalos de predicción. No se aplica point adjustment. Los IC no están ajustados por comparaciones múltiples. Se incluyen mínimos y máximos en `summary.csv`.

En E3, mantener el modelo base reduce la exactitud a 68,92 %. Baum-Welch obtiene 97,21 % en prueba E1; su IC es condicional al único ajuste elegido, sin cubrir incertidumbre entre nuevos entrenamientos. El resultado no acredita eficacia en producción.

## Validación ejecutada

1. Cuatro pruebas `unittest`: enumeración exacta de rutas y posteriores, validación y semillas, emisiones empíricas frente a B analítica, monotonía EM.
2. Recomputación de 4000 métricas individuales desde las predicciones CSV; comprobación de resúmenes y símbolos.
3. Dos ejecuciones completas; **20 archivos científicos CSV/JSON idénticos por SHA-256** en el mismo entorno. Ver `results/validation.json`.
4. Revisión de las cifras insertadas en Word mediante `docs/claims.json`; revisión visual de todas las páginas antes de entregar.

Una nueva ejecución de `validate_results.py` sin `--compare` no realiza la comparación de bytes y reemplaza el registro de validación; use `--compare replay` para documentar ambas verificaciones. PDFs y DOCX pueden contener metadatos variables y no forman parte de la comparación de bytes.

## Estructura de los datos

| Archivo | Contenido |
|---|---|
| `data/sequences.csv` | Escenario, réplica, minuto, estado, latencia, errores, símbolo y cuatro predicciones |
| `data/training_sequences.csv` | 4800 minutos independientes para Baum-Welch |
| `results/metrics.csv` | Métricas de cada método y réplica |
| `results/summary.csv` | n, media, DE, mínimo, máximo e IC 95 % por métrica |
| `results/confusion.csv` | Matrices de confusión por réplica |
| `results/process_metrics.csv`, `process_summary.csv` | Latencia, errores, ocupación crítica, transiciones y NLL |
| `results/paired_*.csv` | Diferencias entre métodos calculadas por réplica |
| `results/sensitivity*.csv`, `prior_*.csv` | Sensibilidad de matrices y del prior |
| `results/baum_welch_history.csv` | Log verosimilitud por iteración y reinicio |
| `results/learned_*.csv`, `learned_model.json` | Predicciones, métricas y parámetros aprendidos |
| `results/design.json`, `environment.json` | Semillas, diseño y versiones del entorno |

`critical_recall` puede ser ausente si una réplica no contiene críticos; F1 se fija en cero para una clase sin soporte ni predicciones. Los resúmenes registran el n efectivo. En esta ejecución, las métricas críticas cuentan con las 50 réplicas.

## Regenerar los documentos

Los DOCX ya están incluidos. Para reconstruirlos desde los CSV:

```bash
python -m pip install -r requirements-docs.txt
python build_documents.py
```

La ejecución escribe `docs/Articulo_HMM.docx` y `docs/Guion_sustentacion.docx`. Las ecuaciones son imágenes de 300 dpi generadas con Matplotlib y conservan su fuente matemática en el script. Se debe revisar el diseño de página si se cambia el contenido; la paginación puede variar según las fuentes o la versión de Word. El código de los documentos contiene interpretación específica de esta ejecución: si se cambia el diseño experimental, también se debe revisar y actualizar la narrativa y el README.

## Preparar la publicación en GitHub

La carpeta es el repositorio listo para subir. No contiene credenciales ni un remoto configurado. No se publicó automáticamente. Crear un repositorio vacío en GitHub y ejecutar desde esta carpeta:

```bash
git init
git add .
git commit -m "Agregar simulacion HMM reproducible"
git branch -M main
git remote add origin URL_DEL_REPOSITORIO
git push -u origin main
```

Reemplazar `URL_DEL_REPOSITORIO` por la URL real. `.gitignore` excluye entornos, cachés y `replay/`, pero conserva los resultados entregables. La grabación MP4 corresponde al estudiante; el guion está preparado para mostrar evidencia ejecutada sin esperar un entrenamiento completo durante el video.

## Límites de verificación

No se usaron datos reales ni se midieron costos o latencias de alertas en producción. La revisión bibliográfica es dirigida, no exhaustiva; no hubo acceso autenticado a Scopus/Web of Science/IEEE Xplore ni verificación de cuartiles. Algunas fuentes se corroboraron con versiones de autores o contenido indexado porque la apertura directa estaba bloqueada. El detalle está en `references/verification.md`.

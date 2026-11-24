# Guion de sustentación

MP4 · 1920 × 1080 · 16:9 · Duración objetivo 2:50, máximo 3:00.

## 0:00–0:12 — Gancho

**Pantalla:** Mostrar figura 02, con el cursor sobre un pico de latencia.

¿Un pico de latencia significa que un servicio web está fallando? No siempre. Este proyecto utiliza el historial de latencia y errores para inferir una condición que no observamos directamente.

## 0:12–0:32 — Problema y motivación

**Pantalla:** Mostrar título del proyecto y los tres nombres de estados en README.

El problema consiste en distinguir un servicio normal, degradado o crítico. Una lectura aislada puede confundirnos, porque los estados generan observaciones que se superponen. El objetivo fue construir una solución sencilla, reproducible y capaz de cuantificar esa incertidumbre.

## 0:32–1:00 — Modelo y matrices

**Pantalla:** Mostrar π, A y B en parameters.json; ampliar filas para que sean legibles.

Usé un modelo oculto de Markov con tres estados y seis símbolos de observación. Pi representa el estado inicial; A describe permanencia, deterioro y recuperación; B relaciona cada estado con las observaciones. Simulé latencias lognormales y errores binomiales. Después los agrupé en tres bandas de latencia y dos bandas de errores. Todas las probabilidades son válidas y cada fila suma uno.

## 1:00–1:27 — Método y simulación

**Pantalla:** Mostrar funciones forward y viterbi brevemente; ejecutar python demo.py.

Implementé Forward para inferencia en línea, Viterbi para reconstruir la trayectoria y Baum-Welch para aprender parámetros sin etiquetas. Ejecuté cuatro escenarios con cincuenta repeticiones de mil cuatrocientos cuarenta minutos: base, mayor persistencia crítica, observaciones solapadas y arranque crítico. Las semillas están fijadas y el entrenamiento está separado de la prueba.

## 1:27–2:00 — Resultados cuantitativos

**Pantalla:** Mostrar figura 01 y después figura 03; resaltar E1 y E3.

En el escenario base, Viterbi logró 97,31 por ciento de exactitud, frente a 92,65 del método sin memoria. Con más solapamiento, la exactitud bajó a 86,95 por ciento y el reconocimiento del estado crítico quedó en 49,17 por ciento. Si además se conservan las probabilidades originales, la exactitud cae a 68,92 por ciento. Los gráficos muestran intervalos de confianza del noventa y cinco por ciento entre repeticiones.

## 2:00–2:27 — Aporte y límites

**Pantalla:** Mostrar validation.json, README y la curva de Baum-Welch si hay tiempo.

El aporte es un experimento auditable que conecta matrices, simulación y resultados. Dos ejecuciones completas produjeron veinte archivos científicos idénticos. Sin embargo, estos son datos sintéticos. Viterbi utiliza información futura y no debe confundirse con una alarma en tiempo real. Además, Baum-Welch llegó al límite de iteraciones sin cumplir todavía la tolerancia estricta de convergencia.

## 2:27–2:50 — Conclusión

**Pantalla:** Volver a figura 01; cerrar mostrando la carpeta del proyecto.

Concluyo que la memoria temporal ayuda, pero su eficacia depende de la separación entre observaciones y de probabilidades bien especificadas. Cambiar el estado inicial afectó sobre todo el comienzo de la secuencia. El siguiente paso es validar con telemetría real y medir el tiempo de detección de los incidentes. El código y los datos permiten reproducir todo el análisis.

Narración: 360 palabras. Ensayar duración antes de exportar. El MP4 debe grabarlo el estudiante.

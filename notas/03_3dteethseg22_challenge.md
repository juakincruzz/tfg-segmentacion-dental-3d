# 3DTeethSeg'22: 3D Teeth Scan Segmentation and Labeling Challenge

- **Referencia:** Ben-Hamadou, A. *et al.* arXiv:2305.18277 [cs.CV], mayo **2023**. DOI: 10.48550/arXiv.2305.18277
- **Clave BibTeX:** `ben-hamadou3DTeethSeg223DTeeth2023`
- **Tipo:** informe de reto (*challenge report*) celebrado como evento satélite de MICCAI 2022. 32 autores: los organizadores más los seis equipos participantes.
- **Leído:** 23–25 de agosto de 2026

## De qué va

El paper habla del reto 3DTeethSeg'22 y los resultados obtenidos. Este paper contribuye con: 
- **Dataset Teeth3DS**: este dataset consta de 1800 escaneos intraorales de 900 pacientes, anotados diente a diente y validados clínicamente.
- **Protocolo de evaluación**: incluyen tres métricas oficiales (TLA (Teeth Localization Accuracy), TSA (Teeth Segmentation Accuracy), TIR (Teeth Identification Rate)) y código público.
- **Descripción de los algoritmos**: habla de aquellos que llegaron a la fase final del reto con su comparativa respectiva.

**Este paper asienta las bases de este TFG.** A diferencia de los papers 1 y 2, en este hay métodos, datos y métricas. Esto es la fuente del baseline contra el que hay que medirse y del hueco que justifica la contribución.

> "The challenge aimed to evaluate six algorithms for teeth detection, segmentation, and labeling tasks."

-> Fueron seis de los diez equipos que llegaron a subir sus soluciones a la fase final, y de 44 registrados.

---

## Cajón: INTRODUCCIÓN

### Por qué importa el problema

> “Teeth localization, segmentation, and labeling from intra-oral 3D scans are essential tasks in modern dentistry to enhance dental diagnostics, treatment planning, and population-based studies on oral health.”

-> El paper habla de que la motivación de este reto es meramente clínica, no tiene nada que ver con lo forense. Este reto existe por la ortodoncia y la prostodoncia. El uso forense es algo que aporto yo desde el paper 1
En una parte del paper se menciona que los datos clínicos habían sido cogidos de pacientes que necesitaban tratamiento ortodóncico (50%) o tratamiento protésico (50%). Además también aporta datos como el sexo
(50% eran hombres y 50% eran mujeres), la edad (aproximadamente el 70% eran menores de 16 años, 27% entre 16 y 59 años, y finalmente, 3% mayores de 60 años). De esto último igualmente hablaré más adelante en **MÉTODOS**

-> HIPÓTESIS: Si el 50% necesitaba un tratamiento protésico eso se refiere a dientes ausentes o dañados **PENDIENTE DE VERIFICAR**

### Las cuatro dificultades que el propio paper enumera

> "1. The teeth position and shape variation across subjects. 2. The presence of abnormalities in dentition. For example, teeth crowding which results in teeth misalignment and thus non-explicit boundaries between neighboring teeth. Moreover, lacking teeth and holes are commonly seen among people. 3. Damaged teeth. 4. The presence of braces, and other dental equipment."

-> Estas son las dificultades citables. Los dientes ausentes aparecen en el punto 2, los autores lo mencionan como común en la población.

### Y el alcance que los organizadores se autoimponen

> "The challenge we propose will particularly focus on point 1, i.e., the teeth position and shape variation across subjects. With the extension of available data in the mid and long term, the other points will also be addressed in further editions of the challenge."

-> Esto es clave ya que los mismos organizadores dicen que solo se van a centrar en el punto 1 y que los dientes ausentes, dañados y los brackets se harán en ediciones futuras.

---

## Cajón: FUNDAMENTOS TEÓRICOS

### Las tres tareas, definidas sin ambigüedad

> "Localization refers to the precise identification and positioning of a tooth, including the calculation of its 3D centroid. Segmentation, on the other hand, involves identifying the vertices that pertain to a detected tooth, allowing for the demarcation of its boundaries. Labeling involves assigning a specific class to a detected and segmented tooth. In this work, we adhere to the FDI teeth numbering system."

-> Terminología para la memoria: **Localización != segmentación != etiquetado**, son cosas distintas con métricas distintas. Confundir las tres tareas es el error típico al escribir de esto.
Las métricas son: TLA (localización), TSA (segmentación) y TIR (etiquetado).

### Sistema FDI

Se distingue por dos dígitos con distintos significados:

1. El cuadrante desde el POV del paciente (1 superior derecho, 2 superior izquierdo, 3 inferior izquierdo, 4 inferior derecho).
2. Posición va del 1 (incisivo central) hasta el 8 (tercer molar).

La arcada completa son 32 dientes, 16 por maxilar. En JSON, para la encía se usa la etiqueta y la instancia 0.

-> **OJO**: el paper no menciona si Teeth3DS usa los cuadrantes 5-8 de dentición temporal, el 70% de los pacientes son menores de 16 años. Al descargar los datos hay que revisarlo.

### Formato de los datos

Malla en `.obj`, anotación en `.json` con dos vectores, `labels` e `instances`, ambos de longitud igual al número de vértices.

> "The length of the tables ”labels” and ”instances” is the same as the total number of vertices in the corresponding 3D scan."

-> Se anota por vértice, no por cara ni por punto muestreado. Eso condiciona el pipeline: si el método decima o submuestrea la malla, tiene que llevar la predicción de vuelta a la resolución original (KNN, vecino más cercano, interpolación) antes de evaluar.

---

## Cajón: ESTADO DEL ARTE

El punto 1.2 organiza la literatura previa en dos familias.

### Familia 1: características hechas a mano

Tres subtipos: **curvatura de superficie** (Zhao 2006, Yuan 2010, Wu 2014, Kronfeld 2010), **líneas de contorno** (Sinthanayothin 2008, Yaqi 2010) y **campos armónicos** (Zou 2015, Liao 2015).

> "The approaches described above fall short when it comes to robust and fully automated segmentation of dental 3D scans. Setting the optimal threshold value for surface curvature-based methods is not straightforward. Indeed, these methods are still sensitive to noise, and selecting the wrong threshold can systematically affect the segmentation accuracy [...] Also, contour-line approaches are time-consuming, tough to use, and closely rely on human interaction. Finally, the harmonic field techniques involve sophisticated and heavy pre-processing steps."

-> Lo que pasa es que cada subtipo falla por un motivo distinto:

1. **Curvatura de la superficie**: el umbral óptimo no es claro y es sensible al ruido.
2. **Líneas de contorno**: son lentas y dependen del operador.
3. **Campos armónicos**: preprocesado pesado y sofisticado.

Ninguno es a la vez robusto y totalmente automático.

### Familia 2: aprendizaje profundo, subdividida por tipo de entrada

**Entrada 2D** — se proyecta el 3D a imagen y se aplica una CNN: Cui 2019 (Mask R-CNN sobre CBCT), Miki 2017 (AlexNet), Rao 2020 (FCN residual + CRF denso), Zhang 2020 (mapeo isomorfo a espacio paramétrico armónico + U-Net).

**Entrada 3D** — se opera sobre la malla o la nube de puntos directamente: Sun 2020 (FeaStNet, GCN), Xu 2018 (dos CNN independientes), Zanjani 2019b (PointNet + discriminador adversarial), Lian 2020 (PointNet con módulos *graph-constrained*), Tian 2019 (octree disperso + CNN jerárquicas), Cui 2020 (TSegNet: centroides y después recorte por diente), Zanjani 2019a (RPN Monte Carlo + Mask R-CNN + tabla de consulta sobre centroides), Ma 2020 (SRF-Net), Zhao 2021b (convoluciones de atención en grafo), Zhao 2022 (TSGCN, dos flujos: coordenadas y normales), Qiu 2022 (DArch).

### Los cuatro trabajos que hay que leer de aquí

De toda la lista, cuatro son los que tocan directamente el problema del **etiquetado con contexto de arcada**, y ya están en `bibliografia/tfg.bib`:

| Trabajo | Clave BibTeX | Por qué |
|---|---|---|
| Cui *et al.*, TSegNet (2020/2021) | `cuiTSegNetEfficientAccurate2021` | Arquitectura de dos etapas centroide→recorte que copian IGIP y Chompers |
| Ma *et al.*, SRF-Net (2020) | `maSRFNetSpatialRelationship2020` | Modela la relación espacial entre dientes adyacentes. **Competidor directo** |
| Lian *et al.* (2020) | `lianDeepMultiScaleMesh2020` | Módulos *graph-constrained*, reutilizados por el equipo OS |
| Qiu *et al.*, DArch (2022) | `qiuDArchDentalArch2022` | Curva de arcada por regresión de Bézier + GCN, con anotación débil |

> Sobre Qiu 2022: "the dental arch is initially generated by Bezier curve regression, and then refined using a graph-based convolutional network (GCN)."

-> DArch usa la curva de la arcada, pero para detectar los centroides (muestreo APS), no para etiquetar: su salida son máscaras sin número FDI. Comprobado al leerlo, ficha 04. Orden de lectura acordado: TSegNet -> SRF-Net -> DArch -> Lian.

---

## Cajón: MÉTODOS

### Cómo se construyó el dataset (punto 2)

Escáneres: Primescan (Dentsply), Trios3 (3Shape), iTero Element 2 Plus. Precisión de 10 a 90 µm, resolución de 30 a 80 pts/mm². Clínicas de Francia y Bélgica, conforme al RGPD, datos anonimizados por UUID.

> "All acquired clinical data are collected for patients requiring either orthodontic (50%) or prosthetic treatment (50%). The provided dataset follows a real-world patient age distribution: 50% male 50% female, about 70% under 16 years-old, about 27% between 16-59 years-old, about 3% over 60 years old."

-> Dos sesgos que el paper no declara:

1. El 100% de los pacientes tenían alguna patología o necesitaban algún tratamiento; no había casos de bocas sanas.
2. El 70% de los pacientes son menores de 16 años, lo que es un desajuste de dominio en el uso forense respecto a la población adulta general sobre la que se identifica a las víctimas de un desastre.


Anotación en ocho pasos con validación clínica y ciclos de corrección. El paso interesante es el 3: **mapeo UV por parametrización armónica** para aplanar cada diente recortado y anotar el borde en 2D con la curvatura superpuesta, sin cambiar el punto de vista 3D. El resultado se revierte a 3D en el paso 5.

> "each tooth was individually annotated by a human-machine hybrid algorithm"

-> Las anotaciones se hicieron de manera híbrida. La calidad del *ground truth* está condicionada por el algoritmo que la asistió. Todos los métodos se puntúan contra esa anotación, así que ninguno puede superar la calidad del algoritmo que la generó. Es un techo del benchmark, no un defecto de un equipo en concreto.

### Los seis métodos, en una tabla

| Equipo | Representación | Idea central | Etapas |
|---|---|---|---|
| **CGIP** | Nube de puntos 3D | Point Transformer + *Point Grouping Module* + *Tooth Cropping Module*; DBSCAN sobre puntos desplazados por offsets; *Boundary Aware Point Sampling* | Instancia → semántica por voto mayoritario |
| **FiboSeg** | Renderizado 2D multivista | PyTorch3D; normales como RGB + profundidad como 4.º canal; U-Net residual de MONAI; voto mayoritario ponderado | Render → segmenta en 2D → devuelve a la malla |
| **IGIP** | Nube de puntos 3D | PointNet++ para centroides, *density peaks clustering*, segmentación por parche, clasificación forma⊕posición a 33 clases | 5 etapas + post-proceso por curva de arcada |
| **TeethSeg** | Voxelización | 3D U-Net por maxilar + *Random Walker* guiado por una función de convexidad | Grueso → refinado geométrico |
| **OS** | Vista cenital 2D + malla | HRNet sobre imagen 512×512 para mapas de calor de centroides, 16 canales; DBSCAN; recorte circular/elíptico; *graph-constrained learning* + *graph-cut* | Localiza en 2D → segmenta en 3D |
| **Chompers** | Nube de puntos 3D | Stratified Transformer; **32 etiquetas colapsadas a 7 clases**; pérdida *Normalized Euclidean* + *Separation* | Centroides ×6 → segmentación ×2 → fusión por IoU |

### Detalles que merecen apunte

**FiboSeg — el buffer `pix_to_face`:**

> "The rendering engine provides a map that relates pixels in the images to faces in the mesh and allows rapid extraction of point data (normals, curvatures, labels, etc.) as well as setting information back into the mesh after inference."

-> Esta es la pieza que hace viable un método 2D sobre datos 3D: el rasterizador devuelve, para cada píxel, el índice de la cara que lo generó. La transferencia malla↔imagen es **bidireccional y exacta**, no una aproximación. Sin esto, proyectar a 2D perdería la correspondencia con los vértices que hay que etiquetar.

**FiboSeg — la augmentación que importa:**

> "We augment the data by applying random rotations and randomly removing dental crowns (excluding wisdom teeth)."

-> **Único equipo que entrena quitando coronas al azar.** Es exactamente simular el caso de diente ausente. Y es el equipo que más sube de TSA (4.º) a TIR (2.º). No es casualidad.

**IGIP — la crítica a SRF-Net:**

> "Ma et al. (2020) use the teeth feature vectors with neighborhood relations for better labeling accuracy, but it relies on a regular teeth distribution."

-> **La frase más importante del paper para este TFG.** El equipo que gana la métrica de etiquetado le reprocha al principal competidor que asuma una arcada regular.

**IGIP — sin conocimiento previo del maxilar:**

> "No prior information about whether the model belongs to the upper or lower jaw is needed in our method, because the incisors of the upper and lower jaw have the most significant difference in shapes and sizes, and the global feature extracted in this step will tell."

-> Da un eje nuevo para la tabla del estado del arte: **cuánto conocimiento previo necesita cada método**. IGIP no necesita saber el maxilar; FiboSeg tampoco; OS lo asume implícitamente (16 canales); Chompers y TeethSeg lo necesitan explícitamente.

**IGIP — el post-proceso por curva de arcada:**

> "predicted centroids are predicted onto xOy plane and fit a para-curve as the dental arch curve. Then, based on the curve, the relative positions for each tooth are calculated, and some typical errors can be fixed. For example, if two teeth have the same label, then their labels can be corrected through the sorted label sequence; or if the labels are disordered, they can be reordered based on the order of teeth."

-> Ajustar una parábola en el plano xOy y ordenar los centroides a lo largo de ella. **Sin red, sin entrenamiento**, y consigue el mejor TIR del reto. El listón de la contribución empieza aquí, no en cero.

**IGIP y Chompers convergen en la misma corrección de la pérdida:**

IGIP añade a su pérdida de centroides un término con λ = 0.2:

> "ci1 and ci2 are the ground truth centroids with the minimum and the second minimum distance from ĉi respectively, used to push a predicted centroid away from other ground truth centroids"

Chompers llama *Separation* a lo mismo, pero normalizando por el radio del diente.

-> **Dos equipos independientes llegan al mismo arreglo:** empujar el centroide predicho lejos del segundo centroide real más próximo, para que dos centroides no colapsen en el mismo diente. Chompers además elimina el sesgo hacia dientes grandes con la normalización por radio. Esto se cita, no se reinventa.

---

## Cajón: EXPERIMENTOS

### Protocolo y datos

> "separated into training (1200 scans, 16004 teeth) and test data (600 scans, 7995 teeth)"

1200 escaneos y 16 004 dientes para entrenar; 600 escaneos y 7995 dientes de test.

> "participants were not granted access to the test scans directly. Instead, they were required to submit their code within a docker container. The dockers were then evaluated on hidden test data, preventing any retraining on the test data or overfitting through fine-tuning."

-> Por ese protocolo las seis filas de la Tabla 2 son comparables entre sí: mismo test oculto, misma implementación de las métricas y ningún equipo pudo ajustar sobre el test. Los datos y los scripts de evaluación ya son públicos, así que puedo medirme contra esas mismas cifras, pero solo manteniendo la misma disciplina: no tocar el test hasta el final. Si lo uso para elegir hiperparámetros, mis números dejan de ser comparables con la tabla aunque ejecute el mismo script.


### Las tres métricas oficiales

**TLA (Teeth Localization Accuracy).**

> "mean of normalized Euclidean distance between ground truth (GT) teeth centroids and the closest localized teeth centroid. Each computed Euclidean distance is normalized by the size of the corresponding GT tooth. In case of no centroid (e.g. algorithm crashes or missing output for a given scan) a nominal penalty of 5 per GT tooth will be given."

-> Distancia, así que **menor es mejor**. Pero la Tabla 2 publica **Exp(−TLA)**, donde mayor es mejor. Hay que tener cuidado al citar cifras. La penalización de 5 en el espacio exponencial es exp(−5) ≈ 0.0067, es decir, casi cero: **fallar en detectar un diente se castiga durísimo**.

**TSA (Teeth Segmentation Accuracy).** F1 medio sobre todas las instancias de diente. Se calcula sobre **vértices**.

**TIR (Teeth Identification Rate).**

> "A true identification is considered when for a given GT Tooth, the closest detected tooth centroid: is localized at a distance under half of the GT tooth size, and is attributed the same label as the GT tooth"

-> Métrica **compuesta**: exige a la vez detectar bien (a menos de medio tamaño de diente) y etiquetar bien. Un método puede fallar el TIR por un error de localización aunque su clasificador sea perfecto.

### Resultados (Tabla 2)

| Equipo | Exp(−TLA) | TSA | TIR | Score |
|---|---|---|---|---|
| **CGIP** | 0.9658 | **0.9859** | 0.9100 | **0.9539** |
| **FiboSeg** | **0.9924** | 0.9293 | 0.9223 | 0.9480 |
| **IGIP** | 0.9244 | 0.9750 | **0.9289** | 0.9427 |
| **TeethSeg** | 0.9184 | 0.9678 | 0.8538 | 0.9133 |
| **OS** | 0.7845 | 0.9693 | 0.8940 | 0.8826 |
| **Chompers** | 0.6242 | 0.8886 | 0.8795 | 0.7974 |

> "the method proposed by the CGIP team holds the top position. However, when focusing specifically on the teeth localization task, the FiboSeg team achieves the highest score [...] the IGIP team exhibits the best performance in the tooth labeling task"

-> **Ningún equipo gana las tres.** Cada tarea tiene un ganador distinto.

La lectura por columnas de esta tabla (cómo se agrega el Score, quién ganaría sin el TLA y lo que esconde la exponencial) está en Observaciones propias 1, 2 y 3.


### Evaluación cualitativa

> "Missing tooth detection is observed across multiple teams, but it is more pronounced in the results of the IGIP team (sample d) and the OS team (samples a and b, for instance)."

-> El campeón de etiquetado es, cualitativamente, **uno de los peores en no perder dientes**. Detalle importante, ver observación propia nº 5.

### Lo que el reto no mide

1. No hay resultados desglosados por clase FDI, así que el paper no permite saber si el error se concentra en los terceros molares, que es lo esperable.
2. No hay dispersión ni significación estadística: una cifra por equipo y métrica, sin desviación típica ni test alguno. Con 600 escaneos de test podrían haberla dado.
3. No hay tiempo de ejecución ni coste computacional. Los propios organizadores lo proponen para futuras ediciones, con lo que reconocen la ausencia.
4. Las métricas promedian sobre dientes. Un método que falle sistemáticamente en las bocas con ausencias apenas mueve la media sobre casi 8000 dientes.

-> El punto 4 es el que condiciona mi trabajo. Si la contribución va sobre los casos con dientes ausentes, el promedio global no puede demostrarla: hay que reportar la métrica sobre el subconjunto de escaneos con ausencias, y esa medición no existe en el paper.

---

## Cajón: CONCLUSIONES Y TRABAJO FUTURO

> "Future directions could include the incorporation of more variabilities in the dataset, such as more challenging cases with missing or damaged teeth and ambiguous labeling scenarios to provide a more comprehensive evaluation and enhance the algorithms' capability to handle real-world scenarios effectively."

→ Los organizadores cierran el paper diciendo que **al dataset le faltan casos difíciles con dientes ausentes**. Es a la vez la confirmación del hueco y **una advertencia seria para mi planificación**: si Teeth3DS no contiene bastantes casos duros, no podré demostrar la mejora sobre ellos. Ver «Pendiente de verificar».

También proponen para futuras ediciones evaluar la suavidad del borde encía/diente y medir tiempo de ejecución y complejidad computacional.

---

## Observaciones propias

Cinco cosas que **no están en el paper** y he deducido leyéndolo. Cada una es defendible con la Tabla 2 en la mano.

### 1. La fórmula del Score no está escrita, pero es la media aritmética simple

Comprobado en las seis filas. CGIP: (0.9658 + 0.9859 + 0.9100) / 3 = 0.9539. IGIP: (0.9244 + 0.9750 + 0.9289) / 3 = 0.9427. Y así las seis.

### 2. La media sin ponderar deja que la métrica más dispersa decida el podio

Rangos de cada columna: Exp(−TLA) **0.368**, TSA 0.097, TIR 0.075. La localización se dispersa casi cuatro veces más que las otras dos, así que domina la media aunque pese lo mismo nominalmente.

**Si se quita el TLA y se promedian solo TSA y TIR:**

| Equipo | (TSA+TIR)/2 | Puesto | Cambio |
|---|---|---|---|
| IGIP | 0.9520 | 1.º | ▲ 2 |
| CGIP | 0.9480 | 2.º | ▼ 1 |
| OS | 0.9317 | 3.º | ▲ 2 |
| FiboSeg | 0.9258 | 4.º | ▼ 2 |
| TeethSeg | 0.9108 | 5.º | ▼ 1 |
| Chompers | 0.8841 | 6.º | = |

→ **Ganaría IGIP, no CGIP.** El ranking oficial del reto no es un hecho neutral, es consecuencia de una decisión de agregación no justificada en el paper.

### 3. La exponencial comprime diferencias reales de localización

Invirtiendo Exp(−TLA), el TLA en bruto de FiboSeg es 0.0076 y el de CGIP 0.0348: el error de localización de CGIP es **4.5 veces mayor**, y sin embargo en la tabla las dos cifras parecen casi iguales (0.9924 frente a 0.9658). La transformación exponencial aplana el rango bueno y estira el malo.

Añadido: la media mezcla **una distancia transformada con dos proporciones**. Son magnitudes de naturaleza distinta y promediarlas sin normalizar es discutible.

### 4. No es la vista global de la arcada lo que mejora el etiquetado

Dos equipos suben de puesto entre TSA y TIR, y lo hacen por **mecanismos distintos**: FiboSeg entrenando con coronas eliminadas al azar, IGIP con el prior explícito de la curva de arcada. La explicación fácil («tener vista global de la arcada ayuda a etiquetar») **no se sostiene**: el equipo OS tiene una vista cenital completa de toda la arcada y aun así baja del 3.º al 4.º puesto entre TSA y TIR.

*Salvedad obligada: n = 6. Esto es una observación sobre seis puntos, no una conclusión estadística.*

### 5. Un módulo de asignación global sobre centroides hereda los fallos de detección

IGIP gana en etiquetado y, sin embargo, el análisis cualitativo lo señala junto a OS como los que más dientes se dejan sin detectar. Un post-proceso que reordena etiquetas **opera sobre los centroides que la etapa de detección le entregó**: no puede recuperar un diente que nunca se detectó. Es una limitación estructural de la vía que pensaba seguir, y hay que decirla en la memoria antes de que la diga el tribunal.

**Y un hueco concreto en el post-proceso de IGIP:** ordenar a lo largo de la arcada arregla etiquetas duplicadas y desordenadas, pero **no arregla el origen de la numeración**. Si falta un diente al final de una hemiarcada, la secuencia resultante es perfectamente consistente y perfectamente desplazada; el criterio de IGIP no puede detectarlo, porque no hay ni duplicado ni desorden que ver.

---

## El hueco que justifica el TFG

Tres evidencias independientes que apuntan al mismo sitio:

1. **El propio SRF-Net lo declara** en su resumen: usa *«the priori ordered position information of tooth arrangement»*.
2. **IGIP lo critica** en este mismo paper: *«it relies on a regular teeth distribution»*.
3. **Los datos lo desmienten**: 16 004 dientes / 1200 escaneos = **13.3 dientes por escaneo** en entrenamiento, y 7995 / 600 = **13.3** en test. Una arcada completa tiene 16. **Falta una media de casi tres dientes por escaneo.**

→ La contribución **no es** usar el contexto de la arcada: eso ya lo hacen SRF-Net, IGIP y DArch. La contribución es **usarlo sin asumir que la arcada está completa**.

El listón del etiquetado es IGIP: parábola + ordenación, sin entrenamiento, mejor TIR del reto. DArch queda fuera de esa comparación, porque su curva de arcada aprendida (Bézier + GCN) alimenta la detección de centroides, no la asignación de números FDI. Sí es el listón de la *detección*, y su curva me sirve como referencia para ordenar los dientes.

---

## Conexiones

- **Con la ficha 01 (Forrest 2019).** Forrest argumenta que el futuro de la odontología forense está en la comparación de superficies 3D y que el proceso es candidato a automatizarse. Este paper aporta justo la pieza que allí falta: datos 3D públicos, anotados y una métrica. *La unión entre ambos es aportación mía: este paper no menciona lo forense en ninguna parte.*
- **Con la ficha 02 (Lee 2024).** Los tres escáneres usados aquí (Primescan, Trios3, iTero) aparecen en las tablas de modelos de aquella revisión. Sirve para justificar en la memoria que Teeth3DS se adquirió con equipos representativos de la práctica clínica real.
- **Limitación heredada de la ficha 01.** Forrest deja abiertas dos preguntas —cuánto degrada la coincidencia el tratamiento restaurador u ortodóncico, y cuál es el fragmento mandibular mínimo que aún permite identificar—. Ninguna de las dos se puede responder con Teeth3DS: aquí siempre se escanea la arcada entera de un paciente vivo, nunca fragmentos.

---

## Pendiente de verificar

- [ ] **¿Etiqueta Teeth3DS los cuadrantes 5–8 de dentición temporal?** El 70% de los pacientes tiene menos de 16 años y el paper no lo dice. Comprobar en los JSON al descargar.
- [ ] **¿Hay suficientes casos duros?** Contar la distribución de etiquetas por escaneo. Si no hay bastantes escaneos con dientes ausentes, el plan B es eliminación sintética de dientes, como hace FiboSeg para augmentación.
- [ ] **Trampa de citación:** la clave de Zotero es `cuiTSegNetEfficientAccurate2021` porque *Medical Image Analysis* vol. 69 es de abril de 2021, y Zotero tiene razón. Pero **toda la literatura, incluido este paper, lo cita como «Cui et al. 2020»**. Decidir qué año usar y ser consistente.
- [ ] Verificar la licencia exacta de Teeth3DS al descargarlo (CC BY-NC-ND 4.0 según la propuesta) y dejarlo escrito en la memoria.
- [ ] **¿Implica «prosthetic treatment» dientes ausentes o dañados?** El 50% de los pacientes lo necesitaba. Si se confirma, el dataset tiene más casos duros de los que sus propios autores dan a entender. Comprobar contando etiquetas al descargar.
- [x] **¿DArch asume arcada completa?** Resuelto el 11/09/2026 al leerlo: la pregunta no llega a plantearse porque DArch no etiqueta. Separa los dientes y ya. El hueco del TFG sigue en pie. Ver ficha 04.

---

## ¿Volver a él?

**Sí, constantemente.** A diferencia de las fichas 01 y 02, este paper es material de trabajo, no de contexto:

- La **Tabla 2** es la tabla de referencia contra la que se comparará cualquier resultado propio.
- El **§3.2** es la definición operativa de las métricas que hay que implementar o, mejor, tomar del `evaluation.py` oficial.
- El **§4** es el catálogo de decisiones de diseño ya probadas: qué backbone, qué clustering, qué pérdida, qué post-proceso.
- El repositorio `github.com/abenhamadou/3DTeethSeg22_challenge` tiene los datos y el script de evaluación.

Es la primera ficha **sin ningún cajón vacío**.

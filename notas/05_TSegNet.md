# TSegNet: An efficient and accurate tooth segmentation network on 3D dental model.

## 1. ¿Qué problema resuelve?

> Automatic and accurate segmentation of dental models is a fundamental task in computer-aided dentistry. Previous methods can achieve satisfactory segmentation results on normal dental models; however, they fail to robustly handle challenging clinical cases such as dental models with missing, crowding, or misaligned teeth before orthodontic treatments.

> Mask-MCNet transforms the dental model into point cloud data and uses a volumetric anchor-based region proposal network for tooth detection and segmentation. However, the proposal generation module results in the resolution deduction and requires huge memory resources.

> we present a novel end-to-end learning-based  method  for  automatic  tooth  segmentation  on  3D  dental models.

El problema: los métodos existentes segmentan bien los modelos dentales normales, pero fallan en casos clínicos complejos que llegan antes de la ortodoncia, es decir, dientes ausentes, apiñados o malposicionados. La introducción añade otras dos dificultades: la frontera entre el diente y la encía apenas tiene señal geométrica, y los modelos arrastran artefactos del proceso de fabricación o de los brackets que lleva puesto el paciente (Figura 1).

La causa de fondo la dicen ellos mismos:

> most of these methods make a strongly restrictive assumption that the dental models consist of a complete set of natural teeth, which is difficult to be satisfied, for example nearly 70% of the patients in orthodontic clinics are at the tooth exfoliation time so they often do not have a fixed number of teeth

Casi el 70% de los pacientes de ortodoncia está en fase de recambio dental, así que no tienen número fijo de dientes. **Es el mismo argumento en el que se apoya mi propuesta, publicado en 2020.** Hay que decidir cómo me posiciono ante esto (ver secciones 5 y 6).

Menciona al método Mask-MCNet haciendo crítica de dos cosas: su generación de propuestas basada en anclas pierde resolución y necesita mucha memoria.

Cómo lo resuelven: Proponen un nuevo método basado en el aprendizaje de extremo a extremo que es TSegNet. El algoritmo que ellos usan detecta todos los dientes mediante un esquema de votación de centroides dentales sensible a la distancia en la primera etapa, lo que garantiza la localización precisa de los objetos dentales incluso con posiciones irregulares en modelos dentales anómalos. En la segunda etapa, se ha diseñado un módulo de segmentación en cascada que tiene en cuenta el nivel de confianza para segmentar cada diente individualmente y resolver las ambigüedades causadas por los casos difíciles mencionados anteriormente.

## 2. ¿Qué entra y qué sale?

Qué entra: la nube de puntos 3D extraída del modelo dental. Extraen los vértices de la malla y los submuestrean uniformemente hasta obtener una nube P de dimensión N x 6, con N = 16 000 puntos. Cada punto lleva sus coordenadas y su normal (6 valores). Cada arcada, superior o inferior, se procesa por separado.

Qué sale: una máscara por diente, con la encía como fondo, y el número de cada diente según la notación ISO-3950 (FDI) (Figura 3). Las etiquetas de la nube de puntos se transfieren de vuelta a la superficie de la malla mediante interpolación trilineal. La Figura 8 muestra el proceso completo, desde la entrada hasta los dientes segmentados.

## 3. ¿Qué hace nuevo que los anteriores no hacían?

> instead of the traditional approach that utilizes bounding boxes to crop the detected objects (He et al., 2017; Hou et al., 2019; Zhou and Tuzel, 2018), we exploit the centroid (i.e. the center of mass) of a tooth to identify each tooth object based on our observation that regardless of the tooth shape, position and orientation, the centroid point is a stable feature point inside the tooth shape.

> We propose a novel pipeline that formulates the dental model segmentation as two sub-problems: robust tooth centroids prediction and accurate individual tooth segmentation on point cloud data.

Aportan tres cosas frente a lo anterior:

1. **Detectar cada diente por su centroide en lugar de por una caja envolvente.** Mask-MCNet y los detectores habituales usan cajas o anclas volumétricas, que pierden resolución y consumen mucha memoria. Además, cuando los dientes son pequeños y están muy juntos, las cajas se solapan. El centroide, en cambio, cae siempre dentro del diente, sea cual sea su forma, posición u orientación. La sección 4.4 y la Figura 13 lo comparan visualmente.

2. **Votación de centroides consciente de la distancia.** Cada punto submuestreado aprende su desplazamiento hasta el centroide de su diente, y solo votan los puntos cercanos a él. A eso se añaden dos pérdidas: una Chamfer, que ajusta el conjunto de centroides, y otra de separación, que evita que los centroides de dientes vecinos se junten. Después, DBSCAN agrupa los votos en un centroide por diente. La ablación (Tabla 1) mide cuánto aporta cada término.

3. **Segmentación en cascada con mapa de confianza.** Alrededor de cada centroide recortan los 4096 puntos más cercanos. Cada propuesta combina coordenadas, características y un campo de distancia al centroide. Una primera subred (S1) genera un mapa de confianza que la segunda (S2) usa como atención para afinar las zonas dudosas, sobre todo la frontera entre diente y encía. La Tabla 2 muestra la mejora frente a no usar cascada.

Además, **no asumen que la arcada esté completa**, cosa que sí hacían la mayoría de métodos anteriores (ver sección 1). Como TSegNet detecta los dientes uno a uno, el número de dientes no está fijado de antemano.

## 4. ¿Cómo demuestra que funciona? Datos, métricas y contra quién.

> The dataset includes a total of 2000 dental models (1000 upper jaws and 1000 lower jaws), where each dental surface contains about 150,000 faces and 80,000 vertices. To train the network, we randomly split it into three subsets, 1500 models for training, 100 models for validating and 400 models for testing.

El dataset son 2000 modelos dentales (1000 superiores y 1000 inferiores) de pacientes antes o después de la ortodoncia, con muchos casos anómalos: apiñamiento, dientes ausentes y brackets. Cada malla tiene unas 150 000 caras y 80 000 vértices. Se reparten al azar en 1500 para entrenamiento, 100 para validación y 400 para test. Los etiquetaron a mano, y el centroide de cada diente se calcula a partir de su máscara.

Como en DArch, **el dataset es privado**, así que sus cifras no se pueden comparar con las de Teeth3DS ni con las del reto.

Métricas:
- **Centroides:** MeanD y MaxD, calculadas en los dos sentidos (de los centroides reales a los predichos y al revés).
- **Segmentación:** DSC sobre la nube de puntos y DSC sobre la superficie de la malla, este ponderado por el área de las caras.
- **Identificación (etiquetado):** F1 macro, citando a Opitz & Burst 2019.

Entrenamiento: primero 500 épocas solo la red de centroides y luego 100 épocas conjuntas, con Adam y lr = 1e-3, en una 1080Ti (unas 4 h + 18 h).

Contra quién (Tabla 3): PointNet++, Harmonic Field (Zou 2015, semiautomático) y Mask-MCNet. Todos se entrenan con la misma entrada (coordenadas y normales).

| Método | DSC nube (%) | DSC superficie (%) | F1 (%) | Tiempo (s) |
|---|---:|---:|---:|---:|
| PointNet++ | 86.1 | 87.7 | 87.4 | **0.3** |
| Harmonic Field† | 93.2 | 93.4 | – | 30.0 |
| Mask-MCNet | 91.5 | 92.5 | 91.2 | 18.1 |
| TSegNet | **98.0** | **98.6** | **94.2** | 0.8 |

† semiautomático: necesita que el usuario marque información a mano, y no etiqueta los dientes.

TSegNet es el mejor en todo salvo en tiempo, donde PointNet++ es más rápido (0.3 s frente a 0.8 s). A Mask-MCNet le saca 6.5 puntos de DSC y 3 de F1, y es unas 22 veces más rápido.

Dato interesante de la Tabla 3: PointNet++ se queda en 73.0 de DSC en los premolares. Los autores lo explican porque los pacientes de ortodoncia están en recambio y tienen un número variable de premolares, y los niños no los tienen hasta los 10 años. **Es un ejemplo concreto de cómo un método que asume la dentición completa falla justo en los dientes que cambian.**

Ablación:
- **Tabla 1 (centroides):** cada término de la pérdida (filtro de distancia, Chamfer y separación) reduce el error de los centroides. La separación es la que más baja la MaxD, sobre todo en los incisivos apiñados (Figura 5).
- **Tabla 2 (segmentación):** el DSC medio en la nube pasa de 96.1 (base) a 97.4 (cascada) y a 98.0 (TSegNet). El F1 va de 92.5 a 93.4 y a 94.2.

Robustez (Figura 10): separan el test en 206 casos anormales y 194 normales. TSegNet apenas baja en los anormales, mientras que PointNet++ y Mask-MCNet caen bastante. Las cifras solo se ven en la gráfica, no dan números.

## 5. ¿Qué no dice o no mide?

**Nada garantiza que la numeración sea coherente.** Cada diente recibe su número FDI de forma independiente: se clasifica la característica global de su propuesta en S2 (la pérdida L_ID). No hay ningún paso que impida:
- que dos dientes reciban el mismo número;
- que los números no sigan el orden de la arcada;
- que un diente acabe con un número del lado equivocado.

No dan ninguna cifra de cuántas veces pasa esto.

**Nunca usan la arcada.** Ni la palabra aparece en el paper. Cada diente se detecta y se etiqueta mirando solo sus puntos cercanos, sin ninguna referencia a la posición que ocupa en el conjunto.

**El F1 macro no está bien definido para los dientes ausentes.** No explican qué pasa cuando un diente no está en el modelo, se detecta uno que no existe o se deja sin detectar uno que sí existe. Tampoco dan el F1 por tipo de diente.

**No hay cifras de identificación en los casos de dientes ausentes.** La Figura 14 distingue dos casos:
- (b) falta un diente pero no se ve ningún hueco, porque los vecinos lo han cerrado;
- (c) falta un diente y queda el hueco.

El caso (b) es justo el más difícil para etiquetar, ya que el número no se puede deducir por la posición. Solo muestran imágenes de que los centroides se detectan bien, no si los números salen bien.

**Fallos reconocidos (Figura 15):** no detecta una muela del juicio con forma anormal y segmenta mal un diente rudimentario. Lo atribuyen a que son casos poco frecuentes en el entrenamiento.

**Llamarlo *end-to-end* es generoso.** DBSCAN, el recorte de los 4096 puntos, la fusión de propuestas por IoU y la interpolación no se aprenden, y el entrenamiento va en dos fases.

**Erratas del paper:**
- En la ablación, el texto escribe «bNet_cp-C-CD» donde la Tabla 1 pone «bNet_cp-D-CD».
- El pie de la Tabla 3 habla de comparaciones «qualitative», pero son cuantitativas.
- «resolution deduction» debería ser *reduction*.
- «so they they» (duplicado en el original).

## 6. ¿Qué me llevo yo para el TFG?

1. **TSegNet ya etiqueta y ya usa mi argumento.** Detecta los dientes sin asumir la dentición completa, les pone número FDI y justifica el problema con el mismo dato del 70% de pacientes en recambio. No puedo presentar como novedad «etiquetar sin asumir 32 dientes». Además, en la ficha 03 lo describo solo como la arquitectura de dos etapas que copian IGIP y Chompers, y hay que añadir que etiqueta.
2. **Mi hueco hay que reformularlo así: etiquetar con coherencia global sin asumir la arcada completa.** TSegNet etiqueta cada diente por separado, sin mirar a los demás ni la arcada.

    Ojo, que el paso de coherencia no es nuevo del todo. IGIP (ficha 03) ya ordena los centroides sobre una parábola y corrige números repetidos o desordenados. Pero lo hace reordenando la secuencia de etiquetas, y el paper no explica qué ocurre cuando falta un diente y no queda hueco visible.

    Lo que yo aporto es asignar los números FDI de forma conjunta con el método húngaro (Kuhn 1955): sin repetir ninguno y dejando posiciones vacías cuando falten dientes (vía A). La forma de la arcada puede sacarse de DArch, que la estima a partir de los centroides.
3. **Tengo que medir lo que TSegNet no mide.** Para que el aporte se vea, la evaluación debe incluir:
    - la tasa de números repetidos y de errores de orden o de lado;
    - resultados separados en casos con dientes ausentes, sobre todo el caso sin hueco visible de la Figura 14(b).
4. **Es un listón de referencia para el etiquetado:** F1 = 94.2 en su dataset privado. No se puede comparar directamente con Teeth3DS, pero hay que citarlo junto a IGIP en la ficha 03 (líneas 322-324).
5. **Sirve para la Introducción y el Estado del arte.** Da el dato del 70% (Cobourne & DiBiase 2015) y el ejemplo de los premolares de PointNet++, que muestra por qué falla asumir la dentición completa.
6. **Cita:** Cui et al., *Medical Image Analysis* 69 (2021) 101949. Se publicó en línea en diciembre de 2020, por eso parte de la literatura lo cita como 2020. En la memoria usaré 2021, que es el volumen. Con esto queda resuelto el pendiente de la línea 340 de la ficha 03.

## 7. Pendiente de verificar

- Revisar si TSegNet tiene código público o si se ha reimplementado en 3DTeethSeg'22, para poder usarlo como línea base con Teeth3DS.
- DArch compara con TSegNet en su propio dataset (IoU 94.83 frente a 95.93 de DArch). Comprobar si esa comparación es con código original o reimplementado.
- Leer Mask-MCNet (Zanjani 2019) al menos por encima, porque es el principal rival con el que se comparan.

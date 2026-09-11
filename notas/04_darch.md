# DArch: Dental Arch Prior-assisted 3D Tooth Instance Segmentation with Weak Annotations

## 1. ¿Qué problema resuelve?

> Automatic tooth instance segmentation on 3D dental models is a fundamental task for computer-aided orthodontic treatments. Existing learning-based methods rely heavily on expensive point-wise annotations. To alleviate this problem, we are the first to explore a low-cost annotation way for 3D tooth instance segmentation, i.e., labeling all tooth centroids and only a few teeth for each dental model.

El problema es que existen métodos basados en el aprendizaje que dependen en gran medida de costosas anotaciones punto a punto. Hablan de que han conseguido ser los primeros en explorar una manera de anotar de bajo coste para la segmentación en instancia 3D donde se anotan todos los centroides y máscara solo en el 20% de los dientes. Anotar un modelo completo cuesta 30.5 minutos; con su anotación débil, 9.12 minutos.

## 2. ¿Qué le entra y qué le sale?

Dos modos:

- **Entrenamiento**: las dos redes se entrenan por separado. El detector aprende con todos los centroides y el segmentador con parches recortados alrededor de los pocos dientes que tienen máscara.
- **Inferencia**: es cuando las redes ya están entrenadas: modelo dental -> muestreo a nube de puntos -> detector de centroides -> recorte de un parche alrededor de cada centroide -> segmentador -> fusión de los parches.

Lo que sale después de esto es una máscara por diente, sin número, los colores son para diferenciar cada diente.

## 3. ¿Qué hace nuevo que los anteriores no hacían?

> We are the first to explore a low-cost annotation way for 3D tooth instance segmentation and propose a novel framework named DArch to handle this challenging task with weak annotations. We hope this attempt will inspire more learning-based methods in the weakly-annotated scenario. We propose a coarse-to-fine method to estimate the dental arch. Specifically, the dental arch is initially approximated by Bézier curve regression, and then a graph-based convolutional network (GCN) is used for further refinement. We introduce a dental arch-aware point sampling (APS) module for tooth centroid detection by introducing dental arch prior to assist the proposal generation. Extensive experiments have shown that our proposed DArch can vastly improve the performance of tooth centroid detection compared to other methods using other sampling strategies. As for the segmentation performance, our DArch is superior to the state-of-the-art methods in both weakly- and fully-annotated scenarios.

La arcada se aproxima primero mediante la regresión de una curva de Bézier y después una red convolacional sobre grafos (GCN) la ajusta.

Introducen un muestreo de puntos que tiene en cuenta la arcada dental (APS): donde VoteNet elige puntos repartidos uniformemente (FPS), DArch elige los que están cerca de la arcada.

Afirman que DArch supera a los métodos del estado del arte en segmentación, tanto con anotación débil como completa.

## 4. ¿Cómo demuestra que funciona? Datos, métricas y contra quién.

> We collected 4,773 3D dental models from 3,231 patients before orthodontics. We randomly select 3,973 models as the training models and the rest 800 models as the test models. All training dental models contain a total of 54,658 in teeth instances. All the dental models are fully annotated, in which all tooth instances of each dental model are manually labeled by professional dentists.

Cogieron 4773 modelos dentales 3D de 3231 pacientes antes de la ortodoncia. Seleccionaron aleatoriamente 3973 modelos para entrenamiento y los 800 restantes para test. Los modelos de entrenamiento contienen 54 658 / 3973 = 13.8 dientes por modelo, cifra muy parecida a los 13.3 de Teeth3DS

El dataset que han cogido es privado, no es el de Teeth3DS, así que sus cifras no se pueden comparar con las del reto.

Métricas: Acc, Recall y Chamfer Distance (C. Dist.) para la detección de centroides; IoU y Dice para la segmentación.

Contra quién: en detección contra VoteNet, MLCVNet, Group-free 3D, TSegNet y VoteNet & PointNet++; en segmentación, solo TSegNet y VoteNet & PointNet++. Las columnas *Weak* son el entrenamiento con máscara solo en el 20% de los dientes.

| Method | Tooth centroid detection |  |  | Tooth instance segmentation |  |  |  |
|---|---:|---:|---:|---:|---:|---:|---:|
|         | Acc. | Recall | C. Dist.       | Full IoU | Full Dice | Weak IoU | Weak Dice |
| VoteNet | 88.82 | 85.68 | 0.036 | - | - | - | - |
| MLCVNet | 90.86 | 85.68 | **0.033** | - | - | - | - |
| Group-free 3D | 91.14 | **92.70** | 0.035 | - | - | - | - |
| TSegNet | 99.41 | 84.94 | 0.037 | 94.83 | 96.91 | 93.39 | 95.83 |
| VoteNet & PointNet++ | 84.32 | **85.40** | 0.040 | 93.92 | 96.29 | 93.38 | 95.97 |
| DArch | **99.68** | 85.39 | 0.037 | **95.93** | **97.70** | **95.42** | **97.38** |

En detección de centroides son los mejores en Accuracy, y en segmentación obtienen los mejores resultados. No obstante, en Recall pierden por 7.3 puntos frente a Group-free 3D, y en C.Dist. tienen 0.004 más de distancia que MLCVNet (peor, porque cuanto menor, mejor).

DArch casi nunca se equivoca cuando detecta un diente (de ahí que destaquen tanto en Accuracy) pero se deja sin detectar ~15 de cada 100 en caso de que el Recall se calcule como es habitual.

En segmentación es el mejor en su propio dataset, donde solo tiene dos competidores y les saca entre 1 y 2 puntos de IoU sin dar desviación típica. No se puede decir que sea el mejor método de segmentación de dientes ya que no compitió en 3DTeethSeg'22, así que no hay comparación en terreno neutral.

## 5. ¿Qué no dice o no mide?

No etiqueta los dientes: la salida no lleva número FDI.

> some of which have missing, crowding, or misaligned teeth.

Mencionan los dientes ausentes, apiñados y malposicionados como reto, pero no dan ningún resultado sobre esos casos.

No se define cómo se calculan Acc y Recall.

No dicen qué dientes se quedan sin detectar.

El tiempo de anotación lo midió una sola persona, que además es uno de los autores del paper, sobre 10 modelos y sin decir en qué orden anotó cada tipo.

## 6. ¿Qué me llevo yo para el TFG? 

1. **Mi hueco sigue en pie.** DArch no compite con mi propuesta porque no etiqueta los dientes: solo los separa. Hay que corregir la ficha 03, que lo presenta como un método que usa la arcada para etiquetar (líneas 116 y 322-324, y el pendiente de la 343).
2. **La arcada se puede estimar a partir de los centroides.** DArch obtiene la curva de la arcada con una red aprendida (Bézier + GCN). Esa curva podría servirme de referencia para ordenar los dientes detectados antes de asignarles su número FDI.
3. **El Recall se queda en ~85%.** Un diente que no se detecta no se puede etiquetar. Además, para un etiquetado que trabaje sobre los centroides, un diente no detectado es indistinguible de un diente ausente: si la numeración va por posición, el fallo puede desplazar el número de los dientes vecinos.
4. **Dos citas útiles.**
    - **Noroozi 2001** (*The dental arch form revisited*, publicado en la revista *The Angle Orthodontist*): según DArch, muestra que la forma de la arcada humana se puede describir con la función beta. Sirve para Fundamentos teóricos.
    - **Kuhn 1955** (método húngaro): resuelve el problema de asignación, que consiste en emparejar dos conjuntos uno a uno con el menor coste total. DArch lo usa para muestrear puntos, a mí me serviría para asignar los números FDI a los dientes detectados sin repetir ninguno, dejando posiciones vacías cuando falten dientes (vía A).

## 7. Pendiente de verificar

- La fila Coarse + Fine de la Tabla 3 no coincide con ninguna configuración de las Tablas 1 y 2; revisar el Supplementary.
- Leer Noroozi 2001 para confirmar lo de la función beta, porque de momento solo lo sé por la cita de DArch.

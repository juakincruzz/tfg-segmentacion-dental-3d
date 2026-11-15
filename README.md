# Segmentación y etiquetado automático de dientes en escaneos intraorales 3D mediante aprendizaje profundo

Trabajo de Fin de Grado del Grado en Ingeniería Informática de la **Universidad de Granada** (ETSIIT).

- **Autor:** Joaquín Cruz Lorenzo
- **Tutor:** Pablo Mesejo Santiago (DECSAI)
- **Mentor:** Antonio David Villegas Yeguas

## El problema

Los escáneres intraorales reconstruyen la arcada dental en 3D mediante luz estructurada, sin necesidad de moldes de impresión ni de radiación ionizante. Estos modelos son cada vez más habituales en odontología clínica y tienen además interés forense: la comparación de registros dentales *antemortem* y *postmortem* constituye una herramienta para la identificación de víctimas de desastres (DVI).

Procesar estos datos manualmente es lento y laborioso. El objetivo de este trabajo es desarrollar un sistema capaz de **segmentar las coronas dentales e identificar cada pieza con su etiqueta FDI**, prestando especial atención a la coherencia de la numeración y a las posiciones correspondientes a dientes ausentes.

El problema presenta distintas dificultades: los dientes tienen formas similares, su posición en la arcada condiciona su identificación y pueden existir ausencias, desplazamientos dentales o alteraciones anatómicas.

El trabajo se centra en la segmentación y el etiquetado dental, como tareas previas a una posible comparación automática de registros. No realiza directamente la identificación forense de personas.

## Datos

Se utiliza **Teeth3DS+**, un conjunto de datos público publicado en el contexto del reto 3DTeethSeg'22 de MICCAI 2022.

Contiene **1.800 escaneos intraorales de 900 pacientes**, con una arcada superior y otra inferior por paciente. Cada escaneo incluye:

- Un archivo `.obj` con la malla tridimensional.
- Un archivo `.json` con las etiquetas FDI y los identificadores de instancia de cada vértice.

Los datos pueden descargarse desde el repositorio oficial de OSF:

**https://osf.io/xctdy/**

Para este proyecto se utilizan las partes 1 a 6, que contienen los escaneos y sus anotaciones. Se descarta la parte 7 al no disponer de las anotaciones necesarias para las tareas desarrolladas.

Los datos **no se incluyen en este repositorio**. Se distribuyen bajo licencia CC BY-NC-ND 4.0 y deben obtenerse desde su fuente original.

## Estructura

```text
memoria/        Memoria del TFG (LaTeX)
notas/          Fichas de lectura de la bibliografía
bibliografia/   Referencias y fichero .bib
src/            Código fuente
notebooks/      Exploración y análisis
tests/          Pruebas
resultados/     Resultados y análisis de los experimentos
data/           Datos originales y preprocesados (no versionados)
runs/           Pesos y registros de entrenamiento (no versionados)
```

## Instalación

El proyecto se desarrolla en **Python 3.14.4**, utilizando principalmente PyTorch y PyTorch Geometric.

Las versiones de las dependencias se encuentran especificadas en `requirements.txt`. La configuración actual utiliza PyTorch con soporte para CUDA 12.8 y está orientada al entrenamiento con una GPU NVIDIA compatible.

Desde la raíz del repositorio, se crea y activa un entorno virtual:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

A continuación, se instalan las dependencias:

```bash
python -m pip install -r requirements.txt
```

Para comprobar que la instalación funciona correctamente, se pueden ejecutar las pruebas:

```bash
python -m pytest tests/
```

## Estado del proyecto

Se ha completado la revisión bibliográfica inicial, el análisis de Teeth3DS y la implementación de las herramientas necesarias para preparar los datos y entrenar una primera línea base de segmentación.

El sistema utiliza una arquitectura **PointNet++**, adaptada para clasificar los puntos de los escaneos en 33 clases: encía y 32 posiciones dentales FDI.

Actualmente, el repositorio contiene los siguientes scripts:

- `src/teeth3ds.py`: lectura de escaneos de Teeth3DS y utilidades de numeración FDI. 
- `src/conteo_dientes.py`: estadísticas de dientes presentes y ausentes.
- `src/explorar_pyg.py`: exploración de las mallas y su representación en PyTorch Geometric.
- `src/figura_scopus.py`: generación de una figura sobre publicaciones científicas a partir de datos de Scopus.
- `src/preprocesar.py`: muestreo de puntos mediante FPS, normalización y conversión de etiquetas a 33 clases.
- `src/split_pacientes.py`: división de los datos por paciente, estratificada según el número de ausencias, sin contar los terceros molares.
- `src/split_oficial.py`: preparación de los conjuntos de entrenamiento, validación y prueba a partir de la división del reto.
- `src/dataset.py`: carga de los escaneos preprocesados como objetos `Data` de PyTorch Geometric.
- `src/modelo.py`: implementación de la arquitectura PointNet++ para segmentación semántica.
- `src/entrenar.py`: entrenamiento, validación y registro de métricas de la red.

Cada entrenamiento guarda en `runs/` todo lo que genera: los pesos del mejor modelo (`mejor.pt`), el registro por época (`registro.csv`) y el IoU por clase (`iou_mejor.csv`). Esta carpeta no se incluye en el control de versiones por el tamaño de los pesos. Las métricas de cada experimento, es decir, los dos archivos `.csv`, se copian después a `resultados/`, que sí se versiona.

El desarrollo de los métodos de numeración y asignación global, así como la evaluación completa del sistema, continúa en curso.

## Reproducción del entrenamiento

El proceso se organiza en tres etapas: preprocesado de los escaneos, generación de los conjuntos de datos y entrenamiento de la red.

Los comandos siguientes se ejecutan desde la raíz del repositorio, una vez instaladas las dependencias y descargado Teeth3DS.

### 1. Preprocesado

El primer paso consiste en seleccionar 16.000 puntos por escaneo mediante *Farthest Point Sampling* (FPS), normalizar las coordenadas y convertir las etiquetas FDI a clases consecutivas.

```bash
python src/preprocesar.py data \
    --salida data/procesado \
    --puntos 16000
``` 

Los escaneos procesados se guardan como archivos `.pt` para evitar repetir el muestreo durante cada época de entrenamiento.

Los escaneos con anotaciones FDI duplicadas se excluyen del procesamiento y sus identificadores se registran en `data/procesado/descartados.txt`.

### 2. División de los datos

Se utilizan dos divisiones alternativas.

**División propia**

Se realiza por paciente y se estratifica según el número de ausencias dentales, sin contar los terceros molares.

```bash
python src/split_pacientes.py data \
    --salida data/splits/propio \
    --semilla 42
```

La distribución prevista es del 64 % para entrenamiento, 16 % para validación y 20 % para prueba.

**División oficial del reto**

Se conserva el conjunto de prueba del reto 3DTeethSeg'22 y se divide su conjunto de entrenamiento en un 80 % para entrenamiento y un 20 % para validación, manteniendo la estratificación por ausencias.

Los archivos originales del reto deben estar en `data/splits/3DTeethSeg22/`.

```bash
python src/split_oficial.py data \
    --salida data/splits/oficial \
    --semilla 42
```

Ambas opciones generan los archivos `train.txt`, `val.txt` y `test.txt`, que pueden utilizarse directamente con el mismo `Dataset`.

### 3. Entrenamiento

Para entrenar PointNet++ utilizando la división propia:

```bash
python src/entrenar.py \
    --splits data/splits/propio \
    --procesado data/procesado \
    --epocas 30 \
    --batch-size 8 \
    --lr 0.001 \
    --salida runs/pointnet2_propio \
    --semilla 42
```

Para utilizar la división oficial, basta con cambiar `--splits` por `data/splits/oficial` y seleccionar otro directorio de salida.

El entrenamiento utiliza Adam y evalúa el modelo después de cada época mediante el conjunto de validación. Se conserva el modelo con el mejor mIoU de validación.

En el directorio indicado mediante `--salida` se generan:

- `mejor.pt`: pesos del mejor modelo.
- `registro.csv`: pérdida, exactitud, mIoU, *learning rate*, tiempo y memoria de GPU de cada época.
- `iou_mejor.csv`: IoU por clase del mejor modelo.

El mIoU utilizado durante el entrenamiento se calcula sobre los puntos muestreados. Las métricas oficiales de 3DTeethSeg'22 requieren una evaluación posterior sobre las mallas originales.

El conjunto de prueba no se utiliza para seleccionar el modelo ni ajustar sus hiperparámetros.

## Licencia

El código de este repositorio se publica bajo licencia MIT (ver [LICENSE](LICENSE)).

Esta licencia no alcanza a los conjuntos de datos ni a la bibliografía referenciada, que conservan sus condiciones de uso originales.
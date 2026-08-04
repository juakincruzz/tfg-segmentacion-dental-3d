# Clinical Application of Intraoral Scanners in Dentistry: A Narrative Review

- **Referencia:** Lee, Y.; Ku, H.-M.; Jun, M.-K. *Oral* **2024**, 4(4), 639–652. DOI: 10.3390/oral4040049
- **Clave BibTeX:** `leeClinicalApplicationIntraoral2024`
- **Tipo:** revisión narrativa clínica. 50 estudios, enero 2014 – noviembre 2024, sobre PubMed, Scopus y Web of Science.
- **Leído:** 4 de agosto de 2026

## De qué va

Revisa para qué se usan los escáneres intraorales (IOS) en la clínica dental: diagnóstico de caries, desgaste, placa y enfermedad periodontal; eficiencia en ortodoncia, prostodoncia y cirugía maxilofacial; y experiencia de paciente y operador.

**Da poco para este TFG y conviene saberlo de antemano.** Solo alimenta la Introducción. No explica cómo funciona un escáner ni contiene nada computacional.

> **Nota de lectura:** el artículo real ocupa las líneas 264–406 del Markdown; todo lo anterior es *boilerplate* de MDPI. Las tablas con los modelos de escáner están al final, a partir de la línea 536, detrás de la bibliografía.

---

## Cajón: INTRODUCCIÓN

### Qué es un IOS y qué captura

> "Intraoral scanners (IOSs) have established themselves as essential devices in digital innovation, playing a crucial role in collecting the shape and size of the dental arch through 3D imaging technology and digitizing anatomical structures within the oral cavity."

→ Definición de partida. La unidad de trabajo es la **arcada completa**, no dientes sueltos.

### Por qué sustituyen a la impresión tradicional

> "Traditional physical impression methods cause discomfort for patients and have limitations in accuracy due to deformation or errors in the impression material. Additionally, plaster cast models obtained from these impressions have several drawbacks, such as the potential for breakage, wear from continuous measurements, and the need for storage space in dental offices."

→ Coincide con lo que el paper 1 dice desde el lado forense: los modelos de escayola se rompen, se desgastan y ocupan espacio, y las consultas están dejando de guardarlos.

### El párrafo que respalda la propuesta del TFG

> "The clinical applications of IOSs are gradually expanding, particularly in areas such as orthodontic treatment, the fabrication of fixed and removable prosthetics, dental implant planning, and oral and maxillofacial surgery. Digital data allows for in-depth analyses, such as spatial analysis, treatment simulations, movement predictions, and tooth shape analyses, contributing to reducing errors during treatment processes and enhancing patient satisfaction."

→ **La cita más rentable del paper.** La propuesta del TFG afirma que estos modelos permiten *"la simulación del movimiento, extracción y modificación de las estructuras dentales en entornos clínicos"*. Aquí está la fuente que lo sostiene casi literalmente: *movement predictions*, *tooth shape analyses*, *treatment simulations*.

### Precisión clínica

> "When an IOS was used, the average difference was only 0.022 mm, which was confirmed to be within the clinically acceptable range."

→ El número duro. Contexto a no olvidar: el estudio es en **dentición mixta** (temporales y permanentes conviviendo), lo que enlaza con la duda pendiente de si en Teeth3DS aparecen los cuadrantes 5–8.

### Sensibilidad a nivel de micras

Con defectos artificiales de 60, 80 y 120 micras:

> "In particular, small defects were detected more reliably than large defects. This suggests that 3D scanning tools such as the IOS can be very effective in monitoring subtle changes in the tooth structure."

→ *Monitoring subtle changes* = comparar adquisiciones del mismo sujeto separadas en el tiempo. Es exactamente la operación que el paper 1 describe como base de la comparación AM/PM. **Evidencia técnica de que la resolución da para el uso forense.**

---

## Cajón: DIFICULTAD DEL PROBLEMA

### Brackets: están en los datos porque no se retiran

> "In addition, even when equipped with multi-bracket appliances, it is not necessary to remove the archwire before IOS because there is almost no distortion in the digital model, which contributes to the simplification of the photographing process and to the patient's comfort."

→ Razón clínica de por qué aparecen brackets en los escaneos reales. La propuesta del TFG los cita como fuente de dificultad; esta es la justificación de que no es un caso rebuscado sino práctica rutinaria.

### Variabilidad del operador

> "Another study also showed that scanning practice and clinical experience affected the reproducibility of IOS and the image quality of digital scanners."

→ Distinto operador, distinta calidad de malla. Fuente de variabilidad en los datos de entrada; justifica la necesidad de robustez.

---

## Cajón: LIMITACIONES

### Apertura bucal mínima

> "However, the IOS has limitations in clinical applications because it cannot sufficiently capture soft tissue information when the mouth opening is less than 20 mm."

→ **Cruzar con el paper 1**, que señala que el rigor mortis dificulta abrir las mandíbulas de un cadáver. Juntos delimitan una restricción real del escaneo intraoral postmortem. Observación propia, no de los autores. Va a Conclusiones o trabajo futuro.

### Falta de estandarización

> "...new research results may appear depending on the need for standardization and evaluation criteria."

→ Justifica por qué importan los benchmarks públicos con métricas comunes. Puente natural hacia el paper 3 y el reto 3DTeethSeg.

---

## Hardware citado (tablas del final)

TRIOS 3 y TRIOS 4 (3Shape, Copenhague) · iTero Element 2 y 5D (Align Technology) · CS 3600 (Carestream) · 3M True Definition · Maestro3D.

→ Sirve para nombrar hardware real al describir la modalidad de imagen. **Comprobar con qué escáner se capturó Teeth3DS**: si coincide con alguno, hay una frase gratis conectando el dataset con la práctica clínica.

---

## Cajones vacíos

**Estado del arte, Métodos, Experimentos** y, lo más relevante, **Fundamentos teóricos de adquisición**: el paper no explica en ningún momento cómo funciona un escáner intraoral. Ni luz estructurada, ni confocal, ni resolución, ni formato de salida.

→ **Hueco identificado:** la propuesta del TFG dice explícitamente *"usando luz estructurada"* y ahora mismo no hay fuente que lo respalde. Hace falta otra referencia para la parte técnica de adquisición.

Cuatro cajones de seis vacíos.

---

## Criterio sobre el peso de la fuente

Es una revisión **narrativa**, no sistemática, en *Oral*, una revista modesta de MDPI. Vale perfectamente para sostener que los escáneres intraorales están extendidos en la práctica clínica, que es lo que se le pide. No conviene apoyar en ella ninguna afirmación técnica fuerte.

## ¿Volver a él?

No. Exprimido.

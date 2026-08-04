# Segmentación y etiquetado automático de dientes en escaneos intraorales 3D mediante aprendizaje profundo

Trabajo de Fin de Grado del Grado en Ingeniería Informática de la **Universidad de Granada** (ETSIIT).

- **Autor:** Joaquín Cruz Lorenzo
- **Tutor:** Pablo Mesejo Santiago (DECSAI)
- **Mentor:** Antonio David Villegas Yeguas

## El problema

Los escáneres intraorales reconstruyen la arcada dental en 3D mediante luz estructurada, sin necesidad de moldes de impresión ni de radiación ionizante. Estos modelos son cada vez más habituales en odontología clínica y tienen además interés forense: la comparación de adquisiciones separadas en el tiempo es la base de la identificación de restos en operaciones de identificación de víctimas de desastres (DVI).

Procesar estos datos a mano es lento y tedioso. El objetivo de este trabajo es desarrollar modelos de aprendizaje profundo capaces de **segmentar las coronas dentales e identificar cada pieza con su etiqueta FDI** a partir de la malla 3D, incluyendo la detección de dientes ausentes.

No es un problema trivial: los dientes se parecen entre sí, su posición en la arcada condiciona la interpretación, y hay que lidiar con piezas dañadas, brackets de ortodoncia y diversas patologías.

## Datos

Se emplea **3DTeethSeg / Teeth3DS**, un conjunto público de 1800 escaneos intraorales anotados, publicado como parte de uno de los retos de la conferencia MICCAI 2022.

Los datos **no se incluyen en este repositorio**: se distribuyen bajo licencia CC BY-NC-ND 4.0 y deben obtenerse desde su fuente original.

## Estructura

```
memoria/        Memoria del TFG (LaTeX)
notas/          Fichas de lectura de la bibliografía
bibliografia/   Referencias y fichero .bib
src/            Código fuente
notebooks/      Exploración y análisis
tests/          Pruebas
data/           Datos (no versionado)
```

## Estado

Fase inicial: revisión bibliográfica. Todavía no hay código.

## Licencia

El código de este repositorio se publica bajo licencia MIT (ver [LICENSE](LICENSE)). Esta licencia no alcanza a los conjuntos de datos ni a la bibliografía referenciada, que conservan sus condiciones de uso originales.

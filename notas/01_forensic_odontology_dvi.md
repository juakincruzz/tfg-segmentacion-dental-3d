# Forensic odontology in DVI: current practice and recent advances

- **Referencia:** Forrest, A. *Forensic Sciences Research* **2019**, 4(4), 316–330. DOI: 10.1080/20961790.2019.1678710
- **Clave BibTeX:** `forrestForensicOdontologyDVI2019`
- **Tipo:** revisión de campo, escrita desde la práctica forense. Sin componente computacional.
- **Leído:** 3–4 de agosto de 2026

## De qué va

Describe cómo se identifica a las víctimas de un desastre masivo comparando el perfil dental *antemortem* (AM), reconstruido a partir de los registros del dentista, con el perfil *postmortem* (PM), obtenido examinando los restos. Repasa los tipos de registro disponibles ordenados de menos a más fiables, y termina argumentando que el futuro del campo está en los datos 3D.

**Es la fuente de motivación del TFG, no de método.** Es de 2019: anterior al reto 3DTeethSeg y a todo el aprendizaje profundo sobre mallas dentales. No menciona una sola red neuronal. No debe citarse como estado del arte.

---

## Cajón: INTRODUCCIÓN

### Impacto cuantificado de la odontología forense

> "When good-quality AM data are available, forensic odontology classically identifies approximately 60% of victims, and contributes to approximately 30% of further identifications in collaboration with other identifying methods."

→ Cifra de impacto para abrir la memoria: justifica que el problema importa y a cuánta gente afecta.

### El 3D es el futuro declarado del campo

> "The future of forensic odontology DVI techniques is likely to include the use of 3D datasets for comparison."

→ Un autor de dentro del campo, no un informático, señalando la dirección. Es la frase que conecta el problema forense con la modalidad de imagen del TFG.

### Ventajas del escaneo 3D de superficie frente a las alternativas

> "They do not rely on ionising radiation (unlike X-rays and CT scans) and are not affected by the presence of prior dental treatments. Unlike CT data, they are equally useful regardless of whether the teeth contain fillings (of any material) or not."

→ Justifica **por qué esta modalidad y no radiografía ni TC**. El TC sufre *beam hardening* con las restauraciones metálicas; el escaneo de superficie no. Con la ironía que el propio paper señala: en TC, los casos con más valor identificativo (muchos empastes metálicos) son justo los peor reconstruidos.

---

## Cajón: FUNDAMENTOS TEÓRICOS

### Notación FDI — la definición formal de las etiquetas del problema

> "the mouth is divided into four quadrants; the upper right quadrant is indicated as quadrant 1, the upper left as quadrant 2, and so on clockwise around the mouth. Within each quadrant there are eight teeth in a fully dentate adult mouth, and they are numbered 1 to 8 from the midline backwards."

| Cuadrante | Zona | Dientes |
|---|---|---|
| 1 | Superior derecho | 11–18 |
| 2 | Superior izquierdo | 21–28 |
| 3 | Inferior izquierdo | 31–38 |
| 4 | Inferior derecho | 41–48 |

**Derecha e izquierda son las del paciente, no las del observador.** Confirmado en el pie de la Figura 1 del propio paper: el diente 45 es el segundo premolar inferior *derecho*.

→ Va a Fundamentos teóricos, con diagrama propio. Es además la especificación contra la que validar los datos: qué etiquetas son legales y a qué lado del plano sagital debe caer cada cuadrante.

**Cuidado en el código:** si en el preprocesado se espeja una malla o se cambia el signo de un eje, se intercambian los cuadrantes 1↔2 y 3↔4 sin que nada falle. Candidato claro a test.

### Ninguna notación cubre los dientes supernumerarios

> "None of these systems has gained full international acceptance and none of them copes with supernumerary teeth."

→ Limitación del propio esquema de etiquetado, no del método. Relevante para discutir casos límite.

---

## Cajón: DIFICULTAD DEL PROBLEMA

> "Teeth may be missing because they have failed to develop. The presence of disease or pathology including periodontal (gum) conditions and dental caries (tooth decay), the presence of tooth crowding, or unusual arrangements of teeth in a dental arch [...] can all add additional features for comparison."

→ El paper lo enumera como *ventaja* para individualizar a una persona. Para el TFG es justo lo contrario: **es lo que rompe el etiquetado**. Agenesias, apiñamiento y disposiciones atípicas desplazan la numeración secuencial de la arcada. Es la razón clínica de por qué el etiquetado FDI es más difícil que la segmentación, y coincide con lo que la propuesta del TFG menciona sobre dientes faltantes y patologías.

---

## Cajón: TRABAJO FUTURO Y HUECO QUE JUSTIFICA EL TFG

### El proceso está sin automatizar

> "It is likely that the technique of 3 D comparison will become increasingly important for use in single-case identifications and this process potentially can be automated for use in DVI operations."

### No hay herramientas

> "At present, there is a dearth of affordable easy-to-use public-domain software running on multiple platforms to permit easy and quick 3 D object comparisons from multiple different imaging modalities"

Lo mejor que cita disponible es MeshLab.

### Preguntas abiertas que el propio autor enuncia

> "The smallest fragment size that can be used to confidently identify an individual using this technique is not known, and since some disasters involve fragmentation of the jaws, this is an important question to answer."

> "To what extent does major dental restorative work affect the outcome? Data are not yet available on the results of comparing orthodontic scans (a specialty that routinely scans entire dental arches) when the teeth are moved during treatment."

→ Material directo para el capítulo de trabajo futuro.

### Sobre la unicidad dental

> "The question of whether dentitions are recognisably unique has never been answered, just as it has never been answered for fingerprints."

→ Honestidad científica del campo. Conviene recogerlo: da rigor y evita sobrevender lo que la identificación dental demuestra.

---

## Cajones vacíos

**Estado del arte, Métodos y Experimentos.** El paper no contiene ningún método computacional. Ya ha dado todo lo que tenía.

---

## Conexiones

- Con el **paper 2**: aquí se dice que ortodoncia y prostodoncia son los adoptantes tempranos del escaneo 3D y que hay que pedirles los registros; el paper 2 lo confirma con datos, siendo ortodoncia su bloque de aplicación mayor.
- Con el **paper 2**, observación propia: aquí se menciona que *"rigor mortis may cause difficulty in opening the jaws"*; el paper 2 dice que por debajo de 20 mm de apertura bucal el escáner no captura bien. **Juntos identifican una limitación real del escaneo intraoral postmortem que ninguno de los dos enuncia por separado.** No es de ninguno de los dos autores: es aportación propia y va a Conclusiones.

## Delimitación importante para la memoria

Este paper trata de **comparar** un perfil AM contra uno PM para identificar a una persona. **El TFG no hace eso**: hace el paso previo, segmentar y etiquetar los dientes de un único escaneo.

Es un prerrequisito necesario y bien motivado —sin dientes individualizados y numerados no hay comparación estructurada posible—, pero no es identificación. Plantearlo de otro modo en la Introducción es una pregunta garantizada en la defensa.

Formulación honesta y más sólida: *este trabajo aborda la etapa de estructuración automática del modelo 3D, prerrequisito de la comparación AM/PM que la literatura forense señala como el futuro del campo pero que sigue sin automatizar.*

## ¿Volver a él?

No, salvo para recuperar alguna cita concreta. Está exprimido.

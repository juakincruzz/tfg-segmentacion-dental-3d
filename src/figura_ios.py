"""Busca una arcada con ausencia intercalada y crea una figura de tres paneles.

Ejemplos (desde la raíz del repositorio):
    python src/figura_ios.py --buscar data/
    python src/figura_ios.py data/lower/<id>/<id>_lower.obj imagenes/figura_ios.png
    python src/figura_ios.py data/lower/<id>/<id>_lower.obj imagenes/figura_ios.png --elev 90

(a) Malla tridimensional original del escaneo, representada en gris.
(b) Etiquetas FDI de referencia y posición ausente.
(c) Simulación de una numeración consecutiva sin respetar el hueco.

El panel (c) es una simulación didáctica, NO una predicción de PointNet++.
No se modifican los datos originales del escaneo.
"""

import argparse
from pathlib import Path

import numpy as np

from teeth3ds import (
    FDI_POR_ARCADA,
    dientes_ausentes,
    dientes_presentes,
    es_tercer_molar,
    leer_anotacion,
    listar_escaneos
)

COLORES = {
    0: "#D9D9D9", # Encía
    1: "#0072B2", # Incisivo
    2: "#0072B2", # Incisivo
    3: "#E69F00", # Canino
    4: "#009E73", # Premolar
    5: "#009E73", # Premolar
    6: "#D55E00", # Molar
    7: "#D55E00", # Molar
    8: "#D55E00", # Molar
}

# Profundidad máxima de la base que se mostrará.
# Umbral ajustado visualmente para mejorar la presentación.
UMBRAL_BASE_MM = 6.0

def ausencia_intercalada(presentes, arcada):
    """Devuelve el único ausente NO tercer molar, si tiene ambos vecinos.
    Un vecino tiene que pertenecer al mismo cuadrante (se comprueba 
    explícitamente, para no emparejar posiciones de cuadrantes distintos)."""
    presentes = set(presentes)
    ausentes = [
        d for d in dientes_ausentes(presentes, arcada)
        if not es_tercer_molar(d)
    ]
    if len(ausentes) != 1: return None

    d = ausentes[0]
    mismo_cuadrante = d // 10 == (d - 1) // 10 == (d + 1) // 10

    if mismo_cuadrante and d - 1 in presentes and d + 1 in presentes: return d

    return None

def leer_descartados(raiz):
    ruta = Path(raiz) / "procesado" / "descartados.txt"

    if not ruta.is_file():
        print(f"Aviso: {ruta} no existe; no se pueden excluir descartes registrados.")
        return set()

    return {
        linea.strip() for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    }

def buscar_candidatos(raiz):
    """Lista escaneos aptos para la figura, sin cargar las mallas OBJ."""
    raiz = Path(raiz)
    descartados = leer_descartados(raiz)
    candidatos = []

    for ruta_json in listar_escaneos(raiz):
        if ruta_json.stem in descartados: continue

        if not ruta_json.with_suffix(".obj").is_file(): continue

        anotacion = leer_anotacion(ruta_json)
        arcada = anotacion["jaw"]
        presentes = dientes_presentes(anotacion["labels"])
        ausente = ausencia_intercalada(presentes, arcada)

        if ausente is not None:
            candidatos.append((str(anotacion["id_patient"]), arcada, ausente, ruta_json.with_suffix(".obj")))

    # Primero los casos con ausencia del 35; luego el resto por identificador.
    candidatos.sort(key=lambda x: (x[2] != 35, x[1] == "lower", x[0]))
    print(f"Candidatos encontrados: {len(candidatos)}")
    print("ID paciente           Arcada  FDI ausente  Ruta OBJ")
    for identificador, arcada, ausente, ruta_obj in candidatos:
        print(f"{identificador:<20}  {arcada:<7}  {ausente:<12}  {ruta_obj}")
    print("\nAbrir varios candidatos en MeshLab y elegir uno sin brackets y con buena geometría.")

    return candidatos


def mayoria_por_cara(etiquetas, caras):
    """Etiqueta mayoritaria entre los tres vértices de cada triángulo.
    
    Si las tres etiquetas son distintas, no hay mayoría: el triángulo se
    representa como borde de encía (0), en lugar de inventar una etiqueta.
    """
    e = etiquetas[caras]
    a, b, c = e[:, 0], e[:, 1], e[:, 2]

    return np.where(a == b, a, np.where(a == c, a, np.where(b == c, b, 0)))


def leer_malla(ruta_obj):
    import trimesh

    ruta_obj = Path(ruta_obj)
    ruta_json = ruta_obj.with_suffix(".json")
    if not ruta_json.is_file(): raise FileNotFoundError(f"No se encuentra el JSON: {ruta_json}")

    # No procesar: los índices del OBJ deben seguir correspondiendo al JSON.
    malla = trimesh.load_mesh(ruta_obj, process=False)
    if not isinstance(malla, trimesh.Trimesh): raise ValueError(f"El OBJ no contiene una única malla: {ruta_obj}")

    anotacion = leer_anotacion(ruta_json)
    etiquetas = anotacion["labels"]
    if len(etiquetas) != len(malla.vertices): 
        raise ValueError(f"Las etiquetas FDI y los vértices no coinciden: "
                         f"{len(etiquetas)} frente a {len(malla.vertices)}")

    if not len(malla.faces): raise ValueError(f"La malla no contiene triángulos.")

    arcada = anotacion["jaw"]
    if arcada not in FDI_POR_ARCADA: raise ValueError(f"Arcada no reconocida: {arcada}")

    permitidos = set(FDI_POR_ARCADA[arcada]) | {0}
    otros = set(dientes_presentes(etiquetas)) - permitidos

    if otros: raise ValueError(f"El JSON contiene etiquetas incompatibles: {sorted(otros)}")

    ausente = ausencia_intercalada(dientes_presentes(etiquetas), arcada)
    if ausente is None: raise ValueError(f"Este escaneo no tiene exactamente una ausencia intercalada "
                                         "(excluyendo terceros molares). Usa --buscar.")

    # Teeth3DS no proporciona colores RGB útiles de forma consistente.
    # El panel (a) representa la malla en gris, conservando su relieve.
    rgb_cara = np.full((len(malla.faces), 3), 200 / 255.0, dtype=np.float32)
    fdi_cara = mayoria_por_cara(etiquetas, malla.faces)

    return malla, etiquetas, rgb_cara, fdi_cara, arcada, ausente


def centroides_dentales(vertices, etiquetas):
    return {
        fdi: vertices[etiquetas == fdi].mean(axis=0)
        for fdi in dientes_presentes(etiquetas)
    }


def ejes_oclusales(centroides, arcada):
    """Calcula una rotación para alinear el plano oclusal con XY."""

    puntos = np.array(list(centroides.values()))
    centro = puntos.mean(axis=0)

    # Ajustar el plano de los centroides mediante SVD.
    _, _, vh = np.linalg.svd(puntos - centro, full_matrices = False)
    normal_plano = vh[-1]
    normal_plano /= np.linalg.norm(normal_plano)

    anteriores = np.array([
        p for d, p in centroides.items() if d % 10 <= 2
    ])
    posteriores = np.array([
        p for d, p in centroides.items() if 6 <= d % 10 <= 8
    ])

    q_derecho, q_izquierdo = (
        (1, 2) if arcada == "upper" else (4, 3)
    )

    derecha = np.array([
        p for d, p in centroides.items() if d // 10 == q_derecho
    ])
    izquierda = np.array([
        p for d, p in centroides.items() if d // 10 == q_izquierdo
    ])

    if any(len(x) == 0 for x in (anteriores, posteriores, derecha, izquierda)):
        raise ValueError("No hay suficientes dientes para orientar la arcada.")

    # Eje Y: desde los dientes posteriores hacia los incisivos.
    frente = anteriores.mean(axis=0) - posteriores.mean(axis=0)
    frente -= np.dot(frente, normal_plano) * normal_plano

    norma = np.linalg.norm(frente)

    if norma < 1e-8: raise ValueError("No se puede determinar la dirección anterior.")

    frente /= norma

    # Eje X: desde la derecha del paciente hacia su izquierda.
    horizontal = izquierda.mean(axis=0) - derecha.mean(axis=0)

    horizontal -= np.dot(horizontal, normal_plano) * normal_plano
    horizontal -= np.dot(horizontal, frente) * frente

    norma = np.linalg.norm(horizontal)

    if norma < 1e-8: raise ValueError("No se puede determinar la lateralidad.")

    horizontal /= norma

    # Producto vectorial para garantizar un sistema dextrógiro (Z hacia arriba).
    normal = np.cross(horizontal, frente)
    normal /= np.linalg.norm(normal)

    rotacion = np.stack([horizontal, frente, normal])

    # Comprobar que es una rotación y no una reflexión.
    if not np.isclose(np.linalg.det(rotacion), 1.0, atol = 1e-6):
        raise ValueError("La transformación no es una rotación válida.")

    return rotacion, centro

def transformar(vertices, centroides, arcada):
    """Rota los vértices y centroides solo para su visualización."""

    rotacion, centro = ejes_oclusales(centroides, arcada)

    puntos = (vertices - centro) @ rotacion.T

    centros = {
        fdi: (pos - centro) @ rotacion.T
        for fdi, pos in centroides.items()
    }

    return puntos, centros


def numeracion_simulada(centros, arcada):
    """Simula ordenación desde la línea media en cada cuadrante.

    Se usa atan2 respecto al centro de la arcada (media de centroides).
    Esta asignación NO proviene del modelo entrenado ni del método N2 real.
    """
    centro_xy = np.mean(np.array(list(centros.values()))[:, :2], axis=0)
    derecho = (1 if arcada == "upper" else 4)
    asignacion = {}

    for cuadrante in ((1, 2) if arcada == "upper" else (3, 4)):
        dientes = [d for d in centros if d // 10 == cuadrante]

        def angulo_desde_linea_media(d):
            x, y = centros[d][:2] - centro_xy
            angulo = np.arctan2(y, x)

            if cuadrante == derecho: return (angulo + np.pi / 2) % (2 * np.pi)

            return (3 * np.pi / 2 - angulo) % (2 * np.pi)

        for i, d in enumerate(sorted(dientes, key = angulo_desde_linea_media), start = 1):
            asignacion[d] = cuadrante * 10 + i

    return asignacion


def colores_de_cara(etiquetas_cara, asignacion = None):
    from matplotlib.colors import to_rgb

    asignacion = asignacion or {}
    tabla_rgb = {clase: to_rgb(hex_color) for clase, hex_color in COLORES.items()}
    colores = np.empty((len(etiquetas_cara), 3), dtype=np.float32)

    for fdi in np.unique(etiquetas_cara):
        fdi = int(fdi)
        numero = asignacion.get(fdi, fdi)
        tipo = 0 if numero == 0 else numero % 10
        colores[etiquetas_cara == fdi] = tabla_rgb[tipo]

    return colores


def elevacion_automatica(vertices, etiquetas):
    """Estimación de qué lado de la malla mira hacia las coronas."""
    diente = vertices[etiquetas != 0, 2]
    encia = vertices[etiquetas == 0, 2]

    if len(diente) == 0 or len(encia) == 0: return 90

    return 90 if np.median(diente) >= np.median(encia) else -90


def dibujar(ruta_obj, salida, elev = None):
    import matplotlib
    matplotlib.use("Agg")
    # Se registra Axes3D antes de crear subplots, útil para algunas instalaciones.
    from mpl_toolkits.mplot3d import Axes3D # noqa: F401
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    from matplotlib.patches import Patch

    malla, etiquetas, rgb_real, fdi_cara, arcada, ausente = leer_malla(ruta_obj)
    vertices = np.asarray(malla.vertices)
    caras = np.asarray(malla.faces)
    centroides = centroides_dentales(vertices, etiquetas)
    puntos, centros = transformar(vertices, centroides, arcada)
    asignacion = numeracion_simulada(centros, arcada)
    esperado = {
        d: d - 1 if d // 10 == ausente // 10 and d > ausente else d
        for d in centros
    }

    if asignacion != esperado:
        raise ValueError(
            "La ordenación angular no reproduce el desplazamiento FDI esperado. "
            "Elige otro escaneo o comprueba sus centroides antes de publicar "
            "la figura. Orden obtenido: " + str(asignacion)
        )

    # El valor es automático, pero se puede forzar con --elev +90 / -90.
    if elev is None: elev = elevacion_automatica(puntos, etiquetas)

    # Con una vista desde -Z, invertimos SOLO la coordenada de representación X,
    # para conservar las posiciones izquierda/derecha en la imagen final.
    if elev == -90:
        puntos[:, 0] *= -1

        for c in centros.values():
            c[0] *= -1

    azim = -90 if elev == 90 else 90

    colores_gt = colores_de_cara(fdi_cara)
    colores_sim = colores_de_cara(fdi_cara, asignacion)
    colores_paneles = (rgb_real, colores_gt, colores_sim)

    # Eliminar las caras de la base situadas a más de 6 mm
    # por debajo del plano definido por los centroides dentales.
    signo_corona = 1 if elev == 90 else -1

    altura_cara = (
        puntos[caras][:, :, 2] * signo_corona
    ).min(axis = 1)

    # Conservar todos los dientes y la encía próxima a las coronas.
    mantener = (fdi_cara != 0) | (altura_cara > -UMBRAL_BASE_MM)

    # Eliminar triángulos de encía con aristas superiores a 3 mm.
    vertices_cara = puntos[caras]

    arista_1 = np.linalg.norm(vertices_cara[:, 0] - vertices_cara[:, 1], axis = 1)
    arista_2 = np.linalg.norm(vertices_cara[:, 1] - vertices_cara[:, 2], axis = 1)
    arista_3 = np.linalg.norm(vertices_cara[:, 2] - vertices_cara[:, 0], axis = 1)
    arista_maxima = np.maximum.reduce([arista_1, arista_2, arista_3])

    mantener &= (fdi_cara != 0) | (arista_maxima <= 3.0)

    # Aplicar la misma máscara a las caras y a los tres paneles.
    caras = caras[mantener]
    colores_paneles = tuple(colores[mantener] for colores in colores_paneles)

    # Posición Z de los rótulos por encima de la corona, no en el centro del diente.
    zmin, zmax = float(puntos[:, 2].min()), float(puntos[:, 2].max())
    separacion_z = max(zmax - zmin, 1.0) * 0.04
    signo = 1 if elev == 90 else -1
    z_texto = {
        fdi: (float(puntos[etiquetas == fdi, 2].max()) if elev == 90
              else float(puntos[etiquetas == fdi, 2].min())) + signo * separacion_z
        for fdi in centros
    }
    falta_xy = (centros[ausente - 1][:2] + centros[ausente + 1][:2]) / 2
    z_falta = max(z_texto.values()) if elev == 90 else min(z_texto.values())

    # Polígonos compartidos en los tres paneles, con idéntica perspectiva.
    triangulos = puntos[caras]

    # Calcular los límites únicamente con los vértices visibles.
    puntos_visibles = puntos[np.unique(caras)]
    minimo = puntos_visibles.min(axis=0)
    maximo = puntos_visibles.max(axis=0)

    rangos = np.maximum(maximo - minimo, 1e-5)
    margenes = np.array([0.06, 0.06, 0.10]) * rangos

    fig, ejes = plt.subplots(1, 3, subplot_kw={"projection": "3d"}, figsize=(12, 3.5), dpi = 120)
    luz = LightSource(azdeg = 315, altdeg = 80)

    for i, (ax, color_cara) in enumerate(zip(ejes, colores_paneles)):
        coleccion = Poly3DCollection(triangulos, facecolors = color_cara, linewidths = 0, 
                                     shade = True, lightsource = luz, antialiased = False, rasterized = True)
        ax.add_collection3d(coleccion)
        ax.set_xlim(minimo[0] - margenes[0], maximo[0] + margenes[0])
        ax.set_ylim(minimo[1] - margenes[1], maximo[1] + margenes[1])
        ax.set_zlim(minimo[2] - margenes[2], maximo[2] + margenes[2])
        ax.set_box_aspect(rangos, zoom = 1.4)
        ax.view_init(elev = elev, azim = azim, roll = 0)
        ax.set_proj_type("ortho")
        ax.set_axis_off()
        ax.set_title(f"({chr(ord('a') + i)})", fontsize = 13, pad = 2)

        if i == 0: continue

        for fdi, c in centros.items():
            etiqueta = (asignacion[fdi] if i == 2 else fdi)
            rojo = i == 2 and etiqueta != fdi
            ax.text(c[0], c[1], z_texto[fdi], str(etiqueta), zdir = None,
                    ha = "center", va = "center", fontsize = 6, 
                    color = "#BC2525" if rojo else "#101010",
                    weight = "bold", zorder = 20, 
                    bbox = {"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.88})

        if i == 1:
            ax.text(falta_xy[0], falta_xy[1], z_falta, f"({ausente})", zdir = None,
                    ha = "center", va = "center", fontsize = 6, color = "#4A4A4A", zorder = 21,
                    bbox = {"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "#7A7A7A", "alpha": 0.90})

    fig.legend(
        handles = [
            Patch(facecolor = COLORES[1], label = "Incisivo"),
            Patch(facecolor = COLORES[3], label = "Canino"),
            Patch(facecolor = COLORES[4], label = "Premolar"),
            Patch(facecolor = COLORES[6], label = "Molar"),
            Patch(facecolor = COLORES[0], label = "Encía")
        ], 
        loc = "lower center", ncol = 5, frameon = False, fontsize = 8,
        bbox_to_anchor = (0.5, 0.015)
    )

    fig.subplots_adjust(left = 0.005, right = 0.995, bottom = 0.07, top = 0.93, wspace = 0.02)

    salida = Path(salida)
    salida.parent.mkdir(parents = True, exist_ok = True)
    fig.savefig(salida, dpi = 300, bbox_inches = "tight", facecolor = "white")
    plt.close(fig)

    incorrectas = {real: pred for real, pred in asignacion.items() if real != pred}

    print(f"Escaneo: {ruta_obj} ({arcada}), ausente: {ausente}")
    print(f"Vista: elev = {elev}, azim = {azim}")
    print(f"Etiquetas simuladas incorrectas: {incorrectas}")
    print(f"Figura guardada: {salida} (PNG, 300 dpi)")
    print("ATENCIÓN: el panel (c) es una numeración simulada, no una predicción.")

    return salida


def main():
    parser = argparse.ArgumentParser(description = __doc__.splitlines()[0])
    parser.add_argument("obj", nargs = "?", type = Path, help = "ruta OBJ del escaneo elegido")
    parser.add_argument("salida", nargs = "?", type = Path, help = "ruta de salida .png")
    parser.add_argument("--buscar", type = Path, metavar = "CARPETA", help = "listar escaneos con una ausencia intercalada")
    parser.add_argument("--elev", type = int, choices = (90, -90), default = None, help = "forzar vista oclusal desde +Z o -Z (por defecto: automática)")
    args = parser.parse_args()

    if args.buscar is not None: 
        if args.obj is not None or args.salida is not None:
            parser.error("--buscar se usa sin OBJ ni salida.")

        buscar_candidatos(args.buscar)
    else:
        if args.obj is None or args.salida is None:
            parser.error("indica OBJ y ruta PNG, o bien usa --buscar CARPETA")

        if args.salida.suffix.lower() != ".png":
            parser.error("la salida debe ser un archivo .png")

        dibujar(args.obj, args.salida, args.elev)


if __name__ == "__main__":
    main()
"""
data_loader.py
===============

PROPÓSITO GENERAL DEL SCRIPT:
Módulo auxiliar (no se ejecuta directamente) usado por
"15_predictions.py". Provee una única función para cargar el dataset
enriquecido y descartar las filas sin variable objetivo válida antes de
pasarlas al resto del pipeline de modelado.

Ubicación según el sys.path.append de 15_predictions.py: carpeta
"02_data_cleaning" (una de las tres carpetas agregadas al path, junto a
"04_database" y "06_modeling" — no se puede confirmar desde este
archivo solo en cuál de las tres vive exactamente, pero por su
propósito de carga/limpieza de datos, "02_data_cleaning" es la más
coherente).
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import pandas as pd    # Para leer el CSV y filtrar filas


# ── 2. FUNCIÓN DE CARGA ───────────────────────────────────────────────────

def load_data(path):
    """
    Carga el dataset desde 'path' y elimina las filas donde la variable
    objetivo del modelo ("sales_volume_num") sea nula.

    Parámetros:
        path (str | Path): ruta al archivo CSV a cargar.

    Devuelve:
        pd.DataFrame: el dataset cargado, sin filas con
        "sales_volume_num" nulo.
    """

    # Carga el CSV completo en un DataFrame, sin ninguna validación
    # previa de que el archivo exista (a diferencia de los scripts 02 y
    # 03 del pipeline de extracción, que sí comprobaban con
    # FileNotFoundError antes de leer).
    df = pd.read_csv(path)

    # Elimina las filas donde "sales_volume_num" es NaN. Esto es
    # necesario porque esa columna es la VARIABLE OBJETIVO (y) del
    # modelo en "15_predictions.py": un modelo de regresión no puede
    # entrenarse ni evaluarse con valores nulos en la variable a
    # predecir, así que se descartan esas filas por completo en este
    # punto, antes de que lleguen al resto del pipeline de modelado.
    # (Nota: esto responde directamente al mensaje de diagnóstico que
    # imprime 15_predictions.py justo después de llamar a load_data:
    # "Valores nulos en la variable objetivo: 0" — siempre debería dar 0
    # gracias a este dropna, salvo que la columna no exista en absoluto,
    # en cuyo caso esta línea lanzaría un KeyError en vez de continuar.)
    df = df.dropna(subset=["sales_volume_num"])

    return df
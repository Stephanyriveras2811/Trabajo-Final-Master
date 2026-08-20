"""
preprocessing.py
==================

PROPÓSITO GENERAL DEL SCRIPT:
Módulo auxiliar (no se ejecuta directamente) usado por
"15_predictions.py". Construye el preprocesador de variables numéricas
que se inserta como primer paso dentro de cada Pipeline de modelo
(Regresión Lineal y Random Forest) en "models.py": imputa valores
faltantes con la media y estandariza las variables.

Ubicación según el sys.path.append de 15_predictions.py: carpeta
"06_modeling" (junto a models.py y evaluation.py).

Este módulo confirma EXACTAMENTE lo que describe el documento del
proyecto en la sección "Preparación de los datos para el modelado":
"las variables numéricas fueron preprocesadas mediante imputación de
valores faltantes utilizando la media y posteriormente estandarizadas
para mantener una escala homogénea durante el entrenamiento de los
modelos."
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
from sklearn.pipeline import Pipeline           # Para encadenar imputación + escalado en un solo transformador
from sklearn.compose import ColumnTransformer    # Para aplicar ese pipeline a un subconjunto específico de columnas
from sklearn.preprocessing import StandardScaler # Estandarización (media 0, desviación estándar 1)
from sklearn.impute import SimpleImputer         # Imputación de valores faltantes


# ── 2. FUNCIÓN DE CONSTRUCCIÓN DEL PREPROCESADOR ─────────────────────────

def get_preprocessor(columns):
    """
    Construye un ColumnTransformer de scikit-learn que aplica, a las
    columnas indicadas, primero imputación de nulos por la media y
    luego estandarización.

    Parámetros:
        columns (list[str]): nombres de las columnas numéricas a las
            que se les aplicará el preprocesamiento. En
            15_predictions.py se le pasa X.columns.tolist(), es decir,
            TODAS las columnas de features (product_price, discount,
            discount_pct, product_star_rating, product_num_ratings,
            popularity_score, premium_badge_count, rating_balance) —
            todas se tratan como numéricas, sin distinguir categóricas.

    Devuelve:
        ColumnTransformer: transformador sin entrenar (se ajusta
        automáticamente al llamar .fit() sobre el Pipeline completo que
        lo contiene, en models.py / 15_predictions.py).
    """

    # Sub-pipeline que se aplicará a las columnas numéricas:
    numeric_transformer = Pipeline(steps=[
        # Paso 1: Imputación. Reemplaza cada valor nulo (NaN) de una
        # columna con la MEDIA de esa misma columna (calculada sobre
        # los datos de entrenamiento durante el .fit(), y reutilizada
        # tal cual sobre los datos de prueba durante el .transform(),
        # para no filtrar información del conjunto de prueba hacia el
        # de entrenamiento).
        ("imputer", SimpleImputer(strategy="mean")),

        # Paso 2: Escalado. Estandariza cada columna para que tenga
        # media 0 y desviación estándar 1. Es importante para la
        # Regresión Lineal (evita que variables con escalas muy
        # distintas, como "product_price" en decenas/cientos frente a
        # "rating_balance" en un rango de -1 a 1, dominen el modelo
        # solo por su magnitud) y, aunque Random Forest no lo necesita
        # estrictamente (los árboles no son sensibles a la escala), no
        # perjudica su desempeño y simplifica el código al compartir el
        # mismo preprocesador entre ambos modelos.
        ("scaler", StandardScaler())
    ])

    # Envuelve el sub-pipeline anterior en un ColumnTransformer,
    # aplicándolo específicamente a la lista de columnas recibida
    # (etiquetado internamente como "num"). Aunque aquí solo hay un
    # grupo de columnas (todas numéricas), usar ColumnTransformer en vez
    # de aplicar el Pipeline directamente sobre el DataFrame deja la
    # puerta abierta a agregar en el futuro otro transformador para
    # columnas categóricas (por ejemplo, un OneHotEncoder), sin tener
    # que reestructurar el resto del código de modelado.
    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, columns)
        ]
    )
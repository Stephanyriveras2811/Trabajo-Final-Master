"""
models.py
==========

PROPÓSITO GENERAL DEL SCRIPT:
Módulo auxiliar (no se ejecuta directamente) usado por
"15_predictions.py". Construye los dos modelos predictivos del proyecto
(Regresión Lineal y Random Forest), cada uno encapsulado en un Pipeline
de scikit-learn junto con el preprocesador de datos recibido como
parámetro.

Ubicación según el sys.path.append de 15_predictions.py: carpeta
"06_modeling" (junto a evaluation.py y probablemente preprocessing.py).

Confirma exactamente el supuesto hecho en la documentación de
15_predictions.py: que el paso final de cada Pipeline se llama "model"
— de ahí que en el script principal se pueda acceder a
"model_rf.named_steps['model'].feature_importances_" para extraer la
importancia de variables del Random Forest.
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
from sklearn.pipeline import Pipeline               # Para encadenar preprocesamiento + modelo en un solo objeto
from sklearn.linear_model import LinearRegression    # Modelo de Regresión Lineal
from sklearn.ensemble import RandomForestRegressor   # Modelo de Random Forest para regresión


# ── 2. FUNCIÓN DE CONSTRUCCIÓN DE MODELOS ────────────────────────────────

def get_models(preprocessor):
    """
    Construye y devuelve dos Pipelines de scikit-learn, uno por cada
    modelo predictivo usado en el proyecto. Ambos comparten el mismo
    preprocesador (recibido como parámetro), de modo que el
    preprocesamiento de las variables (imputación, escalado, etc., según
    lo definido en preprocessing.py) se aplica de forma idéntica antes
    de entrenar cualquiera de los dos modelos.

    Parámetros:
        preprocessor: un transformador de scikit-learn (típicamente un
            ColumnTransformer), ya configurado, que se inserta como
            primer paso de cada Pipeline.

    Devuelve:
        tuple(model_lr, model_rf): los dos Pipelines sin entrenar,
        listos para llamar a .fit(X_train, y_train) en el script
        principal.
    """

    # --- Pipeline 1: Regresión Lineal ---
    # Encadena el preprocesador con un modelo de Regresión Lineal
    # "vainilla" (sin hiperparámetros personalizados; usa los valores
    # por defecto de scikit-learn).
    model_lr = Pipeline([
        ("preprocessor", preprocessor),
        ("model", LinearRegression())
    ])

    # --- Pipeline 2: Random Forest ---
    # Encadena el mismo preprocesador con un Random Forest configurado
    # con hiperparámetros específicos, no los valores por defecto:
    #   - random_state=42     -> reproducibilidad (mismos árboles en
    #                            cada ejecución)
    #   - max_depth=8         -> limita la profundidad máxima de cada
    #                            árbol a 8 niveles, para reducir el
    #                            riesgo de sobreajuste (overfitting) en
    #                            un dataset pequeño
    #   - min_samples_leaf=5  -> cada hoja del árbol debe tener al menos
    #                            5 muestras, otra medida para evitar que
    #                            el modelo memorice casos individuales
    #                            en vez de generalizar
    # Estos dos últimos parámetros son coherentes con el hallazgo del
    # documento: el Random Forest inicialmente obtenía R²=1.00 (señal
    # clara de sobreajuste/data leakage); limitar la profundidad y el
    # tamaño mínimo de hoja es una forma estándar de contener ese
    # sobreajuste, complementaria a la corrección del split por grupos
    # hecha en 15_predictions.py con GroupShuffleSplit.
    model_rf = Pipeline([
        ("preprocessor", preprocessor),
        ("model", RandomForestRegressor(random_state=42, max_depth=8, min_samples_leaf=5))
    ])

    # Devuelve ambos modelos como una tupla, en el mismo orden en que
    # se desempaquetan en 15_predictions.py:
    # model_lr, model_rf = get_models(preprocessor)
    return model_lr, model_rf
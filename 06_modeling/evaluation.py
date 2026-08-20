"""
evaluation.py
==============

PROPÓSITO GENERAL DEL SCRIPT:
Módulo auxiliar (no se ejecuta directamente) usado por
"15_predictions.py". Provee una única función que calcula las tres
métricas estándar de evaluación para modelos de regresión (MAE, RMSE,
R²) y las devuelve en un diccionario, listo para imprimir o tabular.

Ubicación según el sys.path.append de 15_predictions.py: probablemente
"06_modeling", junto a "models.py" (ambos son piezas específicas del
paso de modelado, a diferencia de "data_loader.py" que es más de carga
de datos).

Confirma exactamente las claves usadas en 15_predictions.py
("MAE", "RMSE", "R2") al construir la tabla comparativa de modelos y al
imprimir los resultados de cada uno.
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import numpy as np    # Para calcular la raíz cuadrada (RMSE = sqrt(MSE))
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
# mean_absolute_error -> Error Absoluto Medio (MAE)
# mean_squared_error  -> Error Cuadrático Medio (MSE), base para el RMSE
# r2_score            -> Coeficiente de determinación (R²)


# ── 2. FUNCIÓN DE EVALUACIÓN ──────────────────────────────────────────────

def evaluate(y_test, y_pred):
    """
    Calcula tres métricas estándar para evaluar un modelo de regresión,
    comparando los valores reales (y_test) contra los valores predichos
    por el modelo (y_pred).

    Parámetros:
        y_test: valores reales de la variable objetivo (conjunto de prueba).
        y_pred: valores predichos por el modelo para ese mismo conjunto.

    Devuelve:
        dict con tres claves:
          - "MAE":  Error Absoluto Medio. Promedio de las diferencias
                     absolutas entre valor real y predicho. Está en las
                     mismas unidades que la variable objetivo (unidades
                     de venta estimadas) y es fácil de interpretar
                     directamente ("en promedio, el modelo se equivoca
                     por X unidades").
          - "RMSE": Raíz del Error Cuadrático Medio. Similar al MAE,
                     pero al elevar al cuadrado antes de promediar,
                     penaliza más fuerte los errores grandes (outliers
                     de predicción). Siempre es mayor o igual al MAE.
          - "R2":   Coeficiente de determinación. Indica qué proporción
                     de la variabilidad de la variable objetivo es
                     explicada por el modelo. 1.0 = predicción perfecta;
                     0.0 = el modelo no explica nada mejor que predecir
                     siempre el promedio; puede ser NEGATIVO si el
                     modelo predice peor que ese promedio simple (que es
                     justamente lo que reportó el documento del proyecto
                     tras corregir el data leakage: R² negativo tanto en
                     Regresión Lineal como en Random Forest).
    """
    return {
        # Diferencia absoluta promedio entre valores reales y predichos.
        "MAE": mean_absolute_error(y_test, y_pred),

        # RMSE se calcula manualmente como la raíz cuadrada del MSE, ya
        # que en la versión de scikit-learn usada aquí no se pasa el
        # parámetro squared=False directamente a mean_squared_error
        # (que en versiones más nuevas de sklearn permite obtener el
        # RMSE sin pasar por np.sqrt manualmente).
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),

        # Coeficiente de determinación R².
        "R2": r2_score(y_test, y_pred)
    }
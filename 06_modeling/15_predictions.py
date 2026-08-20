"""
15_predictions.py
==================

PROPÓSITO GENERAL DEL SCRIPT:
Entrenar y evaluar dos modelos predictivos (Regresión Lineal y Random
Forest) para estimar el volumen de ventas ("sales_volume_num") de los
productos, a partir de variables de precio, descuento, valoración y
popularidad. Corresponde a la sección "Modelos predictivos y evaluación"
del documento del proyecto, incluyendo la corrección del problema de
"fuga de datos" (data leakage) mediante GroupShuffleSplit.

Es el script referenciado explícitamente en el pipeline de "main.py"
(carpeta "06_modeling"), y el único paso de modelado mencionado ahí —
es decir, es el punto de llegada del pipeline completo.

DEPENDENCIAS EXTERNAS (módulos propios del proyecto, no incluidos en
este archivo — no fueron compartidos, así que se documentan aquí solo
según cómo se usan, infiriendo su comportamiento a partir de las
llamadas):
  - data_loader.load_data(csv_path)      -> carga y probablemente valida el CSV
  - preprocessing.get_preprocessor(cols) -> arma un ColumnTransformer/pipeline de sklearn
  - models.get_models(preprocessor)      -> construye los Pipelines de LR y RF ya con el preprocesador
  - evaluation.evaluate(y_true, y_pred)  -> calcula MAE, RMSE y R2 (según las claves usadas después)

Si quieres una documentación igual de detallada de esos 4 archivos,
compártelos y los documento con el mismo nivel de detalle.
"""

# =========================
# 1. IMPORTACIONES
# =========================

import pandas as pd                # Manipulación de datos y construcción de tablas de resultados
import matplotlib.pyplot as plt    # Generación de gráficos
import seaborn as sns              # Gráfico de barras de importancia de variables
import os                          # Para construir rutas de archivo
import sys                         # Para modificar el path de búsqueda de módulos de Python

# Calcula la carpeta raíz del proyecto: sube dos niveles desde este
# script (equivalente a lo que en otros scripts se hacía con
# Path(__file__).resolve().parent.parent, pero aquí usando os.path en
# vez de pathlib — es el único script del pipeline que mezcla ambos
# estilos de manejo de rutas; todos los anteriores usaban pathlib.Path).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agrega manualmente al "path" de búsqueda de Python las carpetas donde
# viven los módulos propios del proyecto (data_loader, preprocessing,
# models, evaluation), para poder importarlos más abajo como si fueran
# librerías instaladas. Esto es necesario porque esos módulos no están
# en la misma carpeta que este script, sino repartidos en otras carpetas
# del proyecto (04_database, 02_data_cleaning, 06_modeling).
sys.path.append(os.path.join(BASE_DIR, "04_database"))
sys.path.append(os.path.join(BASE_DIR, "02_data_cleaning"))
sys.path.append(os.path.join(BASE_DIR, "06_modeling"))

# Herramientas de scikit-learn para dividir los datos en entrenamiento/prueba.
from sklearn.model_selection import train_test_split, GroupShuffleSplit
# (Nota: train_test_split se importa pero NO se usa en ningún punto del
# script — la división real se hace con GroupShuffleSplit más abajo. Es
# un import sin uso, probablemente residuo de una versión anterior del
# código antes de corregir el data leakage.)

# Módulos propios del proyecto, importados desde las rutas agregadas arriba.
from data_loader import load_data          # Función para cargar el CSV
from preprocessing import get_preprocessor  # Función que arma el preprocesador de columnas
from models import get_models                # Función que arma los modelos (con el preprocesador incluido)
from evaluation import evaluate               # Función que calcula las métricas de evaluación


# =========================
# 2. CARGA DE DATOS
# =========================

# Ruta al dataset enriquecido (salida del script 08), construida con
# os.path.join en vez de pathlib.
csv_path = os.path.join(
    BASE_DIR,
    "03_output",
    "audifonos_unificado_limpio_enriquecido.csv"
    )

# Carga el CSV a través de la función load_data del módulo propio
# (en vez de pd.read_csv directo, como en los scripts anteriores) —
# probablemente incluye alguna validación o transformación adicional
# encapsulada en ese módulo.
df = load_data(csv_path)
print("Primeras filas del conjunto de datos:")
print(df.head())

print("\nInformación del conjunto de datos:")
print(df.info())   # Muestra tipos de dato y conteo de no-nulos por columna


# =========================
# 3. SELECCIÓN DE VARIABLES
# =========================

# Variable objetivo (lo que se quiere predecir): el volumen de ventas
# estimado, generado en el script 08.
y = df["sales_volume_num"]

# Variables predictoras (features) seleccionadas para el modelo. Todas
# provienen de columnas creadas en scripts anteriores del pipeline
# (extracción directa o feature engineering del script 08).
features = [
    "product_price",
    "discount",
    "discount_pct",
    "product_star_rating",
    "product_num_ratings",
    "popularity_score",
    "premium_badge_count",
    "rating_balance"
]

X = df[features]

# Informa cuántos valores nulos tiene la variable objetivo (relevante
# porque los NaN en "y" pueden causar errores al entrenar el modelo si
# no se filtran o imputan en algún paso posterior, por ejemplo dentro
# de get_preprocessor o load_data).
print("\nValores nulos en la variable objetivo:", y.isna().sum())


# =========================
# 4. DIVISIÓN DE DATOS
# =========================

# GroupShuffleSplit divide los datos en entrenamiento/prueba respetando
# GRUPOS: todas las filas de un mismo grupo (aquí, un mismo "asin")
# quedan juntas en el mismo conjunto (todas en train o todas en test),
# nunca repartidas entre ambos.
# Esto es la corrección del "data leakage" mencionada en el documento:
# como el dataset tiene múltiples filas históricas por producto (una
# por punto de precio), un split aleatorio simple (train_test_split)
# podía dejar el mismo producto tanto en entrenamiento como en prueba,
# inflando artificialmente el desempeño del modelo (R²=1.00 mencionado
# en el documento antes de la corrección).
gss = GroupShuffleSplit(test_size=0.2, random_state=42)

# .split(...) devuelve un generador de particiones; next(...) toma la
# primera (y única, porque no se especificó n_splits>1) partición
# generada. groups=df["asin"] es la clave: agrupa por producto.
train_idx, test_idx = next(gss.split(X, y, groups=df["asin"]))

# Usa los índices generados para separar físicamente los datos.
X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]


# =========================
# 5. PREPROCESAMIENTO
# =========================

# Construye el preprocesador (probablemente un ColumnTransformer de
# sklearn con imputación de nulos por la media y escalado, según lo que
# describe el documento: "las variables numéricas fueron preprocesadas
# mediante imputación de valores faltantes utilizando la media y
# posteriormente estandarizadas"). No se ve el contenido de esta función
# aquí — solo se sabe que recibe la lista de nombres de columnas.
preprocessor = get_preprocessor(X.columns.tolist())


# =========================
# 6. CREACIÓN Y ENTRENAMIENTO DE MODELOS
# =========================

# get_models(preprocessor) probablemente devuelve dos objetos Pipeline
# de sklearn, cada uno con el preprocesador como primer paso y el
# modelo (LinearRegression / RandomForestRegressor) como paso final —
# de ahí que más abajo se acceda a "model_rf.named_steps['model']"
# para extraer las importancias de variables del Random Forest.
model_lr, model_rf = get_models(preprocessor)

# Entrena y predice con Regresión Lineal.
model_lr.fit(X_train, y_train)
y_pred_lr = model_lr.predict(X_test)

# Entrena y predice con Random Forest.
model_rf.fit(X_train, y_train)
y_pred_rf = model_rf.predict(X_test)


# =========================
# 7. EVALUACIÓN
# =========================

# evaluate(y_true, y_pred) del módulo propio devuelve un diccionario de
# métricas (se infiere por el uso posterior: incluye al menos "MAE",
# "RMSE" y "R2").
metrics_lr = evaluate(y_test, y_pred_lr)
metrics_rf = evaluate(y_test, y_pred_rf)

print("\n==============================")
print("Resultados - Regresión Lineal")
print("==============================")
for metric, value in metrics_lr.items():
    print(f"{metric}: {value:.4f}")

print("\n==============================")
print("Resultados - Random Forest")
print("==============================")
for metric, value in metrics_rf.items():
    print(f"{metric}: {value:.4f}")


# =========================
# 8. COMPARACIÓN DE MODELOS
# =========================

# Arma una tabla comparativa entre ambos modelos, con las métricas
# principales, redondeada a 4 decimales — coincide con el formato de la
# tabla "MAE / RMSE / R²" que aparece en el documento del proyecto.
results = pd.DataFrame({
    "Modelo": ["Regresión Lineal", "Random Forest"],
    "MAE": [metrics_lr["MAE"], metrics_rf["MAE"]],
    "RMSE": [metrics_lr["RMSE"], metrics_rf["RMSE"]],
    "R²": [metrics_lr["R2"], metrics_rf["R2"]]
})

results = results.round(4)

print("\n==============================")
print("Comparación de modelos")
print("==============================")
print(results)


# =========================
# 9. IMPORTANCIA DE VARIABLES
# =========================

# Extrae las importancias de variables directamente del modelo Random
# Forest ya entrenado. "named_steps['model']" asume que dentro del
# Pipeline de get_models, el paso final del modelo se llama "model".
# feature_importances_ es un atributo propio de RandomForestRegressor
# que indica cuánto contribuye cada variable a las predicciones.
importances = model_rf.named_steps["model"].feature_importances_

# Empareja cada nombre de variable (en el mismo orden que "features")
# con su importancia, y ordena de mayor a menor relevancia.
importance_df = pd.DataFrame({
    "Variable": features,
    "Importancia": importances
}).sort_values(by="Importancia", ascending=False)

print("\n==============================")
print("Importancia de variables")
print("==============================")
print(importance_df)


# =========================
# 10. VISUALIZACIÓN
# =========================

# Gráfico de barras horizontales con la importancia de cada variable,
# ordenado de mayor a menor (por el orden ya aplicado en importance_df).
plt.figure(figsize=(10, 6))

sns.barplot(
    data=importance_df,
    x="Importancia",
    y="Variable"
)

plt.title("Importancia de Variables - Random Forest")
plt.xlabel("Importancia")
plt.ylabel("Variables")
plt.tight_layout()
# No se guarda con plt.savefig() antes de mostrar (mismo patrón que los
# scripts 11 y 13) — el gráfico no queda persistido como archivo.
plt.show()
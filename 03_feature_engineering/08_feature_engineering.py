"""
08_feature_engineering.py
==========================
 
PROPÓSITO GENERAL DEL SCRIPT:
Tomar el dataset validado por "07_final_data_validation.py"
(audifonos_unificado_limpio.csv) y aplicarle transformaciones de tipos
de datos y creación de nuevas variables (feature engineering): precios
numéricos, volumen de ventas parseado, distribución de calificaciones
expandida en columnas, variables booleanas, descuentos, popularidad,
balance de valoraciones y categoría del producto. El resultado se guarda
como "audifonos_unificado_limpio_enriquecido.csv" en "03_output".

Es el paso que conecta la etapa de limpieza/validación (05-07) con el
análisis exploratorio (EDA) y el modelado: aquí se generan la mayoría de
las variables derivadas que se usarán en los pasos siguientes.
"""
 
# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import pandas as pd        # Para cargar, transformar y exportar el DataFrame
import re                  # Para extraer números y sufijos (K/M) del texto de sales_volume
import ast                 # Para convertir texto con forma de dict/lista (p. ej. "{'5': 10}") a objetos reales de Python
from pathlib import Path   # Para construir rutas de archivo de forma portable
 
 
# ── 2. RUTAS ───────────────────────────────────────────────────────────────
 
# Ruta base del proyecto: sube dos niveles desde este script.
base_path = Path(__file__).resolve().parent.parent
 
# Archivo de entrada: el dataset validado (salida de 07).
input_file = base_path / "03_output" / "audifonos_unificado_limpio.csv"
 
# Archivo de salida: el dataset enriquecido con las nuevas variables.
output_file = base_path / "03_output" / "audifonos_unificado_limpio_enriquecido.csv"

 
# ── 3. CARGA DE DATOS ────────────────────────────────────────────────────
 
# Carga el CSV validado en un DataFrame.
# (No valida antes si input_file existe; si falta, pandas lanzará su
# propio error.)
df = pd.read_csv(input_file)

print("Archivo cargado correctamente.")
print(df.head())
 
 
# ── 4. CONVERSIÓN DE PRECIOS ────────────────────────────────────────────
 
# Columnas de precio que deben quedar como numéricas.
price_cols = ["product_price", "product_original_price"]

for col in price_cols:
    if col in df.columns:
        # Convierte a numérico; cualquier valor no convertible (texto,
        # símbolos, vacío) queda como NaN en vez de lanzar error
        # (errors="coerce"). A esta altura del pipeline los precios ya
        # deberían venir limpios de "$" y comas desde el script 01, pero
        # esta conversión sirve como red de seguridad adicional.
        df[col] = pd.to_numeric(df[col], errors="coerce")
 
 
# ── 5. SALES VOLUME (PARSEO DE TEXTO A NÚMERO) ──────────────────────────
 
def parse_sales_volume(value):
    """
    Convierte valores de texto como "1.2K" o "3M" (formato típico que
    devuelve la API para el volumen de ventas) a un número entero real.
    Ejemplos: "1.2K" -> 1200, "3M" -> 3000000, "500" -> 500.
    Si el valor es nulo o no se puede interpretar, devuelve 0.
    """
 
    # Si el valor es nulo (NaN), se asume volumen de ventas 0.
    if pd.isna(value):
        return 0
 
    # Busca un número (con decimales opcionales) seguido opcionalmente
    # de una letra K o M (mayúscula o minúscula). Ej: "1.2K", "500", "3M".
    match = re.search(r"(\d+\.?\d*)([KkMm]?)", str(value))
 
    # Si el texto no contiene un patrón numérico reconocible, se asume 0.
    if not match:
        return 0
 
    number = float(match.group(1))     # Parte numérica (ej. 1.2)
    suffix = match.group(2).upper()    # Sufijo K o M (o vacío)
 
    # Aplica el multiplicador según el sufijo.
    if suffix == "K":
        number *= 1000
    elif suffix == "M":
        number *= 1000000
 
    # Se devuelve como entero (se pierde la parte decimal residual tras
    # multiplicar, lo cual es aceptable para un conteo de ventas estimado).
    return int(number)
 
 
# Si existe la columna original "sales_volume" (texto), se crea la nueva
# columna numérica "sales_volume_num" aplicando la función anterior fila
# por fila.
if "sales_volume" in df.columns:
    df["sales_volume_num"] = df["sales_volume"].apply(parse_sales_volume)
 
 
# ── 6. DISTRIBUCIÓN DE CALIFICACIONES (EXPANSIÓN A COLUMNAS) ────────────
 
def parse_rating_dist(value):
    """
    Convierte el campo 'rating_distribution' (que llega como texto con
    forma de diccionario, p. ej. "{'5': 120, '4': 30, ...}") en un
    diccionario de PORCENTAJES por estrella, con claves con el formato
    "pct_5stars", "pct_4stars", etc. Si el valor no es interpretable o
    la suma de conteos es 0, devuelve un diccionario vacío.
    """
 
    try:
        # ast.literal_eval interpreta el texto como una estructura de
        # Python (dict, list, etc.) de forma segura, sin ejecutar código.
        ratings = ast.literal_eval(str(value))
 
        # Si el resultado no es un diccionario, no hay nada que procesar.
        if not isinstance(ratings, dict):
            return {}

        total = sum(ratings.values())
 
        # Evita división por cero si todos los conteos son 0.
        if total == 0:
            return {}
 
        # Convierte cada conteo absoluto en su proporción sobre el total,
        # renombrando la clave con el prefijo "pct_" y sufijo "stars".
        return {
            f"pct_{k}stars": v / total
            for k, v in ratings.items()
        }

    except Exception:
        # Cualquier error de parseo (texto mal formado, tipo inesperado,
        # etc.) se traduce en un diccionario vacío, sin detener el script.
        return {}


if "rating_distribution" in df.columns:
 
    # Aplica la función a cada fila, obteniendo una Serie de diccionarios,
    # y con .apply(pd.Series) expande cada diccionario en columnas
    # separadas (p. ej. pct_5stars, pct_4stars, pct_3stars...).
    # .fillna(0) rellena con 0 las combinaciones de fila/columna donde esa
    # estrella no apareció en el diccionario original de esa fila.
    rating_expanded = (
        df["rating_distribution"]
        .apply(parse_rating_dist)
        .apply(pd.Series)
        .fillna(0)
    )
 
    # Une las nuevas columnas de porcentaje al DataFrame principal,
    # pegándolas como columnas adicionales (axis=1).
    df = pd.concat([df, rating_expanded], axis=1)
 
 
# ── 7. VARIABLES BOOLEANAS ───────────────────────────────────────────────
 
# Columnas que representan indicadores sí/no de Amazon (insignias,
# certificaciones, contenido enriquecido del producto, etc.).
bool_cols = [
    "is_amazon_choice",
    "is_prime",
    "has_aplus",
    "has_brandstory"
]

for col in bool_cols:
    if col in df.columns:
        # Los valores nulos se interpretan como False (ausencia del
        # distintivo), y luego se fuerza el tipo a booleano real.
        df[col] = (
            df[col]
            .fillna(False)
            .astype(bool)
        )
 
 
# ── 8. FEATURE ENGINEERING (VARIABLES DERIVADAS) ─────────────────────────
 
# "deal_badge" pasa de ser texto (posiblemente vacío o con una etiqueta
# de oferta) a un booleano: True si el campo tiene contenido no vacío
# tras quitar espacios, False si está vacío o era nulo.
df["deal_badge"] = (
    df["deal_badge"]
    .fillna("")
    .astype(str)
    .str.strip()
    != ""
)
 
# Descuento en valor absoluto: precio original menos precio actual.
df["discount"] = (
    df["product_original_price"] -
    df["product_price"]
)
 
# Descuento en porcentaje sobre el precio original.
# .replace(0, pd.NA) evita división por cero cuando el precio original
# es 0: en ese caso el resultado queda como NaN en vez de infinito/error.
df["discount_pct"] = (
    df["discount"] /
    df["product_original_price"].replace(0, pd.NA)
) * 100
 
# Puntaje de popularidad: rating promedio multiplicado por el número de
# reseñas. Combina "qué tan bien calificado está" con "cuánta gente lo
# calificó", para distinguir productos muy bien valorados pero con pocas
# reseñas de productos consistentemente bien valorados por muchos usuarios.
df["popularity_score"] = (
    df["product_star_rating"] *
    df["product_num_ratings"]
)
 
# Ventas relativas al precio: volumen de ventas dividido por el precio
# (+1 para evitar división por cero cuando el precio es 0). Da una
# medida de "cuántas ventas por unidad de precio" genera el producto.
df["sales_per_price"] = (
    df["sales_volume_num"] /
    (df["product_price"].replace(0, pd.NA) + 1)
)
 
# Cuenta cuántos de los distintivos booleanos (bool_cols) tiene el
# producto activados, sumando True/False fila por fila (True cuenta
# como 1). Da una medida agregada de "cuántas insignias premium" tiene.
df["premium_badge_count"] = df[bool_cols].sum(axis=1)
 
# Balance de valoraciones: diferencia entre el porcentaje de reseñas de
# 5 estrellas y el de 1 estrella. Un valor alto indica opiniones
# mayormente positivas; un valor bajo o negativo indica polarización o
# predominio de opiniones negativas.
# df.get(...) se usa en vez de df["..."] para no fallar si esas columnas
# no llegaron a crearse en el paso 6 (p. ej. si "rating_distribution" no
# existía o ningún producto tenía esas estrellas específicas).
df["rating_balance"] = (
    df.get("pct_5stars", 0) -
    df.get("pct_1stars", 0)
)
 
 
# ── 9. CATEGORÍA DEL PRODUCTO ────────────────────────────────────────────
 
def extract_category_name(value):
    """
    Extrae el nombre de la categoría desde el campo 'category', que llega
    como texto con forma de diccionario (p. ej. "{'name': 'Electronics',
    'id': ...}"). Devuelve solo el valor de la clave 'name', o None si no
    se puede interpretar.
    """
 
    try:
        category = ast.literal_eval(str(value))

        if isinstance(category, dict):
            return category.get("name")

        return None

    except Exception:
        return None

if "category" in df.columns:
    # Si existe la columna original, se crea "category_name" aplicando
    # la función anterior a cada fila.
    df["category_name"] = df["category"].apply(extract_category_name)
else:
    # Si la columna "category" no existe en absoluto, se crea igual
    # "category_name" pero con valor None en todas las filas, para que
    # el resto del pipeline pueda asumir que la columna siempre existe.
    df["category_name"] = None
 
 
# ── 10. EXPORTAR ─────────────────────────────────────────────────────────
 
# Guarda el DataFrame enriquecido, sin incluir el índice de pandas.
df.to_csv(output_file, index=False)

print("\nDataset enriquecido creado correctamente.")
print(f"Archivo guardado en:\n{output_file}")
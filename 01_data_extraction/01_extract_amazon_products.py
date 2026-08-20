"""
01_extract_amazon_products.py
==============================
 
PROPÓSITO GENERAL DEL SCRIPT:
Consultar la API "Real-Time Amazon Data" (vía RapidAPI) con el endpoint
de búsqueda "/search" para el término "wireless headphones", recorriendo
varias páginas de resultados. Con los productos obtenidos arma un
DataFrame de pandas, limpia y normaliza campos numéricos (precios,
rating, descuento), filtra filas sin precio válido, y exporta el
catálogo resultante a Excel y CSV
("audifonos_inalambricos_amazon_us.xlsx" / ".csv").
 
Este es el primer paso del pipeline: genera el CSV de productos que
luego usa "02_extract_product_details.py" para obtener el detalle de
cada ASIN.
"""

# ── 1. IMPORTS ──────────────────────────────────────────────────────────
import requests                    # Para hacer las peticiones HTTP a la API de RapidAPI
import pandas as pd                # Para leer el CSV de entrada y construir los CSV de salida
import json                        # Importado pero no usado explícitamente en el cuerpo del script
import os                          # Para leer variables de entorno (la API key)
import time                        # Para pausar entre peticiones (time.sleep) y no saturar la API
from dotenv import load_dotenv     # Para cargar variables de entorno desde un archivo .env
from pathlib import Path           # Para construir rutas de archivo de forma portable

# ── 2. CARGA DE CREDENCIALES (.env) ─────────────────────────────────────
 
# Construye la ruta al archivo .env, ubicado dos niveles arriba del script
# (de 01_data_extraction sube a la raíz del proyecto y entra a "config").
env_path = Path(__file__).resolve().parent.parent /"config" / ".env"
 
# Carga las variables definidas en el .env encontrado hacia el entorno del proceso.
load_dotenv(dotenv_path=env_path)

# Lee la API key de RapidAPI desde la variable de entorno RAPIDAPI_KEY.
API_KEY = os.getenv("RAPIDAPI_KEY")
 
# Si no se encontró la key, se detiene la ejecución con un error claro.
# (Nota: el mensaje menciona "amazon_headphones", pero la variable que
# realmente se busca es "RAPIDAPI_KEY" — es un desajuste menor en el texto
# del error, no afecta la lógica.)
if not API_KEY:
    raise ValueError("No se encontró la variable de entorno amazon_headphones")


# Cabeceras HTTP requeridas por RapidAPI: la key de autenticación y el host
# del servicio "Real-Time Amazon Data" que se va a consultar.
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
}
# ── 3. BÚSQUEDA DE PRODUCTOS (PAGINADA) ─────────────────────────────────
 
productos = []                      # Acumula los productos crudos (dicts) de todas las páginas
query = "wireless headphones"       # Término de búsqueda fijo para esta extracción
 
# Recorre hasta 10 páginas de resultados de búsqueda (1 a 10 inclusive).
for page in range(1, 11):  
    url = "https://real-time-amazon-data.p.rapidapi.com/search"
     
    # Parámetros de la búsqueda: término, número de página y país.
    querystring = {
        "query": query,
        "page": str(page),
        "country": "US"
    }
 
    # Mensajes de diagnóstico: qué página se está consultando y con qué parámetros.
    print(f"\nConsultando página {page}")
    print("Parámetros enviados:", querystring)
    
    try:
        # Petición GET con timeout de 30 segundos para no bloquear el script
        # indefinidamente si la API no responde.
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        # Lanza excepción si la respuesta HTTP es un error (4xx/5xx),
        # capturada por el except de abajo.
        response.raise_for_status()
        
        data = response.json()
 
        # Si la API responde pero con un estado distinto de "OK", se informa
        # el mensaje de error y se corta el bucle (no tiene sentido seguir
        # pidiendo más páginas si la API está fallando).
        if data.get("status") != "OK":
            print(f"Error en API página {page}: {data.get('message', data)}")
            break
        
        # Extrae la lista de productos de esta página; si no existe la
        # estructura esperada, devuelve una lista vacía por defecto.
        items = data.get("data", {}).get("products", [])
        
        # Si la página no trajo productos, se asume que ya no hay más
        # resultados y se termina la paginación.
        if not items:
            print(f"Página {page}: no hay más resultados")
            break
        
        # Agrega los productos de esta página al acumulado total.
        productos.extend(items)
        print(f"Página {page} → {len(items)} productos (total acumulado: {len(productos)})")
        
    except requests.exceptions.RequestException as e:        
        # Cubre errores de red, timeout, DNS, etc. Se informa y se corta
        # el bucle (no se reintenta la página fallida).
        print(f"Error en request página {page}: {e}")
        break
    
# ── 4. LIMPIEZA Y NORMALIZACIÓN DEL DATAFRAME ───────────────────────────
 
# Solo se procesa si se obtuvo al menos un producto en total.
if productos:
    df = pd.DataFrame(productos)

# NOTA DE INDENTACIÓN (es la técnica de agregar espacios al principio de las líneas de código): las siguientes
# líneas, desde el "for col in [...]" en adelante, quedan FUERA del bloque
# "if productos:" porque no están indentadas dentro de él. Esto significa
# que si "productos" estuviera vacío, "df" no existiría y el script
# fallaría con un NameError al llegar a este "for". En la práctica solo
# funciona correctamente cuando sí hubo productos.
 
# Asegura que existan las columnas clave que el resto del script necesita;
# si la API no las devolvió, se crean vacías (None) para evitar errores
# más adelante.
for col in[
    "product_price",
    "product_original_price",
    "product_star_rating",
    "product_num_ratings"
    ]:
    if col not in df.columns:
        df[col] = None
 
    # --- Limpieza de "product_price" ---
    # Convierte a texto, quita el símbolo "$" y las comas de miles.
    df["product_price"] = (
        df["product_price"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    # Convierte el texto limpio a número; lo que no se pueda convertir
    # queda como NaN (errors="coerce") en vez de lanzar una excepción.
    df["product_price"] = pd.to_numeric(
        df["product_price"],
        errors="coerce"
    )
    # --- Limpieza de "product_original_price" (mismo procedimiento) ---
    df["product_original_price"] = (
        df["product_original_price"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    df["product_original_price"] = pd.to_numeric(
        df["product_original_price"], errors="coerce")
    
    # --- Cálculo del descuento (%) ---
    # Fórmula: (precio original - precio actual) / precio original * 100.
    df["discount"] = (
    (df["product_original_price"] - df["product_price"])
    / df["product_original_price"]) * 100
    # Si el cálculo dio NaN (p. ej. sin precio original), se asume 0% de descuento.
    df["discount"] = df["discount"].fillna(0)

    # --- Convertir rating a numérico ---
    df["product_star_rating"] = pd.to_numeric(
        df["product_star_rating"],
        errors="coerce")

    # --- Convertir cantidad de valoraciones a numérico ---
    df["product_num_ratings"] = pd.to_numeric(
        df["product_num_ratings"],
        errors="coerce")

    # Descarta las filas donde el precio quedó como NaN (no se pudo
    # limpiar/convertir), ya que sin precio el producto no es útil
    # para el análisis posterior.
    df = df[df["product_price"].notna()]
    
 
    # NOTA: todo este bloque (limpieza de precios, descuento, ratings,
    # filtro de precio) está dentro del "for col in [...]", por lo que
    # en la práctica se repite una vez por cada columna de la lista de
    # arriba (4 veces). El resultado final es el mismo porque las
    # operaciones son constantes, pero es trabajo redundante: por
    # indentación debería estar fuera del "for", ejecutándose una sola vez.
 
    # Columnas finales que se quieren conservar en el catálogo exportado.
    columnas_interes = [
        'asin',
        'product_title',
        'product_price',
        'product_original_price',
        'discount',
        'product_star_rating',
        'product_num_ratings',
        'sales_volume',
        'is_prime',
        'is_best_seller',
        'is_amazon_choice',
        'currency','product_url'
        ]
 
    # Filtra la lista anterior dejando solo las columnas que realmente
    # existen en el DataFrame (por si la API no devolvió alguna de ellas).
    cols_existentes = [col for col in columnas_interes if col in df.columns]
    
    if cols_existentes:
        # Muestra en consola una vista previa de las primeras 10 filas.
        print("\nListado de audífonos inalámbricos (primeras filas):")
        print(df[cols_existentes].head(10).to_string(index=False))
 
        # Exporta el catálogo limpio a Excel...
        df[cols_existentes].to_excel("audifonos_inalambricos_amazon_us.xlsx", index=False)
        print("\nGuardado en: audifonos_inalambricos_amazon_us.xlsx")
 
        # ...y también a CSV (codificación utf-8-sig para que Excel abra
        # bien los acentos/caracteres especiales en Windows).
        df[cols_existentes].to_csv("audifonos_inalambricos_amazon_us.csv", index=False, encoding="utf-8-sig")
    else:
        # Si ninguna de las columnas esperadas existe, se avisa y se
        # muestran las primeras filas "crudas" tal cual vinieron de la API,
        # para poder diagnosticar qué campos sí llegaron.
        print("No se encontraron las columnas esperadas. Imprimiendo primeras filas crudas:")
        print(df.head(3))
else:
    # Caso en que la búsqueda no devolvió ningún producto en ninguna página.
    print("\nNo se obtuvieron productos válidos.")
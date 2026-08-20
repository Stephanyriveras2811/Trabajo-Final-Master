"""
02_extract_product_details.py
==============================
 
PROPÓSITO GENERAL DEL SCRIPT:
Tomar el catálogo de productos generado por "01_extract_amazon_products.py"
(archivo "audifonos_inalambricos_amazon_us.csv"), extraer sus ASINs, y
consultar la API "Real-Time Amazon Data" (vía RapidAPI) con el endpoint
"/product-details" para obtener la ficha completa de cada producto
(precio, descripción, imágenes, especificaciones, etc.). Los resultados
exitosos se guardan en "detalles_audifonos.csv" y los ASINs que fallaron,
junto con su error, en "errores_detalles.csv".
 
Es el segundo paso del pipeline: recibe el catálogo de "01" y produce el
detalle enriquecido que alimentará los pasos siguientes (p. ej. historial
de precios en "03_extract_price_history.py").
"""
 
# ── 1. IMPORTS ──────────────────────────────────────────────────────────
import requests                    # Para hacer las peticiones HTTP a la API de RapidAPI
import pandas as pd                # Para leer el CSV de entrada y construir los CSV de salida
import os                          # Para leer variables de entorno (la API key)
import time                        # Para pausar entre peticiones (time.sleep) y no saturar la API
from dotenv import load_dotenv     # Para cargar variables de entorno desde un archivo .env
from pathlib import Path           # Para construir rutas de archivo de forma portable

 
# ── 2. CARGA DE CREDENCIALES (.env) ─────────────────────────────────────
 
# Ruta al .env, ubicado dos niveles arriba del script (de 01_data_extraction
# sube a la raíz del proyecto y entra a "config").
env_path = Path(__file__).resolve().parent.parent / "config" / ".env"

# Mensajes de diagnóstico: dónde se busca el .env y si existe. Útiles para
# depurar problemas de rutas si el script se ejecuta desde otra carpeta.
print("Buscando .env en:", env_path)
print("Existe:", env_path.exists())

# Carga las variables definidas en ese .env hacia el entorno del proceso.
load_dotenv(dotenv_path=env_path)

# Lee la API key de RapidAPI desde la variable de entorno RAPIDAPI_KEY.
API_KEY = os.getenv("RAPIDAPI_KEY")

# Si no se encontró la key, se detiene la ejecución con un error claro,
# en vez de fallar más adelante con un error genérico de autenticación.
if not API_KEY:
    raise ValueError("No se encontró RAPIDAPI_KEY en el archivo .env")

# Confirma (sin imprimir la key real) que sí se cargó correctamente.
print("API encontrada:", API_KEY is not None)
 
# Cabeceras HTTP requeridas por RapidAPI: la key de autenticación y el
# host del servicio "Real-Time Amazon Data" que se va a consultar.
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
}

 
# ── 3. CARGA DEL CSV DE PRODUCTOS (SALIDA DE "01") ──────────────────────
 
# Ruta al CSV generado por el script 01 (se espera en la misma carpeta).
archivo_productos = Path(__file__).resolve().parent / "audifonos_inalambricos_amazon_us.csv"

# Verifica que el archivo exista antes de leerlo; si no, lanza un error
# explícito con la ruta que se intentó usar.
if not archivo_productos.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo: {archivo_productos}")

# Carga el CSV completo en un DataFrame de pandas.
df_productos = pd.read_csv(archivo_productos)

# Valida que exista la columna "asin", indispensable para consultar el
# detalle de cada producto. Si falta, se detiene con un mensaje claro.
if "asin" not in df_productos.columns:
    raise ValueError("La columna 'asin' no existe en amazon_products_raw.csv")

# Extrae la lista de ASINs únicos y sin valores nulos:
#   .dropna()    -> descarta filas sin ASIN
#   .astype(str) -> asegura que todos sean texto (evita mezclas de tipos)
#   .unique()    -> elimina duplicados
#   .tolist()    -> convierte el resultado a una lista de Python
asins = (
    df_productos["asin"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)
# Informa cuántos ASINs distintos se van a consultar.
print(f"ASINs encontrados: {len(asins)}")
 
 
# ── 4. CONSULTA DE DETALLES POR CADA ASIN ───────────────────────────────
 
detalles = []   # Acumula los datos de producto obtenidos con éxito
errores = []    # Acumula los ASINs que fallaron, junto al mensaje de error
 
# Endpoint de la API que devuelve el detalle completo de un producto por ASIN.
url = "https://real-time-amazon-data.p.rapidapi.com/product-details"
 
# Recorre cada ASIN de la lista, uno por uno.
for asin in asins:
    try:
        # Parámetros de la consulta: el ASIN a buscar y el país (US).
        querystring = {
            "asin": asin,
            "country": "US"
        }
        # Petición GET con headers, parámetros y timeout de 30 segundos,
        # para no quedarse esperando indefinidamente si la API no responde.
        response = requests.get(
            url,
            headers=headers,
            params=querystring,
            timeout=30
        )
 
        # Si la respuesta HTTP indica error (4xx/5xx), lanza una excepción
        # que será capturada por el bloque except de abajo.
        response.raise_for_status()
 
        # Extrae el campo "data" del JSON de respuesta; si no existe,
        # usa un diccionario vacío por defecto.
        data = response.json().get("data", {})

        if data:
            # Si hay datos, se agregan a la lista de resultados y se
            # confirma en consola con un check.
            detalles.append(data)
            print(f"✓ {asin}")
        else:
            # Si la API respondió pero sin datos útiles, se advierte
            # en consola pero no se detiene el proceso.
            print(f"{asin} sin datos")
        # Pausa de 1 segundo entre peticiones para respetar límites de
        # uso (rate limiting) de la API y evitar bloqueos.
        time.sleep(1)

    except Exception as e:
        # Si algo falla (timeout, error HTTP, JSON inválido, etc.), se
        # registra el ASIN y el error, y se continúa con el siguiente
        # ASIN sin interrumpir todo el proceso.
        errores.append({
            "asin": asin,
            "error": str(e)
        })
        print(f"✗ {asin} - {e}")
 
 
# ── 5. CONSOLIDACIÓN Y EXPORTACIÓN DE RESULTADOS ────────────────────────
 
# Convierte la lista de detalles obtenidos en un DataFrame de pandas.
# (Igual que en el script 01, si "detalles" está vacío este DataFrame
# queda vacío pero sí se crea, así que no hay riesgo de NameError aquí.)
df_detalles = pd.DataFrame(detalles)
 
# Reporta cuántos productos se lograron extraer con éxito.
print(f"\nDetalles extraídos: {len(df_detalles)}")
 
# Muestra qué columnas trajo la API (útil para saber qué campos hay
# disponibles: precio, título, imágenes, reseñas, especificaciones, etc.).
print("\nColumnas obtenidas:")
print(df_detalles.columns.tolist())
 
# Guarda los detalles exitosos en un CSV, sin incluir el índice numérico
# de pandas como columna.
df_detalles.to_csv("detalles_audifonos.csv",index=False)

print("\nArchivo generado: detalles_audifonos.csv")
 
# Si hubo errores durante el proceso, se guardan aparte en su propio CSV
# para poder revisarlos o reintentarlos después.
if errores:
    df_errores = pd.DataFrame(errores)
    df_errores.to_csv(
        "errores_detalles.csv",
        index=False
    )
    print(
        f"Errores registrados: {len(df_errores)} "
        "(errores_detalles.csv)"
    )
 
# Vista previa final: muestra las primeras filas del resultado en consola
# para una verificación rápida de que todo salió bien.
print("\nPrimeras filas:")
print(df_detalles.head())
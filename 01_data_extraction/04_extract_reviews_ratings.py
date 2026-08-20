"""
04_extract_reviews_ratings.py
==============================
 
PROPÓSITO GENERAL DEL SCRIPT:
Tomar el catálogo de productos generado por "01_extract_amazon_products.py"
(archivo "audifonos_inalambricos_amazon_us.csv"), extraer sus ASINs, y
consultar la API "Real-Time Amazon Data" (vía RapidAPI) con el endpoint
"/product-reviews" para descargar hasta 3 páginas de reseñas por cada
producto. Las reseñas obtenidas se guardan en "reseñas_audifonos.csv" y
los fallos en "errores_reviews.csv".
"""
 
# ── 1. IMPORTS ──────────────────────────────────────────────────────────
import requests                    # Para hacer las peticiones HTTP a la API de RapidAPI
import pandas as pd                # Para leer el CSV de entrada y construir el CSV de salida
import os                          # Para leer variables de entorno (la API key)
from dotenv import load_dotenv     # Para cargar variables de entorno desde un archivo .env
from pathlib import Path           # Para construir rutas de archivo de forma portable
 
 
# ── 2. CARGA DE CREDENCIALES (.env) ─────────────────────────────────────
 
# Ruta al .env, ubicado dos niveles arriba del script (de 01_data_extraction
# sube a la raíz del proyecto y entra a "config").
env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
 
# Carga las variables definidas en ese .env hacia el entorno del proceso.
# (A diferencia de los scripts 01-03, aquí no se imprime la ruta ni si
# existe el .env antes de cargarlo — no hay mensajes de diagnóstico previos.)
load_dotenv(dotenv_path=env_path)
 
# Lee la API key de RapidAPI desde la variable de entorno RAPIDAPI_KEY.
API_KEY = os.getenv("RAPIDAPI_KEY")
 
# Si no se encontró la key, se detiene la ejecución con un error claro.
if not API_KEY:
    raise ValueError("No se encontró RAPIDAPI_KEY")
 
# Cabeceras HTTP requeridas por RapidAPI: la key de autenticación y el
# host del servicio "Real-Time Amazon Data" que se va a consultar.
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
}
 
 
# ── 3. CARGA DEL CSV DE PRODUCTOS (SALIDA DE "01") ──────────────────────
 
# A diferencia de 01-03, aquí la ruta al CSV es relativa ("audifonos_...csv")
# en vez de construirse con Path(__file__).resolve().parent. Esto significa
# que el script solo encontrará el archivo si se ejecuta desde la carpeta
# donde vive el CSV; si se ejecuta desde otro directorio de trabajo, fallará.
# Tampoco valida antes si el archivo existe (no hay FileNotFoundError
# explícito como en 02 y 03): si no existe, pandas lanzará su propio error.
df_productos = pd.read_csv("audifonos_inalambricos_amazon_us.csv")
 
# Extrae los ASINs únicos, descartando nulos. (Aquí no se valida antes si
# la columna "asin" existe, ni se hace .astype(str) como en los scripts
# anteriores — si "asin" no está en el CSV, esta línea lanzará un KeyError.)
asins = df_productos["asin"].dropna().unique().tolist()
 
# Informa cuántos ASINs distintos se van a procesar.
print(f"ASINs encontrados: {len(asins)}")
 
 
# ── 4. DESCARGA DE RESEÑAS POR CADA ASIN (HASTA 3 PÁGINAS) ──────────────
 
reseñas = []    # Acumula las reseñas obtenidas de todos los productos
errores = []    # Acumula los (asin, page) que fallaron, junto al error
 
# Endpoint de la API que devuelve las reseñas de un producto, paginadas.
url = "https://real-time-amazon-data.p.rapidapi.com/product-reviews"
 
# Bucle externo: recorre cada ASIN del catálogo.
for asin in asins:
    # Bucle interno: para cada ASIN, intenta descargar hasta 3 páginas
    # de reseñas (páginas 1, 2 y 3).
    for page in range(1, 4):
 
        # Parámetros de la consulta: ASIN, número de página y país.
        querystring = {
            "asin": asin,
            "page": str(page),
            "country": "US"
        }

        try:
            # Petición GET con timeout de 30 segundos.
            # (Nota: a diferencia de 02 y 03, aquí no hay time.sleep()
            # entre peticiones, por lo que este script consulta la API
            # más rápido y sin pausa de cortesía entre llamadas.)
            response = requests.get(
                url,
                headers=headers,
                params=querystring,
                timeout=30
            )
 
            # Si la API responde con 429 (demasiadas peticiones / límite
            # de uso alcanzado), se avisa y se corta el bucle de páginas
            # para ese ASIN.
            # IMPORTANTE: este "break" solo rompe el bucle interno (páginas)
            # del ASIN actual; el bucle externo sigue e intentará el
            # siguiente ASIN de todos modos, por lo que si el límite de la
            # API ya se agotó, seguirá recibiendo 429 en cada ASIN
            # restante hasta terminar de recorrer toda la lista.
            if response.status_code == 429:
                print("Límite alcanzado")
                break
 
            # Si la respuesta HTTP indica otro tipo de error (4xx/5xx),
            # lanza una excepción capturada por el except de abajo.
            response.raise_for_status()
 
            # Extrae la lista de reseñas del JSON de respuesta; si no
            # existe el campo "data", usa una lista vacía por defecto.
            data = response.json().get("data", [])
 
            # Recorre cada reseña individual de esta página.
            for r in data:
                if isinstance(r, dict):
                    # Caso esperado: la reseña es un diccionario con sus
                    # propios campos (texto, rating, autor, etc.). Se le
                    # agrega el ASIN para poder relacionarla con el
                    # producto al analizar los datos después.
                    r["asin"] = asin
                    reseñas.append(r)
                else:
                    # Caso de respaldo: si la reseña no viene como
                    # diccionario (p. ej. es solo texto plano), se
                    # envuelve en un diccionario simple con el ASIN y
                    # el contenido crudo, para no perder el dato ni
                    # romper el script.
                    reseñas.append({
                        "asin": asin,
                        "review": r
                    })

        except Exception as e:
                    # Caso de respaldo: si la reseña no viene como
                    # diccionario (p. ej. es solo texto plano), se
                    # envuelve en un diccionario simple con el ASIN y
                    # el contenido crudo, para no perder el dato ni
                    # romper el script.
            errores.append({
                "asin": asin,
                "page": page,
                "error": str(e)
            })
            print(f"Error {asin}: {e}")
 
 
# ── 5. CONSOLIDACIÓN Y EXPORTACIÓN DE RESULTADOS ────────────────────────
 
# Convierte la lista de reseñas acumuladas en un DataFrame de pandas.
df_reseñas = pd.DataFrame(reseñas)
 
# Reporta cuántas reseñas se lograron extraer en total.
print(f"\nReviews extraídas: {len(df_reseñas)}")
 
# Guarda las reseñas en un CSV, sin incluir el índice numérico de pandas
# como columna.
df_reseñas.to_csv(
    "reseñas_audifonos.csv",
    index=False
)
 
# Si hubo errores durante el proceso, se guardan aparte en su propio CSV
# para poder revisarlos o reintentarlos después.
if errores:
    pd.DataFrame(errores).to_csv(
        "errores_reviews.csv",
        index=False
    )

print("Archivo generado: reseñas_audifonos.csv")
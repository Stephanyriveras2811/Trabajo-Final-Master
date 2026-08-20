"""
03_extract_price_history.py
============================
 
PROPÓSITO GENERAL DEL SCRIPT:
Tomar el catálogo de productos generado por "01_extract_amazon_products.py"
(archivo "audifonos_inalambricos_amazon_us.csv"), extraer sus ASINs, y
consultar la API de Keepa (https://api.keepa.com/product) para obtener el
historial de precios de cada producto. De ese historial se conserva
únicamente el último año, y se guarda en formato "largo" (una fila por
cada punto de precio en el tiempo) en "historial_precios_keepa_1year.csv".
Los ASINs que fallaron se registran en "errores_keepa.csv".
 
Nota sobre Keepa: la API devuelve el historial como una lista plana
[tiempo_1, precio_1, tiempo_2, precio_2, ...] donde el tiempo está en
"Keepa minutes" (minutos desde el 2011-01-01) y el precio en centavos
(o -1 si no hay dato disponible para ese punto).
"""
 
# ── 1. IMPORTS ──────────────────────────────────────────────────────────
import requests                          # Para hacer las peticiones HTTP a la API de Keepa
import pandas as pd                      # Para construir y exportar los DataFrames de resultados
from datetime import datetime, timedelta # Para convertir "Keepa minutes" a fechas y calcular el corte de 1 año
import time                              # Para pausar entre peticiones (time.sleep)
import os                                # Para leer variables de entorno (la API key)
from dotenv import load_dotenv           # Para cargar variables de entorno desde un archivo .env
from pathlib import Path                 # Para construir rutas de archivo de forma portable


# ── 2. CARGA DE CREDENCIALES (.env) ─────────────────────────────────────
 
# Ruta al .env, ubicado dos niveles arriba del script (de 01_data_extraction
# sube a la raíz del proyecto y entra a "config").
env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
 
# Mensajes de diagnóstico: dónde se busca el .env y si existe.
print("Buscando .env en:", env_path)
print("Existe:", env_path.exists())
 
# Carga las variables definidas en ese .env hacia el entorno del proceso.
load_dotenv(dotenv_path=env_path)
 
# Lee la API key de Keepa desde la variable de entorno KEEPA_KEY.
# (Nota: a diferencia de los scripts 01 y 02, aquí se usa una key distinta,
# KEEPA_KEY, no RAPIDAPI_KEY, porque Keepa es un servicio independiente.)
API_KEY = os.getenv("KEEPA_KEY")
 
# Si no se encontró la key, se detiene la ejecución con un error claro.
if not API_KEY:
    raise ValueError("No se encontró KEEPA en el archivo .env")

# Confirma (sin imprimir la key real) que sí se cargó correctamente.
print("API encontrada:", API_KEY is not None)
 
 
# ── 3. CARGA DEL CSV DE PRODUCTOS (SALIDA DE "01") ──────────────────────
 
# Ruta al CSV generado por el script 01 (se espera en la misma carpeta).
archivo_productos = (Path(__file__).resolve().parent/ "audifonos_inalambricos_amazon_us.csv"
)
 
# Verifica que el archivo exista antes de leerlo; si no, lanza un error
# explícito con la ruta que se intentó usar.
if not archivo_productos.exists():
    raise FileNotFoundError(f"No se encontró el archivo: {archivo_productos}")

# Carga el CSV completo en un DataFrame de pandas.
df_productos = pd.read_csv(archivo_productos)

# Valida que exista la columna "asin"; si falta, se detiene con un
# mensaje claro en vez de fallar más adelante de forma confusa.
if "asin" not in df_productos.columns:
    raise ValueError(
        "La columna 'asin' no existe en el archivo"
    )
 
# Extrae la lista de ASINs únicos y sin valores nulos:
#   .dropna()    -> descarta filas sin ASIN
#   .astype(str) -> asegura que todos sean texto
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


# ── 4. CONFIGURACIÓN DE LA CONSULTA A KEEPA ─────────────────────────────
 
# Endpoint de Keepa para obtener información (incluido historial) de un producto.
url = "https://api.keepa.com/product"
 
all_rows = []   # Acumula, en formato "largo", cada punto de precio con su fecha y ASIN
errores = []    # Acumula los ASINs que fallaron, junto al mensaje de error
 
# Fecha de corte: solo se conservarán puntos de precio de los últimos 365 días
# a partir del momento en que se ejecuta el script.
one_year_ago = datetime.now() - timedelta(days=365)


# ── 5. CONSULTA Y PROCESAMIENTO DEL HISTORIAL POR CADA ASIN ─────────────

for asin in asins:

    try:
 
        # Parámetros de la consulta a Keepa:
        #   key     -> la API key
        #   domain  -> 1 = Amazon.com (marketplace de EE. UU.)
        #   asin    -> el producto a consultar
        #   history -> 1 = incluir el historial de precios en la respuesta
        params = {
            "key": API_KEY,
            "domain": 1,
            "asin": asin,
            "history": 1
        }
 
        # Petición GET con timeout de 30 segundos.
        response = requests.get(
            url,
            params=params,
            timeout=30
        )
 
        # Lanza excepción si la respuesta HTTP es un error (4xx/5xx).
        response.raise_for_status()

        data = response.json()
 
        # Valida que la respuesta tenga la estructura esperada.
        if "products" not in data:
            raise ValueError(
                f"Respuesta inesperada: {data}"
            )
 
        # Valida que la lista de productos no venga vacía.
        if len(data["products"]) == 0:
            raise ValueError(
                "No se encontraron productos"
            )
 
        # Se toma el primer (y único esperado) producto de la respuesta.
        product = data["products"][0]
 
        # Valida que el producto traiga el campo "csv", donde Keepa
        # almacena las distintas series históricas (precios, rankings, etc.).
        if "csv" not in product:
            raise ValueError(
                "No existe historial de precios"
            )
 
        # "csv"[0] corresponde específicamente a la serie de "precio Amazon".
        # Es una lista plana alternada: [tiempo, precio, tiempo, precio, ...]
        prices = product["csv"][0]
 
        # Recorre la lista de 2 en 2: cada par es un (tiempo, precio).
        for i in range(0, len(prices), 2):
 
            keepa_time = prices[i]     # Tiempo en "Keepa minutes"
            price = prices[i + 1]      # Precio en centavos (o -1 si no hay dato)
 
            # Keepa usa -1 para indicar que no hay precio registrado en
            # ese punto; esos registros se omiten.
            if price == -1:
                continue
 
            # Conversión de "Keepa minutes" a fecha real: Keepa cuenta los
            # minutos transcurridos desde el 2011-01-01 00:00.
            date = (
                datetime(2011, 1, 1)
                + timedelta(minutes=keepa_time)
            )
 
            # Solo se conserva el punto si cae dentro del último año.
            if date >= one_year_ago:

                all_rows.append({
                    "asin": asin,
                    "date": date,
                    "price": price / 100   # Keepa expresa el precio en centavos; se convierte a unidades monetarias
                })
 
        # Confirmación en consola de que el ASIN se procesó con éxito.
        print(f"✓ {asin}")
 
        # Pausa de 2 segundos entre peticiones para respetar los límites
        # de uso (rate limiting) de la API de Keepa.
        time.sleep(2)

    except Exception as e:
 
        # Si algo falla (timeout, error HTTP, estructura inesperada, sin
        # historial, etc.), se registra el ASIN y el error, y se continúa
        # con el siguiente ASIN sin interrumpir todo el proceso.
        errores.append({
            "asin": asin,
            "error": str(e)
        })

        print(f"✗ {asin} - {e}")
 
 
# ── 6. CONSOLIDACIÓN Y EXPORTACIÓN DE RESULTADOS ────────────────────────
 
# Convierte todos los puntos de precio acumulados (de todos los ASINs) en
# un único DataFrame en formato "largo" (una fila por punto de precio).
df = pd.DataFrame(all_rows)
 
# Reporta cuántos registros de precio se obtuvieron en total.
print(f"\nRegistros extraídos: {len(df)}")
 
# Muestra las columnas generadas (asin, date, price).
print("\nColumnas generadas:")
print(df.columns.tolist())
 
# Guarda el historial de precios del último año en un CSV.
df.to_csv(
    "historial_precios_keepa_1year.csv",
    index=False
)
 
print(
    "\nArchivo generado: "
    "historial_precios_keepa_1year.csv"
)

# Si hubo errores durante el proceso, se guardan aparte en su propio CSV
# para poder revisarlos o reintentarlos después.
if errores:

    df_errores = pd.DataFrame(errores)

    df_errores.to_csv(
        "errores_keepa.csv",
        index=False
    )

    print(
        f"Errores registrados: "
        f"{len(df_errores)}"
    )
 
# Vista previa final: primeras filas del resultado, para verificación rápida.
print("\nPrimeras filas:")
print(df.head())
"""
12_inventory_analysis.py
=========================

PROPÓSITO GENERAL DEL SCRIPT:
Consultar la API de Keepa para un conjunto de ASINs fijado manualmente
en el código, y extraer información de disponibilidad/inventario de cada
producto (disponibilidad en Amazon, disponibilidad de terceros/FBA y
condición del producto). El resultado se guarda en "keepa_stock.csv".

A diferencia de los scripts anteriores del pipeline, este NO lee la
lista de ASINs desde el catálogo generado en la etapa de extracción
(audifonos_inalambricos_amazon_us.csv); usa una lista de 32 ASINs
escrita directamente en el código.
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import requests                    # Para hacer las peticiones HTTP a la API de Keepa
import csv                         # Para escribir el archivo de salida directamente como CSV
import os                          # Para leer variables de entorno (la API key)
from dotenv import load_dotenv     # Para cargar variables de entorno desde un archivo .env


# ── 2. CARGA DE CREDENCIALES (.env) ──────────────────────────────────────

# Carga el .env SIN especificar una ruta (a diferencia de 01-04, que
# construían la ruta con Path(__file__).resolve().parent.parent /
# "config" / ".env"). load_dotenv() sin argumentos busca un archivo
# ".env" en el directorio de trabajo actual (desde donde se ejecuta el
# script), no necesariamente en la carpeta "config" del proyecto. Esto
# significa que este script solo cargará las credenciales correctamente
# si se ejecuta desde una carpeta donde haya un ".env" accesible, o si
# las variables ya están definidas en el entorno del sistema por otro medio.
load_dotenv()

# Lee la API key desde la variable de entorno "KEEPA".
# IMPORTANTE: el script "03_extract_price_history.py" usa el nombre de
# variable "KEEPA_KEY", no "KEEPA". Si el archivo .env del proyecto solo
# define "KEEPA_KEY", esta línea devolverá None y el script fallará con
# el ValueError de abajo — es una inconsistencia de nombres entre
# scripts que conviene unificar.
API_KEY = os.getenv("KEEPA")

# Si no se encontró la key, se detiene la ejecución con un error claro.
if not API_KEY:
    raise ValueError("No se encontró la API KEY de Keepa en el .env")


# ── 3. LISTA DE ASINs (FIJA, ESCRITA EN EL CÓDIGO) ───────────────────────

# A diferencia de 02, 03 y 04 (que leían los ASINs desde el CSV generado
# por el script 01), aquí la lista de 32 ASINs está codificada
# directamente ("hardcodeada"). Esto implica que si el catálogo de
# productos cambia (nuevos productos agregados o eliminados en 01), esta
# lista NO se actualiza automáticamente y debe editarse a mano.
asins = [
    "B0FQFB8FMG","B0DGHMNQ5Z","B0FT2DC92C","B09LYF2ST7","B0CQXMXJC5",
    "B0CTBCDD6D","B0GHJNT877","B0C3HCD34R","B08WM3LMJF","B0BQPNMXQV",
    "B0CFV9XR2Q","B0G64H1QX7","B09BF64J55","B0G4W9HX8K","B0BS1RT9S2",
    "B0C8PR4W22","B0DN45YMP6","B0G6CNF8RM","B0D4TL3DD3","B0CZPLV566",
    "B0D635YLCT","B09NNBBY8F","B0BS1QCFHX","B092CP8ZH4","B0CZPGX972",
    "B0FG2PMNS2","B0CRTR3PMF","B0CT9XTKKM","B0GCH8VJQQ","B0BTYCRJSS",
    "B0G64GBBRR","B09FT58QQP"
]

# Endpoint de Keepa para obtener información de un producto.
url = "https://api.keepa.com/product"


# ── 4. CONSULTA Y ESCRITURA DIRECTA A CSV ────────────────────────────────

# Abre el archivo de salida en modo escritura ("w"). newline="" evita
# que el módulo csv agregue líneas en blanco extra entre filas en
# Windows. encoding="utf-8" asegura que los títulos de producto con
# acentos u otros caracteres especiales se guarden correctamente.
# A diferencia de los scripts 01-11 (que acumulan los resultados en una
# lista y arman un DataFrame de pandas al final con pd.to_csv), este
# script escribe fila por fila directamente con el módulo csv estándar
# de Python, sin pasar por pandas.
with open("keepa_stock.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    # Escribe la fila de encabezados.
    writer.writerow(["ASIN", "Título", "Disponible Amazon", "Disponible Terceros", "Estado"])

    # Recorre cada ASIN de la lista fija.
    for asin in asins:

        # Parámetros de la consulta: key de autenticación, dominio
        # (1 = Amazon.com / EE. UU.) y el ASIN a consultar.
        params = {
            "key": API_KEY,
            "domain": 1,
            "asin": asin
        }

        try:
            # Petición GET con timeout de 20 segundos (más corto que los
            # 30 segundos usados en los scripts anteriores).
            response = requests.get(url, params=params, timeout=20)

            # Lanza excepción si la respuesta HTTP es un error (4xx/5xx).
            response.raise_for_status()

            data = response.json()

            # Toma el primer producto de la lista de resultados. Si
            # "products" no existe o viene vacía, product.get(...)
            # (más abajo) usa un diccionario vacío por defecto, así que
            # no se lanza un error explícito aquí como sí hacía el
            # script 03 con sus "raise ValueError" — cualquier campo
            # faltante simplemente cae en su valor por defecto ("Sin
            # título", "No disponible", etc.).
            product = data.get("products", [{}])[0]

            # Si el producto no trae su propio ASIN en la respuesta, se
            # usa el ASIN original que se envió en la consulta.
            asin_val = product.get("asin", asin)
            title = product.get("title", "Sin título")

            # Campos de disponibilidad e inventario. Si Keepa no
            # devuelve el campo, se usa un texto por defecto en vez de
            # dejarlo vacío o nulo.
            available_amazon = product.get("availabilityAmazon", "No disponible")
            available_third = product.get("availabilityFBA", "No disponible")
            condition = product.get("condition", "No especificado")

            # Escribe la fila con los datos obtenidos para este ASIN.
            writer.writerow([asin_val, title, available_amazon, available_third, condition])

            print(f"✓ {asin}")

        except Exception as e:
            # Cualquier error (timeout, error HTTP, índice fuera de
            # rango si "products" viene vacía, etc.) se informa en
            # consola y el script continúa con el siguiente ASIN.
            # A diferencia de otros scripts del pipeline, aquí NO se
            # acumulan los errores en una lista ni se exportan a un CSV
            # de errores aparte — solo quedan impresos en la consola de
            # esa ejecución, y se pierden si no se registra la salida.
            print(f"✗ Error con {asin}: {e}")

print("Archivo 'keepa_stock.csv' creado con éxito.")
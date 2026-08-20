"""
06_merge_datasets.py
=====================
 
PROPÓSITO GENERAL DEL SCRIPT:
Unir (merge) el archivo de detalles de producto ya limpio (generado por
"05_clean_product_details.py") con el historial de precios de Keepa
(generado por "03_extract_price_history.py"), usando el ASIN como llave
de unión. El resultado es un único dataset "largo" (una fila por cada
punto de precio en el tiempo, con toda la información del producto
repetida en cada fila) que se guarda en la carpeta "03_output" como
"audifonos_unificado.csv".
 
Es el paso final de la etapa de limpieza/integración: combina las dos
fuentes de datos (detalles + historial) en un solo archivo listo para
análisis o modelado.
"""
 
# ── 1. IMPORTS ──────────────────────────────────────────────────────────
import pandas as pd        # Para leer, unir y exportar los DataFrames
from pathlib import Path   # Para construir rutas de archivo de forma portable
 
 
# ── 2. FUNCIÓN PRINCIPAL DE UNIÓN ────────────────────────────────────────
 
def unir_datasets(detalles_path, historial_path, output):
    """
    Lee los dos CSV de entrada (detalles de producto e historial de
    precios), los une por ASIN, guarda el resultado en 'output' y
    devuelve el DataFrame unificado.
    """
 
    # Carga ambos CSV en DataFrames separados.
    detalles = pd.read_csv(detalles_path)
    historial = pd.read_csv(historial_path)
 
    # Normaliza los nombres de columnas de ambos DataFrames:
    #   .str.strip() -> quita espacios en blanco al inicio/final del nombre
    #   .str.lower() -> convierte todo a minúsculas
    # Esto es necesario porque "05_clean_product_details.py" renombró la
    # columna a "ASIN" (mayúsculas), mientras que "historial" trae "asin"
    # (minúsculas, tal como lo generó "03_extract_price_history.py").
    # Al pasar ambas a minúsculas, la columna de unión queda como "asin"
    # en los dos DataFrames.
    detalles.columns = detalles.columns.str.strip().str.lower()
    historial.columns = historial.columns.str.strip().str.lower()
 
    # Une los dos DataFrames por la columna "asin":
    #   - Se parte de "historial" (una fila por punto de precio) y se le
    #     agregan las columnas de "detalles" (información del producto).
    #   - how="left" conserva TODAS las filas de "historial", aunque no
    #     exista un ASIN correspondiente en "detalles" (en ese caso, las
    #     columnas de detalles quedarían con NaN para esas filas).
    unificado = historial.merge(detalles, on="asin", how="left")
 
    # Crea una columna adicional "asin_group", idéntica a "asin". Sirve
    # como una copia del identificador, útil por ejemplo para agrupar
    # (groupby) sin alterar o perder la columna original "asin" en pasos
    # posteriores del análisis.
    unificado["asin_group"] = unificado["asin"]
 
    # Guarda el DataFrame unificado en la ruta de salida, sin incluir el
    # índice numérico de pandas como columna.
    unificado.to_csv(output, index=False)

    print(f"Archivo unificado guardado en: {output}")
 
    # Devuelve el DataFrame unificado, útil si la función se reutiliza
    # como módulo importado en vez de ejecutarse directamente.
    return unificado
 
 
# ── 3. BLOQUE DE EJECUCIÓN DIRECTA ──────────────────────────────────────
 
# Este bloque solo se ejecuta si el script se corre directamente
# (python 06_merge_datasets.py), no si se importa como módulo.
if __name__ == "__main__":

 
    # Ruta base del proyecto: sube dos niveles desde este script
    # (de la carpeta de limpieza a la raíz del proyecto).
    base_path = Path(__file__).resolve().parent.parent
 
    # Ruta de entrada 1: el CSV de detalles ya limpio (salida de 05).
    detalles_path = base_path / "02_cleaning" / "detalles_limpio.csv"
 
    # Ruta de entrada 2: el CSV de historial de precios (salida de 03).
    historial_path = base_path / "01_data_extraction" / "historial_precios_keepa_1year.csv"
 
    # Ruta de salida: el CSV unificado final, dentro de la carpeta "03_output".
    output_path = base_path / "03_output" / "audifonos_unificado.csv"
 
    # Crea la carpeta de destino si no existe (parents=True crea también
    # carpetas intermedias faltantes; exist_ok=True evita error si ya existe).
    output_path.parent.mkdir(parents=True, exist_ok=True)
 
    # Ejecuta la unión con las rutas definidas arriba.
    unir_datasets(detalles_path, historial_path, output_path)
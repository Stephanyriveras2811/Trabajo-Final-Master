"""
05_clean_product_details.py
============================
 
PROPÓSITO GENERAL DEL SCRIPT:
Limpiar el archivo de detalles de producto generado por
"02_extract_product_details.py" (detalles_audifonos.csv): estandariza el
nombre de la columna de identificador a "ASIN" y elimina productos
duplicados. El resultado se guarda en la carpeta "02_cleaning" del
proyecto, como "detalles_limpio.csv".
 
Es el primer paso de la etapa de limpieza del pipeline (carpeta
"02_cleaning"), y consume la salida de la etapa de extracción (carpeta
"01_data_extraction").
"""
 
# ── 1. IMPORTS ──────────────────────────────────────────────────────────
from pathlib import Path   # Para construir rutas de archivo de forma portable
import pandas as pd        # Para leer, limpiar y exportar el DataFrame de detalles
 
 
# ── 2. FUNCIÓN PRINCIPAL DE LIMPIEZA ─────────────────────────────────────

def limpiar_detalles(path, output):
    """
    Lee el CSV de detalles en 'path', lo limpia y guarda el resultado en
    'output'. Devuelve también el DataFrame limpio, por si se quiere
    seguir usando en memoria (por ejemplo, si esta función se importa y
    se llama desde otro script del pipeline).
    """
 
    # Carga el CSV de detalles de producto en un DataFrame.
    detalles = pd.read_csv(path)
 
    # Si existe una columna "asin" (en minúscula, como la generan los
    # scripts de extracción), se renombra a "ASIN" para estandarizar el
    # nombre de la columna identificadora en toda la etapa de limpieza.
    if "asin" in detalles.columns:
        detalles.rename(columns={"asin": "ASIN"}, inplace=True)
 
    # Si ya existe (o quedó) la columna "ASIN", se eliminan las filas
    # duplicadas según ese identificador, conservando una sola fila por
    # producto. Esto cubre el caso de que la extracción haya traído el
    # mismo ASIN más de una vez.
    if "ASIN" in detalles.columns:
        detalles = detalles.drop_duplicates(subset=["ASIN"])
 
    # Guarda el DataFrame limpio en la ruta de salida indicada, sin
    # incluir el índice numérico de pandas como columna.
    detalles.to_csv(output, index=False)
    print(f"Archivo limpio guardado en: {output}")
 
    # Devuelve el DataFrame limpio, útil si la función se reutiliza
    # como módulo importado en vez de ejecutarse directamente.
    return detalles
 
 
# ── 3. BLOQUE DE EJECUCIÓN DIRECTA ──────────────────────────────────────
 
# Este bloque solo se ejecuta si el script se corre directamente
# (python 05_clean_product_details.py), no si se importa como módulo
# desde otro script.
if __name__ == "__main__":
 
    # Ruta base del proyecto: sube dos niveles desde este script
    # (de la carpeta de limpieza a la raíz del proyecto).
    base_path = Path(__file__).resolve().parent.parent
 
    # Ruta de entrada: el CSV de detalles generado por el script 02,
    # ubicado en la carpeta "01_data_extraction".
    input_path = base_path / "01_data_extraction" / "detalles_audifonos.csv"
 
    # Ruta de salida: el CSV limpio, dentro de la carpeta "02_cleaning".
    output_path = base_path / "02_cleaning" / "detalles_limpio.csv"
 
    # Crea la carpeta de destino si no existe (parents=True crea también
    # carpetas intermedias faltantes; exist_ok=True evita error si ya existe).
    output_path.parent.mkdir(parents=True, exist_ok=True)
 
    # Ejecuta la limpieza con las rutas definidas arriba.
    limpiar_detalles(input_path, output_path)
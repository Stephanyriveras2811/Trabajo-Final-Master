"""
07_final_data_validation.py
============================
 
PROPÓSITO GENERAL DEL SCRIPT:
Tomar el dataset unificado generado por "06_merge_datasets.py"
(audifonos_unificado.csv), hacer una validación final básica —eliminar
registros duplicados y reportar valores nulos por columna— y guardar el
resultado como "audifonos_unificado_limpio.csv" en la carpeta "03_output".
 
Es el último paso de la etapa de limpieza/integración antes de pasar el
dataset a la fase de análisis (EDA) o modelado.
"""
 
# ── 1. IMPORTS ──────────────────────────────────────────────────────────
import pandas as pd        # Para cargar, validar y exportar el DataFrame
from pathlib import Path   # Para construir rutas de archivo de forma portable
 
 
# ── 2. RUTAS ─────────────────────────────────────────────────────────────
 
# Ruta base del proyecto: sube dos niveles desde este script
# (de la carpeta actual a la raíz del proyecto).
base_path = Path(__file__).resolve().parent.parent
 
# Archivo de entrada: el dataset unificado producido por el script 06.
input_file = base_path / "03_output" / "audifonos_unificado.csv"
 
# Archivo de salida: el dataset validado/limpio, en la misma carpeta "03_output".
output_file = base_path / "03_output" / "audifonos_unificado_limpio.csv"
 
 
# ── 3. CARGA DE DATOS ────────────────────────────────────────────────────
 
# Carga el CSV unificado en un DataFrame.
# (Nota: a diferencia de otros scripts del pipeline, aquí no se valida
# antes si "input_file" existe — si no está, pandas lanzará su propio
# error de archivo no encontrado.)
df = pd.read_csv(input_file)

print("Archivo cargado correctamente.")
print(f"Registros: {len(df)}")
print(f"Columnas: {len(df.columns)}")
 
 
# ── 4. VALIDACIÓN ─────────────────────────────────────────────────────────
 
# Cuenta cuántas filas están completamente duplicadas (todas sus columnas
# son idénticas a otra fila). Esto es distinto del drop_duplicates(subset=
# ["ASIN"]) del script 05: aquí se comparan TODAS las columnas, no solo el
# identificador, lo cual tiene sentido porque a esta altura el dataset ya
# tiene una fila por cada combinación de (asin, fecha, precio, detalles...),
# así que una duplicación exacta de fila sí sería un registro repetido real.
duplicados = df.duplicated().sum()

if duplicados > 0:
    # Si se encontraron duplicados, se informa cuántos y se eliminan,
    # conservando la primera aparición de cada fila (comportamiento por
    # defecto de drop_duplicates()).
    print(f"Se eliminaron {duplicados} registros duplicados.")
    df = df.drop_duplicates()
else:
    print("No se encontraron registros duplicados.")
 
# Muestra, por cada columna, cuántos valores nulos (NaN) tiene.
# IMPORTANTE: esto es solo un REPORTE en consola — el script NO elimina
# ni imputa esos valores nulos; el dataset se exporta con ellos intactos.
print("\nValores nulos por columna:")
print(df.isnull().sum())
 
 
# ── 5. GUARDAR DATASET LIMPIO ────────────────────────────────────────────
 
# Crea la carpeta de destino si no existe (parents=True crea también
# carpetas intermedias faltantes; exist_ok=True evita error si ya existe).
# En este caso normalmente ya existe, porque es la misma carpeta "03_output"
# donde se guardó "audifonos_unificado.csv" en el script anterior.
output_file.parent.mkdir(parents=True, exist_ok=True)
 
# Guarda el DataFrame (sin duplicados exactos, pero con los nulos que
# tuviera) en el archivo de salida, sin incluir el índice de pandas.
df.to_csv(output_file, index=False)

print(f"\nArchivo generado correctamente:")
print(output_file)
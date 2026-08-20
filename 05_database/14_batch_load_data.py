"""
14_batch_load_data.py
======================

PROPÓSITO GENERAL DEL SCRIPT:
Cargar el dataset final enriquecido (audifonos_unificado_limpio_enriquecido.csv)
a una base de datos SQL Server, en una tabla llamada "amazon_raw", y
verificar que el número de filas cargadas coincida con el número de
filas del archivo original. Corresponde a la sección "Carga de los
datos" del documento del proyecto (dentro de "Almacenamiento de los
datos"): "se verificó que el número de registros almacenados en la base
de datos coincidiera con el número de registros presentes en el archivo
original, garantizando así la integridad de la información."

DEPENDENCIA EXTERNA (módulo propio del proyecto, no compartido):
  - conexion.engine -> objeto de conexión a la base de datos
    (probablemente un SQLAlchemy Engine apuntando a SQL Server, dado que
    se usa directamente con pandas.DataFrame.to_sql() y pd.read_sql(),
    ambos compatibles con SQLAlchemy).

A pesar del nombre del archivo ("batch_load_data"), la tabla de destino
se llama "amazon_raw", que sugiere que este es un paso de carga inicial
/ "en bruto" hacia SQL Server, posiblemente anterior a la creación del
modelo estrella (fact_product_metrics, dim_product, dim_date) descrito
más adelante en el documento — es decir, probablemente existan otros
scripts (no compartidos) que transformen "amazon_raw" en las tablas de
hechos y dimensiones finales.
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import pandas as pd            # Para leer el CSV y cargarlo a SQL / consultar SQL
from conexion import engine    # Módulo propio: provee el objeto de conexión a la base de datos


# ── 2. CARGA DEL CSV ─────────────────────────────────────────────────────

# Lee el dataset final con ruta RELATIVA (igual que los scripts 11 y 13
# — no usa Path(__file__)... como los scripts 01-10). El script debe
# ejecutarse desde la carpeta donde está el CSV para encontrarlo.
df = pd.read_csv("audifonos_unificado_limpio_enriquecido.csv")
print("Datos cargados desde CSV:")
print(df.head())


# ── 3. CARGA A SQL SERVER ─────────────────────────────────────────────────

print("Cargando datos a SQL...")

# Envía el DataFrame completo a la base de datos, creando (o
# reemplazando) la tabla "amazon_raw".
#   if_exists="replace" -> si la tabla ya existe, la BORRA por completo
#                          y la vuelve a crear desde cero con los datos
#                          actuales. Esto significa que cada ejecución
#                          de este script sobrescribe todo el histórico
#                          previamente cargado en "amazon_raw" — no es
#                          una carga incremental ni un "upsert", es una
#                          recarga total.
#   index=False          -> no incluye el índice numérico de pandas
#                          como una columna adicional en la tabla SQL.
df.to_sql("amazon_raw", engine, if_exists="replace", index=False)

print("Carga finalizada")


# ── 4. VERIFICACIÓN DE INTEGRIDAD (CONTEO DE FILAS) ──────────────────────

# Cantidad de filas en el DataFrame original (ya en memoria, en Python).
count_csv = len(df)

# Cantidad de filas en la tabla recién cargada, consultada directamente
# a la base de datos con una consulta SQL de conteo.
# (Nota: pd.read_sql devuelve un DataFrame de una sola fila/columna, no
# un número simple — count_sql es un DataFrame con una columna "total",
# no un entero. Esto es relevante para el siguiente paso, ver nota abajo.)
count_sql = pd.read_sql("SELECT COUNT(*) as total FROM amazon_raw", engine)

print("Filas CSV:", count_csv)
# Imprime el DataFrame completo (con su índice y encabezado de columna
# "total"), no el número aislado. Por ejemplo, en vez de mostrar
# simplemente "20", mostraría algo como:
#    total
# 0     20
# Para obtener solo el número, habría sido más preciso escribir
# count_sql["total"][0] o count_sql.iloc[0, 0].
# Esto NO es un error que rompa el script, pero hace que la
# verificación visual sea menos directa de leer que una comparación
# explícita como "if count_csv == count_sql['total'][0]: print('OK')".
print("Filas SQL:", count_sql)
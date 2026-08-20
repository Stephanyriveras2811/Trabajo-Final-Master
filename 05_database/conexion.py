"""
conexion.py
============

PROPÓSITO GENERAL DEL SCRIPT:
Módulo auxiliar que crea y expone un objeto de conexión ("engine") a
SQL Server, reutilizado por "14_batch_load_data.py" (import "from
conexion import engine") y probablemente por cualquier otro script del
proyecto que necesite leer o escribir en la base de datos (por ejemplo,
el/los script(s) que arman el modelo estrella con fact_product_metrics,
dim_product y dim_date).

Usa autenticación de Windows (Trusted_Connection=yes), por lo que no
requiere usuario/contraseña en el .env — solo el nombre del servidor y
de la base de datos.

También incluye un bloque de auto-test (if __name__ == "__main__") para
verificar la conexión ejecutando este archivo directamente.
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import os                              # Para leer variables de entorno
from pathlib import Path               # Para construir rutas de archivo portables

import urllib                          # Para codificar el string de conexión (urllib.parse.quote_plus)
from dotenv import load_dotenv         # Para cargar variables de entorno desde un archivo .env
from sqlalchemy import create_engine   # Para crear el objeto "engine" de conexión a la base de datos


# ── 2. CARGA DE VARIABLES DE ENTORNO ─────────────────────────────────────

# Ruta al .env, ubicada dos niveles arriba de este script (mismo patrón
# que los scripts 01-04 del pipeline de extracción: de la carpeta actual
# sube a la raíz del proyecto y entra a "config").
env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# Lee el nombre del servidor y de la base de datos SQL Server desde las
# variables de entorno. (Nota: a diferencia de las API keys usadas en
# los scripts de extracción, aquí NO se leen usuario ni contraseña,
# porque la conexión usa autenticación integrada de Windows —ver el
# parámetro Trusted_Connection=yes más abajo—, no login SQL.)
server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")

# Si falta cualquiera de los dos valores, se detiene la ejecución con un
# error claro, en vez de fallar más adelante con un error de conexión
# genérico y menos comprensible.
if not server or not database:
    raise ValueError(
        "No se encontraron SQL_SERVER o SQL_DATABASE en el archivo .env."
    )


# ── 3. CONSTRUCCIÓN DEL STRING DE CONEXIÓN ───────────────────────────────

# Arma el string de conexión ODBC con los parámetros necesarios:
#   DRIVER              -> el driver ODBC 17 de Microsoft para SQL Server
#                          (debe estar instalado en el sistema operativo
#                          donde corre el script, no es algo que Python
#                          instale por sí solo)
#   SERVER               -> el nombre/dirección del servidor SQL Server
#   DATABASE             -> el nombre de la base de datos específica
#   Trusted_Connection   -> "yes" indica autenticación integrada de
#                          Windows (usa las credenciales del usuario del
#                          sistema operativo actual, no un usuario/
#                          contraseña de SQL Server)
#
# urllib.parse.quote_plus(...) codifica todo ese string para que sea
# seguro incluirlo como parte de una URL (escapa espacios, símbolos como
# {}, ;, = que de otro modo romperían el formato de la URL de conexión).
params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes;"
)


# ── 4. CREACIÓN DEL ENGINE DE SQLALCHEMY ─────────────────────────────────

# Crea el objeto "engine" de SQLAlchemy, usando el dialecto "mssql"
# (Microsoft SQL Server) con el driver "pyodbc". El string de conexión
# codificado (params) se pasa como parámetro "odbc_connect" dentro de la
# URL. Este es el objeto que importan otros scripts del proyecto (como
# 14_batch_load_data.py) para leer/escribir en la base de datos con
# pandas (to_sql, read_sql).
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


# ── 5. PRUEBA DE CONEXIÓN (SOLO AL EJECUTAR ESTE ARCHIVO DIRECTAMENTE) ───

# Este bloque NO se ejecuta cuando otro script hace
# "from conexion import engine" — solo corre si conexion.py se ejecuta
# directamente (python conexion.py). Sirve como una forma rápida de
# verificar, de forma aislada, que las credenciales y el driver ODBC
# están correctamente configurados, sin tener que correr todo el
# pipeline de carga de datos.
if __name__ == "__main__":
    try:
        # Abre una conexión de prueba y la cierra automáticamente al
        # salir del bloque "with" (aunque no se ejecuta ninguna consulta,
        # el solo hecho de conectar exitosamente confirma que el
        # servidor, la base de datos y el driver están accesibles).
        with engine.connect() as conn:
            print("Conexión exitosa a SQL Server")
    except Exception as e:
        # Si la conexión falla (servidor inaccesible, base de datos
        # inexistente, driver ODBC no instalado, credenciales de Windows
        # sin permisos, etc.), se captura la excepción y se imprime el
        # detalle del error en vez de dejar que el traceback completo
        # interrumpa la ejecución de forma menos legible.
        print("Error de conexión:")
        print(e)
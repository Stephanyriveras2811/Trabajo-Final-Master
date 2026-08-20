"""
11_sales_patterns_analysis.py
==============================

PROPÓSITO GENERAL DEL SCRIPT:
Analizar el volumen de ventas estimado por marca, identificando los
productos/marcas con mayores ventas (>= 5000 unidades estimadas). Genera
un gráfico de barras horizontales con las marcas ordenadas de mayor a
menor volumen de ventas.

Corresponde a la parte de "Análisis exploratorio de los datos" descrita
en el documento como "analizar la distribución de las ventas por marca".

Entrada: audifonos_unificado_limpio_enriquecido.csv (salida de 08),
         leído con ruta RELATIVA (no con Path(__file__)... como en la
         mayoría de los scripts anteriores del pipeline).
Salida: ninguna a disco — solo muestra el gráfico en pantalla
        (plt.show()), no lo guarda con plt.savefig() como sí hacían
        los scripts 09 y 10.
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import pandas as pd                # Manipulación de datos
import matplotlib.pyplot as plt    # Generación de gráficos
import seaborn as sns              # Gráfico de barras estilizado
from pathlib import Path                          # Rutas de archivo portables


# ── 2. CARGA Y PREPARACIÓN DE DATOS ──────────────────────────────────────
 
# Ruta base del proyecto: sube dos niveles desde este script.
base_path = Path(__file__).resolve().parent.parent

# Ruta al dataset enriquecido (salida del script 08).
output = base_path / "03_output" / "audifonos_unificado_limpio_enriquecido.csv"

df = pd.read_csv(output)


# ── 3. LIMPIEZA BÁSICA Y PREPARACIÓN ──────────────────────────────────────

# Convierte "date" a tipo fecha real; los valores no interpretables
# quedan como NaT.
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Elimina filas sin fecha válida o sin ASIN, ya que ambas son
# indispensables para el análisis (no se puede ordenar por fecha ni
# identificar el producto si faltan).
df = df.dropna(subset=['date', 'asin'])

# Igual que en los scripts 09 y 10: el dataset está en formato "largo"
# (una fila por punto de precio en el tiempo). Se ordena por fecha y se
# conserva solo la última fila (más reciente) de cada ASIN, para tener
# un único registro por producto.
df_recent = df.sort_values('date').groupby('asin').last().reset_index()


# ── 4. EXTRACCIÓN DEL NOMBRE DE MARCA ─────────────────────────────────────

# Si la columna "product_byline" (que en Amazon suele traer algo como
# "Visit the Sony Store") no existe en el dataset, se crea con el valor
# por defecto "Unknown" en todas las filas, para que el resto del script
# no falle por columna faltante.
if "product_byline" not in df_recent.columns:
    df_recent["product_byline"] = "Unknown"

# Limpia el texto de "product_byline" para quedarse solo con el nombre
# de la marca: quita el prefijo "Visit the " y el sufijo " Store", y
# recorta espacios sobrantes. Ejemplo: "Visit the Sony Store" -> "Sony".
df_recent['brand_short'] = (
    df_recent['product_byline']
    .str.replace('Visit the ', '', regex=False)
    .str.replace(' Store', '', regex=False)
    .str.strip()
)


# ── 5. PREPARACIÓN DEL VOLUMEN DE VENTAS ─────────────────────────────────

# Convierte "sales_volume_num" a numérico. df_recent.get('sales_volume_num', 0)
# devuelve la columna si existe, o el valor 0 si no existe en absoluto
# (en cuyo caso pd.to_numeric(0, ...) generaría un solo valor escalar,
# no una columna — este caso límite dejaría el script en un estado
# inconsistente, aunque en la práctica la columna sí debería existir
# porque la genera el script 08).
df_recent['sales_volume_num'] = pd.to_numeric(
    df_recent.get('sales_volume_num', 0),
    errors='coerce'
)

# Elimina filas donde el volumen de ventas no se pudo convertir a número
# (quedó como NaN tras el paso anterior).
df_recent = df_recent.dropna(subset=['sales_volume_num'])


# ── 6. FILTRO: PRODUCTOS DE ALTAS VENTAS ─────────────────────────────────

# Se queda solo con los productos cuyo volumen de ventas estimado es de
# al menos 5000 unidades — un umbral fijo (hardcodeado) para destacar
# los productos de mayor demanda.
high_sales = df_recent[df_recent['sales_volume_num'] >= 5000].copy()

# Ordena de mayor a menor volumen de ventas, para que el gráfico de
# barras quede ordenado visualmente de arriba hacia abajo (o de mayor a
# menor según el orden en que Seaborn dibuje las categorías).
high_sales = high_sales.sort_values('sales_volume_num', ascending=False)


# ── 7. VISUALIZACIÓN: GRÁFICO DE BARRAS HORIZONTALES ─────────────────────

plt.figure(figsize=(11, 7))

# Barras horizontales: eje X = volumen de ventas, eje Y = marca.
# (Nota: si varios productos comparten la misma marca, "brand_short" no
# es único, por lo que podría haber varias barras con la misma etiqueta
# de marca en el eje Y en vez de una sola barra agregada por marca — el
# script no hace un groupby por marca antes de graficar, grafica un
# producto por barra usando el nombre de marca como etiqueta.)
bars = sns.barplot(
    data=high_sales,
    x='sales_volume_num',
    y='brand_short',
    palette='viridis'
)

# Agrega el valor numérico exacto al final de cada barra, como etiqueta
# de texto con separador de miles (formato "5,000").
for bar in bars.patches:
    bars.text(
        bar.get_width() + 200,                  # Posición X: un poco después del final de la barra
        bar.get_y() + bar.get_height()/2,       # Posición Y: centrada verticalmente en la barra
        f'{int(bar.get_width()):,}',            # Texto: el valor de la barra, formateado con comas de miles
        va='center',
        fontsize=10,
        fontweight='bold'
    )

plt.title(
    'Productos con Mayores Ventas Estimadas\n(Última observación por ASIN)',
    fontsize=14, pad=20
)

plt.xlabel('Ventas estimadas por mes (unidades)', fontsize=12)
plt.ylabel('Marca / Tienda', fontsize=12)

plt.grid(axis='x', alpha=0.3, linestyle='--')

plt.tight_layout()

# Muestra el gráfico en pantalla. A diferencia de los scripts 09 y 10,
# este script NO llama a plt.savefig() antes de plt.show(), por lo que
# el gráfico no queda guardado como archivo de imagen — solo se ve en
# la ejecución interactiva y se perdería en una ejecución no interactiva
# (por ejemplo, corrido desde una terminal sin entorno gráfico).
plt.show()
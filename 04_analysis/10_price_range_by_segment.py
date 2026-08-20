"""
10_price_range_by_segment.py
=============================

PROPÓSITO GENERAL DEL SCRIPT:
Analizar los rangos de precio de los productos mediante la segmentación
MANUAL por rangos fijos (Económico / Medio / Premium) — la misma regla
usada como línea base en "09_exploratory_data_analysis.py" (K-Means),
pero aquí es el foco principal, no solo una comparación. Este script
corresponde a la parte del "Análisis exploratorio de los datos" descrita
en el documento como "identificar los rangos de precios de los
productos": genera una tabla resumen por segmento, un hallazgo textual
automático, y un boxplot anotado con ejemplos de marcas por segmento.

Entrada: audifonos_unificado_limpio_enriquecido.csv (salida de 08).
Salidas:
  - tabla_precio_por_segmento.csv
  - figura_precio_por_segmento.png (boxplot)
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import pandas as pd                # Manipulación de datos
import matplotlib.pyplot as plt    # Generación de gráficos
import seaborn as sns              # Boxplot estadístico
from pathlib import Path           # Rutas de archivo portables


# ── 2. CARGA DE DATOS ─────────────────────────────────────────────────────

# Ruta base del proyecto: sube dos niveles desde este script.
base_path = Path(__file__).resolve().parent.parent

# Ruta al dataset enriquecido (salida del script 08).
output_file = base_path / "03_output" / "audifonos_unificado_limpio_enriquecido.csv"

df = pd.read_csv(output_file)

print("Archivo cargado correctamente.")
# Nota: falta el paréntesis de llamada — "df.head" imprime la
# representación del MÉTODO (un objeto <bound method...>), no las
# primeras filas del DataFrame. Para ver los datos debería ser df.head().
print(df.head)


# ── 3. PREPARACIÓN: UN REGISTRO POR PRODUCTO ─────────────────────────────

# Convierte la columna "date" a tipo fecha real; los valores no
# interpretables quedan como NaT (errors="coerce").
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# El dataset está en formato "largo" (una fila por punto de precio en el
# tiempo). Para analizar el precio ACTUAL de cada producto, se ordena
# por fecha y se conserva solo la última fila (más reciente) de cada
# ASIN — mismo patrón usado en el script 09.
# (Nota: a diferencia de 09, aquí no se normalizan antes los nombres de
# columnas con .str.strip().str.lower(); se asume que ya vienen
# correctos desde el archivo de entrada.)
df_recent = df.sort_values('date').groupby('asin').last().reset_index()


def asignar_segmento(precio):
    """
    Segmentación manual por rangos fijos de precio — idéntica a la
    función homónima del script 09, usada aquí como criterio principal
    de análisis (no solo como comparación).
    """
    if precio <= 40:
        return 'Económico\n($24–$40)'
    elif precio <= 100:
        return 'Medio\n($41–$100)'
    else:
        return 'Premium\n($130–$280)'


# Aplica la segmentación sobre el precio más reciente de cada producto.
df_recent['Segmento'] = df_recent['price'].apply(asignar_segmento)


# ── 4. TABLA RESUMEN POR SEGMENTO ─────────────────────────────────────────

# Por cada segmento: cantidad de productos, precio promedio, mínimo y máximo.
resumen_segmento = (
    df_recent
    .groupby('Segmento')['price']
    .agg(cantidad='count', precio_promedio='mean', precio_min='min', precio_max='max')
    .round(2)
    .reset_index()
)

print("\n==============================")
print("Tabla - Precio por Segmento")
print("==============================")
print(resumen_segmento.to_string(index=False))


# ── 5. HALLAZGO AUTOMÁTICO (TEXTO GENERADO) ──────────────────────────────

# Identifica la fila del segmento con mayor cantidad de productos.
segmento_mayor = resumen_segmento.loc[resumen_segmento['cantidad'].idxmax()]

# Construye e imprime una frase de hallazgo lista para citar en el
# documento del TFM, sustituyendo el nombre del segmento con el mayor
# número de productos y su precio promedio.
# chr(10) es el carácter de salto de línea ('\n'); se usa así porque no
# se puede escribir una barra invertida directamente dentro de una
# f-string en versiones de Python anteriores a 3.12. .replace(chr(10), ' ')
# reemplaza el salto de línea del nombre del segmento (usado para que se
# vea bien en el gráfico) por un espacio, para que la frase quede en una
# sola línea legible.
print(f"\nHallazgo: el segmento '{segmento_mayor['Segmento'].replace(chr(10),' ')}' concentra "
      f"la mayor cantidad de productos ({int(segmento_mayor['cantidad'])} de {len(df_recent)}), "
      f"con un precio promedio de ${segmento_mayor['precio_promedio']:.2f}.")

# Guarda la tabla resumen en CSV, para insertarla directamente como
# tabla en el documento del TFM (mencionado explícitamente en el
# comentario original del script).
resumen_segmento.to_csv("tabla_precio_por_segmento.csv", index=False)


# ── 6. VISUALIZACIÓN: BOXPLOT ANOTADO ────────────────────────────────────

# Boxplot de precio por segmento, con el promedio marcado como triángulo.
plt.figure(figsize=(9, 6))
sns.boxplot(
    x='Segmento',
    y='price',
    data=df_recent,
    palette='Set2',
    width=0.5,
    showmeans=True,
    meanprops={"marker":"^", "markersize":10, "markeredgecolor":"black"}
)

plt.title('Rangos de Precio por Segmento\n(Datos más recientes – 20 productos únicos)', fontsize=14, pad=15)
plt.ylabel('Precio actual ($)', fontsize=12)
plt.xlabel('Segmento', fontsize=12)
plt.grid(True, axis='y', alpha=0.3, linestyle='--')

# Anotaciones de texto manuales dentro del gráfico, con ejemplos de
# marcas representativas de cada segmento. Las posiciones (0, 35),
# (1, 75) y (2, 200) están fijadas "a ojo" (coordenadas x = posición del
# segmento en el eje, y = altura en dólares), NO se calculan
# dinámicamente a partir de los datos. Esto significa que si el dataset
# cambia (nuevos productos, precios distintos), estas anotaciones
# podrían quedar mal ubicadas o desactualizadas y requieren ajuste manual.
plt.text(0, 35, 'KVIDIO, BERIBES,\nSoundcore P20i, JBL', ha='center', va='bottom', fontsize=9, color='darkblue')
plt.text(1, 75, 'JBL, Sony,\nPicun, Apple (básicos)', ha='center', va='bottom', fontsize=9, color='darkblue')
plt.text(2, 200, 'Beats, Apple AirPods Pro 3,\nSennheiser', ha='center', va='bottom', fontsize=9, color='darkblue')

plt.tight_layout()

# Guarda la imagen (ruta relativa, en el directorio de trabajo actual),
# lista para insertar en el documento del TFM.
plt.savefig("figura_precio_por_segmento.png", dpi=150, bbox_inches='tight')

plt.show()
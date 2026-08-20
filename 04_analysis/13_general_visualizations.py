"""
13_general_visualizations.py
=============================

PROPÓSITO GENERAL DEL SCRIPT:
Generar un panel de 4 gráficos (en una sola figura, cuadrícula 2x2) que
resume visualmente el análisis exploratorio del proyecto: distribución
de precios, relación precio/rating/ventas, ventas por marca (top 10), y
evolución del precio en el tiempo para dos productos clave.

Este es el script que más se acerca a un "EDA general" propiamente
dicho, cubriendo de una sola vez varios de los puntos descritos en la
sección "Análisis exploratorio de los datos" del documento:
  - "distribución de las ventas por marca"          -> subplot 3
  - "rangos de precios de los productos"            -> subplot 1
  - "relación... entre precio, rating y ventas"      -> subplot 2
  - evolución de precios en el tiempo (aunque el documento la describe
    como "precio promedio por fecha" a nivel agregado, aquí se muestra
    para productos individuales seleccionados) -> subplot 4

Entrada: audifonos_unificado_limpio_enriquecido.csv, ruta relativa.
Salida: ninguna a disco — solo plt.show(), igual que el script 11.
"""

# ── 1. IMPORTS Y CONFIGURACIÓN GLOBAL ────────────────────────────────────
import pandas as pd                # Manipulación de datos
import matplotlib.pyplot as plt    # Generación de gráficos
import seaborn as sns              # Gráficos estadísticos
from pathlib import Path                          # Rutas de archivo portables
 
# Aplica un estilo visual con fondo blanco y líneas de cuadrícula suaves
# a todos los gráficos generados de aquí en adelante en la ejecución.
sns.set_style("whitegrid")

# Fija la resolución (puntos por pulgada) de las figuras a 100 dpi,
# afectando cómo se ven en pantalla / al exportarlas.
plt.rcParams['figure.dpi'] = 100


# ── 2. CARGA Y PREPARACIÓN DE DATOS ──────────────────────────────────────
 
# Ruta base del proyecto: sube dos niveles desde este script.
base_path = Path(__file__).resolve().parent.parent

# Ruta al dataset enriquecido (salida del script 08).
output = base_path / "03_output" / "audifonos_unificado_limpio_enriquecido.csv"

df = pd.read_csv(output)

# Normaliza los nombres de columnas a minúsculas (sin quitar espacios
# con .str.strip() como sí hacía el script 09).
df.columns = df.columns.str.lower()

# Convierte "date" a tipo fecha real; valores no interpretables -> NaT.
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Elimina filas sin fecha o sin ASIN válidos.
df = df.dropna(subset=['date', 'asin'])

# Colapsa el dataset (formato largo) a un registro por producto: la
# última observación (más reciente) de cada ASIN. Mismo patrón que en
# los scripts 09, 10 y 11.
df_recent = df.sort_values('date').groupby('asin').last().reset_index()


# ── 3. VALIDACIÓN DE COLUMNAS REQUERIDAS ─────────────────────────────────

# Columnas indispensables para los gráficos de este script.
required_cols = ['price', 'product_star_rating', 'sales_volume_num']

# Si alguna de ellas no existe en el DataFrame, se crea con valor 0 en
# todas las filas, para evitar un KeyError más adelante. (Nota: esto es
# un parche de compatibilidad — si la columna realmente falta, el
# gráfico correspondiente mostraría datos en 0, no un error explícito
# ni una advertencia de que faltan datos reales.)
for col in required_cols:
    if col not in df_recent.columns:
        df_recent[col] = 0

# Elimina filas donde falte alguno de esos tres valores clave (después
# de la validación anterior, esto en la práctica solo elimina los NaN
# que ya venían en las columnas que sí existían).
df_recent = df_recent.dropna(subset=['price', 'product_star_rating', 'sales_volume_num'])


# ── 4. EXTRACCIÓN DEL NOMBRE DE MARCA ─────────────────────────────────────

# Si no existe "product_byline", se crea con "unknown" (minúsculas, a
# diferencia del "Unknown" con mayúscula usado en el script 11).
if "product_byline" not in df_recent.columns:
    df_recent["product_byline"] = "unknown"

# Limpia el texto para obtener el nombre corto de marca. A diferencia
# del script 11 (que preservaba las mayúsculas originales del texto),
# aquí primero se pasa todo a minúsculas y al final se aplica
# .str.title() para capitalizar cada palabra de forma consistente
# (ej. "sony" -> "Sony", "jbl audio" -> "Jbl Audio").
df_recent['brand_short'] = (
    df_recent['product_byline']
    .str.lower()
    .str.replace('visit the ', '', regex=False)
    .str.replace(' store', '', regex=False)
    .str.strip()
    .str.title()
)

print(f"→ Usando {len(df_recent)} productos únicos (última observación)\n")


# ── 5. FIGURA CON 4 SUBGRÁFICOS (CUADRÍCULA 2x2) ─────────────────────────

fig = plt.figure(figsize=(14, 12))

# --- Subplot 1 (arriba-izquierda): Histograma de precios ---
ax1 = fig.add_subplot(2, 2, 1)
sns.histplot(df_recent['price'], bins=20, kde=True, color='cornflowerblue', ax=ax1)
ax1.set_title('Histograma de Precios\n(última observación por producto)')
ax1.set_xlabel('Precio actual ($)')
ax1.set_ylabel('Cantidad de productos')

# --- Subplot 2 (arriba-derecha): Precio vs. rating, tamaño = ventas ---
ax2 = fig.add_subplot(2, 2, 2)
sns.scatterplot(
    data=df_recent,
    x='product_star_rating',
    y='price',
    size='sales_volume_num',            # El TAMAÑO de cada punto representa el volumen de ventas
    sizes=(60, 1200),                    # Rango de tamaños de punto (mínimo, máximo) en píxeles
    hue='is_prime' if 'is_prime' in df_recent.columns else None,  # Color según si es Prime (si existe la columna)
    palette='coolwarm',
    alpha=0.8,                           # Transparencia para ver puntos superpuestos
    legend='brief',
    ax=ax2
)

ax2.set_title('Precio vs Rating • Tamaño = Ventas estimadas')
ax2.set_xlabel('Calificación promedio')
ax2.set_ylabel('Precio ($)')
# Línea vertical de referencia en rating=4.4, probablemente para marcar
# un umbral de "buena calificación" y comparar visualmente los productos
# a cada lado de esa línea.
ax2.axvline(4.4, color='gray', ls='--', alpha=0.6)

# --- Cálculo previo al subplot 3: ventas totales por marca (top 10) ---
# Suma el volumen de ventas de todos los productos de cada marca,
# ordena de mayor a menor, y se queda con las 10 marcas de mayor venta.
brand_sales = df_recent.groupby('brand_short')['sales_volume_num'].sum().sort_values(ascending=False).head(10)

# --- Subplot 3 (abajo-izquierda): Ventas por marca (top 10) ---
ax3 = fig.add_subplot(2, 2, 3)
sns.barplot(x=brand_sales.values, y=brand_sales.index, palette='viridis', ax=ax3)
ax3.set_title('Ventas estimadas por marca\n(última observación)')
ax3.set_xlabel('Ventas estimadas mensuales')
ax3.set_ylabel('Marca')

# Agrega el valor numérico (con comas de miles) al final de cada barra.
for i, v in enumerate(brand_sales.values):
    ax3.text(v + 200, i, f'{int(v):,}', va='center', fontsize=9)

# --- Subplot 4 (abajo-derecha): Evolución del precio de productos clave ---
ax4 = fig.add_subplot(2, 2, 4)

# Diccionario de ASINs seleccionados manualmente, con su nombre legible
# como etiqueta. A diferencia del resto del script (que trabaja con
# df_recent, un solo registro por producto), este subplot usa el
# DataFrame "df" original (con TODO el historial de precios), porque
# necesita ver la evolución temporal completa, no solo el último valor.
key_asins = {
    'Apple AirPods Pro 3': 'B0FQFB8FMG',
    'Soundcore P20i': 'B0BTYCRJSS',
}

for label, asin in key_asins.items():
    # Filtra el historial completo de precios para este ASIN específico.
    df_asin = df[df['asin'] == asin].copy()
    df_asin = df_asin.sort_values('date')
    # Solo grafica si hay datos para ese ASIN (evita error si el ASIN
    # no aparece en el dataset, por ejemplo si cambia el catálogo).
    if not df_asin.empty:
        ax4.plot(df_asin['date'], df_asin['price'], marker='o', linewidth=2, label=label)

ax4.set_title('Evolución del precio – Productos clave')
ax4.set_xlabel('Fecha')
ax4.set_ylabel('Precio ($)')
ax4.tick_params(axis='x', rotation=45)   # Rota las etiquetas de fecha para que no se superpongan
ax4.legend()


# ── 6. TÍTULO GENERAL Y RENDERIZADO ──────────────────────────────────────

# Título general para toda la figura (por encima de los 4 subplots).
fig.suptitle('Análisis Exploratorio – Audífonos Amazon\n(Datos más recientes + series temporales selectas)',
             fontsize=15, y=1.02)

# Ajusta el espaciado entre subplots; rect=[0,0,1,0.96] deja un margen
# superior para que el título general (suptitle) no se superponga con
# los subplots.
plt.tight_layout(rect=[0, 0, 1, 0.96])

# Muestra la figura completa. Al igual que el script 11, no se guarda
# con plt.savefig() antes de mostrarla, por lo que el panel no queda
# persistido como archivo de imagen.
plt.show()

print("Gráficas generadas.")
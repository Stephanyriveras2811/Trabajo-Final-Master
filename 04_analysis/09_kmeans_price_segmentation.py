"""
09_exploratory_data_analysis.py
================================
 
PROPÓSITO GENERAL DEL SCRIPT:
A pesar del nombre del archivo, este script NO es el EDA general
(distribución de ventas por marca, rangos de precio, evolución temporal,
etc. — descrito en la sección "Análisis exploratorio de los datos" del
documento). Su contenido corresponde específicamente a la sección
"Segmentación de productos mediante K-Means": aplica clustering no
supervisado sobre el registro más reciente de cada producto, selecciona
el número óptimo de clusters (k), entrena K-Means con k=3, compara el
resultado contra la segmentación manual por rangos de precio, y genera
las visualizaciones y tablas de esa sección (boxplot, scatter, tabla de
resumen por segmento).
 
Entrada: audifonos_unificado_limpio_enriquecido.csv (salida de 08).
Salidas:
  - kmeans_seleccion_k.png       (método del codo + silhouette)
  - tabla_precio_por_segmento_kmeans.csv
  - figura_precio_por_segmento_kmeans.png (boxplot)
  - kmeans_scatter_clusters.png  (scatter precio vs. rating)
"""
 
# ── 1. IMPORTS ────────────────────────────────────────────────────────────
import pandas as pd                              # Manipulación de datos
import numpy as np                                # Operaciones numéricas (log1p)
import matplotlib.pyplot as plt                   # Generación de gráficos
import seaborn as sns                             # Gráficos estadísticos (boxplot, scatterplot)
from sklearn.preprocessing import StandardScaler  # Estandarización de variables antes del clustering
from sklearn.cluster import KMeans                # Algoritmo de clustering K-Means
from sklearn.metrics import silhouette_score      # Métrica para evaluar la calidad de los clusters
from pathlib import Path                          # Rutas de archivo portables
 
 
# ── 2. CARGA Y PREPARACIÓN DE DATOS ──────────────────────────────────────
 
# Ruta base del proyecto: sube dos niveles desde este script.
base_path = Path(__file__).resolve().parent.parent

# Ruta al dataset enriquecido (salida del script 08).
output = base_path / "03_output" / "audifonos_unificado_limpio_enriquecido.csv"

df = pd.read_csv(output)
 
# Normaliza los nombres de columnas a minúsculas y sin espacios extra,
# igual que en "06_merge_datasets.py", para asegurar consistencia
# independientemente de cómo hayan quedado escritas en pasos anteriores.
df.columns = df.columns.str.strip().str.lower()
 
# Convierte la columna "date" a tipo fecha real; cualquier valor que no
# se pueda interpretar como fecha queda como NaT (errors="coerce").
df['date'] = pd.to_datetime(df['date'], errors='coerce')
 
# Como el dataset está en formato "largo" (una fila por punto de precio
# en el tiempo), para la segmentación se necesita UN solo registro por
# producto. Se ordena por fecha y, dentro de cada grupo de "asin", se
# conserva la última fila (el registro más reciente de cada producto).
df_recent = df.sort_values('date').groupby('asin').last().reset_index()


def asignar_segmento(precio):
    """
    Segmentación MANUAL por rangos fijos de precio, usada como línea
    base para comparar contra los resultados de K-Means. Corresponde a
    la clasificación descrita en la sección 1.5.7 del documento del
    proyecto.
    """
    if precio <= 40:
        return 'Económico\n($24–$40)'
    elif precio <= 100:
        return 'Medio\n($41–$100)'
    else:
        return 'Premium\n($130–$280)'
 
 
# Aplica la segmentación manual sobre el precio más reciente de cada producto.
df_recent['Segmento'] = df_recent['price'].apply(asignar_segmento)
 
 
# ── 3. SELECCIÓN DE VARIABLES PARA EL CLUSTERING ─────────────────────────
 
# Variables "base": se usan en su escala original (sin transformar).
features_base = ['price', 'product_star_rating', 'discount_pct', 'rating_balance']
 
# Variables con distribución muy sesgada (pocos productos con valores muy
# altos frente a la mayoría con valores bajos): se transformarán con
# logaritmo (log1p) para reducir el efecto de esos valores extremos.
features_log = ['product_num_ratings', 'sales_volume_num']
 
# Filtra ambas listas dejando solo las columnas que realmente existen en
# df_recent, por si alguna no se generó en pasos anteriores del pipeline.
features_base = [c for c in features_base if c in df_recent.columns]
features_log = [c for c in features_log if c in df_recent.columns]
print("Variables base:", features_base)
print("Variables con log1p:", features_log)
 
# Construye la matriz de variables (X) a partir de las variables base.
X = df_recent[features_base].copy()
 
# Rellena valores nulos con la mediana de cada columna numérica —más
# robusta frente a outliers que la media, adecuada antes de un clustering
# sensible a la escala como K-Means.
X = X.fillna(X.median(numeric_only=True))
 
# Agrega las variables sesgadas transformadas con log1p (log(1 + x), que
# evita problemas con valores de 0, a diferencia de un logaritmo simple).
# Los nulos se rellenan con 0 antes de aplicar la transformación.
for col in features_log:
    X[f'{col}_log'] = np.log1p(df_recent[col].fillna(0))
 
# Lista final de nombres de columnas que componen la matriz de features.
features = list(X.columns)
 
 
# ── 4. ESCALADO DE VARIABLES ─────────────────────────────────────────────
 
# K-Means calcula distancias euclidianas entre puntos, por lo que es
# sensible a la escala de cada variable (una variable en cientos
# dominaría sobre una en decimales). StandardScaler estandariza cada
# columna a media 0 y desviación estándar 1.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
 
 
# ── 5. SELECCIÓN DEL NÚMERO ÓPTIMO DE CLUSTERS (k) ───────────────────────
 
inercias, siluetas = [], []   # Acumulan las métricas para cada valor de k probado
rango_k = range(2, 8)         # Se evalúan valores de k entre 2 y 7
 
for k in rango_k:
    # Entrena K-Means con k clusters. n_init=10 corre el algoritmo 10
    # veces con distintas inicializaciones y se queda con la mejor,
    # para reducir el riesgo de caer en un óptimo local malo.
    # random_state=42 fija la semilla para que el resultado sea reproducible.
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
 
    # Inercia: suma de las distancias al cuadrado de cada punto a su
    # centroide. Baja al aumentar k, pero cada vez menos (de ahí el
    # "método del codo": se busca el punto donde deja de bajar mucho).
    inercias.append(km.inertia_)
 
    # Silhouette score: mide qué tan bien separados y cohesionados están
    # los clusters (rango -1 a 1; más alto es mejor).
    siluetas.append(silhouette_score(X_scaled, labels))
 
# Grafica ambas métricas lado a lado para decidir visualmente el k óptimo.
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(list(rango_k), inercias, marker='o')
axes[0].set_title('Método del codo')
axes[0].set_xlabel('k'); axes[0].set_ylabel('Inercia')
 
axes[1].plot(list(rango_k), siluetas, marker='o', color='darkorange')
axes[1].set_title('Coeficiente de silhouette')
axes[1].set_xlabel('k'); axes[1].set_ylabel('Silhouette')
 
plt.tight_layout()
# Guarda la figura en disco (en el directorio de trabajo actual, no en
# una ruta absoluta construida con Path como el resto de archivos del
# pipeline).
plt.savefig("kmeans_seleccion_k.png", dpi=150, bbox_inches='tight')
plt.show()
 
 
# ── 6. AJUSTE FINAL DE K-MEANS (k=3) ─────────────────────────────────────
 
# Se fija k=3 directamente (no se elige automáticamente en base a las
# métricas anteriores), para poder comparar 1 a 1 con la segmentación
# manual de tres niveles (Económico/Medio/Premium) definida arriba.
k_final = 3
kmeans = KMeans(n_clusters=k_final, random_state=42, n_init=10)
df_recent['cluster'] = kmeans.fit_predict(X_scaled)
 
# Los números de cluster que asigna K-Means (0, 1, 2) son arbitrarios y
# no siguen necesariamente un orden de precio. Este bloque los reordena:
# calcula el precio promedio de cada cluster, los ordena de menor a
# mayor, y reasigna los IDs (0 = más barato, 2 = más caro) para que el
# número de cluster sea interpretable de forma consistente con
# "Económico/Medio/Premium".
orden = df_recent.groupby('cluster')['price'].mean().sort_values().index
mapa_orden = {cluster_id: nuevo_id for nuevo_id, cluster_id in enumerate(orden)}
df_recent['cluster'] = df_recent['cluster'].map(mapa_orden)
 
# Traduce los IDs numéricos ya reordenados (0, 1, 2) a etiquetas legibles.
nombres = {0: 'Económico (K-means)', 1: 'Medio (K-means)', 2: 'Premium (K-means)'}
df_recent['Segmento_kmeans'] = df_recent['cluster'].map(nombres)
 
 
# ── 7. RESUMEN Y COMPARACIÓN CON LA SEGMENTACIÓN MANUAL ──────────────────
 
# Tabla resumen: por cada segmento de K-Means, cantidad de productos,
# precio promedio, mínimo y máximo.
resumen_kmeans = (
    df_recent
    .groupby('Segmento_kmeans')['price']
    .agg(cantidad='count', precio_promedio='mean', precio_min='min', precio_max='max')
    .round(2)
    .reset_index()
)
print("\n==============================")
print("Tabla - Precio por Segmento (K-means)")
print("==============================")
print(resumen_kmeans.to_string(index=False))
 
# Tabla de contingencia (cruce) entre la segmentación manual y la de
# K-Means, para ver cuánto coinciden ambos criterios de clasificación.
# .str.replace('\n', ' ') quita los saltos de línea que tienen las
# etiquetas de "Segmento" (usados solo para que se vean bien en los
# gráficos), para que la tabla impresa en consola sea más legible.
print("\nComparación segmentación manual vs K-means:")
print(pd.crosstab(df_recent['Segmento'].str.replace('\n', ' '), df_recent['Segmento_kmeans']))
 
# Exporta la tabla resumen a CSV (en el directorio de trabajo actual).
resumen_kmeans.to_csv("tabla_precio_por_segmento_kmeans.csv", index=False)
 
 
# ── 8. VISUALIZACIÓN ──────────────────────────────────────────────────────
 
# Boxplot: distribución de precios por segmento de K-Means, con el
# promedio marcado como un triángulo (meanprops).
plt.figure(figsize=(9, 6))
sns.boxplot(
    x='Segmento_kmeans',
    y='price',
    data=df_recent,
    palette='Set2',
    width=0.5,
    showmeans=True,
    meanprops={"marker": "^", "markersize": 10, "markeredgecolor": "black"}
)
plt.title('Segmentación por K-means\n(Datos más recientes)', fontsize=14, pad=15)
plt.ylabel('Precio actual ($)', fontsize=12)
plt.xlabel('Segmento (K-means)', fontsize=12)
plt.grid(True, axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig("figura_precio_por_segmento_kmeans.png", dpi=150, bbox_inches='tight')
plt.show()
 
# Scatter plot: precio vs. rating, coloreado por segmento de K-Means.
# Se usan las columnas ORIGINALES (no las transformadas con log1p), para
# que el gráfico sea directamente interpretable en sus unidades reales.
# Se genera solo si la columna de rating existe en el dataset.
if 'product_star_rating' in df_recent.columns:
    plt.figure(figsize=(8, 6))
    sns.scatterplot(
        data=df_recent, x='price', y='product_star_rating',
        hue='Segmento_kmeans', palette='Set2', s=80
    )
    plt.title('Clusters de K-means: precio vs. rating')
    plt.tight_layout()
    plt.savefig("kmeans_scatter_clusters.png", dpi=150, bbox_inches='tight')
    plt.show()
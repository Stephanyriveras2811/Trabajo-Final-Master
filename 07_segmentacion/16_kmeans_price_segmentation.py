import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from pathlib import Path

# =========================================================
# 1. Cargar y preparar datos (igual que tu script original)
# =========================================================
base_path = Path(__file__).resolve().parent.parent

output = base_path / "03_output" / "audifonos_unificado_limpio_enriquecido.csv"

df = pd.read_csv(output)

df.columns = df.columns.str.strip().str.lower()
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df_recent = df.sort_values('date').groupby('asin').last().reset_index()

def asignar_segmento(precio):
    if precio <= 40:
        return 'Económico\n($24–$40)'
    elif precio <= 100:
        return 'Medio\n($41–$100)'
    else:
        return 'Premium\n($130–$280)'

df_recent['Segmento'] = df_recent['price'].apply(asignar_segmento)

# =========================================================
# 2. Seleccionar variables para el clustering
# =========================================================
# Variables base (sin transformar)
features_base = ['price', 'product_star_rating', 'discount_pct', 'rating_balance']

# Variables muy sesgadas (pocos productos con valores enormes) -> van con log1p
features_log = ['product_num_ratings', 'sales_volume_num']


features_base = [c for c in features_base if c in df_recent.columns]
features_log = [c for c in features_log if c in df_recent.columns]
print("Variables base:", features_base)
print("Variables con log1p:", features_log)

X = df_recent[features_base].copy()
X = X.fillna(X.median(numeric_only=True))

for col in features_log:
    X[f'{col}_log'] = np.log1p(df_recent[col].fillna(0))

features = list(X.columns)

# =========================================================
# 3. Escalar (K-means es sensible a la escala de las variables)
# =========================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================================================
# 4. Elegir k: método del codo + silhouette
# =========================================================
inercias, siluetas = [], []
rango_k = range(2, 8)

for k in rango_k:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    inercias.append(km.inertia_)
    siluetas.append(silhouette_score(X_scaled, labels))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(list(rango_k), inercias, marker='o')
axes[0].set_title('Método del codo')
axes[0].set_xlabel('k'); axes[0].set_ylabel('Inercia')

axes[1].plot(list(rango_k), siluetas, marker='o', color='darkorange')
axes[1].set_title('Coeficiente de silhouette')
axes[1].set_xlabel('k'); axes[1].set_ylabel('Silhouette')

plt.tight_layout()
plt.savefig("kmeans_seleccion_k.png", dpi=150, bbox_inches='tight')
plt.show()

# =========================================================
# 5. Ajustar K-means con el k elegido
#    (usa k=3 para comparar directo con tu regla manual,
#     o cambia por el k que te dé mejor silhouette arriba)
# =========================================================
k_final = 3
kmeans = KMeans(n_clusters=k_final, random_state=42, n_init=10)
df_recent['cluster'] = kmeans.fit_predict(X_scaled)

# Reordenar clusters de menor a mayor precio promedio
# para que el número de cluster sea interpretable
orden = df_recent.groupby('cluster')['price'].mean().sort_values().index
mapa_orden = {cluster_id: nuevo_id for nuevo_id, cluster_id in enumerate(orden)}
df_recent['cluster'] = df_recent['cluster'].map(mapa_orden)

nombres = {0: 'Económico (K-means)', 1: 'Medio (K-means)', 2: 'Premium (K-means)'}
df_recent['Segmento_kmeans'] = df_recent['cluster'].map(nombres)

# =========================================================
# 6. Resumen y comparación con tu segmentación manual
# =========================================================
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

print("\nComparación segmentación manual vs K-means:")
print(pd.crosstab(df_recent['Segmento'].str.replace('\n', ' '), df_recent['Segmento_kmeans']))

resumen_kmeans.to_csv("tabla_precio_por_segmento_kmeans.csv", index=False)

# =========================================================
# 7. Visualización
# =========================================================
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

# Scatter price vs rating coloreado por cluster (columnas originales,
# no las transformadas con log, para que sea interpretable a simple vista)
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
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# =========================================================
# 1. CARGAR LOS DATOS
# =========================================================

# Si ejecutas el código desde Jupyter Notebook:
archivo = Path(__file__).resolve().parent.parent / "03_output" / "audifonos_unificado_limpio_enriquecido.csv"

# Si el archivo se encuentra en la carpeta 03_output:
# archivo = Path("../03_output/audifonos_unificado_limpio_enriquecido.csv")

df = pd.read_csv(archivo, low_memory=False)

# Estandarizar nombres de columnas
df.columns = df.columns.str.strip().str.lower()

# Usar product_price si existe; de lo contrario, usar price
price_col = "product_price" if "product_price" in df.columns else "price"

# Convertir la fecha
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Eliminar registros sin fecha
df = df.dropna(subset=["date"])

# Conservar el registro completo más reciente de cada producto
indices_recientes = df.groupby("asin")["date"].idxmax()
df_recent = df.loc[indices_recientes].copy().reset_index(drop=True)

print(f"Productos únicos analizados: {len(df_recent)}")
print(f"Columna de precio utilizada: {price_col}")


# =========================================================
# 2. SELECCIONAR VARIABLES PARA K-MEANS
# =========================================================

# Variables sin transformación logarítmica
features_base = [
    price_col,
    "product_star_rating",
    "discount_pct",
    "rating_balance"
]

# Variables que pueden presentar valores muy altos
features_log = [
    "product_num_ratings",
    "sales_volume_num"
]

# Mantener solamente las columnas disponibles
features_base = [
    columna for columna in features_base
    if columna in df_recent.columns
]

features_log = [
    columna for columna in features_log
    if columna in df_recent.columns
]

print("\nVariables base:", features_base)
print("Variables transformadas con log1p:", features_log)

# Crear matriz de características
X = df_recent[features_base].copy()

# Convertir a numérico
for columna in features_base:
    X[columna] = pd.to_numeric(X[columna], errors="coerce")

# Sustituir valores faltantes por la mediana
X = X.fillna(X.median())

# Aplicar transformación logarítmica
for columna in features_log:
    valores = pd.to_numeric(
        df_recent[columna],
        errors="coerce"
    ).fillna(0)

    # Evita errores si existen valores negativos
    valores = valores.clip(lower=0)

    X[f"{columna}_log"] = np.log1p(valores)

features = X.columns.tolist()

print("Variables finales para K-Means:", features)


# =========================================================
# 3. ESCALAR LAS VARIABLES
# =========================================================

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


# =========================================================
# 4. EVALUAR EL NÚMERO DE CLUSTERS
# =========================================================

inercias = []
siluetas = []

# Evita probar más clusters que productos disponibles
max_k = min(7, len(df_recent) - 1)
rango_k = range(2, max_k + 1)

for k in rango_k:
    modelo = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    etiquetas = modelo.fit_predict(X_scaled)

    inercias.append(modelo.inertia_)
    siluetas.append(
        silhouette_score(X_scaled, etiquetas)
    )

# Graficar resultados
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(
    list(rango_k),
    inercias,
    marker="o"
)
axes[0].set_title("Método del codo")
axes[0].set_xlabel("Cantidad de clusters (k)")
axes[0].set_ylabel("Inercia")
axes[0].grid(alpha=0.3)

axes[1].plot(
    list(rango_k),
    siluetas,
    marker="o",
    color="darkorange"
)
axes[1].set_title("Coeficiente de silhouette")
axes[1].set_xlabel("Cantidad de clusters (k)")
axes[1].set_ylabel("Silhouette")
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(
    "kmeans_seleccion_k.png",
    dpi=150,
    bbox_inches="tight"
)
plt.show()

# Mostrar resultados numéricos
evaluacion_k = pd.DataFrame({
    "k": list(rango_k),
    "inercia": inercias,
    "silhouette": siluetas
})

print("\nEvaluación de clusters:")
print(evaluacion_k.round(4).to_string(index=False))

# Seleccionar automáticamente el mejor k según silhouette
k_final = evaluacion_k.loc[
    evaluacion_k["silhouette"].idxmax(),
    "k"
]

k_final = int(k_final)

print(f"\nMejor número de clusters según silhouette: {k_final}")


# =========================================================
# 5. ENTRENAR EL MODELO FINAL
# =========================================================

kmeans = KMeans(
    n_clusters=k_final,
    random_state=42,
    n_init=10
)

df_recent["cluster_original"] = kmeans.fit_predict(X_scaled)


# =========================================================
# 6. ORDENAR LOS CLUSTERS POR PRECIO PROMEDIO
# =========================================================

orden_clusters = (
    df_recent
    .groupby("cluster_original")[price_col]
    .mean()
    .sort_values()
    .index
)

mapa_orden = {
    cluster_original: nuevo_cluster
    for nuevo_cluster, cluster_original
    in enumerate(orden_clusters, start=1)
}

df_recent["cluster"] = (
    df_recent["cluster_original"]
    .map(mapa_orden)
)

df_recent["segmento_kmeans"] = (
    "Cluster " + df_recent["cluster"].astype(str)
)


# =========================================================
# 7. CREAR PERFIL DE LOS CLUSTERS
# =========================================================

columnas_resumen = [
    price_col,
    "product_star_rating",
    "discount_pct",
    "rating_balance",
    "product_num_ratings",
    "sales_volume_num"
]

columnas_resumen = [
    columna for columna in columnas_resumen
    if columna in df_recent.columns
]

resumen_clusters = (
    df_recent
    .groupby("segmento_kmeans")[columnas_resumen]
    .mean()
    .round(2)
)

resumen_clusters.insert(
    0,
    "cantidad_productos",
    df_recent.groupby("segmento_kmeans").size()
)

print("\nPerfil promedio de los clusters:")
print(resumen_clusters.to_string())

resumen_clusters.to_csv(
    "perfil_clusters_kmeans.csv"
)


# =========================================================
# 8. VISUALIZACIÓN DE PRECIOS
# =========================================================

plt.figure(figsize=(9, 6))

sns.boxplot(
    data=df_recent,
    x="segmento_kmeans",
    y=price_col,
    hue="segmento_kmeans",
    palette="Set2",
    width=0.5,
    showmeans=True,
    meanprops={
        "marker": "^",
        "markersize": 10,
        "markeredgecolor": "black"
    },
    legend=False
)

plt.title(
    "Distribución de precios por cluster\n"
    "(Datos más recientes por producto)",
    fontsize=14,
    pad=15
)
plt.xlabel("Cluster de K-Means", fontsize=12)
plt.ylabel("Precio actual ($)", fontsize=12)
plt.grid(
    True,
    axis="y",
    alpha=0.3,
    linestyle="--"
)

plt.tight_layout()
plt.savefig(
    "precio_por_cluster_kmeans.png",
    dpi=150,
    bbox_inches="tight"
)
plt.show()


# =========================================================
# 9. PRECIO VS. RATING
# =========================================================

if "product_star_rating" in df_recent.columns:
    plt.figure(figsize=(9, 6))

    sns.scatterplot(
        data=df_recent,
        x=price_col,
        y="product_star_rating",
        hue="segmento_kmeans",
        palette="Set2",
        s=90
    )

    plt.title("Clusters de K-Means: precio frente a rating")
    plt.xlabel("Precio actual ($)")
    plt.ylabel("Calificación del producto")
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        "kmeans_precio_vs_rating.png",
        dpi=150,
        bbox_inches="tight"
    )
    plt.show()


# =========================================================
# 10. GUARDAR RESULTADOS
# =========================================================

df_recent.to_csv(
    "productos_con_clusters_kmeans.csv",
    index=False
)

print("\nAnálisis completado correctamente.")
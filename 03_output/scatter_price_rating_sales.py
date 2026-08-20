import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Cargar datos
df = pd.read_csv("audifonos_unificado_limpio_enriquecido.csv",low_memory=False)

# 2. Limpieza básica
df.columns = df.columns.str.strip().str.lower()
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# 3. Usar solo el registro más reciente por producto (ASIN)
df_latest = (
    df.sort_values('date')
      .groupby('asin', as_index=False)
      .last()
)

# =========================
# RESULTADO ESCRITO
# =========================
correlaciones = df_latest[['price', 'product_star_rating', 'sales_volume_num']].corr().round(3)

print("\n==============================")
print("Matriz de correlación - Precio, Rating, Ventas")
print("==============================")
print(correlaciones)

corr_precio_rating = correlaciones.loc['price', 'product_star_rating']
corr_precio_ventas = correlaciones.loc['price', 'sales_volume_num']

if abs(corr_precio_rating) < 0.2:
    fuerza = "prácticamente nula"
elif abs(corr_precio_rating) < 0.5:
    fuerza = "débil"
else:
    fuerza = "considerable"

print(f"\nHallazgo: la correlación entre precio y rating es {corr_precio_rating:.3f} "
      f"({fuerza}), lo que sugiere que un precio más alto "
      f"{'sí' if abs(corr_precio_rating) >= 0.5 else 'no necesariamente'} "
      f"está asociado a mejores calificaciones.")
print(f"La correlación entre precio y ventas estimadas es {corr_precio_ventas:.3f}.")

# Guardar tabla para insertar en el documento del TFM
correlaciones.to_csv("tabla_correlacion_precio_rating_ventas.csv")

# 4. Gráfico de dispersión
plt.figure(figsize=(9, 6))

sns.scatterplot(
    data=df_latest,
    x='price',
    y='product_star_rating',
    size='sales_volume_num',     # ventas
    sizes=(40, 900),
    alpha=0.7,
    color='steelblue'
)

plt.title('Precio vs Rating (Tamaño = Ventas)', fontsize=14)
plt.xlabel('Precio ($)')
plt.ylabel('Rating promedio')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()

# Guardar la imagen para insertar en el documento del TFM
plt.savefig("figura_precio_vs_rating.png", dpi=150, bbox_inches='tight')

plt.show()
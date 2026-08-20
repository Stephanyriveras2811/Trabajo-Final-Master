import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Cargar datos
df = pd.read_csv("audifonos_unificado_limpio_enriquecido.csv", low_memory=False)

# Limpieza básica
df.columns = df.columns.str.strip().str.lower()
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Usar el registro más reciente por producto
df_latest = (
    df.sort_values('date')
      .groupby('asin', as_index=False)
      .last()
)

# Ventas totales por marca
ventas_marca = (
    df_latest
    .groupby('product_byline')['sales_volume_num']
    .sum()
    .reset_index()
    .sort_values('sales_volume_num', ascending=False)
)

# Tomar las 10 marcas más vendidas
top_marcas = ventas_marca.head(10)

# =========================
# RESULTADO ESCRITO (nuevo)
# =========================
print("\n==============================")
print("Tabla - Ventas por Marca (Top 10)")
print("==============================")
print(top_marcas.to_string(index=False))

total_ventas = ventas_marca['sales_volume_num'].sum()
top_marcas['participacion_%'] = (top_marcas['sales_volume_num'] / total_ventas * 100).round(2)
print("\nParticipación de mercado (%):")
print(top_marcas[['product_byline', 'participacion_%']].to_string(index=False))

marca_lider = top_marcas.iloc[0]
print(f"\nHallazgo: '{marca_lider['product_byline']}' lidera con "
      f"{int(marca_lider['sales_volume_num']):,} unidades vendidas estimadas, "
      f"equivalente al {marca_lider['participacion_%']}% del total analizado.")

# Guardar tabla para insertar en el documento del TFM
top_marcas.to_csv("tabla_ventas_por_marca.csv", index=False)

# Gráfico
plt.figure(figsize=(10, 6))
sns.barplot(
    data=top_marcas,
    x='sales_volume_num',
    y='product_byline',
    palette='Set2'
)

plt.title('Ventas por Marca (Top 10)', fontsize=14)
plt.xlabel('Ventas estimadas')
plt.ylabel('Marca')
plt.grid(True, axis='x', linestyle='--', alpha=0.3)
plt.tight_layout()

# Guardar la imagen para insertar en el documento del TFM
plt.savefig("figura_ventas_por_marca.png", dpi=150, bbox_inches='tight')

plt.show()
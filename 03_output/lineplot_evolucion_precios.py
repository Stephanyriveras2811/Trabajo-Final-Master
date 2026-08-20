import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Cargar datos
df = pd.read_csv("audifonos_unificado_limpio_enriquecido.csv",low_memory=False)

# Limpieza básica
df.columns = df.columns.str.strip().str.lower()
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Eliminar fechas o precios inválidos
df = df.dropna(subset=['date', 'price'])

# Precio promedio por fecha
price_trend = (
    df.groupby('date')['price']
      .mean()
      .reset_index()
      .sort_values('date')
)

# =========================
# RESULTADO ESCRITO (nuevo)
# =========================
print("\n==============================")
print("Tabla - Evolución del Precio Promedio")
print("==============================")
print(price_trend.to_string(index=False))

precio_inicial = price_trend.iloc[0]['price']
precio_final = price_trend.iloc[-1]['price']
fecha_inicial = price_trend.iloc[0]['date'].strftime('%d/%m/%Y')
fecha_final = price_trend.iloc[-1]['date'].strftime('%d/%m/%Y')
variacion_pct = ((precio_final - precio_inicial) / precio_inicial) * 100

fila_max = price_trend.loc[price_trend['price'].idxmax()]
fila_min = price_trend.loc[price_trend['price'].idxmin()]

print(f"\nHallazgo: el precio promedio pasó de ${precio_inicial:.2f} ({fecha_inicial}) "
      f"a ${precio_final:.2f} ({fecha_final}), una variación de "
      f"{variacion_pct:+.2f}% en el periodo analizado.")
print(f"Precio máximo: ${fila_max['price']:.2f} el {fila_max['date'].strftime('%d/%m/%Y')}")
print(f"Precio mínimo: ${fila_min['price']:.2f} el {fila_min['date'].strftime('%d/%m/%Y')}")

# Guardar tabla para insertar en el documento del TFM
price_trend.to_csv("tabla_evolucion_precio.csv", index=False)

# Gráfico de línea
plt.figure(figsize=(10, 6))
sns.lineplot(
    data=price_trend,
    x='date',
    y='price',
    marker='o'
)

plt.title('Evolución del Precio Promedio de Audífonos', fontsize=14)
plt.xlabel('Fecha')
plt.ylabel('Precio promedio ($)')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()

# Guardar la imagen para insertar en el documento del TFM
plt.savefig("figura_evolucion_precio.png", dpi=150, bbox_inches='tight')

plt.show()
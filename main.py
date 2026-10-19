
import pandas as pd
import numpy as np

# ==========================================
# PRACTICA 2: ESQUEMA ESTRELLA
# ==========================================

# 1. SIMULACION DE DATOS OPERACIONALES (OLTP)
np.random.seed(101)
n = 500

df_operativo = pd.DataFrame({
    "id_transaccion": range(1000, 1000 + n),
    "fecha_hora": pd.date_range(
        start="2026-01-01", periods=n, freq="h"
    ),
    "cliente_nombre": np.random.choice(
        ["Juan Pérez", "María Gómez", "Carlos Ruiz"], n
    ),
    "cliente_ciudad": np.random.choice(
        ["Puebla", "CDMX", "Guadalajara"], n
    ),
    "producto_nombre": np.random.choice(
        ["Laptop Dell", "Mouse Logi", "Monitor LG"], n
    ),
    "categoria_prod": np.random.choice(
        ["Cómputo", "Accesorios", "Pantallas"], n
    ),
    "precio_unitario": np.random.choice(
        [15000.0, 350.0, 4500.0], n
    ),
    "cantidad": np.random.randint(1, 5, n)
})

print("\n=== DATOS OPERATIVOS (OLTP) ===")
print(df_operativo.head())
print(f"Total de transacciones: {len(df_operativo)}")


# 2. DIMENSION CLIENTE
dim_cliente = (
    df_operativo[["cliente_nombre", "cliente_ciudad"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

dim_cliente["id_cliente_sk"] = dim_cliente.index + 1

dim_cliente = dim_cliente[
    ["id_cliente_sk", "cliente_nombre", "cliente_ciudad"]
]

print("\n=== DIM_CLIENTE ===")
print(dim_cliente.head())
print(f"Total de registros: {len(dim_cliente)}")


# 3. DIMENSION PRODUCTO
dim_producto = (
    df_operativo[
        ["producto_nombre", "categoria_prod", "precio_unitario"]
    ]
    .drop_duplicates()
    .reset_index(drop=True)
)

dim_producto["id_producto_sk"] = dim_producto.index + 1

dim_producto = dim_producto[
    [
        "id_producto_sk",
        "producto_nombre",
        "categoria_prod",
        "precio_unitario"
    ]
]

print("\n=== DIM_PRODUCTO ===")
print(dim_producto.head())
print(f"Total de registros: {len(dim_producto)}")


# 4. DIMENSION TIEMPO
fechas = (
    df_operativo["fecha_hora"]
    .dt.normalize()
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)
)

dim_tiempo = pd.DataFrame({
    "fecha_completa": fechas
})

dim_tiempo["id_tiempo_sk"] = (
    dim_tiempo["fecha_completa"]
    .dt.strftime("%Y%m%d")
    .astype(int)
)

dim_tiempo["anio"] = dim_tiempo["fecha_completa"].dt.year
dim_tiempo["mes"] = dim_tiempo["fecha_completa"].dt.month
dim_tiempo["dia"] = dim_tiempo["fecha_completa"].dt.day

# ATRIBUTOS ADICIONALES
dias = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

dim_tiempo["dia_semana"] = (
    dim_tiempo["fecha_completa"].dt.dayofweek.map(dias)
)

dim_tiempo["es_fin_semana"] = (
    dim_tiempo["fecha_completa"].dt.dayofweek >= 5
)

print("\n=== DIM_TIEMPO ===")
print(dim_tiempo.head(10))
print(f"Total de registros: {len(dim_tiempo)}")


# 5. TABLA DE HECHOS FACT_VENTAS
fact_ventas = df_operativo.merge(
    dim_cliente,
    on=["cliente_nombre", "cliente_ciudad"],
    how="left",
    validate="many_to_one"
)

fact_ventas = fact_ventas.merge(
    dim_producto,
    on=[
        "producto_nombre",
        "categoria_prod",
        "precio_unitario"
    ],
    how="left",
    validate="many_to_one"
)

fact_ventas["fecha_completa"] = (
    fact_ventas["fecha_hora"].dt.normalize()
)

fact_ventas = fact_ventas.merge(
    dim_tiempo,
    on="fecha_completa",
    how="left",
    validate="many_to_one"
)

# METRICAS DE VENTAS
fact_ventas["monto_total"] = (
    fact_ventas["cantidad"] *
    fact_ventas["precio_unitario"]
)

# DESCUENTO ADICIONAL DEL 5%
# Se aplica cuando se compran 3 o mas unidades
fact_ventas["descuento"] = np.where(
    fact_ventas["cantidad"] >= 3,
    fact_ventas["monto_total"] * 0.05,
    0.0
)

fact_ventas["monto_neto"] = (
    fact_ventas["monto_total"] -
    fact_ventas["descuento"]
)

# SELECCION DE TABLA DE HECHOS
fact_table = fact_ventas[
    [
        "id_transaccion",
        "id_cliente_sk",
        "id_producto_sk",
        "id_tiempo_sk",
        "cantidad",
        "monto_total",
        "descuento",
        "monto_neto"
    ]
].copy()

print("\n=== FACT_VENTAS ===")
print(fact_table.head(10))
print(f"Total de registros: {len(fact_table)}")


# 6. VALIDACIONES
print("\n=== VALIDACION DEL ESQUEMA ESTRELLA ===")

assert len(fact_table) == n, (
    "Error: se perdieron o duplicaron transacciones"
)

assert not fact_table.isnull().any().any(), (
    "Error: existen valores nulos en la tabla de hechos"
)

assert fact_table["id_cliente_sk"].isin(
    dim_cliente["id_cliente_sk"]
).all()

assert fact_table["id_producto_sk"].isin(
    dim_producto["id_producto_sk"]
).all()

assert fact_table["id_tiempo_sk"].isin(
    dim_tiempo["id_tiempo_sk"]
).all()

print("Relaciones entre tablas verificadas correctamente.")
print("No se encontraron valores nulos en Fact_Ventas.")


# 7. RESUMEN GENERAL DE VENTAS
print("\n=== RESUMEN DE VENTAS ===")

print(f"Transacciones: {len(fact_table)}")
print(f"Cantidad vendida: {fact_table['cantidad'].sum()}")
print(f"Ventas brutas: ${fact_table['monto_total'].sum():,.2f}")
print(f"Descuentos: ${fact_table['descuento'].sum():,.2f}")
print(f"Ventas netas: ${fact_table['monto_neto'].sum():,.2f}")

print("\n=== ETL FINALIZADO CORRECTAMENTE ===")

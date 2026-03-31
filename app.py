import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="3D Print Manager", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer datos actuales
df = conn.read(ttl=0) # ttl=0 para que siempre refresque los datos

st.title("🛠️ Control de Pedidos 3D")

menu = st.sidebar.selectbox("Menú", ["Estado de Pedidos", "Nuevo Pedido", "Calculadora"])

if menu == "Calculadora":
    st.header("🧮 Calculadora de Presupuesto")
    col1, col2 = st.columns(2)
    with col1:
        precio_kilo = st.number_input("Precio Filamento (€/kg)", value=20.0)
        gramos = st.number_input("Gramos necesarios", value=0)
    with col2:
        horas = st.number_input("Horas de impresión", value=0.0)
        margen = st.slider("Margen de beneficio %", 0, 200, 100)

    costo_material = (precio_kilo / 1000) * gramos
    costo_luz = (300 / 1000) * horas * 0.15 
    total_base = costo_material + costo_luz
    precio_final = total_base * (1 + margen / 100)
    st.metric("PRECIO RECOMENDADO", f"{precio_final:.2f} €")

elif menu == "Nuevo Pedido":
    st.header("📝 Registrar Nuevo Trabajo")
    with st.form("nuevo_form"):
        cliente = st.text_input("Nombre del Cliente")
        pieza = st.text_input("Nombre de la Pieza")
        gramos_p = st.number_input("Gramos", value=0)
        horas_p = st.number_input("Horas", value=0.0)
        precio_p = st.number_input("Precio Pactado (€)", value=0.0)
        notas = st.text_area("Notas")
        
        if st.form_submit_button("Guardar Pedido"):
            nuevo_dato = pd.DataFrame([{
                "ID": len(df) + 1,
                "Fecha": datetime.now().strftime("%d/%m/%Y"),
                "Cliente": cliente,
                "Pieza": pieza,
                "Estado": "Pendiente",
                "Precio": precio_p,
                "Gramos": gramos_p,
                "Horas": horas_p,
                "Notas": notas
            }])
            updated_df = pd.concat([df, nuevo_dato], ignore_index=True)
            conn.update(data=updated_df)
            st.success("¡Pedido guardado en la nube!")
            st.cache_data.clear()

elif menu == "Estado de Pedidos":
    st.header("📊 Listado de Trabajos")
    if not df.empty:
        # Mostramos una tabla bonita
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("Actualizar Estado")
        # Selector para cambiar estado
        id_pedido = st.selectbox("Selecciona el ID del pedido", df["ID"].tolist())
        nuevo_estado = st.selectbox("Nuevo Estado", ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"])
        
        if st.button("Actualizar Estado"):
            df.loc[df["ID"] == id_pedido, "Estado"] = nuevo_estado
            conn.update(data=df)
            st.success(f"Pedido {id_pedido} actualizado a {nuevo_estado}")
            st.cache_data.clear()
    else:
        st.warning("Aún no hay pedidos registrados.")
        

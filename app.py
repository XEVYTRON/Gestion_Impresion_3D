import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="3D Print Manager", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

st.title("🛠️ Control de Pedidos 3D")

menu = st.sidebar.selectbox("Menú", ["Tablero de Pedidos", "Nuevo Pedido", "Editar Pedido", "Calculadora"])

if menu == "Calculadora":
    st.header("🧮 Calculadora de Presupuesto")
    
    col1, col2 = st.columns(2)
    with col1:
        precio_kilo = st.number_input("Precio Filamento (€/kg)", value=24.0)
        gramos = st.number_input("Gramos necesarios", value=0.0)
    with col2:
        horas = st.number_input("Horas de impresión", value=0.0)
        precio_hora = st.number_input("Precio por hora (€/h)", value=1.0)
        margen = st.slider("Margen de beneficio %", 0, 300, 100)

    # Cálculos con tu fórmula
    costo_material = (precio_kilo / 1000) * gramos
    costo_tiempo = horas * precio_hora
    total_base = costo_material + costo_tiempo
    precio_final = total_base * (1 + margen / 100)

    st.divider()
    st.write("### Desglose de costes:")
    st.write(f"- 🧵 **Material:** {costo_material:.2f} €")
    st.write(f"- ⏱️ **Tiempo de máquina:** {costo_tiempo:.2f} €")
    st.write(f"- ⚙️ **Coste Base Total:** {total_base:.2f} €")
    
    st.metric("PRECIO FINAL PARA EL CLIENTE", f"{precio_final:.2f} €")

elif menu == "Nuevo Pedido":
    st.header("📝 Registrar Nuevo Trabajo")
    with st.form("nuevo_form"):
        cliente = st.text_input("Nombre del Cliente")
        pieza = st.text_input("Nombre de la Pieza")
        gramos_p = st.number_input("Gramos", value=0.0)
        horas_p = st.number_input("Horas", value=0.0)
        precio_p = st.number_input("Precio Pactado (€)", value=0.0)
        notas = st.text_area("Notas")
        
        if st.form_submit_button("Guardar Pedido"):
            nuevo_dato = pd.DataFrame([{
                "ID": len(df) + 1 if not df.empty else 1,
                "Fecha": datetime.now().strftime("%d/%m/%Y"),
                "Cliente": cliente,
                "Pieza": pieza,
                "Estado": "Pendiente",
                "Precio": precio_p,
                "Gramos": gramos_p,
                "Horas": horas_p,
                "Notas": notas
            }])
            updated_df = pd.

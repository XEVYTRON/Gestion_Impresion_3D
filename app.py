import streamlit as st

# Configuración de la página
st.set_page_config(page_title="3D Print Manager", layout="wide")

st.title("🛠️ Control de Pedidos 3D")

# Menú lateral
menu = st.sidebar.selectbox("Menú", ["Nuevo Pedido", "Estado de Pedidos", "Calculadora de Costes"])

if menu == "Calculadora de Costes":
    st.header("🧮 Calculadora de Presupuesto")
    
    col1, col2 = st.columns(2)
    with col1:
        precio_kilo = st.number_input("Precio Filamento (€/kg)", value=20.0)
        gramos = st.number_input("Gramos necesarios", value=0)
    with col2:
        horas = st.number_input("Horas de impresión", value=0.0)
        margen = st.slider("Margen de beneficio %", 0, 200, 50)

    # Cálculos básicos (Electricidad estimada a 300W)
    costo_material = (precio_kilo / 1000) * gramos
    costo_luz = (300 / 1000) * horas * 0.15 
    total_base = costo_material + costo_luz
    precio_final = total_base * (1 + margen / 100)

    st.metric("PRECIO PARA CLIENTE", f"{precio_final:.2f} €")

elif menu == "Nuevo Pedido":
    st.header("📝 Registrar Trabajo")
    with st.form("nuevo_form"):
        cliente = st.text_input("Nombre del Cliente")
        pieza = st.text_input("Nombre de la Pieza")
        color = st.color_picker("Color seleccionado")
        notas = st.text_area("Notas adicionales")
        enviar = st.form_submit_button("Guardar Pedido")
        if enviar:
            st.success(f"Pedido de {cliente} anotado.")

elif menu == "Estado de Pedidos":
    st.header("📊 Flujo de Trabajo")
    st.info("Aquí aparecerán los pedidos para moverlos de estado (Próximamente).")
  

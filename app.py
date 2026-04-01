import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ LIMPIA
st.set_page_config(
    page_title="Xevytron 3D", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Estilos CSS para botones de navegación y ocultar menús de sistema
estilos_app = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {display:none;}
        
        /* Estilo para los botones de navegación superiores */
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: #f0f2f6;
            border: 1px solid #d1d5db;
        }
    </style>
"""
st.markdown(estilos_app, unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_pedidos = conn.read(worksheet="Pedidos", ttl=0) 
    df_presus = conn.read(worksheet="Presupuestos", ttl=0) 
except Exception as e:
    st.error("Error al conectar con la base de datos.")
    st.stop()

# 3. LÓGICA DE PDF
def crear_pdf(cliente, pieza, coste_mat, coste_tiem, precio_fin):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="PRESUPUESTO DE IMPRESIÓN 3D", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(200, 10, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 10, txt=f"Pieza: {pieza}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Desglose:", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"- Material: {coste_mat:.2f} Euros", ln=True)
    pdf.cell(200, 10, txt=f"- Tiempo de máquina: {coste_tiem:.2f} Euros", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {precio_fin:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 4. BARRA DE NAVEGACIÓN SUPERIOR (BOTONES EN FILA)
st.title("🛠️ Xevytron 3D")

# Creamos 3 columnas para los botones de menú
col_nav1, col_nav2, col_nav3 = st.columns(3)

# Usamos el estado de la sesión para saber qué pestaña está activa
if 'menu_activo' not in st.session_state:
    st.session_state.menu_activo = "Producción"

with col_nav1:
    if st.button("📊 Tablero"):
        st.session_state.menu_activo = "Producción"
        st.rerun()

with col_nav2:
    if st.button("🧮 Calcular"):
        st.session_state.menu_activo = "Calculadora"
        st.rerun()

with col_nav3:
    if st.button("📂 Historial"):
        st.session_state.menu_activo = "Historial"
        st.rerun()

st.divider()

# 5. CONTENIDO SEGÚN EL BOTÓN PULSADO

if st.session_state.menu_activo == "Calculadora":
    st.header("🧮 Nueva Calculadora")
    with st.expander("Datos del Cliente", expanded=True):
        c1, c2 = st.columns(2)
        cliente_n = c1.text_input("Cliente")
        pieza_n = c2.text_input("Pieza")
    
    col1, col2 = st.columns(2)
    with col1:
        precio_kilo = st.number_input("Precio Filamento (€/kg)", value=24.0)
        gramos = st.number_input("Gramos", value=0.0)
    with col2:
        horas = st.number_input("Horas", value=0.0)
        precio_hora = st.number_input("Precio/Hora (€)", value=1.0)
        margen = st.slider("Beneficio %", 0, 300, 100)

    c_mat = (precio_kilo / 1000) * gramos
    c_tiem = horas * precio_hora
    p_final = (c_mat + c_tiem) * (1 + margen / 100)
    st.metric("PRECIO FINAL", f"{p_final:.2f} €")

    if st.button("✅ Guardar Presupuesto y Pedido"):
        nuevo_presu = pd.DataFrame([{
            "ID": len(df_presus) + 1, "Fecha": datetime.now().strftime("%d/%m/%Y"),
            "Cliente": cliente_n, "Pieza": pieza_n, "Coste_Material": c_mat,
            "Coste_Tiempo": c_tiem, "Precio_Final": p_final, "Notas": ""
        }])
        nuevo_ped = pd.DataFrame([{
            "ID": len(df_pedidos) + 1, "Fecha": datetime.now().strftime("%d/%m/%Y"),
            "Cliente": cliente_n, "Pieza": pieza_n, "Estado": "Pendiente",
            "Precio": p_final, "Gramos": gramos, "Horas": horas, "Notas": "Presupuestado"
        }])
        conn.update(worksheet="Presupuestos", data=pd.concat([df_presus, nuevo_presu], ignore_index=True))
        conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_ped], ignore_index=True))
        st.success("Guardado correctamente.")
        st.cache_data.clear()

elif st.session_state.menu_activo == "Historial":
    st.header("📂 Historial de Presupuestos")
    busqueda = st.text_input("🔍 Buscar")
    df_f = df_presus[df_presus.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)] if not df_presus.empty else df_presus

    for i, row in df_f.iterrows():
        with st.container(border=True):
            st.write(f"**{row['Pieza']}** - {row['Cliente']}")
            st.write(f"💰 {row['Precio_Final']:.2f} €")
            pdf_b = crear_pdf(str(row['Cliente']), str(row['Pieza']), float(row['Coste_Material']), float(row['Coste_Tiempo']), float(row['Precio_Final']))
            col_pdf, col_del = st.columns(2)
            col_pdf.download_button("📩 PDF", pdf_b, f"Presu_{row['Cliente']}.pdf", key=f"dl_{i}")
            if col_del.button("🗑️ Borrar", key=f"del_{i}"):
                df_presus = df_presus.drop(i)
                conn.update(worksheet="Presupuestos", data=df_presus)
                st.cache_data.clear()
                st.rerun()

elif st.session_state.menu_activo == "Producción":
    st.header("📊 Producción")
    estados = ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]
    
    for est in estados:
        st.subheader(f"📍 {est}")
        items = df_pedidos[df_pedidos["Estado"] == est]
        for _, r in items.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Pieza']}** ({r['Cliente']})")

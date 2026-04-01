import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Xevytron 3D", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- DISEÑO DE BARRA INFERIOR FIJA (CSS) ---
estilos_fijos = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Contenedor flotante en la parte inferior */
        .nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            padding: 10px;
            display: flex;
            justify-content: space-around;
            border-top: 1px solid #ddd;
            z-index: 999999;
        }
        
        /* Espacio al final para que el contenido no quede tapado por el menú */
        .main-content {
            margin-bottom: 80px;
        }
    </style>
"""
st.markdown(estilos_fijos, unsafe_allow_html=True)

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

# 4. NAVEGACIÓN (ESTADO DE SESIÓN)
if 'menu_activo' not in st.session_state:
    st.session_state.menu_activo = "Producción"

# 5. CONTENIDO PRINCIPAL (Metido en un div para el margen inferior)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

st.title("🛠️ Xevytron 3D")

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
        precio_hora = st.number_input("

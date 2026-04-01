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
estilos_app = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {display:none;}
        
        /* Contenedor flotante en la parte inferior */
        .nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            padding: 10px 0;
            display: flex;
            justify-content: space-around;
            border-top: 1px solid #ddd;
            z-index: 999999;
        }
        
        /* Ajuste para que los botones de Streamlit parezcan de app móvil */
        .stButton > button {
            width: 100%;
            border-radius: 10px;
        }

        /* Espacio para que el contenido no quede tapado por el menú inferior */
        .main-content {
            margin-bottom: 100px;
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
    st.error("Error al conectar con las pestañas Pedidos y Presupuestos.")
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
    pdf.cell(200, 10, txt=f"- Tiempo de maquina: {coste_tiem:.2f} Euros", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {precio_fin:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 4. NAVEGACIÓN (ESTADO DE SESIÓN)
if 'menu_activo' not in st.session_state:
    st.session_state.menu_activo = "Producción"

# 5. CONTENIDO PRINCIPAL
st.markdown('<div class="main-content">', unsafe_allow_html=True)

st.title("🛠️ Xevytron 3D")

if st.session_state.menu_activo == "Calculadora":
    st.header("🧮 Calcular")
    cliente_n = st.text_input("Nombre del Cliente")
    pieza_n = st.text

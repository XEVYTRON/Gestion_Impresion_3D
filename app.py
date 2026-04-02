import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="centered", initial_sidebar_state="collapsed")

# --- ESTILOS CSS (DISEÑO PREMIUM ORIGINAL) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
        
        .titulo-seccion { font-size: 22px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 20px; }
        
        /* BOTONES DE NAVEGACIÓN Y ACCIONES: Gris Carbón Oscuro */
        .stButton button { 
            width: 100%; height: 3rem; border-radius: 8px; font-weight: 600; 
            text-transform: uppercase; border: 1px solid #212529; 
            background-color: #343a40 !important; color: #ffffff !important;
        }

        /* TARJETAS: Siempre blancas */
        .card-container { 
            background-color: #ffffff !important; 
            border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; 
            border-left: 6px solid #6f42c1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
            margin-bottom: 5px;
        }

        /* TEXTOS TRABAJOS */
        .trabajo-fecha { font-size: 10px; color: #999; text-transform: uppercase; margin: 0; }
        .trabajo-cliente { font-size: 21px; font-weight: 800; color: #111; text-transform: uppercase; margin: 0; line-height: 1.1; }
        .trabajo-pieza { font-size: 16px; font-weight: 500; color: #555; margin: 0; }
        .trabajo-precio { font-size: 18px; color: #6f42c1; font-weight: bold; margin-top: 5px; }

        /* TEXTOS FACTURAS */
        .factura-meta { font-size: 11px; color: #777; text-transform: uppercase; margin: 0; }
        .factura-cliente { font-size: 18px; font-weight: bold; color: #111; margin: 0; }
        .factura-detalle { font-size: 16px; color: #6f42c1; font-weight: bold; margin: 0; }
        
        /* Iconos PDF y Engranaje */
        [data-testid="stDownloadButton"] button { 
            height: 2.8rem; width: 100%; border-radius: 8px; 
            background-color: #343a40 !important; border: 1px solid #212529 !important;
            color: #ffffff !important;
        }
        [data-testid="stDownloadButton"] button p { color: white !important; font-weight: bold; }

        .stExpander { border: none !important; }
        .stExpander > details > summary { 
            background-color: #343a40 !important; border-radius: 8px; 
            border: 1px solid #212529 !important; height: 2.8rem; 
            display: flex; align-items: center; justify-content: center;
        }
        .stExpander > details > summary svg { fill: white !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        for df in [p, f]:
            if 'Notas' not in df.columns: df['Notas'] = ""
        return p, f
    except:
        return None, None

df_pedidos, df_facturas = cargar_datos()

if df_pedidos is None:
    st.error("Error de conexión. Refresca la página.")
    st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# 3. LÓGICA DE PDF
def crear_factura_pdf(id_fac, fecha, cliente, pieza, gramos, horas, total, notas=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, txt=f"ID: {id_fac} | Fecha: {fecha}", ln=True)
    pdf.cell(200, 8, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 8, txt=f"Trabajo: {pieza}", ln=True)
    if notas:
        pdf.ln(5); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(2

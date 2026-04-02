import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
import base64
from io import BytesIO

# 1. FUNCIÓN PARA EL ICONO DE MÓVIL (Base64)
def get_base64_of_bin_file(img_path):
    try:
        img = Image.open(img_path)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except:
        return ""

logo_base64 = get_base64_of_bin_file("image_7.png")

# 2. CONFIGURACIÓN DE PÁGINA
try:
    logo_image = Image.open("image_7.png")
except:
    logo_image = "🛠️"

st.set_page_config(
    page_title="Xevytron 3D", 
    page_icon=logo_image, 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- INYECCIÓN DE ICONO PARA PANTALLA DE INICIO (MÓVIL) ---
if logo_base64:
    st.markdown(f"""
        <head>
            <link rel="apple-touch-icon" href="data:image/png;base64,{logo_base64}">
            <link rel="icon" sizes="192x192" href="data:image/png;base64,{logo_base64}">
        </head>
    """, unsafe_allow_html=True)

# --- ESTILOS CSS (DISEÑO PREMIUM) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
        
        .titulo-seccion { font-size: 22px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 20px; }
        
        .stButton button { 
            width: 100%; height: 3rem; border-radius: 8px; font-weight: 600; 
            text-transform: uppercase; border: 1px solid #212529; 
            background-color: #343a40 !important; color: #ffffff !important;
        }

        .card-container { 
            background-color: #ffffff !important; 
            border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; 
            border-left: 6px solid #6f42c1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
            margin-bottom: 8px;
        }

        .trabajo-fecha { font-size: 10px; color: #999; text-transform: uppercase; margin: 0; }
        .trabajo-cliente { font-size: 21px; font-weight: 800; color: #111; text-transform: uppercase; margin: 0; line-height: 1.1; }
        .trabajo-pieza { font-size: 16px; font-weight: 500; color: #555; margin: 0; }
        .trabajo-precio { font-size: 18px; color: #6f42c1; font-weight: bold; margin-top: 5px; }

        [data-testid="stDownloadButton"] button, .stExpander > details > summary { 
            height: 2.8rem; width: 100%; border-radius: 8px; 
            background-color: #343a40 !important; border: 1px solid #212529 !important;
            color: #ffffff !important;
        }
        [data-testid="stDownloadButton"] button p { color: white !important; font-weight: bold; }
        .stExpander > details > summary svg { fill: white !important; }
        .stExpander { border: none !important; }
    </style>
""", unsafe_allow_html=True)

# 3. CONEXIÓN A DATOS
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

# 4. LÓGICA DE PDF
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
        pdf.multi_cell(200, 8, txt=f"Notas: {notas}")
    pdf.ln(10); pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {total:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 5. NAVEGACIÓN
if 'seccion' not in st.session_state:
    st.session_state.seccion = "TRABAJOS"

nav1, nav2, nav3 = st.columns(3)
if nav1.button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav2.button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav3.button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
st.divider()

# 6. VISTA: TRABAJOS
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    filtro = st.pills("Estado:", ESTADOS, default="Pendiente")
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    for i, r in items.iterrows():
        with st.container():
            col_dat, col_pdf, col_ed = st.columns([2.2, 0.7, 1.1])
            with col_dat:
                st.markdown(f"""
                    <div class="card-container">
                        <p class="trabajo-fecha">{r['Fecha']}</p>
                        <p class="trabajo-cliente">{r['Cliente']}</p>
                        <p class="trabajo-pieza">{r['Pieza']}</p>
                        <p class="trabajo-precio">{r['Precio']} €</p>
                    </div>
                """, unsafe_allow_html=True)
            with col_pdf:
                n_v = r['Notas'] if pd.notna(r['Notas']) else ""
                pdf = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), n_v)
                st.download_button("PDF", data=pdf, file_name=f"Fac_{r['Cliente']}.pdf", key=f"p_{r['ID']}")
            with col_ed:
                with st.expander("⚙️"):
                    with st.form(f"f_ed_{r['ID']}"):
                        u_cli = st.text_input("Cliente", value=r['Cliente'])
                        u_pie = st.text_input("Pieza", value=r['Pieza'])
                        u_pre = st.number_input("Precio (€)", value=float(r['Precio']))
                        u_not = st.text_area("Notas", value=r['Notas'] if pd.notna(r['Notas']) else "")
                        if st.form_submit_button("Ok"):
                            df_pedidos.loc[i, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                            conn.update(worksheet="Pedidos", data=df_pedidos)
                            # Sincronización factura
                            df_facturas['ID_s'] = df_facturas['ID'].astype(str)
                            idx = df_facturas[df_facturas['ID_s'] == str(r['ID'])].index
                            if not idx.empty:
                                df_facturas.loc[idx, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                                conn.update(worksheet="Facturas", data=df_facturas.drop(columns=['ID_s']))
                            else:
                                nueva = pd.DataFrame([{"ID": r['ID'], "Fecha": r['Fecha'], "Cliente": u_cli, "Pieza": u_pie, "Precio": u_pre, "Gramos": r['Gramos'], "Horas": r['Horas'], "Notas": u_not}])
                                conn.update(worksheet="Facturas", data=pd.concat([df_facturas.drop(columns=['ID_s']), nueva], ignore_index=True))
                            st.cache_data.clear(); st.rerun()
                    if st.button("🗑️", key=f"del_{r['ID']}", type="primary"):
                        df_pedidos = df_pedidos.drop(i)
                        conn.update(worksheet="Pedidos", data=df_pedidos)
                        st.cache_data.clear(); st.rerun()
            
            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"sel_{r['ID']}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_pedidos.loc[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_pedidos)
                st.cache_data.clear(); st.rerun()
        st.divider()

# 7. VISTA: NUEVO TRABAJO
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    c_nom = st.text_input("Cliente")
    p_nom = st.text_input("Pieza")
    ca, cb = st.columns(2)
    gr = ca.number_input("Gramos", min_value=0.0, step=1.0)
    hr = cb.number_input("Horas", min_value=0.0, step=0.5)
    mgn = st.select_slider("Margen %", options=[0, 25, 50, 75, 100, 150, 200, 300], value=100)
    total = ((24/1000 * gr) + (hr * 1.0)) * (1 + mgn/100)
    st.markdown(f"### TOTAL: {total:.2f} €")
    nts = st.text_area("Notas")
    if st.button("GUARDAR TRABAJO"):
        if c_nom and p_nom:
            f_h = datetime.now().strftime("%d/%m/%Y")
            id_u = datetime.now().strftime("%y%m%d%H%M%S")
            row = pd.DataFrame([{"ID": id_u, "Fecha": f_h, "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total, "Gramos": gr, "Horas": hr, "Notas": nts}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, row], ignore_index=True))
            conn.update(worksheet="Facturas", data=pd.concat([df_facturas, row.drop(columns=['Estado'])], ignore_index=True))
            st.cache_data.clear(); st.success("Guardado"); st.rerun()

# 8. VISTA: FACTURAS
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial de Facturas</p>', unsafe_allow_html=True)
    if df_facturas.empty:
        st.info("No hay facturas registradas.")
    else:
        for i, r in df_facturas.iloc[::-1].iterrows():
            with st.container():
                st.markdown(f"""
                    <div class="card-container">
                        <p class="factura-meta">{r['Fecha']} | ID: {r['ID']}</p>
                        <p class="factura-cliente">{r['Cliente']}</p>
                        <p class="factura-detalle">{r['Pieza']} - {r['Precio']} €</p>
                    </div>
                """, unsafe_allow_html=True)
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    pdf_bytes = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), r['Notas'])
                    st.download_button("📩 PDF", data=pdf_bytes, file_name=f"F_{r['Cliente']}.pdf", key=f"f_dl_{i}")
                with c_f2:
                    if st.button("🗑️", key=f"f_del_{i}"):
                        df_facturas = df_facturas.drop(i)
                        conn.update(worksheet="Facturas", data=df_facturas)
                        st.cache_data.clear(); st.rerun()
                st.divider()

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
import base64
from io import BytesIO

# 1. FUNCIÓN PARA EL ICONO DE MÓVIL Y PROCESAMIENTO DE IMÁGENES
def get_base64_of_bin_file(img_path):
    try:
        img = Image.open(img_path)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except:
        return ""

def procesar_imagen_para_gsheets(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        # Convertir a RGB para evitar errores con PNGs transparentes en el PDF
        img = img.convert("RGB")
        # Redimensionar para no saturar el Excel
        img.thumbnail((400, 400))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        return base64.b64encode(buffer.getvalue()).decode()
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

# --- INYECCIÓN DE ICONO PARA MÓVIL ---
if logo_base64:
    st.markdown(f"""
        <head>
            <link rel="apple-touch-icon" href="data:image/png;base64,{logo_base64}">
            <link rel="icon" sizes="192x192" href="data:image/png;base64,{logo_base64}">
        </head>
    """, unsafe_allow_html=True)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden !important; width: 100vw; margin: 0; padding: 0; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stDeployButton {display:none;}
        .titulo-seccion { font-size: 22px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 20px; }
        .stButton button { width: 100%; height: 3rem; border-radius: 8px; font-weight: 600; text-transform: uppercase; background-color: #343a40 !important; color: white !important; }
        .card-container { 
            background-color: #ffffff !important; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; 
            border-left: 6px solid #6f42c1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px;
        }
        [data-testid="stDownloadButton"] button, .stExpander > details > summary { 
            height: 3.2rem; width: 100%; border-radius: 8px; background-color: #343a40 !important; color: white !important; display: flex; align-items: center; justify-content: center; margin-bottom: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# 3. CONEXIÓN A DATOS Y SESIÓN
conn = st.connection("gsheets", type=GSheetsConnection)

if 'v_menu' not in st.session_state:
    st.session_state.v_menu = {}

@st.cache_data(ttl=10)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        for df in [p, f]:
            if 'Notas' not in df.columns: df['Notas'] = ""
            if 'Imagen' not in df.columns: df['Imagen'] = ""
        return p, f
    except:
        return None, None

df_pedidos, df_facturas = cargar_datos()

if df_pedidos is None:
    st.error("Error de conexión. Refresca la página.")
    st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# 4. LÓGICA DE PDF CORREGIDA PARA IMÁGENES
def crear_factura_pdf(id_fac, fecha, cliente, pieza, total, notas="", img_base64=""):
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
    
    # INSERTAR IMAGEN DE REFERENCIA
    if img_base64 and len(str(img_base64)) > 50:
        try:
            # Decodificar imagen
            img_data = base64.b64decode(img_base64)
            img_io = BytesIO(img_data)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 8, txt="Referencia Visual:", ln=True)
            
            # Dibujar imagen (w=60 para que sea visible pero no enorme)
            pdf.image(img_io, x=10, y=pdf.get_y(), w=60)
            pdf.ln(65) # Espacio para que el precio no pise la foto
        except Exception as e:
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(200, 8, txt="(Imagen no disponible en este PDF)", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {total:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 5. NAVEGACIÓN
if 'seccion' not in st.session_state:
    st.session_state.seccion = "TRABAJOS"

nav_cols = st.columns(3)
if nav_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav_cols[2].button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
st.divider()

# 6. VISTA: TRABAJOS
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    filtro = st.pills("Estado:", ESTADOS, default="Pendiente")
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    for i, r in items.iterrows():
        ver = st.session_state.v_menu.get(r['ID'], 0)
        with st.container():
            st.markdown(f"""
                <div class="card-container">
                    <p class="trabajo-fecha">{r['Fecha']}</p>
                    <p class="trabajo-cliente">{r['Cliente']}</p>
                    <p class="trabajo-pieza">{r['Pieza']} | {r['Precio']} €</p>
                </div>
            """, unsafe_allow_html=True)
            
            if r['Imagen']:
                st.image(f"data:image/jpeg;base64,{r['Imagen']}", width=180, caption="Referencia")
            
            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"sel_{r['ID']}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_pedidos.loc[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_pedidos)
                st.cache_data.clear(); st.rerun()
            
            with st.expander("MODIFICAR ⚙️", key=f"exp_{r['ID']}_{ver}"):
                with st.form(f"f_ed_{r['ID']}_{ver}"):
                    u_cli = st.text_input("Cliente", value=r['Cliente'])
                    u_pie = st.text_input("Pieza", value=r['Pieza'])
                    u_pre = st.number_input("Precio (€)", value=float(r['Precio']))
                    u_not = st.text_area("Notas", value=r['Notas'])
                    u_img_file = st.file_uploader("Cambiar Imagen", type=['png', 'jpg', 'jpeg'], key=f"img_u_{r['ID']}")
                    
                    if st.form_submit_button("Ok"):
                        nueva_img_64 = procesar_imagen_para_gsheets(u_img_file) if u_img_file else r['Imagen']
                        df_pedidos.loc[i, ['Cliente', 'Pieza', 'Precio', 'Notas', 'Imagen']] = [u_cli, u_pie, u_pre, u_not, nueva_img_64]
                        conn.update(worksheet="Pedidos", data=df_pedidos)
                        st.session_state.v_menu[r['ID']] = ver + 1 # CAMBIO DE KEY PARA CERRAR
                        st.cache_data.clear(); st.rerun()
                
                if st.button("🗑️ ELIMINAR", key=f"del_{r['ID']}", type="primary"):
                    df_pedidos = df_pedidos.drop(i)
                    conn.update(worksheet="Pedidos", data=df_pedidos); st.cache_data.clear(); st.rerun()

            pdf_data = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'])
            st.download_button("DESCARGAR PDF 📩", data=pdf_data, file_name=f"F_{r['Cliente']}.pdf", key=f"p_{r['ID']}")
        st.divider()

# 7. VISTA: NUEVO TRABAJO
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    c_nom = st.text_input("Cliente")
    p_nom = st.text_input("Pieza")
    col_a, col_b = st.columns(2)
    gr = col_a.number_input("Gramos", min_value=0.0, step=1.0)
    hr = col_b.number_input("Horas", min_value=0.0, step=0.5)
    mgn = st.select_slider("Margen %", options=[0, 25, 50, 75, 100, 150, 200, 300], value=100)
    total = ((24/1000 * gr) + (hr * 1.0)) * (1 + mgn/100)
    st.markdown(f"### TOTAL: {total:.2f} €")
    nts = st.text_area("Notas")
    img_ref = st.file_uploader("Cargar Foto Referencia", type=['png', 'jpg', 'jpeg'])
    
    if st.button("GUARDAR TRABAJO"):
        if c_nom and p_nom:
            img_64 = procesar_imagen_para_gsheets(img_ref)
            f_h = datetime.now().strftime("%d/%m/%Y")
            id_u = datetime.now().strftime("%y%m%d%H%M%S")
            row = pd.DataFrame([{"ID": id_u, "Fecha": f_h, "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total, "Gramos": gr, "Horas": hr, "Notas": nts, "Imagen": img_64}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, row], ignore_index=True))
            conn.update(worksheet="Facturas", data=pd.concat([df_facturas, row.drop(columns=['Estado'])], ignore_index=True))
            st.cache_data.clear(); st.success("¡Guardado!"); st.rerun()

# 8. VISTA: FACTURAS
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    for i, r in df_facturas.iloc[::-1].iterrows():
        with st.container():
            st.markdown(f'<div class="card-container"><p class="factura-meta">{r["Fecha"]} | {r["Cliente"]}</p><p class="factura-cliente">{r["Pieza"]} - {r["Precio"]} €</p></div>', unsafe_allow_html=True)
            if r['Imagen']:
                st.image(f"data:image/jpeg;base64,{r['Imagen']}", width=100)
            pdf_b = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'])
            st.download_button("📩 PDF", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"f_dl_{i}")
            if st.button("🗑️", key=f"f_del_{i}"):
                df_facturas = df_facturas.drop(i)
                conn.update(worksheet="Facturas", data=df_facturas); st.cache_data.clear(); st.rerun()
            st.divider()

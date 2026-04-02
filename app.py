import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
import base64
from io import BytesIO

# --- 1. UTILIDADES DE IMAGEN Y PDF ---
def get_base64_logo(path):
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return ""

def procesar_foto(file):
    if file:
        try:
            img = Image.open(file).convert("RGB")
            img.thumbnail((200, 200))
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=50)
            return base64.b64encode(buf.getvalue()).decode()
        except: return ""
    return ""

def crear_pdf(id_f, fecha, cli, pie, tot, nts="", img_b64=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 7, txt=f"ID: {id_f} | Fecha: {fecha}", ln=True)
    pdf.cell(200, 7, txt=f"Cliente: {cli}", ln=True)
    pdf.cell(200, 7, txt=f"Trabajo: {pie}", ln=True)
    if nts:
        pdf.ln(2); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 6, txt=f"Notas: {nts}")
    if img_b64 and len(str(img_b64)) > 100:
        try:
            img_raw = base64.b64decode(img_b64)
            pdf.ln(5); pdf.image(BytesIO(img_raw), w=50); pdf.ln(5)
        except: pass
    pdf.ln(5); pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"TOTAL: {tot:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 2. CONFIGURACIÓN E ICONO ---
logo_b64 = get_base64_logo("image_7.png")
try: icon = Image.open("image_7.png")
except: icon = "🛠️"

st.set_page_config(page_title="Xevytron 3D", page_icon=icon, layout="centered")

if logo_b64:
    st.markdown(f'<head><link rel="apple-touch-icon" href="data:image/png;base64,{logo_b64}"></head>', unsafe_allow_html=True)

# --- 3. ESTILOS CSS ---
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden !important; width: 100vw; }
        #MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none; }
        .titulo-seccion { font-size: 20px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 15px; }
        .stButton button { width: 100%; height: 3rem; border-radius: 8px; font-weight: 600; background-color: #343a40 !important; color: white !important; }
        .card-container { 
            background-color: #ffffff !important; border-radius: 10px; padding: 12px; border: 1px solid #e0e0e0; 
            border-left: 6px solid #6f42c1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px;
        }
        .card-fecha { font-size: 10px; color: #999; margin: 0; text-transform: uppercase; }
        .card-nombre { font-size: 18px; font-weight: 800; color: #6f42c1 !important; margin: 0; text-transform: uppercase; line-height: 1.2; }
        .card-info { font-size: 14px; color: #555; margin: 0; }
        [data-testid="stDownloadButton"] button, .stExpander > details > summary { 
            height: 3.1rem; width: 100%; border-radius: 8px; background-color: #343a40 !important; color: white !important; margin-bottom: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. CONEXIÓN Y DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if 'v_menu' not in st.session_state: st.session_state.v_menu = {}

@st.cache_data(ttl=2)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        for df in [p, f]:
            if 'ID' in df.columns:
                df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
            for col in ['Notas', 'Imagen']:
                if col not in df.columns: df[col] = ""
        return p, f
    except: return None, None

df_p, df_f = cargar_datos()
if df_p is None: st.error("Error al conectar con Google Sheets"); st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 5. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
nav_cols = st.columns(3)
if nav_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav_cols[2].button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
st.divider()

# --- 6. VISTA: TRABAJOS (CON BUSCADOR) ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    
    # BUSCADOR INTELIGENTE
    busqueda = st.text_input("🔍 Buscar cliente o pieza...", placeholder="Ej: Juan o Casco").lower()
    
    filtro_estado = st.pills("Filtrar por estado:", ESTADOS, default="Pendiente")
    
    # Lógica de filtrado doble: por estado Y por texto
    items = df_p[df_p["Estado"] == filtro_estado]
    if busqueda:
        items = items[items['Cliente'].str.lower().str.contains(busqueda) | 
                      items['Pieza'].str.lower().str.contains(busqueda)]
    
    if items.empty:
        st.info("No se han encontrado trabajos con ese nombre.")
    
    for i, r in items.iterrows():
        id_actual = str(r['ID'])
        ver = st.session_state.v_menu.get(id_actual, 0)
        
        with st.container():
            st.markdown(f"""
                <div class="card-container">
                    <p class="card-fecha">{r['Fecha']} | ID: {id_actual}</p>
                    <p class="card-nombre">{r['Cliente']}</p>
                    <p class="card-info">{r['Pieza']} | <b>{r['Precio']} €</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            if r['Imagen'] and len(str(r['Imagen'])) > 100:
                st.image(f"data:image/jpeg;base64,{r['Imagen']}", width=150)

            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"s_{id_actual}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_p.loc[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p)
                st.cache_data.clear(); st.rerun()
            
            with st.expander("MODIFICAR TRABAJO ⚙️", key=f"e_{id_actual}_{ver}"):
                with st.form(f"f_{id_actual}_{ver}"):
                    u_cli = st.text_input("Cliente", value=r['Cliente'])
                    u_pie = st.text_input("Pieza", value=r['Pieza'])
                    u_pre = st.number_input("Precio", value=float(r['Precio']))
                    u_not = st.text_area("Notas", value=r['Notas'])
                    u_img = st.file_uploader("Nueva Foto", type=['jpg', 'jpeg', 'png'])
                    
                    if st.form_submit_button("GUARDAR CAMBIOS"):
                        img_64 = procesar_foto(u_img) if u_img else r['Imagen']
                        idx_p = df_p[df_p['ID'].astype(str) == id_actual].index
                        df_p.loc[idx_p, ['Cliente', 'Pieza', 'Precio', 'Notas', 'Imagen']] = [u_cli, u_pie, u_pre, u_not, img_64]
                        conn.update(worksheet="Pedidos", data=df_p)
                        
                        idx_f = df_f[df_f['ID'].astype(str) == id_actual].index
                        if not idx_f.empty:
                            df_f.loc[idx_f, ['Cliente', 'Pieza', 'Precio', 'Notas', 'Imagen']] = [u_cli, u_pie, u_pre, u_not, img_64]
                            conn.update(worksheet="Facturas", data=df_f)
                        
                        st.session_state.v_menu[id_actual] = ver + 1
                        st.cache_data.clear(); st.rerun()

                if st.button("🗑️ ELIMINAR PERMANENTE", key=f"d_{id_actual}"):
                    df_p = df_p[df_p['ID'].astype(str) != id_actual]
                    conn.update(worksheet="Pedidos", data=df_p)
                    df_f = df_f[df_f['ID'].astype(str) != id_actual]
                    conn.update(worksheet="Facturas", data=df_f)
                    st.cache_data.clear(); st.rerun()

            pdf_b = crear_pdf(id_actual, r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'])
            st.download_button("DESCARGAR PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{id_actual}")
        st.divider()

# --- 7. VISTA: NUEVO TRABAJO ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    c_nom = st.text_input("Nombre Cliente")
    p_nom = st.text_input("Nombre de la Pieza")
    ca, cb = st.columns(2)
    gr = ca.number_input("Gramos totales", min_value=0.0)
    hr = cb.number_input("Horas totales", min_value=0.0)
    mgn = st.select_slider("Margen (%)", options=[0, 50, 100, 150, 200, 300], value=100)
    total = ((0.024 * gr) + (hr * 1.0)) * (1 + mgn/100)
    st.markdown(f"### TOTAL: {total:.2f} €")
    nts = st.text_area("Notas / Observaciones")
    img_f = st.file_uploader("Subir Imagen Referencia", type=['jpg', 'jpeg', 'png'])
    
    if st.button("GUARDAR EN BASE DE DATOS"):
        if c_nom and p_nom:
            img_64 = procesar_foto(img_f)
            id_u = datetime.now().strftime("%y%m%d%H%M%S")
            row = pd.DataFrame([{
                "ID": id_u, "Fecha": datetime.now().strftime("%d/%m/%Y"), 
                "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", 
                "Precio": total, "Gramos": gr, "Horas": hr, "Notas": nts, "Imagen": img_64
            }])
            conn.update(worksheet="Pedidos", data=pd.concat([df_p, row], ignore_index=True))
            conn.update(worksheet="Facturas", data=pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True))
            st.cache_data.clear(); st.success("¡Trabajo guardado!"); st.rerun()

# --- 8. VISTA: FACTURAS (CON BUSCADOR) ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial de Facturas</p>', unsafe_allow_html=True)
    
    # BUSCADOR INTELIGENTE EN FACTURAS
    busqueda_f = st.text_input("🔍 Buscar en historial...", placeholder="Nombre o pieza...").lower()
    
    items_f = df_f.iloc[::-1]
    if busqueda_f:
        items_f = items_f[items_f['Cliente'].str.lower().str.contains(busqueda_f) | 
                          items_f['Pieza'].str.lower().str.contains(busqueda_f)]
    
    if items_f.empty:
        st.info("No hay facturas que coincidan con la búsqueda.")
    else:
        for i, r in items_f.iterrows():
            with st.container():
                st.markdown(f"""
                    <div class="card-container">
                        <p class="card-fecha">{r['Fecha']} | ID: {r['ID']}</p>
                        <p class="card-nombre">{r['Cliente']}</p>
                        <p class="card-info">{r['Pieza']} - <b>{r['Precio']} €</b></p>
                    </div>
                """, unsafe_allow_html=True)
                if r['Imagen'] and len(str(r['Imagen'])) > 100:
                    st.image(f"data:image/jpeg;base64,{r['Imagen']}", width=100)
                
                pdf_b = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'])
                st.download_button("DESCARGAR 📩", data=pdf_b, file_name=f"Factura_{r['Cliente']}.pdf", key=f"fpdf_{r['ID']}")
                
                if st.button("BORRAR FACTURA 🗑️", key=f"fdel_{r['ID']}"):
                    df_f_upd = df_f[df_f['ID'].astype(str) != str(r['ID'])]
                    conn.update(worksheet="Facturas", data=df_f_upd)
                    st.cache_data.clear(); st.rerun()
                st.divider()

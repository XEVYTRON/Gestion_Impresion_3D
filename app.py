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

# --- 3. ESTILOS CSS ADAPTADOS (MODO OSCURO + LOGO FONDO) ---
st.markdown(f"""
    <style>
        /* Limpieza de márgenes y scroll */
        html, body, [data-testid="stAppViewContainer"] {{
            overflow-x: hidden !important;
            max-width: 100vw !important;
            margin: 0; padding: 0;
        }}

        #MainMenu, footer, header, .stDeployButton {{ visibility: hidden; display: none; }}
        
        .titulo-seccion {{ font-size: 20px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 20px; }}
        
        /* BOTONES NAVEGACIÓN (Gris carbón con transparencia) */
        .stButton button {{ 
            width: 100%; height: 3.5rem; border-radius: 8px; font-weight: 600; 
            text-transform: uppercase; border: 1px solid #444; 
            background-color: rgba(50, 50, 50, 0.8) !important; color: white !important;
        }}

        /* --- LOGO OMNIPRESENTE (MEJORADO) --- */
        .watermark {{
            position: fixed;
            top: 55%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 300px;
            opacity: 0.1; /* Muy sutil para no molestar */
            z-index: -100;
            pointer-events: none;
        }}

        /* TARJETAS (Adaptables a modo claro/oscuro) */
        .card-container {{ 
            background-color: rgba(128, 128, 128, 0.1) !important; 
            border-radius: 10px; padding: 15px; 
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-left: 6px solid #6f42c1; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
            margin-bottom: 10px; width: 100%; box-sizing: border-box;
        }}
        .card-fecha {{ font-size: 10px; color: gray; margin: 0; text-transform: uppercase; }}
        .card-nombre {{ font-size: 20px; font-weight: 800; color: #6f42c1 !important; margin: 0; text-transform: uppercase; }}
        
        /* Ajuste de botones y expanders */
        [data-testid="stDownloadButton"] button, .stExpander > details > summary {{ 
            height: 3rem; width: 100%; border-radius: 8px; 
            background-color: #333 !important; color: white !important; margin-bottom: 8px;
        }}
    </style>
    <img src="data:image/png;base64,{logo_b64}" class="watermark">
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
if df_p is None: st.error("Error de conexión"); st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 5. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
nav_cols = st.columns(3)
if nav_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav_cols[2].button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
st.divider()

# --- 6. VISTA: TRABAJOS ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    busqueda = st.text_input("🔍 Buscar...", placeholder="Cliente o pieza").lower()
    filtro_estado = st.pills("Estado:", ESTADOS, default="Pendiente")
    
    items = df_p[df_p["Estado"] == filtro_estado]
    if busqueda:
        items = items[items['Cliente'].str.lower().str.contains(busqueda) | 
                      items['Pieza'].str.lower().str.contains(busqueda)]
    
    for i, r in items.iterrows():
        id_actual = str(r['ID'])
        ver = st.session_state.v_menu.get(id_actual, 0)
        with st.container():
            st.markdown(f"""
                <div class="card-container">
                    <p class="card-fecha">{r['Fecha']} | ID: {id_actual}</p>
                    <p class="card-nombre">{r['Cliente']}</p>
                    <p>{r['Pieza']} | <b>{r['Precio']} €</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            if r['Imagen'] and len(str(r['Imagen'])) > 100:
                st.image(f"data:image/jpeg;base64,{r['Imagen']}", width=150)

            nuevo_e = st.selectbox("Cambiar estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"s_{id_actual}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_p.loc[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p); st.cache_data.clear(); st.rerun()
            
            with st.expander("MODIFICAR ⚙️", key=f"e_{id_actual}_{ver}"):
                with st.form(f"f_{id_actual}_{ver}"):
                    u_cli = st.text_input("Cliente", value=r['Cliente'])
                    u_pie = st.text_input("Pieza", value=r['Pieza'])
                    u_pre = st.number_input("Precio", value=float(r['Precio']))
                    u_not = st.text_area("Notas", value=r['Notas'])
                    u_img = st.file_uploader("Nueva Foto", type=['jpg', 'jpeg', 'png'])
                    if st.form_submit_button("Ok"):
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

                if st.button("🗑️ ELIMINAR", key=f"d_{id_actual}", type="primary"):
                    df_p = df_p[df_p['ID'].astype(str) != id_actual]; conn.update(worksheet="Pedidos", data=df_p)
                    df_f = df_f[df_f['ID'].astype(str) != id_actual]; conn.update(worksheet="Facturas", data=df_f)
                    st.cache_data.clear(); st.rerun()

            pdf_b = crear_pdf(id_actual, r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'])
            st.download_button("PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{id_actual}")
        st.divider()

# --- 7. VISTA: NUEVO TRABAJO ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    c_nom = st.text_input("Cliente")
    p_nom = st.text_input("Pieza")
    ca, cb = st.columns(2)
    gr = ca.number_input("Gramos", min_value=0.0); hr = cb.number_input("Horas", min_value=0.0)
    mgn = st.select_slider("Margen %", options=[0, 50, 100, 200], value=100)
    total = ((0.024 * gr) + (hr * 1.0)) * (1 + mgn/100)
    st.markdown(f"### TOTAL: {total:.2f} €")
    nts = st.text_area("Notas")
    img_f = st.file_uploader("Foto Referencia", type=['jpg', 'jpeg', 'png'])
    if st.button("GUARDAR"):
        if c_nom and p_nom:
            img_64 = procesar_foto(img_f); id_u = datetime.now().strftime("%y%m%d%H%M%S")
            row = pd.DataFrame([{"ID": id_u, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total, "Gramos": gr, "Horas": hr, "Notas": nts, "Imagen": img_64}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_p, row], ignore_index=True))
            conn.update(worksheet="Facturas", data=pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True))
            st.cache_data.clear(); st.success("¡Guardado!"); st.rerun()

# --- 8. VISTA: FACTURAS ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    busqueda_f = st.text_input("🔍 Buscar...", placeholder="Nombre o pieza").lower()
    items_f = df_f.iloc[::-1]
    if busqueda_f:
        items_f = items_f[items_f['Cliente'].str.lower().str.contains(busqueda_f) | items_f['Pieza'].str.lower().str.contains(busqueda_f)]
    
    for i, r in items_f.iterrows():
        with st.container():
            st.markdown(f'<div class="card-container"><p class="card-fecha">{r["Fecha"]} | ID: {r["ID"]}</p><p class="card-nombre">{r["Cliente"]}</p><p>{r["Pieza"]} - <b>{r["Precio"]} €</b></p></div>', unsafe_allow_html=True)
            if r['Imagen'] and len(str(r['Imagen'])) > 100: st.image(f"data:image/jpeg;base64,{r['Imagen']}", width=100)
            pdf_b = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'])
            st.download_button("DESCARGAR 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"fpdf_{r['ID']}")
            if st.button("BORRAR 🗑️", key=f"fdel_{r['ID']}"):
                conn.update(worksheet="Facturas", data=df_f[df_f['ID'].astype(str) != str(r['ID'])]); st.cache_data.clear(); st.rerun()
            st.divider()

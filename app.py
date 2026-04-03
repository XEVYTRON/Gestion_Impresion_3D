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
            img.thumbnail((150, 150))
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=40)
            return base64.b64encode(buf.getvalue()).decode()
        except: return ""
    return ""

def crear_pdf(id_f, fecha, cli, pie, tot, nts="", img_b64="", img_b64_2=""):
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
    
    pdf.ln(5)
    y_inicial = pdf.get_y()
    if img_b64 and len(str(img_b64)) > 100:
        try:
            pdf.image(BytesIO(base64.b64decode(img_b64)), x=10, y=y_inicial, w=40)
        except: pass
    if img_b64_2 and len(str(img_b64_2)) > 100:
        try:
            pdf.image(BytesIO(base64.b64decode(img_b64_2)), x=55, y=y_inicial, w=40)
        except: pass
    
    if (img_b64 and len(str(img_b64)) > 100) or (img_b64_2 and len(str(img_b64_2)) > 100):
        pdf.set_y(y_inicial + 45)

    pdf.ln(5); pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"TOTAL: {tot:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 2. CONFIGURACIÓN ---
logo_b64 = get_base64_logo("image_7.png")
try: icon = Image.open("image_7.png")
except: icon = "🛠️"

st.set_page_config(page_title="Xevytron 3D", page_icon=icon, layout="centered")

# --- 3. ESTILOS CSS ---
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden !important; width: 100vw; margin: 0; padding: 0; }
        #MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none; }
        .titulo-seccion { font-size: 20px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 15px; }
        .stButton button { width: 100%; height: 3rem; border-radius: 8px; font-weight: 600; text-transform: uppercase; background-color: #343a40 !important; color: white !important; }
        .card-container { background-color: #ffffff !important; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; border-left: 6px solid #6f42c1; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; }
        .card-fecha { font-size: 10px; color: #777 !important; margin-bottom: 2px; text-transform: uppercase; }
        .card-nombre { font-size: 18px; font-weight: 800; color: #6f42c1 !important; margin: 0; text-transform: uppercase; }
        .card-pieza { font-size: 15px; color: #333 !important; font-weight: 600; margin-top: 4px; }
        .card-nota { font-size: 13px; color: #555 !important; font-style: italic; margin-top: 2px; line-height: 1.2; }
        .card-precio { font-size: 17px; color: #111 !important; font-weight: 900; margin-top: 8px; border-top: 1px solid #eee; pt: 5px; }
        [data-testid="stMetricValue"] { font-size: 24px !important; color: #6f42c1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CONEXIÓN Y DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if 'v_menu' not in st.session_state: st.session_state.v_menu = {}
if 'form_reset_key' not in st.session_state: st.session_state.form_reset_key = 0

@st.cache_data(ttl=2)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        for df in [p, f]:
            if 'ID' in df.columns:
                df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
            for col in ['Notas', 'Imagen', 'Imagen2']:
                if col in df.columns:
                    df[col] = df[col].astype(str).replace(['nan', 'None', '0', '0.0'], '')
                else: df[col] = ""
            for col in ['Gramos', 'Horas', 'Precio']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                else: df[col] = 0.0
        return p, f
    except: return None, None

df_p, df_f = cargar_datos()
if df_p is None: st.error("Error de conexión"); st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 5. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
nav_cols = st.columns(4)
if nav_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav_cols[2].button("HISTORIAL"): st.session_state.seccion = "FACTURAS"; st.rerun()
if nav_cols[3].button("📊"): st.session_state.seccion = "ESTADISTICAS"; st.rerun()
st.divider()

# --- 6. VISTA: TRABAJOS ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    busqueda = st.text_input("🔍 Buscar cliente o pieza...", placeholder="Ej: Juan").lower()
    filtro_estado = st.pills("Estado:", ESTADOS, default="Pendiente")
    items = df_p[df_p["Estado"] == filtro_estado].sort_values(by="ID", ascending=True)
    if busqueda:
        items = items[items['Cliente'].str.lower().str.contains(busqueda) | items['Pieza'].str.lower().str.contains(busqueda)]
    
    for i, r in items.iterrows():
        id_actual = str(r['ID'])
        ver = st.session_state.v_menu.get(id_actual, 0)
        with st.container():
            nota_texto = f"Notas: {r['Notas']}" if r['Notas'] else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {id_actual}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p><p class="card-nota">{nota_texto}</p><p class="card-precio">Precio: {r['Precio']} €</p></div>""", unsafe_allow_html=True)
            c_img_a, c_img_b = st.columns(2)
            if r['Imagen'] and len(str(r['Imagen'])) > 100: c_img_a.image(f"data:image/jpeg;base64,{r['Imagen']}", width=70)
            if r['Imagen2'] and len(str(r['Imagen2'])) > 100: c_img_b.image(f"data:image/jpeg;base64,{r['Imagen2']}", width=70)
            
            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"s_{id_actual}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_p.at[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p); st.cache_data.clear(); st.rerun()
            
            with st.expander("MODIFICAR ⚙️", key=f"e_{id_actual}_{ver}"):
                with st.form(f"f_ed_{id_actual}_{ver}"):
                    u_cli = st.text_input("Cliente", value=r['Cliente']); u_pie = st.text_input("Pieza", value=r['Pieza'])
                    u_pre = st.number_input("Precio", value=float(r['Precio'])); u_not = st.text_area("Notas", value=r['Notas'])
                    u_img1 = st.file_uploader("Foto 1", type=['jpg', 'jpeg', 'png']); u_img2 = st.file_uploader("Foto 2", type=['jpg', 'jpeg', 'png'])
                    if st.form_submit_button("Ok"):
                        img1_64 = procesar_foto(u_img1) if u_img1 else r['Imagen']
                        img2_64 = procesar_foto(u_img2) if u_img2 else r['Imagen2']
                        idx_p = df_p[df_p['ID'].astype(str) == id_actual].index
                        if not idx_p.empty:
                            row_idx = idx_p[0]
                            df_p.at[row_idx, 'Cliente'] = u_cli; df_p.at[row_idx, 'Pieza'] = u_pie
                            df_p.at[row_idx, 'Precio'] = float(u_pre); df_p.at[row_idx, 'Notas'] = u_not
                            df_p.at[row_idx, 'Imagen'] = str(img1_64); df_p.at[row_idx, 'Imagen2'] = str(img2_64)
                            conn.update(worksheet="Pedidos", data=df_p)
                        idx_f = df_f[df_f['ID'].astype(str) == id_actual].index
                        if not idx_f.empty:
                            f_row_idx = idx_f[0]
                            df_f.at[f_row_idx, 'Cliente'] = u_cli; df_f.at[f_row_idx, 'Pieza'] = u_pie
                            df_f.at[f_row_idx, 'Precio'] = float(u_pre); df_f.at[f_row_idx, 'Notas'] = u_not
                            df_f.at[f_row_idx, 'Imagen'] = str(img1_64); df_f.at[f_row_idx, 'Imagen2'] = str(img2_64)
                            conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.v_menu[id_actual] = ver + 1; st.cache_data.clear(); st.rerun()
                if st.button("🗑️ ELIMINAR", key=f"d_{id_actual}"):
                    df_p = df_p[df_p['ID'].astype(str) != id_actual]; conn.update(worksheet="Pedidos", data=df_p)
                    df_f = df_f[df_f['ID'].astype(str) != id_actual]; conn.update(worksheet="Facturas", data=df_f)
                    st.cache_data.clear(); st.rerun()
            pdf_b = crear_pdf(id_actual, r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'], r['Imagen2'])
            st.download_button("PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{id_actual}")
        st.divider()

# --- 7. VISTA: NUEVO TRABAJO (PRECIO REAL-TIME Y LIMPIEZA SIN ERRORES) ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    
    # TRUCO: El contenedor cambia de ID para limpiar los inputs al guardar
    with st.container(key=f"nuevo_pedido_container_{st.session_state.form_reset_key}"):
        c_nom = st.text_input("Nombre Cliente", key=f"cli_{st.session_state.form_reset_key}")
        p_nom = st.text_input("Pieza", key=f"pie_{st.session_state.form_reset_key}")
        ca, cb = st.columns(2)
        gr = ca.number_input("Gramos", min_value=0.0, key=f"gr_{st.session_state.form_reset_key}")
        hr = cb.number_input("Horas", min_value=0.0, key=f"hr_{st.session_state.form_reset_key}")
        mgn = st.select_slider("Margen %", options=[0, 50, 100, 150, 200, 300], value=100, key=f"mgn_{st.session_state.form_reset_key}")
        
        # PRECIO EN TIEMPO REAL
        total_preview = ((0.024 * gr) + (hr * 1.0)) * (1 + mgn/100)
        st.markdown(f"### TOTAL ESTIMADO: {total_preview:.2f} €")
        
        nts = st.text_area("Notas", key=f"nts_{st.session_state.form_reset_key}")
        f_col1, f_col2 = st.columns(2)
        img_f1 = f_col1.file_uploader("Foto 1", type=['jpg', 'jpeg', 'png'], key=f"img1_{st.session_state.form_reset_key}")
        img_f2 = f_col2.file_uploader("Foto 2", type=['jpg', 'jpeg', 'png'], key=f"img2_{st.session_state.form_reset_key}")
        
        if st.button("GUARDAR TRABAJO"):
            if c_nom and p_nom:
                img1_64 = str(procesar_foto(img_f1)); img2_64 = str(procesar_foto(img_f2))
                id_u = datetime.now().strftime("%y%m%d%H%M%S")
                row = pd.DataFrame([{"ID": id_u, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total_preview, "Gramos": gr, "Horas": hr, "Notas": nts, "Imagen": img1_64, "Imagen2": img2_64}])
                conn.update(worksheet="Pedidos", data=pd.concat([df_p, row], ignore_index=True))
                conn.update(worksheet="Facturas", data=pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True))
                
                # CAMBIAMOS LA LLAVE PARA QUE TODO SE VACÍE SOLO
                st.session_state.form_reset_key += 1
                st.cache_data.clear()
                st.success("¡Guardado! Formulario limpio.")
                st.rerun()
            else:
                st.error("Rellena Cliente y Pieza.")

# --- 8. HISTORIAL Y 9. ESTADÍSTICAS (MANTENIDOS IGUAL) ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    items_f = df_f.sort_values(by="ID", ascending=True)
    for i, r in items_f.iterrows():
        with st.container():
            nota_texto_f = f"Notas: {r['Notas']}" if r['Notas'] else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {r['ID']}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p><p class="card-nota">{nota_texto_f}</p><p class="card-precio">Precio: {r['Precio']} €</p></div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if r['Imagen'] and len(str(r['Imagen'])) > 100: c1.image(f"data:image/jpeg;base64,{r['Imagen']}", use_container_width=True)
            if r['Imagen2'] and len(str(r['Imagen2'])) > 100: c2.image(f"data:image/jpeg;base64,{r['Imagen2']}", use_container_width=True)
            pdf_b = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Imagen'], r['Imagen2'])
            st.download_button("DESCARGAR 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"fpdf_{r['ID']}")
            st.divider()

elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Dashboard VYE3D</p>', unsafe_allow_html=True)
    if not df_f.empty:
        df_f['Precio'] = pd.to_numeric(df_f['Precio'], errors='coerce'); df_f['Gramos'] = pd.to_numeric(df_f['Gramos'], errors='coerce')
        df_f['Horas'] = pd.to_numeric(df_f['Horas'], errors='coerce'); df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Ventas", f"{df_f['Precio'].sum():.2f} €"); m2.metric("Gramos Usados", f"{df_f['Gramos'].sum()/1000:.2f} Kg"); m3.metric("Horas Totales", f"{df_f['Horas'].sum():.0f} h")
        st.divider(); st.subheader("📈 Ventas Mensuales")
        ventas_mes = df_f.set_index('Fecha_DT').resample('M')['Precio'].sum(); st.bar_chart(ventas_mes)

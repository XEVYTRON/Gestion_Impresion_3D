import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from io import BytesIO

# --- 1. UTILIDADES DE PDF (SÚPER SIMPLE) ---
def get_base64_logo(path):
    import base64
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except: return ""

def crear_pdf(id_f, fecha, cli, pie, tot, nts=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 7, txt=f"ID: {id_f} | Fecha: {fecha}", ln=True)
    pdf.cell(200, 7, txt=f"Cliente: {cli}", ln=True)
    pdf.cell(200, 7, txt=f"Trabajo: {pie}", ln=True)
    if nts and nts.strip() != "":
        pdf.ln(2); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 6, txt=f"Notas: {nts}")
    
    pdf.ln(10); pdf.set_font("Arial", 'B', 14)
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
    </style>
""", unsafe_allow_html=True)

# --- 4. DATOS (SÓLO TEXTO) ---
conn = st.connection("gsheets", type=GSheetsConnection)
if 'v_menu' not in st.session_state: st.session_state.v_menu = {}
if 'form_reset_key' not in st.session_state: st.session_state.form_reset_key = 0

@st.cache_data(ttl=2)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        
        # Columnas que queremos conservar (Ignoramos Imágenes)
        cols_validas = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Estado', 'Precio', 'Gramos', 'Horas', 'Notas']
        
        def limpiar_df(df, es_factura=False):
            # Quedarnos solo con las columnas que no sean de imagen
            columnas_existentes = [c for c in cols_validas if c in df.columns]
            if es_factura and 'Estado' in columnas_existentes: columnas_existentes.remove('Estado')
            df = df[columnas_existentes].copy()
            
            if 'ID' in df.columns:
                df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
            if 'Notas' in df.columns:
                df['Notas'] = df['Notas'].astype(str).replace(['nan', 'None', '0', '0.0'], '')
            for col in ['Gramos', 'Horas', 'Precio']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            return df

        return limpiar_df(p), limpiar_df(f, True)
    except: return None, None

df_p, df_f = cargar_datos()
if df_p is None: st.error("Fallo de conexión. Verifica tu Excel."); st.stop()

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
    busqueda = st.text_input("🔍 Buscar...", placeholder="Nombre o pieza").lower()
    filtro_estado = st.pills("Estado:", ESTADOS, default="Pendiente")
    
    items = df_p[df_p["Estado"] == filtro_estado].sort_values(by="ID", ascending=True)
    if busqueda:
        items = items[items['Cliente'].str.lower().str.contains(busqueda) | items['Pieza'].str.lower().str.contains(busqueda)]
    
    for i, r in items.iterrows():
        id_actual = str(r['ID'])
        ver = st.session_state.v_menu.get(id_actual, 0)
        with st.container():
            nota_texto = f"Notas: {r['Notas']}" if r['Notas'] and r['Notas'].strip() != "" else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {id_actual}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p><p class="card-nota">{nota_texto}</p><p class="card-precio">Precio: {r['Precio']} €</p></div>""", unsafe_allow_html=True)
            
            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"s_{id_actual}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_p.at[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p); st.cache_data.clear(); st.rerun()
            
            with st.expander("MODIFICAR ⚙️", key=f"e_{id_actual}_{ver}"):
                with st.form(f"f_ed_{id_actual}_{ver}"):
                    u_cli = st.text_input("Cliente", value=r['Cliente'])
                    u_pie = st.text_input("Pieza", value=r['Pieza'])
                    u_pre = st.number_input("Precio", value=float(r['Precio']))
                    u_not = st.text_area("Notas", value=r['Notas'])
                    
                    if st.form_submit_button("GUARDAR CAMBIOS"):
                        # Aseguramos que la nota sea texto limpio
                        nota_final = str(u_not).strip()
                        
                        # 1. Actualizar Pedidos
                        idx_p = df_p[df_p['ID'].astype(str) == id_actual].index
                        if not idx_p.empty:
                            df_p.at[idx_p[0], 'Cliente'] = u_cli
                            df_p.at[idx_p[0], 'Pieza'] = u_pie
                            df_p.at[idx_p[0], 'Precio'] = float(u_pre)
                            df_p.at[idx_p[0], 'Notas'] = nota_final
                            conn.update(worksheet="Pedidos", data=df_p)
                        
                        # 2. Actualizar Facturas
                        idx_f = df_f[df_f['ID'].astype(str) == id_actual].index
                        if not idx_f.empty:
                            df_f.at[idx_f[0], 'Cliente'] = u_cli
                            df_f.at[idx_f[0], 'Pieza'] = u_pie
                            df_f.at[idx_f[0], 'Precio'] = float(u_pre)
                            df_f.at[idx_f[0], 'Notas'] = nota_final
                            conn.update(worksheet="Facturas", data=df_f)
                        
                        st.session_state.v_menu[id_actual] = ver + 1
                        st.cache_data.clear()
                        st.success("¡Cambios guardados!")
                        st.rerun()

                if st.button("🗑️ ELIMINAR", key=f"d_{id_actual}"):
                    df_p = df_p[df_p['ID'].astype(str) != id_actual]; conn.update(worksheet="Pedidos", data=df_p)
                    df_f = df_f[df_f['ID'].astype(str) != id_actual]; conn.update(worksheet="Facturas", data=df_f)
                    st.cache_data.clear(); st.rerun()

            pdf_b = crear_pdf(id_actual, r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'])
            st.download_button("PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{id_actual}")
        st.divider()

# --- 7. VISTA: NUEVO TRABAJO ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    with st.container(key=f"cont_{st.session_state.form_reset_key}"):
        c_nom = st.text_input("Nombre Cliente", key=f"c_{st.session_state.form_reset_key}")
        p_nom = st.text_input("Pieza", key=f"p_{st.session_state.form_reset_key}")
        ca, cb = st.columns(2)
        gr = ca.number_input("Gramos", min_value=0.0, key=f"g_{st.session_state.form_reset_key}")
        hr = cb.number_input("Horas", min_value=0.0, key=f"h_{st.session_state.form_reset_key}")
        mgn = st.select_slider("Margen %", options=[0, 50, 100, 150, 200, 300], value=100, key=f"m_{st.session_state.form_reset_key}")
        total = ((0.024 * gr) + (hr * 1.0)) * (1 + mgn/100)
        st.markdown(f"### TOTAL ESTIMADO: {total:.2f} €")
        nts = st.text_area("Notas", key=f"n_{st.session_state.form_reset_key}")
        
        if st.button("GUARDAR TRABAJO"):
            if c_nom and p_nom:
                id_u = datetime.now().strftime("%y%m%d%H%M%S")
                row = pd.DataFrame([{"ID": id_u, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total, "Gramos": gr, "Horas": hr, "Notas": str(nts).strip()}])
                conn.update(worksheet="Pedidos", data=pd.concat([df_p, row], ignore_index=True))
                conn.update(worksheet="Facturas", data=pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True))
                st.session_state.form_reset_key += 1; st.cache_data.clear(); st.rerun()
            else: st.error("Rellena Cliente y Pieza")

# --- 8. HISTORIAL Y 9. ESTADÍSTICAS (SIMPLIFICADO) ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    items_f = df_f.sort_values(by="ID", ascending=True)
    for i, r in items_f.iterrows():
        with st.container():
            nota_f = f"Notas: {r['Notas']}" if r['Notas'] and r['Notas'].strip() != "" else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {r['ID']}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p><p class="card-nota">{nota_f}</p><p class="card-precio">Precio: {r['Precio']} €</p></div>""", unsafe_allow_html=True)
            pdf_b = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'])
            st.download_button("PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{r['ID']}")
            st.divider()

elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Dashboard</p>', unsafe_allow_html=True)
    if not df_f.empty:
        df_f['Precio'] = pd.to_numeric(df_f['Precio'], errors='coerce'); df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y")
        st.metric("Total Ventas", f"{df_f['Precio'].sum():.2f} €")
        ventas_mes = df_f.set_index('Fecha_DT').resample('M')['Precio'].sum(); st.bar_chart(ventas_mes)

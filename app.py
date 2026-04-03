import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from io import BytesIO

# --- CONFIGURACIÓN DE SEGURIDAD (Cambia tu contraseña aquí) ---
PASSWORD_APP = "xevy2024"

# --- 1. UTILIDADES DE PDF (CON SOPORTE PARA CARACTERES ESPAÑOLES) ---
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
    # Usamos latin-1 para compatibilidad con fpdf estándar y caracteres españoles
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    
    def limpiar_texto(t):
        # fpdf estándar necesita este encoding para tildes y ñ
        return str(t).encode('latin-1', 'replace').decode('latin-1')

    pdf.cell(200, 7, txt=limpiar_texto(f"ID: {id_f} | Fecha: {fecha}"), ln=True)
    pdf.cell(200, 7, txt=limpiar_texto(f"Cliente: {cli}"), ln=True)
    pdf.cell(200, 7, txt=limpiar_texto(f"Trabajo: {pie}"), ln=True)
    
    nts_limpia = str(nts) if nts and str(nts).lower() != 'nan' else ""
    if nts_limpia.strip() != "":
        pdf.ln(2); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 6, txt=limpiar_texto(f"Notas: {nts_limpia}"))
    
    pdf.ln(10); pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"TOTAL: {tot:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 2. INICIO DE LA APP ---
logo_b64 = get_base64_logo("image_7.png")
try: icon = Image.open("image_7.png")
except: icon = "🛠️"
st.set_page_config(page_title="Xevytron 3D", page_icon=icon, layout="centered")

# --- 3. LOGIN DE SEGURIDAD ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso VYE3D</h1>", unsafe_allow_html=True)
    pass_input = st.text_input("Introduce la contraseña para entrar", type="password")
    if st.button("ENTRAR"):
        if pass_input == PASSWORD_APP:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- 4. ESTILOS CSS ---
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
        .card-precio { font-size: 17px; color: #111 !important; font-weight: 900; margin-top: 8px; border-top: 1px solid #eee; padding-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. CONEXIÓN Y DATOS (CON DOBLE CACHÉ PARA ESTABILIDAD) ---
conn = st.connection("gsheets", type=GSheetsConnection)
if 'df_p' not in st.session_state: st.session_state.df_p = None
if 'df_f' not in st.session_state: st.session_state.df_f = None
if 'v_menu' not in st.session_state: st.session_state.v_menu = {}
if 'form_reset_key' not in st.session_state: st.session_state.form_reset_key = 0

def cargar_datos_gsheets():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        cols_p = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Estado', 'Precio', 'Gramos', 'Horas', 'Notas']
        cols_f = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas']
        
        def procesar(df, columnas):
            for col in columnas:
                if col not in df.columns: df[col] = ""
            df = df[columnas].copy()
            df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
            df['Notas'] = df['Notas'].astype(str).replace(['nan', 'None', '0', '0.0', 'NaN'], '')
            for col in ['Precio', 'Gramos', 'Horas']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            return df
        
        st.session_state.df_p = procesar(p, cols_p)
        st.session_state.df_f = procesar(f, cols_f)
    except:
        st.error("Error cargando Google Sheets")

if st.session_state.df_p is None:
    cargar_datos_gsheets()

df_p = st.session_state.df_p
df_f = st.session_state.df_f

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 6. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
nav_cols = st.columns(4)
if nav_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav_cols[2].button("HISTORIAL"): st.session_state.seccion = "FACTURAS"; st.rerun()
if nav_cols[3].button("📊"): st.session_state.seccion = "ESTADISTICAS"; st.rerun()
st.divider()

# --- 7. VISTA: TRABAJOS ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    busqueda = st.text_input("🔍 Buscar...", placeholder="Cliente o pieza").lower()
    filtro_estado = st.pills("Estado:", ESTADOS, default="Pendiente")
    
    items = df_p[df_p["Estado"] == filtro_estado].sort_values(by="ID", ascending=True)
    if busqueda:
        items = items[items['Cliente'].str.lower().str.contains(busqueda) | items['Pieza'].str.lower().str.contains(busqueda)]
    
    for i, r in items.iterrows():
        id_actual = str(r['ID'])
        ver = st.session_state.v_menu.get(id_actual, 0)
        with st.container():
            t_nota = str(r['Notas']).strip()
            html_nota = f'<p class="card-nota">Notas: {t_nota}</p>' if t_nota != "" else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {id_actual}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p>{html_nota}<p class="card-precio">Precio: {float(r['Precio']):.2f} €</p></div>""", unsafe_allow_html=True)
            
            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"s_{id_actual}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_p.at[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p)
                st.session_state.df_p = df_p # Actualizamos sesión
                st.rerun()
            
            with st.expander("MODIFICAR ⚙️", key=f"e_{id_actual}_{ver}"):
                with st.form(f"f_ed_{id_actual}_{ver}"):
                    u_cli = st.text_input("Cliente", value=r['Cliente'])
                    u_pie = st.text_input("Pieza", value=r['Pieza'])
                    u_pre = st.number_input("Precio", value=float(r['Precio']))
                    u_not = st.text_area("Notas", value=t_nota)
                    if st.form_submit_button("Ok"):
                        idx_p = df_p[df_p['ID'].astype(str) == id_actual].index
                        if not idx_p.empty:
                            df_p.at[idx_p[0], 'Cliente'] = u_cli; df_p.at[idx_p[0], 'Pieza'] = u_pie
                            df_p.at[idx_p[0], 'Precio'] = u_pre; df_p.at[idx_p[0], 'Notas'] = str(u_not).strip()
                            conn.update(worksheet="Pedidos", data=df_p)
                        idx_f = df_f[df_f['ID'].astype(str) == id_actual].index
                        if not idx_f.empty:
                            df_f.at[idx_f[0], 'Cliente'] = u_cli; df_f.at[idx_f[0], 'Pieza'] = u_pie
                            df_f.at[idx_f[0], 'Precio'] = u_pre; df_f.at[idx_f[0], 'Notas'] = str(u_not).strip()
                            conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_p = df_p; st.session_state.df_f = df_f
                        st.session_state.v_menu[id_actual] = ver + 1; st.rerun()

                # --- BORRADO SEGURO CON CONFIRMACIÓN ---
                conf_key = f"confirm_{id_actual}"
                if conf_key not in st.session_state: st.session_state[conf_key] = False
                
                if not st.session_state[conf_key]:
                    if st.button("🗑️ ELIMINAR", key=f"d_{id_actual}"):
                        st.session_state[conf_key] = True
                        st.rerun()
                else:
                    st.warning("¿Seguro que quieres borrar?")
                    c1, c2 = st.columns(2)
                    if c1.button("SÍ, BORRAR ✅", key=f"si_{id_actual}"):
                        df_p = df_p[df_p['ID'].astype(str) != id_actual]
                        df_f = df_f[df_f['ID'].astype(str) != id_actual]
                        conn.update(worksheet="Pedidos", data=df_p)
                        conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_p = df_p; st.session_state.df_f = df_f
                        st.session_state[conf_key] = False
                        st.rerun()
                    if c2.button("CANCELAR ❌", key=f"no_{id_actual}"):
                        st.session_state[conf_key] = False
                        st.rerun()

            pdf_b = crear_pdf(id_actual, r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'])
            st.download_button("PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{id_actual}")
        st.divider()

# --- 8. VISTA: NUEVO TRABAJO ---
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
                new_p = pd.concat([df_p, row], ignore_index=True)
                new_f = pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True)
                conn.update(worksheet="Pedidos", data=new_p)
                conn.update(worksheet="Facturas", data=new_f)
                st.session_state.df_p = new_p; st.session_state.df_f = new_f
                st.session_state.form_reset_key += 1; st.rerun()
            else: st.error("Rellena Cliente y Pieza")

# --- 9. HISTORIAL ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    items_f = df_f.sort_values(by="ID", ascending=True)
    for i, r in items_f.iterrows():
        with st.container():
            v_nota = str(r['Notas']).strip()
            h_nota = f'<p class="card-nota">Notas: {v_nota}</p>' if v_nota != "" else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {r['ID']}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p>{h_nota}<p class="card-precio">Precio: {float(r['Precio']):.2f} €</p></div>""", unsafe_allow_html=True)
            pdf_b = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'])
            st.download_button("PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_f_{r['ID']}")
            st.divider()

# --- 10. ESTADÍSTICAS ---
elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Dashboard</p>', unsafe_allow_html=True)
    if not df_f.empty:
        df_f['Precio'] = pd.to_numeric(df_f['Precio'], errors='coerce')
        df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y")
        st.metric("Total Ventas", f"{df_f['Precio'].sum():.2f} €")
        ventas_mes = df_f.set_index('Fecha_DT').resample('M')['Precio'].sum()
        st.bar_chart(ventas_mes)

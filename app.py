import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from io import BytesIO

# --- 1. SEGURIDAD CON SECRETS ---
# Si estás en local, Streamlit buscará en .streamlit/secrets.toml
# Si estás en la web, configurarlo en el panel de Streamlit Cloud
try:
    PASSWORD_APP = st.secrets["password"]
except:
    # Contraseña de emergencia por si no has configurado los Secrets aún
    PASSWORD_APP = "xevy2024"

# --- 2. UTILIDADES DE PDF ---
def crear_pdf(id_f, fecha, cli, pie, tot, nts=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    
    def limpiar_texto(t):
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

# --- 3. CONFIGURACIÓN E ICONO ---
try: icon = Image.open("image_7.png")
except: icon = "🛠️"
st.set_page_config(page_title="Xevytron 3D", page_icon=icon, layout="centered")

# --- 4. ACCESO DE SEGURIDAD ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso Xevytron 3D</h1>", unsafe_allow_html=True)
    pass_input = st.text_input("Contraseña", type="password")
    if st.button("ENTRAR"):
        if pass_input == PASSWORD_APP:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- 5. ESTILOS CSS ---
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

# --- 6. DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if 'df_p' not in st.session_state: st.session_state.df_p = None
if 'df_f' not in st.session_state: st.session_state.df_f = None
if 'form_reset_key' not in st.session_state: st.session_state.form_reset_key = 0

def cargar_datos_gsheets():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        cols_base = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas']
        
        def limpiar(df, con_estado=False):
            cols = cols_base + (['Estado'] if con_estado else [])
            for c in cols:
                if c not in df.columns: df[c] = ""
            df = df[cols].copy()
            df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).strip()
            df['Notas'] = df['Notas'].astype(str).replace(['nan', 'None', 'NaN'], '')
            for n in ['Precio', 'Gramos', 'Horas']:
                df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0.0)
            return df
        
        st.session_state.df_p = limpiar(p, True)
        st.session_state.df_f = limpiar(f, False)
    except:
        st.error("Error cargando Google Sheets")

if st.session_state.df_p is None:
    cargar_datos_gsheets()

df_p, df_f = st.session_state.df_p, st.session_state.df_f
ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 7. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
nav_cols = st.columns(4)
if nav_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav_cols[2].button("HISTORIAL"): st.session_state.seccion = "FACTURAS"; st.rerun()
if nav_cols[3].button("📊"): st.session_state.seccion = "ESTADISTICAS"; st.rerun()
st.divider()

# --- 8. VISTA: TRABAJOS ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    busqueda = st.text_input("🔍 Buscar...", placeholder="Cliente o pieza").lower()
    filtro_estado = st.pills("Estado:", ESTADOS, default="Pendiente")
    
    items = df_p[df_p["Estado"] == filtro_estado].sort_values(by="ID", ascending=True)
    if busqueda:
        items = items[items['Cliente'].str.lower().str.contains(busqueda) | items['Pieza'].str.lower().str.contains(busqueda)]
    
    for i, r in items.iterrows():
        id_act = str(r['ID'])
        with st.container():
            t_not = str(r['Notas']).strip()
            h_not = f'<p class="card-nota">Notas: {t_not}</p>' if t_not else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {id_act}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p>{h_not}<p class="card-precio">Precio: {r['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            
            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"s_{id_act}", label_visibility="collapsed")
            if nuevo_e != r['Estado']:
                df_p.at[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p)
                st.session_state.df_p = df_p; st.rerun()
            
            with st.expander("MODIFICAR ⚙️"):
                with st.form(f"f_{id_act}"):
                    u_cli = st.text_input("Cliente", value=r['Cliente'])
                    u_pie = st.text_input("Pieza", value=r['Pieza'])
                    u_pre = st.number_input("Precio", value=float(r['Precio']))
                    u_not = st.text_area("Notas", value=t_not)
                    if st.form_submit_button("Ok"):
                        idx_p = df_p[df_p['ID'].astype(str) == id_act].index
                        if not idx_p.empty:
                            df_p.at[idx_p[0], 'Cliente'] = u_cli; df_p.at[idx_p[0], 'Pieza'] = u_pie
                            df_p.at[idx_p[0], 'Precio'] = u_pre; df_p.at[idx_p[0], 'Notas'] = str(u_not).strip()
                            conn.update(worksheet="Pedidos", data=df_p)
                        idx_f = df_f[df_f['ID'].astype(str) == id_act].index
                        if not idx_f.empty:
                            df_f.at[idx_f[0], 'Cliente'] = u_cli; df_f.at[idx_f[0], 'Pieza'] = u_pie
                            df_f.at[idx_f[0], 'Precio'] = u_pre; df_f.at[idx_f[0], 'Notas'] = str(u_not).strip()
                            conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_p = df_p; st.session_state.df_f = df_f; st.rerun()

                # --- CONFIRMACIÓN DE BORRADO ---
                c_key = f"c_{id_act}"
                if c_key not in st.session_state: st.session_state[c_key] = False
                if not st.session_state[c_key]:
                    if st.button("🗑️ ELIMINAR", key=f"del_{id_act}"):
                        st.session_state[c_key] = True; st.rerun()
                else:
                    st.warning("¿Seguro?")
                    c1, c2 = st.columns(2)
                    if c1.button("SÍ ✅", key=f"si_{id_act}"):
                        df_p = df_p[df_p['ID'].astype(str) != id_act]
                        df_f = df_f[df_f['ID'].astype(str) != id_act]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_p = df_p; st.session_state.df_f = df_f; st.session_state[c_key] = False; st.rerun()
                    if c2.button("NO ❌", key=f"no_{id_act}"):
                        st.session_state[c_key] = False; st.rerun()

            pdf_b = crear_pdf(id_act, r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'])
            st.download_button("PDF 📩", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{id_act}")
        st.divider()

# --- 9. VISTA: NUEVO TRABAJO (CON PRECIO REAL) ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    with st.container(key=f"cont_{st.session_state.form_reset_key}"):
        c_n = st.text_input("Cliente", key=f"c_{st.session_state.form_reset_key}")
        p_n = st.text_input("Pieza", key=f"p_{st.session_state.form_reset_key}")
        ca, cb = st.columns(2)
        gr = ca.number_input("Gramos", min_value=0.0, key=f"g_{st.session_state.form_reset_key}")
        hr = cb.number_input("Horas", min_value=0.0, key=f"h_{st.session_state.form_reset_key}")
        mg = st.select_slider("Margen %", options=[0, 50, 100, 150, 200, 300], value=100, key=f"m_{st.session_state.form_reset_key}")
        tot = ((0.024 * gr) + (hr * 1.0)) * (1 + mg/100)
        st.markdown(f"### TOTAL: {tot:.2f} €")
        nt = st.text_area("Notas", key=f"n_{st.session_state.form_reset_key}")
        if st.button("GUARDAR"):
            if c_n and p_n:
                id_u = datetime.now().strftime("%y%m%d%H%M%S")
                row = pd.DataFrame([{"ID": id_u, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": c_n, "Pieza": p_n, "Estado": "Pendiente", "Precio": tot, "Gramos": gr, "Horas": hr, "Notas": str(nt).strip()}])
                new_p = pd.concat([df_p, row], ignore_index=True); new_f = pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True)
                conn.update(worksheet="Pedidos", data=new_p); conn.update(worksheet="Facturas", data=new_f)
                st.session_state.df_p = new_p; st.session_state.df_f = new_f; st.session_state.form_reset_key += 1; st.rerun()

# --- 10. HISTORIAL Y ESTADISTICAS ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    for i, r in df_f.sort_values(by="ID", ascending=True).iterrows():
        with st.container():
            n_t = str(r['Notas']).strip(); h_t = f'<p class="card-nota">Notas: {n_t}</p>' if n_t else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {r['ID']}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p>{h_t}<p class="card-precio">Precio: {r['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            pdf_f = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'])
            st.download_button("PDF 📩", data=pdf_f, file_name=f"F_{r['Cliente']}.pdf", key=f"pf_{r['ID']}")
            st.divider()

elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Estadísticas</p>', unsafe_allow_html=True)
    if not df_f.empty:
        st.metric("Total Ventas", f"{df_f['Precio'].sum():.2f} €")
        df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y")
        v_m = df_f.set_index('Fecha_DT').resample('M')['Precio'].sum()
        st.bar_chart(v_m)

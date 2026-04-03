import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from io import BytesIO

# --- 1. SEGURIDAD (SECRETS + ENLACE POR URL) ---
try:
    PASSWORD_APP = st.secrets["password"]
except:
    PASSWORD_APP = "xevy2024" 

# --- 2. UTILIDADES DE PDF (SOPORTE CARACTERES ESPAÑOLES) ---
def crear_pdf(id_factura, fecha, cliente, pieza, total, notas=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    
    def format_es(texto):
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    pdf.cell(200, 7, txt=format_es(f"ID: {id_factura} | Fecha: {fecha}"), ln=True)
    pdf.cell(200, 7, txt=format_es(f"Cliente: {cliente}"), ln=True)
    pdf.cell(200, 7, txt=format_es(f"Trabajo: {pieza}"), ln=True)
    
    # Limpieza para el PDF
    nota_pdf = str(notas).strip()
    if nota_pdf and nota_pdf.lower() != 'nan' and nota_pdf != '0.0':
        pdf.ln(2); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 6, txt=format_es(f"Notas: {nota_pdf}"))
    
    pdf.ln(10); pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"TOTAL: {total:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 3. CONFIGURACIÓN ---
try: icon = Image.open("image_7.png")
except: icon = "🛠️"
st.set_page_config(page_title="Xevytron 3D", page_icon=icon, layout="centered")

# --- 4. ACCESO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if "p" in st.query_params and st.query_params["p"] == PASSWORD_APP:
    st.session_state.autenticado = True

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

# --- 6. DATOS Y CONEXIÓN (FILTRO ANTI-NAN REFORZADO) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_y_formatear(df, con_estado=False):
    columnas_requeridas = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas']
    if con_estado: columnas_requeridas.append('Estado')
    
    # 1. Asegurar columnas
    for col in columnas_requeridas:
        if col not in df.columns: df[col] = ""
    
    df = df[columnas_requeridas].copy()
    
    # 2. LIMPIEZA AGRESIVA DE NAN
    df['Notas'] = df['Notas'].fillna('').astype(str)
    df['Notas'] = df['Notas'].replace(['nan', 'NaN', 'None', 'null', '0.0', '0'], '')
    # Filtro final por si acaso
    df['Notas'] = df['Notas'].apply(lambda x: "" if str(x).lower().strip() == "nan" else x)
    
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    for num_col in ['Precio', 'Gramos', 'Horas']:
        df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=2)
def cargar_datos_completos():
    try:
        p_raw = conn.read(worksheet="Pedidos", ttl=0)
        f_raw = conn.read(worksheet="Facturas", ttl=0)
        return limpiar_y_formatear(p_raw, True), limpiar_y_formatear(f_raw, False)
    except: return None, None

if 'df_pedidos' not in st.session_state: st.session_state.df_pedidos = None
if 'df_facturas' not in st.session_state: st.session_state.df_facturas = None
if 'form_reset_key' not in st.session_state: st.session_state.form_reset_key = 0

if st.session_state.df_pedidos is None:
    st.session_state.df_pedidos, st.session_state.df_facturas = cargar_datos_completos()

df_p, df_f = st.session_state.df_pedidos, st.session_state.df_facturas

if df_p is None:
    st.error("⚠️ Error de conexión."); st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 7. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
nav_cols = st.columns(4)
if nav_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav_cols[2].button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
if nav_cols[3].button("📊"): st.session_state.seccion = "ESTADISTICAS"; st.rerun()
st.divider()

# --- 8. VISTA: TRABAJOS ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    f_nom = st.text_input("🔍 Buscar...", placeholder="Cliente o pieza").lower()
    
    try: est_act = st.pills("Estado:", ESTADOS, default="Pendiente")
    except: est_act = st.selectbox("Estado:", ESTADOS)

    items = df_p[df_p["Estado"] == est_act].sort_values(by="ID", ascending=True)
    if f_nom:
        items = items[items['Cliente'].str.lower().str.contains(f_nom) | items['Pieza'].str.lower().str.contains(f_nom)]
    
    for i, row in items.iterrows():
        id_job = str(row['ID'])
        with st.container():
            # FILTRO VISUAL ANTI-NAN
            raw_nota = str(row['Notas']).strip()
            txt_nota = raw_nota if raw_nota.lower() != "nan" and raw_nota != "" else ""
            h_nota = f'<p class="card-nota">Notas: {txt_nota}</p>' if txt_nota else ""
            
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{row['Fecha']} | ID: {id_job}</p><p class="card-nombre">{row['Cliente']}</p><p class="card-pieza">Pieza: {row['Pieza']}</p>{h_not if 'h_not' in locals() else h_nota}<p class="card-precio">Precio: {row['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            
            upd_est = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(row['Estado']), key=f"st_{id_job}")
            if upd_est != row['Estado']:
                df_p.at[i, "Estado"] = upd_est
                conn.update(worksheet="Pedidos", data=df_p)
                st.session_state.df_pedidos = df_p; st.rerun()
            
            with st.expander("MODIFICAR ⚙️"):
                with st.form(f"fm_{id_job}"):
                    e_cli = st.text_input("Cliente", value=row['Cliente'])
                    e_pie = st.text_input("Pieza", value=row['Pieza'])
                    e_pre = st.number_input("Precio", value=float(row['Precio']))
                    e_not = st.text_area("Notas", value=txt_nota)
                    if st.form_submit_button("Guardar"):
                        df_p.loc[df_p['ID'].astype(str) == id_job, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [e_cli, e_pie, e_pre, str(e_not).strip()]
                        df_f.loc[df_f['ID'].astype(str) == id_job, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [e_cli, e_pie, e_pre, str(e_not).strip()]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f; st.rerun()

                # BORRADO SEGURO
                c_key = f"dk_{id_job}"
                if c_key not in st.session_state: st.session_state[c_key] = False
                if not st.session_state[c_key]:
                    if st.button("🗑️ ELIMINAR", key=f"bd_{id_job}"):
                        st.session_state[c_key] = True; st.rerun()
                else:
                    st.warning("¿Seguro?")
                    b1, b2 = st.columns(2)
                    if b1.button("SÍ ✅", key=f"cs_{id_job}"):
                        df_p = df_p[df_p['ID'].astype(str) != id_job]
                        df_f = df_f[df_f['ID'].astype(str) != id_job]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                        st.session_state[c_key] = False; st.rerun()
                    if b2.button("NO ❌", key=f"cn_{id_job}"):
                        st.session_state[c_key] = False; st.rerun()

            st.download_button("PDF 📩", data=crear_pdf(id_job, row['Fecha'], row['Cliente'], row['Pieza'], float(row['Precio']), row['Notas']), file_name=f"F_{row['Cliente']}.pdf", key=f"pb_{id_job}")
        st.divider()

# --- 9. VISTA: NUEVO TRABAJO ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    with st.container(key=f"cn_{st.session_state.form_reset_key}"):
        n_cli = st.text_input("Cliente", key=f"ic_{st.session_state.form_reset_key}")
        n_pie = st.text_input("Pieza", key=f"ip_{st.session_state.form_reset_key}")
        cg, ch = st.columns(2)
        gms = cg.number_input("Gramos", min_value=0.0, key=f"ig_{st.session_state.form_reset_key}")
        hrs = ch.number_input("Horas", min_value=0.0, key=f"ih_{st.session_state.form_reset_key}")
        mgn = st.select_slider("Margen %", options=[0, 50, 100, 150, 200, 300], value=100, key=f"im_{st.session_state.form_reset_key}")
        
        p_fin = ((0.024 * gms) + (hrs * 1.0)) * (1 + mgn/100)
        st.markdown(f"### TOTAL ESTIMADO: {p_fin:.2f} €")
        n_not = st.text_area("Notas", key=f"in_{st.session_state.form_reset_key}")
        
        if st.button("GUARDAR TRABAJO"):
            if n_cli and n_pie:
                id_n = datetime.now().strftime("%y%m%d%H%M%S")
                r_n = pd.DataFrame([{"ID": id_n, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": n_cli, "Pieza": n_pie, "Estado": "Pendiente", "Precio": p_fin, "Gramos": gms, "Horas": hrs, "Notas": str(n_not).strip()}])
                df_p = pd.concat([df_p, r_n], ignore_index=True)
                df_f = pd.concat([df_f, r_n.drop(columns=['Estado'])], ignore_index=True)
                conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                st.session_state.form_reset_key += 1; st.rerun()
            else: st.error("⚠️ Rellena Cliente y Pieza.")

# --- 10. FACTURAS ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial de Facturas</p>', unsafe_allow_html=True)
    b_fac = st.text_input("🔍 Buscar...", placeholder="Nombre o pieza").lower()
    items_f = df_f.sort_values(by="ID", ascending=True)
    if b_fac:
        items_f = items_f[items_f['Cliente'].str.lower().str.contains(b_fac) | items_f['Pieza'].str.lower().str.contains(b_fac)]
        
    for i, row in items_f.iterrows():
        with st.container():
            # FILTRO ANTI-NAN HISTORIAL
            rn_h = str(row['Notas']).strip()
            tn_h = rn_h if rn_h.lower() != "nan" and rn_h != "" else ""
            hn_h = f'<p class="card-nota">Notas: {tn_h}</p>' if tn_h else ""
            
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{row['Fecha']} | ID: {row['ID']}</p><p class="card-nombre">{row['Cliente']}</p><p class="card-pieza">Pieza: {row['Pieza']}</p>{hn_h}<p class="card-precio">Precio: {row['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            pdf_h = crear_pdf(row['ID'], row['Fecha'], row['Cliente'], row['Pieza'], float(row['Precio']), row['Notas'])
            st.download_button("PDF 📩", data=pdf_h, file_name=f"F_{row['Cliente']}.pdf", key=f"ph_{row['ID']}")
            st.divider()

# --- 11. ESTADÍSTICAS ---
elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Dashboard</p>', unsafe_allow_html=True)
    if not df_f.empty:
        st.metric("Total Ventas", f"{df_f['Precio'].sum():.2f} €")
        df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y")
        st.bar_chart(df_f.set_index('Fecha_DT').resample('M')['Precio'].sum())

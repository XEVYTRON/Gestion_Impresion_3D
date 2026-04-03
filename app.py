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
    
    nota_limpia = str(notas) if notas and str(notas).lower() != 'nan' else ""
    if nota_limpia.strip() != "":
        pdf.ln(2); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 6, txt=format_es(f"Notas: {nota_limpia}"))
    
    pdf.ln(10); pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"TOTAL: {total:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 3. CONFIGURACIÓN ---
try: icon = Image.open("image_7.png")
except: icon = "🛠️"
st.set_page_config(page_title="Xevytron 3D", page_icon=icon, layout="centered")

# --- 4. ACCESO (URL PARAMS + SESSION STATE) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# Revisar si la clave viene en la URL (?p=clave)
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

# --- 6. DATOS Y CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_y_formatear(df, con_estado=False):
    columnas_requeridas = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas']
    if con_estado: columnas_requeridas.append('Estado')
    
    for col in columnas_requeridas:
        if col not in df.columns: df[col] = ""
    
    df = df[columnas_requeridas].copy()
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df['Notas'] = df['Notas'].astype(str).replace(['nan', 'None', 'NaN', 'null', '0.0'], '')
    
    for num_col in ['Precio', 'Gramos', 'Horas']:
        df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=2)
def cargar_datos_completos():
    try:
        pedidos_raw = conn.read(worksheet="Pedidos", ttl=0)
        facturas_raw = conn.read(worksheet="Facturas", ttl=0)
        return limpiar_y_formatear(pedidos_raw, True), limpiar_y_formatear(facturas_raw, False)
    except: return None, None

# Inicialización de estados de sesión
if 'df_pedidos' not in st.session_state: st.session_state.df_pedidos = None
if 'df_facturas' not in st.session_state: st.session_state.df_facturas = None
if 'form_reset_key' not in st.session_state: st.session_state.form_reset_key = 0

if st.session_state.df_pedidos is None:
    st.session_state.df_pedidos, st.session_state.df_facturas = cargar_datos_completos()

df_p = st.session_state.df_pedidos
df_f = st.session_state.df_facturas

if df_p is None:
    st.error("⚠️ No se pudo conectar con Google Sheets."); st.stop()

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
    filtro_nombre = st.text_input("🔍 Buscar...", placeholder="Cliente o pieza").lower()
    
    try: estado_actual = st.pills("Estado:", ESTADOS, default="Pendiente")
    except: estado_actual = st.selectbox("Estado:", ESTADOS)

    items = df_p[df_p["Estado"] == estado_actual].sort_values(by="ID", ascending=True)
    if filtro_nombre:
        items = items[items['Cliente'].str.lower().str.contains(filtro_nombre) | items['Pieza'].str.lower().str.contains(filtro_nombre)]
    
    for i, row in items.iterrows():
        id_job = str(row['ID'])
        with st.container():
            txt_nota = str(row['Notas']).strip()
            html_nota = f'<p class="card-nota">Notas: {txt_nota}</p>' if txt_nota else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{row['Fecha']} | ID: {id_job}</p><p class="card-nombre">{row['Cliente']}</p><p class="card-pieza">Pieza: {row['Pieza']}</p>{html_nota}<p class="card-precio">Precio: {row['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            
            update_estado = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(row['Estado']), key=f"status_{id_job}")
            if update_estado != row['Estado']:
                df_p.at[i, "Estado"] = update_estado
                conn.update(worksheet="Pedidos", data=df_p)
                st.session_state.df_pedidos = df_p; st.rerun()
            
            with st.expander("MODIFICAR ⚙️"):
                with st.form(f"f_mod_{id_job}"):
                    c_edit = st.text_input("Cliente", value=row['Cliente'])
                    p_edit = st.text_input("Pieza", value=row['Pieza'])
                    pr_edit = st.number_input("Precio", value=float(row['Precio']))
                    n_edit = st.text_area("Notas", value=txt_nota)
                    if st.form_submit_button("Guardar"):
                        df_p.loc[df_p['ID'].astype(str) == id_job, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [c_edit, p_edit, pr_edit, str(n_edit).strip()]
                        df_f.loc[df_f['ID'].astype(str) == id_job, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [c_edit, p_edit, pr_edit, str(n_edit).strip()]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f; st.rerun()

                # BORRADO SEGURO
                confirm_key = f"del_ask_{id_job}"
                if confirm_key not in st.session_state: st.session_state[confirm_key] = False
                if not st.session_state[confirm_key]:
                    if st.button("🗑️ ELIMINAR", key=f"btn_del_{id_job}"):
                        st.session_state[confirm_key] = True; st.rerun()
                else:
                    st.warning("¿Seguro?")
                    b1, b2 = st.columns(2)
                    if b1.button("SÍ ✅", key=f"confirm_ok_{id_job}"):
                        df_p = df_p[df_p['ID'].astype(str) != id_job]
                        df_f = df_f[df_f['ID'].astype(str) != id_job]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                        st.session_state[confirm_key] = False; st.rerun()
                    if b2.button("NO ❌", key=f"confirm_no_{id_job}"):
                        st.session_state[confirm_key] = False; st.rerun()

            st.download_button("PDF 📩", data=crear_pdf(id_job, row['Fecha'], row['Cliente'], row['Pieza'], float(row['Precio']), row['Notas']), file_name=f"F_{row['Cliente']}.pdf", key=f"pdf_v_{id_job}")
        st.divider()

# --- 9. VISTA: NUEVO TRABAJO (FIXED KEY BUG) ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    
    with st.container(key=f"cont_new_{st.session_state.form_reset_key}"):
        nuevo_cliente = st.text_input("Nombre del Cliente", key=f"input_cli_{st.session_state.form_reset_key}")
        nueva_pieza = st.text_input("Nombre de la Pieza", key=f"input_pie_{st.session_state.form_reset_key}")
        col_g, col_h = st.columns(2)
        gramos = col_g.number_input("Gramos", min_value=0.0, key=f"input_gr_{st.session_state.form_reset_key}")
        horas = col_h.number_input("Horas", min_value=0.0, key=f"input_hr_{st.session_state.form_reset_key}")
        margen = st.select_slider("Margen %", options=[0, 50, 100, 150, 200, 300], value=100, key=f"input_mg_{st.session_state.form_reset_key}")
        
        precio_final = ((0.024 * gramos) + (horas * 1.0)) * (1 + margen/100)
        st.markdown(f"### TOTAL ESTIMADO: {precio_final:.2f} €")
        nuevas_notas = st.text_area("Notas", key=f"input_nt_{st.session_state.form_reset_key}")
        
        if st.button("GUARDAR TRABAJO"):
            if nuevo_cliente and nueva_pieza:
                id_nuevo = datetime.now().strftime("%y%m%d%H%M%S")
                row_new = pd.DataFrame([{
                    "ID": id_nuevo, "Fecha": datetime.now().strftime("%d/%m/%Y"), 
                    "Cliente": nuevo_cliente, "Pieza": nueva_pieza, "Estado": "Pendiente", 
                    "Precio": precio_final, "Gramos": gramos, "Horas": horas, "Notas": str(nuevas_notas).strip()
                }])
                df_p = pd.concat([df_p, row_new], ignore_index=True)
                df_f = pd.concat([df_f, row_new.drop(columns=['Estado'])], ignore_index=True)
                conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                st.session_state.form_reset_key += 1; st.rerun()
            else:
                st.error("⚠️ Debes rellenar el Cliente y la Pieza.")

# --- 10. HISTORIAL ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    for i, row in df_f.sort_values(by="ID", ascending=True).iterrows():
        with st.container():
            n_hist = str(row['Notas']).strip(); h_hist = f'<p class="card-nota">Notas: {n_hist}</p>' if n_hist else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{row['Fecha']} | ID: {row['ID']}</p><p class="card-nombre">{row['Cliente']}</p><p class="card-pieza">Pieza: {row['Pieza']}</p>{h_hist}<p class="card-precio">Precio: {row['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            pdf_data = crear_pdf(row['ID'], row['Fecha'], row['Cliente'], row['Pieza'], float(row['Precio']), row['Notas'])
            st.download_button("PDF 📩", data=pdf_data, file_name=f"F_{row['Cliente']}.pdf", key=f"btn_pdf_f_{row['ID']}")
            st.divider()

# --- 11. ESTADÍSTICAS ---
elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Dashboard</p>', unsafe_allow_html=True)
    if not df_f.empty:
        st.metric("Total Ventas", f"{df_f['Precio'].sum():.2f} €")
        df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y")
        v_mes = df_f.set_index('Fecha_DT').resample('M')['Precio'].sum()
        st.bar_chart(v_mes)

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from io import BytesIO

# --- 1. SEGURIDAD PRO (SECRETS + ENLACE MÁGICO) ---
try:
    PASSWORD_APP = st.secrets["password"]
except:
    PASSWORD_APP = "xevy2024" 

# --- 2. UTILIDADES DE PDF (SOPORTE Ñ Y TILDES) ---
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

# --- 4. CONTROL DE ACCESO (URL PARAMS + SESSION) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# Truco: Si entras con ?p=tu_clave en la URL, te logueas solo
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

# --- 6. GESTIÓN DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_tablas(df, incluye_estado=False):
    columnas_base = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas']
    columnas_final = columnas_base + (['Estado'] if incluye_estado else [])
    for col in columnas_final:
        if col not in df.columns: df[col] = ""
    df = df[columnas_final].copy()
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df['Notas'] = df['Notas'].astype(str).replace(['nan', 'None', 'NaN', 'null', '0.0'], '')
    for n in ['Precio', 'Gramos', 'Horas']:
        df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=2)
def cargar_desde_gsheets():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        return limpiar_tablas(p, True), limpiar_tablas(f, False)
    except: return None, None

if 'df_pedidos' not in st.session_state or st.session_state.df_pedidos is None:
    st.session_state.df_pedidos, st.session_state.df_facturas = cargar_desde_gsheets()

df_p = st.session_state.df_pedidos
df_f = st.session_state.df_facturas

if df_p is None:
    st.error("⚠️ Error de conexión con Google Sheets."); st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 7. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
cols_nav = st.columns(4)
if cols_nav[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if cols_nav[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if cols_nav[2].button("HISTORIAL"): st.session_state.seccion = "FACTURAS"; st.rerun()
if cols_nav[3].button("📊"): st.session_state.seccion = "ESTADISTICAS"; st.rerun()
st.divider()

# --- 8. VISTA: TRABAJOS ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    busqueda = st.text_input("🔍 Buscar...", placeholder="Cliente o pieza").lower()
    
    try: filtro_estado = st.pills("Estado:", ESTADOS, default="Pendiente")
    except: filtro_estado = st.selectbox("Estado:", ESTADOS)

    items = df_p[df_p["Estado"] == filtro_estado].sort_values(by="ID", ascending=True)
    if busqueda:
        items = items[items['Cliente'].str.lower().str.contains(busqueda) | items['Pieza'].str.lower().str.contains(busqueda)]
    
    for i, row in items.iterrows():
        id_actual = str(row['ID'])
        with st.container():
            nota_actual = str(row['Notas']).strip()
            html_nota = f'<p class="card-nota">Notas: {nota_actual}</p>' if nota_actual else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{row['Fecha']} | ID: {id_actual}</p><p class="card-nombre">{row['Cliente']}</p><p class="card-pieza">Pieza: {row['Pieza']}</p>{html_nota}<p class="card-precio">Precio: {row['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            
            nuevo_estado = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(row['Estado']), key=f"sel_{id_actual}")
            if nuevo_estado != row['Estado']:
                df_p.at[i, "Estado"] = nuevo_estado
                conn.update(worksheet="Pedidos", data=df_p)
                st.session_state.df_pedidos = df_p; st.rerun()
            
            with st.expander("MODIFICAR ⚙️"):
                with st.form(f"form_mod_{id_actual}"):
                    edit_cliente = st.text_input("Cliente", value=row['Cliente'])
                    edit_pieza = st.text_input("Pieza", value=row['Pieza'])
                    edit_precio = st.number_input("Precio", value=float(row['Precio']))
                    edit_notas = st.text_area("Notas", value=nota_actual)
                    if st.form_submit_button("Guardar Cambios"):
                        idx_p = df_p[df_p['ID'].astype(str) == id_actual].index
                        if not idx_p.empty:
                            df_p.at[idx_p[0], 'Cliente'] = edit_cliente
                            df_p.at[idx_p[0], 'Pieza'] = edit_pieza
                            df_p.at[idx_p[0], 'Precio'] = edit_precio
                            df_p.at[idx_p[0], 'Notas'] = str(edit_notas).strip()
                            conn.update(worksheet="Pedidos", data=df_p)
                        idx_f = df_f[df_f['ID'].astype(str) == id_actual].index
                        if not idx_f.empty:
                            df_f.at[idx_f[0], 'Cliente'] = edit_cliente
                            df_f.at[idx_f[0], 'Pieza'] = edit_pieza
                            df_f.at[idx_f[0], 'Precio'] = edit_precio
                            df_f.at[idx_f[0], 'Notas'] = str(edit_notas).strip()
                            conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f; st.rerun()

                # BORRADO SEGURO
                key_borrar = f"del_confirm_{id_actual}"
                if key_borrar not in st.session_state: st.session_state[key_borrar] = False
                if not st.session_state[key_borrar]:
                    if st.button("🗑️ ELIMINAR", key=f"btn_del_{id_actual}"):
                        st.session_state[key_borrar] = True; st.rerun()
                else:
                    st.warning("¿Seguro que quieres borrar?")
                    col_b1, col_b2 = st.columns(2)
                    if col_b1.button("SÍ, BORRAR ✅", key=f"confirm_si_{id_actual}"):
                        df_p = df_p[df_p['ID'].astype(str) != id_actual]
                        df_f = df_f[df_f['ID'].astype(str) != id_actual]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                        st.session_state[key_borrar] = False; st.rerun()
                    if col_b2.button("CANCELAR ❌", key=f"confirm_no_{id_actual}"):
                        st.session_state[key_borrar] = False; st.rerun()

            pdf_bytes = crear_pdf(id_actual, row['Fecha'], row['Cliente'], row['Pieza'], float(row['Precio']), row['Notas'])
            st.download_button("PDF 📩", data=pdf_bytes, file_name=f"F_{row['Cliente']}.pdf", key=f"pdf_btn_{id_actual}")
        st.divider()

# --- 9. VISTA: NUEVO TRABAJO (CON VALIDACIÓN Y NOMBRES CLAROS) ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    if 'form_key' not in st.session_state: st.session_state.form_key = 0
    
    with st.container(key=f"container_nuevo_{st.session_state.form_key}"):
        nuevo_cliente = st.text_input("Nombre del Cliente", key=f"input_cli_{st.session_state.form_reset_key}")
        nueva_pieza = st.text_input("Nombre de la Pieza", key=f"input_pie_{st.session_state.form_reset_key}")
        c_gr, c_hr = st.columns(2)
        gramos = c_gr.number_input("Gramos de material", min_value=0.0, key=f"input_gr_{st.session_state.form_reset_key}")
        horas = c_hr.number_input("Horas de impresión", min_value=0.0, key=f"input_hr_{st.session_state.form_reset_key}")
        margen = st.select_slider("Margen de beneficio %", options=[0, 50, 100, 150, 200, 300], value=100, key=f"input_mg_{st.session_state.form_reset_key}")
        
        precio_estimado = ((0.024 * gramos) + (horas * 1.0)) * (1 + margen/100)
        st.markdown(f"### TOTAL A COBRAR: {precio_estimado:.2f} €")
        nuevas_notas = st.text_area("Notas adicionales", key=f"input_nt_{st.session_state.form_reset_key}")
        
        if st.button("GUARDAR TRABAJO"):
            if nuevo_cliente and nueva_pieza:
                id_unico = datetime.now().strftime("%y%m%d%H%M%S")
                nueva_fila = pd.DataFrame([{
                    "ID": id_unico, "Fecha": datetime.now().strftime("%d/%m/%Y"), 
                    "Cliente": nuevo_cliente, "Pieza": nueva_pieza, "Estado": "Pendiente", 
                    "Precio": precio_estimado, "Gramos": gramos, "Horas": horas, "Notas": str(nuevas_notas).strip()
                }])
                df_p = pd.concat([df_p, nueva_fila], ignore_index=True)
                df_f = pd.concat([df_f, nueva_fila.drop(columns=['Estado'])], ignore_index=True)
                conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                st.session_state.form_reset_key += 1; st.rerun()
            else:
                # AQUÍ ESTÁ EL ERROR QUE FALTABA
                st.error("⚠️ Por favor, rellena al menos el Nombre del Cliente y la Pieza para poder guardar.")

# --- 10. HISTORIAL ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial de Trabajos</p>', unsafe_allow_html=True)
    for i, row in df_f.sort_values(by="ID", ascending=True).iterrows():
        with st.container():
            n_hist = str(row['Notas']).strip(); h_hist = f'<p class="card-nota">Notas: {n_hist}</p>' if n_hist else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{row['Fecha']} | ID: {row['ID']}</p><p class="card-nombre">{row['Cliente']}</p><p class="card-pieza">Pieza: {row['Pieza']}</p>{h_hist}<p class="card-precio">Precio: {row['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            pdf_hist = crear_pdf(row['ID'], row['Fecha'], row['Cliente'], row['Pieza'], float(row['Precio']), row['Notas'])
            st.download_button("PDF 📩", data=pdf_hist, file_name=f"F_{row['Cliente']}.pdf", key=f"btn_pdf_hist_{row['ID']}")
            st.divider()

# --- 11. ESTADÍSTICAS ---
elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Resumen de Ventas</p>', unsafe_allow_html=True)
    if not df_f.empty:
        st.metric("Ventas Totales", f"{df_f['Precio'].sum():.2f} €")
        df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y")
        ventas_mes = df_f.set_index('Fecha_DT').resample('M')['Precio'].sum()
        st.bar_chart(ventas_mes)

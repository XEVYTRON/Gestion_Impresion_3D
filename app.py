import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from PIL import Image
from io import BytesIO

# --- 1. SEGURIDAD ---
try:
    PASSWORD_APP = st.secrets["password"]
except:
    PASSWORD_APP = "xevy2024"

# --- 2. UTILIDADES DE PDF ---
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

    nota_limpia = str(notas).strip() if notas and str(notas).lower() != 'nan' else ""
    if nota_limpia != "":
        pdf.ln(2); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 6, txt=format_es(f"Notas: {nota_limpia}"))

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
        .badge-estado { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; background-color: #f1f3f5; color: #6f42c1; border: 1px solid #6f42c1; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 6. DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_df(df, con_estado=False):
    cols = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas']
    if con_estado: cols.append('Estado')
    for c in cols:
        if c not in df.columns: df[c] = ""
    df = df[cols].copy()
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df['Notas'] = df['Notas'].astype(str).replace(['nan', 'NaN', 'None', 'null', '0.0'], '')
    for n in ['Precio', 'Gramos', 'Horas']:
        df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=2)
def cargar_todo():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        return limpiar_df(p, True), limpiar_df(f, False)
    except: return None, None

if 'df_pedidos' not in st.session_state: st.session_state.df_pedidos = None
if 'df_facturas' not in st.session_state: st.session_state.df_facturas = None
if 'form_reset_key' not in st.session_state: st.session_state.form_reset_key = 0

if st.session_state.df_pedidos is None:
    st.session_state.df_pedidos, st.session_state.df_facturas = cargar_todo()

df_p, df_f = st.session_state.df_pedidos, st.session_state.df_facturas
if df_p is None: st.error("Error de conexión con Google Sheets."); st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# --- 7. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
n_cols = st.columns(4)
if n_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if n_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if n_cols[2].button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
if n_cols[3].button("📊"): st.session_state.seccion = "ESTADISTICAS"; st.rerun()
st.divider()

# --- 8. VISTA: TRABAJOS (CORREGIDO) ---
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Gestión de Trabajos</p>', unsafe_allow_html=True)
    
    # Buscador Global
    texto_buscar = st.text_input("🔍 Buscador Global (busca en cualquier estado)", value="").lower().strip()

    if texto_buscar:
        st.info(f"Mostrando resultados para: **{texto_buscar}**")
        # Filtramos en todo df_p sin importar el estado
        mask = (
            df_p['Cliente'].astype(str).str.lower().str.contains(texto_buscar, na=False) |
            df_p['Pieza'].astype(str).str.lower().str.contains(texto_buscar, na=False)
        )
        items_mostrar = df_p[mask].sort_values(by="ID", ascending=False)
    else:
        # Pestañas normales
        try: est_sel = st.pills("Estado:", ESTADOS, default="Pendiente")
        except: est_sel = st.selectbox("Estado:", ESTADOS)
        items_mostrar = df_p[df_p["Estado"] == est_sel].sort_values(by="ID", ascending=False)

    if items_mostrar.empty:
        st.warning("No se encontraron trabajos.")

    for idx, r in items_mostrar.iterrows():
        id_j = str(r['ID'])
        with st.container():
            n_t = str(r['Notas']).strip()
            # Badge de estado solo si estamos buscando
            badge = f'<div class="badge-estado">{r["Estado"]}</div>' if texto_buscar else ""
            html_n = f'<p class="card-nota">Notas: {n_t}</p>' if n_t else ""
            
            st.markdown(f"""<div class="card-container">
                {badge}
                <p class="card-fecha">{r['Fecha']} | ID: {id_j}</p>
                <p class="card-nombre">{r['Cliente']}</p>
                <p class="card-pieza">Pieza: {r['Pieza']}</p>
                {html_n}
                <p class="card-precio">Precio: {r['Precio']:.2f} €</p>
            </div>""", unsafe_allow_html=True)

            nuevo_e = st.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"s_{id_j}")
            if nuevo_e != r['Estado']:
                df_p.at[idx, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p)
                st.session_state.df_pedidos = df_p; st.rerun()
            
            with st.expander("MODIFICAR ⚙️"):
                with st.form(f"fm_{id_j}"):
                    ec = st.text_input("Cliente", value=r['Cliente'])
                    ep = st.text_input("Pieza", value=r['Pieza'])
                    epr = st.number_input("Precio", value=float(r['Precio']))
                    en = st.text_area("Notas", value=n_t)
                    if st.form_submit_button("Guardar"):
                        df_p.loc[df_p['ID'].astype(str) == id_j, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [ec, ep, epr, str(en).strip()]
                        df_f.loc[df_f['ID'].astype(str) == id_j, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [ec, ep, epr, str(en).strip()]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f; st.rerun()

                # BORRADO
                ck = f"dk_{id_j}"
                if ck not in st.session_state: st.session_state[ck] = False
                if not st.session_state[ck]:
                    if st.button("🗑️ ELIMINAR", key=f"bd_{id_j}"):
                        st.session_state[ck] = True; st.rerun()
                else:
                    st.warning("¿Seguro?")
                    b1, b2 = st.columns(2)
                    if b1.button("SÍ ✅", key=f"cs_{id_j}"):
                        df_p = df_p[df_p['ID'].astype(str) != id_j]
                        df_f = df_f[df_f['ID'].astype(str) != id_j]
                        conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                        st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                        st.session_state[ck] = False; st.rerun()
                    if b2.button("NO ❌", key=f"cn_{id_j}"):
                        st.session_state[ck] = False; st.rerun()

            st.download_button("PDF 📩", data=crear_pdf(id_j, r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas']), file_name=f"F_{r['Cliente']}.pdf", key=f"pdf_{id_j}")
        st.divider()

# --- 9. VISTA: NUEVO TRABAJO ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    with st.container(key=f"cn_{st.session_state.form_reset_key}"):
        nc = st.text_input("Cliente", key=f"ic_{st.session_state.form_reset_key}")
        np = st.text_input("Pieza", key=f"ip_{st.session_state.form_reset_key}")
        cg, ch = st.columns(2)
        gms = cg.number_input("Gramos", min_value=0.0, key=f"ig_{st.session_state.form_reset_key}")
        hrs = ch.number_input("Horas", min_value=0.0, key=f"ih_{st.session_state.form_reset_key}")
        mgn = st.select_slider("Margen %", options=[0, 50, 100, 150, 200, 300], value=100, key=f"im_{st.session_state.form_reset_key}")
        pf = ((0.024 * gms) + (hrs * 1.0)) * (1 + mgn/100)
        st.markdown(f"### TOTAL: {pf:.2f} €")
        nn = st.text_area("Notas", key=f"in_{st.session_state.form_reset_key}")
        if st.button("GUARDAR TRABAJO"):
            if nc and np:
                id_n = datetime.now().strftime("%y%m%d%H%M%S")
                row = pd.DataFrame([{"ID": id_n, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": nc, "Pieza": np, "Estado": "Pendiente", "Precio": pf, "Gramos": gms, "Horas": hrs, "Notas": str(nn).strip()}])
                df_p = pd.concat([df_p, row], ignore_index=True)
                df_f = pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True)
                conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
                st.session_state.df_pedidos, st.session_state.df_facturas = df_p, df_f
                st.session_state.form_reset_key += 1; st.rerun()
            else: st.error("Rellena Cliente y Pieza.")

# --- 10. FACTURAS ---
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial de Facturas</p>', unsafe_allow_html=True)
    bf = st.text_input("🔍 Buscar...", placeholder="Nombre o pieza").lower()
    df_f_f = df_f.copy()
    df_f_f['Fecha_DT'] = pd.to_datetime(df_f_f['Fecha'], format="%d/%m/%Y", errors='coerce')
    df_f_f = df_f_f.dropna(subset=['Fecha_DT'])
    if not df_f_f.empty:
        f_min, f_max = df_f_f['Fecha_DT'].min().date(), df_f_f['Fecha_DT'].max().date()
        c1, c2 = st.columns(2)
        d, h = c1.date_input("Desde", f_min), c2.date_input("Hasta", f_max)
        items_f = df_f_f[(df_f_f['Fecha_DT'].dt.date >= d) & (df_f_f['Fecha_DT'].dt.date <= h)].sort_values(by="ID", ascending=False)
    else: items_f = df_f.sort_values(by="ID", ascending=False)
    if bf:
        items_f = items_f[items_f['Cliente'].str.lower().str.contains(bf, na=False) | items_f['Pieza'].str.lower().str.contains(bf, na=False)]
    for i, r in items_f.iterrows():
        with st.container():
            nh = str(r['Notas']).strip(); hnh = f'<p class="card-nota">Notas: {nh}</p>' if nh else ""
            st.markdown(f"""<div class="card-container"><p class="card-fecha">{r['Fecha']} | ID: {r['ID']}</p><p class="card-nombre">{r['Cliente']}</p><p class="card-pieza">Pieza: {r['Pieza']}</p>{hnh}<p class="card-precio">Precio: {r['Precio']:.2f} €</p></div>""", unsafe_allow_html=True)
            pd_f = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'])
            st.download_button("PDF 📩", data=pd_f, file_name=f"F_{r['Cliente']}.pdf", key=f"ph_{r['ID']}")
            st.divider()

# --- 11. ESTADÍSTICAS ---
elif st.session_state.seccion == "ESTADISTICAS":
    st.markdown('<p class="titulo-seccion">Estadísticas</p>', unsafe_allow_html=True)
    if not df_f.empty:
        df_s = df_f.copy()
        df_s['Precio'] = pd.to_numeric(df_s['Precio'], errors='coerce').fillna(0.0)
        df_s['Fecha_DT'] = pd.to_datetime(df_s['Fecha'], format="%d/%m/%Y", errors='coerce')
        st.metric("Total Ventas", f"{df_s['Precio'].sum():.2f} €")
        vm = df_s.dropna(subset=['Fecha_DT']).set_index('Fecha_DT').resample('ME')['Precio'].sum()
        st.bar_chart(vm)

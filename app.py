import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="centered", initial_sidebar_state="collapsed")

# --- ESTILOS CSS (REPARACIÓN DE SCROLL Y MENÚ FIJO) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* FUENTE Y FONDO */
        html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

        /* TÍTULOS */
        .titulo-seccion { font-size: 22px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 20px; color: #333; }

        /* TARJETAS BLANCAS (INTOCABLES) */
        .card-container { 
            background-color: #ffffff !important; 
            border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; 
            border-left: 6px solid #6f42c1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
            margin-bottom: 5px;
        }
        .trabajo-fecha { font-size: 10px; color: #999; text-transform: uppercase; margin: 0; }
        .trabajo-cliente { font-size: 21px; font-weight: 800; color: #111; text-transform: uppercase; margin: 0; line-height: 1.1; }
        .trabajo-pieza { font-size: 16px; font-weight: 500; color: #555; margin: 0; }
        .trabajo-precio { font-size: 18px; color: #6f42c1; font-weight: bold; margin-top: 5px; }

        .factura-meta { font-size: 11px; color: #777; text-transform: uppercase; margin: 0; }
        .factura-cliente { font-size: 18px; font-weight: bold; color: #111; margin: 0; }
        .factura-detalle { font-size: 16px; color: #6f42c1; font-weight: bold; margin: 0; }

        /* BOTONES OSCUROS (ACCIONES) */
        [data-testid="stDownloadButton"] button, .stExpander > details > summary {
            background-color: #343a40 !important; color: white !important; border-radius: 8px !important; border: 1px solid #212529 !important;
            height: 2.8rem !important; display: flex; align-items: center; justify-content: center;
        }
        [data-testid="stDownloadButton"] button p { color: white !important; font-weight: bold; }
        .stExpander > details > summary svg { fill: white !important; }
        .stExpander { border: none !important; }

        /* BARRA DE NAVEGACIÓN INFERIOR (ESTABLE) */
        div[data-testid="stVerticalBlock"] > div:last-child {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            z-index: 9999;
            padding: 10px 5px 25px 5px;
            border-top: 2px solid #6f42c1;
            box-shadow: 0 -4px 15px rgba(0,0,0,0.1);
        }

        /* FORZAR FILA HORIZONTAL EN EL MENÚ */
        div[data-testid="stVerticalBlock"] > div:last-child [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 5px !important;
        }
        div[data-testid="stVerticalBlock"] > div:last-child [data-testid="column"] {
            flex: 1 !important;
            min-width: 0 !important;
        }

        /* BOTONES DEL MENÚ INFERIOR */
        div[data-testid="stVerticalBlock"] > div:last-child button {
            background-color: #343a40 !important; color: white !important;
            height: 3.5rem !important; font-size: 10px !important; font-weight: 700 !important;
            border-radius: 10px !important; border: 1px solid #212529 !important;
        }

        /* ESPACIO PARA QUE EL SCROLL NO QUEDE TAPADO ABAJO */
        .stApp { padding-bottom: 120px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        for df in [p, f]:
            if 'Notas' not in df.columns: df['Notas'] = ""
        return p, f
    except: return None, None

df_p, df_f = cargar_datos()

if df_p is None:
    st.error("Error de conexión. Espera un poco y refresca.")
    st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

def crear_pdf(id_fac, fecha, cli, pie, gr, hr, tot, nts=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, txt=f"ID: {id_fac} | Fecha: {fecha}", ln=True)
    pdf.cell(200, 8, txt=f"Cliente: {cli}", ln=True)
    pdf.cell(200, 8, txt=f"Trabajo: {pie}", ln=True)
    if nts:
        pdf.ln(5); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 8, txt=f"Notas: {nts}")
    pdf.ln(10); pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"TOTAL: {tot:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 3. LÓGICA DE NAVEGACIÓN
if 'seccion' not in st.session_state:
    st.session_state.seccion = "TRABAJOS"

# CONTENIDO SEGÚN SECCIÓN
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    filtro = st.pills("Estado:", ESTADOS, default="Pendiente")
    items = df_p[df_p["Estado"] == filtro]
    
    for i, r in items.iterrows():
        with st.container():
            c_dat, c_pdf, c_ed = st.columns([2.2, 0.7, 1.1])
            with c_dat:
                st.markdown(f'<div class="card-container"><p class="trabajo-fecha">{r["Fecha"]}</p><p class="trabajo-cliente">{r["Cliente"]}</p><p class="trabajo-pieza">{r["Pieza"]}</p><p class="trabajo-precio">{r["Precio"]} €</p></div>', unsafe_allow_html=True)
            with c_pdf:
                n_v = r['Notas'] if pd.notna(r['Notas']) else ""
                pdf_b = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), n_v)
                st.download_button("PDF", data=pdf_b, file_name=f"F_{r['Cliente']}.pdf", key=f"p_{r['ID']}")
            with c_ed:
                with st.expander("⚙️"):
                    with st.form(f"ed_{r['ID']}"):
                        u_cli = st.text_input("Cliente", value=r['Cliente'])
                        u_pie = st.text_input("Pieza", value=r['Pieza'])
                        u_pre = st.number_input("Precio (€)", value=float(r['Precio']))
                        u_not = st.text_area("Notas", value=r['Notas'] if pd.notna(r['Notas']) else "")
                        if st.form_submit_button("Ok"):
                            df_p.loc[i, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                            conn.update(worksheet="Pedidos", data=df_p)
                            # Sincronización con Facturas
                            df_f['ID_s'] = df_f['ID'].astype(str)
                            idx = df_f[df_f['ID_s'] == str(r['ID'])].index
                            if not idx.empty:
                                df_f.loc[idx, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                                conn.update(worksheet="Facturas", data=df_f.drop(columns=['ID_s']))
                            else:
                                nueva = pd.DataFrame([{"ID": r['ID'], "Fecha": r['Fecha'], "Cliente": u_cli, "Pieza": u_pie, "Precio": u_pre, "Gramos": r['Gramos'], "Horas": r['Horas'], "Notas": u_not}])
                                conn.update(worksheet="Facturas", data=pd.concat([df_f.drop(columns=['ID_s']), nueva], ignore_index=True))
                            st.cache_data.clear(); st.rerun()
                    if st.button("🗑️", key=f"del_{r['ID']}", type="primary"):
                        df_p = df_p.drop(i)
                        conn.update(worksheet="Pedidos", data=df_p)
                        st.cache_data.clear(); st.rerun()
            nuevo_e = st.select_slider("Mover:", options=ESTADOS, value=filtro, key=f"sl_{r['ID']}", label_visibility="collapsed")
            if nuevo_e != filtro:
                df_p.loc[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_p)
                st.cache_data.clear(); st.rerun()
        st.divider()

elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    c_nom = st.text_input("Cliente")
    p_nom = st.text_input("Pieza")
    ca, cb = st.columns(2)
    gr = ca.number_input("Gramos", min_value=0.0, step=1.0)
    hr = cb.number_input("Horas", min_value=0.0, step=0.5)
    mgn = st.select_slider("Margen %", options=[0, 25, 50, 75, 100, 150, 200, 300], value=100)
    total = ((24/1000 * gr) + (hr * 1.0)) * (1 + mgn/100)
    st.markdown(f"### TOTAL: {total:.2f} €")
    nts = st.text_area("Notas")
    if st.button("GUARDAR TRABAJO"):
        if c_nom and p_nom:
            f_h = datetime.now().strftime("%d/%m/%Y")
            id_u = datetime.now().strftime("%y%m%d%H%M%S")
            row = pd.DataFrame([{"ID": id_u, "Fecha": f_h, "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total, "Gramos": gr, "Horas": hr, "Notas": nts}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_p, row], ignore_index=True))
            conn.update(worksheet="Facturas", data=pd.concat([df_f, row.drop(columns=['Estado'])], ignore_index=True))
            st.cache_data.clear(); st.success("¡Guardado!"); st.rerun()

elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial</p>', unsafe_allow_html=True)
    for i, r in df_f.iloc[::-1].iterrows():
        with st.container():
            st.markdown(f'<div class="card-container"><p class="factura-meta">{r["Fecha"]} | ID: {r["ID"]}</p><p class="factura-cliente">{r["Cliente"]}</p><p class="factura-detalle">{r["Pieza"]} - {r["Precio"]} €</p></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                pdf_bytes = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), r['Notas'])
                st.download_button("📩 PDF", data=pdf_bytes, file_name=f"F_{r['Cliente']}.pdf", key=f"f_dl_{i}")
            with c2:
                if st.button("🗑️", key=f"f_del_{i}"):
                    df_f = df_f.drop(i)
                    conn.update(worksheet="Facturas", data=df_f)
                    st.cache_data.clear(); st.rerun()
            st.divider()

# 4. MENÚ INFERIOR FIJO (DEBE IR AL FINAL)
st.write("") # Espacio para empujar el menú
bot1, bot2, bot3 = st.columns(3)
with bot1:
    if st.button("TRABAJOS", key="m1"):
        st.session_state.seccion = "TRABAJOS"; st.rerun()
with bot2:
    if st.button("NUEVO", key="m2"):
        st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
with bot3:
    if st.button("FACTURAS", key="m3"):
        st.session_state.seccion = "FACTURAS"; st.rerun()

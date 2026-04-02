import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="centered", initial_sidebar_state="collapsed")

# --- ESTILOS CSS (BARRA INFERIOR FIJA Y HORIZONTAL) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
        
        .titulo-seccion { font-size: 22px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 20px; }
        
        /* Espacio al final para que el menú no tape el contenido */
        .main-content { margin-bottom: 120px; }

        /* MENÚ INFERIOR FIJO */
        div[data-testid="stVerticalBlock"] > div:last-child {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #ffffff;
            z-index: 1000;
            padding: 10px 5px 25px 5px;
            border-top: 2px solid #6f42c1;
            box-shadow: 0 -4px 15px rgba(0,0,0,0.15);
        }

        /* FORZAR COLUMNAS EN HORIZONTAL EN MÓVIL */
        div[data-testid="stVerticalBlock"] > div:last-child [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: 5px !important;
        }

        /* AJUSTE DE COLUMNAS INDIVIDUALES */
        div[data-testid="stVerticalBlock"] > div:last-child [data-testid="column"] {
            width: 32% !important;
            flex: 1 1 auto !important;
            min-width: 0 !important;
        }

        /* BOTONES DEL MENÚ (Gris Carbón Oscuro) */
        .stButton button { 
            width: 100%; height: 3.8rem; border-radius: 12px; font-weight: 700; 
            text-transform: uppercase; border: 1px solid #212529; 
            background-color: #343a40 !important; color: #ffffff !important;
            font-size: 10px !important; /* Texto algo más pequeño para que quepa bien */
            padding: 0px 2px !important;
        }

        /* TARJETAS BLANCAS */
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
        
        [data-testid="stDownloadButton"] button { 
            height: 2.8rem; width: 100%; border-radius: 8px; 
            background-color: #343a40 !important; border: 1px solid #212529 !important;
            color: #ffffff !important;
        }
        [data-testid="stDownloadButton"] button p { color: white !important; font-weight: bold; }

        .stExpander { border: none !important; }
        .stExpander > details > summary { 
            background-color: #343a40 !important; border-radius: 8px; 
            border: 1px solid #212529 !important; height: 2.8rem; 
            display: flex; align-items: center; justify-content: center;
        }
        .stExpander > details > summary svg { fill: white !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        for df in [p, f]:
            if 'Notas' not in df.columns: df['Notas'] = ""
        return p, f
    except:
        return None, None

df_pedidos, df_facturas = cargar_datos()

if df_pedidos is None:
    st.error("Error de conexión. Refresca la página.")
    st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# 3. LÓGICA DE PDF
def crear_factura_pdf(id_fac, fecha, cliente, pieza, gramos, horas, total, notas=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="XEVYTRON 3D - FACTURA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, txt=f"ID: {id_fac} | Fecha: {fecha}", ln=True)
    pdf.cell(200, 8, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 8, txt=f"Trabajo: {pieza}", ln=True)
    if notas:
        pdf.ln(5); pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 8, txt=f"Notas: {notas}")
    pdf.ln(10); pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {total:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 4. CONTENIDO PRINCIPAL
if 'seccion' not in st.session_state:
    st.session_state.seccion = "TRABAJOS"

st.markdown('<div class="main-content">', unsafe_allow_html=True)

if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    filtro = st.pills("Estado:", ESTADOS, default="Pendiente", key="nav_pills")
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    for i, r in items.iterrows():
        with st.container():
            col_dat, col_pdf, col_ed = st.columns([2.2, 0.7, 1.1])
            with col_dat:
                st.markdown(f'<div class="card-container"><p class="trabajo-fecha">{r["Fecha"]}</p><p class="trabajo-cliente">{r["Cliente"]}</p><p class="trabajo-pieza">{r["Pieza"]}</p><p class="trabajo-precio">{r["Precio"]} €</p></div>', unsafe_allow_html=True)
            with col_pdf:
                n_v = r['Notas'] if pd.notna(r['Notas']) else ""
                pdf = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), n_v)
                st.download_button("PDF", data=pdf, file_name=f"F_{r['Cliente']}.pdf", key=f"btn_p_{r['ID']}")
            with col_ed:
                with st.expander("⚙️"):
                    with st.form(f"f_edit_{r['ID']}"):
                        u_cli = st.text_input("Cliente", value=r['Cliente'])
                        u_pie = st.text_input("Pieza", value=r['Pieza'])
                        u_pre = st.number_input("Precio (€)", value=float(r['Precio']))
                        u_not = st.text_area("Notas", value=r['Notas'] if pd.notna(r['Notas']) else "")
                        if st.form_submit_button("Ok"):
                            df_pedidos.loc[i, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                            conn.update(worksheet="Pedidos", data=df_pedidos)
                            # Sincronizar factura
                            df_facturas['ID_s'] = df_facturas['ID'].astype(str)
                            idx = df_facturas[df_facturas['ID_s'] == str(r['ID'])].index
                            if not idx.empty:
                                df_facturas.loc[idx, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                                conn.update(worksheet="Facturas", data=df_facturas.drop(columns=['ID_s']))
                            else:
                                nueva_f = pd.DataFrame([{"ID": r['ID'], "Fecha": r['Fecha'], "Cliente": u_cli, "Pieza": u_pie, "Precio": u_pre, "Gramos": r['Gramos'], "Horas": r['Horas'], "Notas": u_not}])
                                conn.update(worksheet="Facturas", data=pd.concat([df_facturas.drop(columns=['ID_s']), nueva_f], ignore_index=True))
                            st.cache_data.clear(); st.rerun()
                    if st.button("🗑️", key=f"btn_del_{r['ID']}", type="primary"):
                        df_pedidos = df_pedidos.drop(i)
                        conn.update(worksheet="Pedidos", data=df_pedidos)
                        st.cache_data.clear(); st.rerun()
            nuevo_e = st.select_slider("Mover:", options=ESTADOS, value=filtro, key=f"btn_sl_{r['ID']}", label_visibility="collapsed")
            if nuevo_e != filtro:
                df_pedidos.loc[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_pedidos)
                st.cache_data.clear(); st.rerun()
        st.divider()

elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    c_nom = st.text_input("Cliente")
    p_nom = st.text_input("Pieza")
    ca, cb = st.columns(2)
    gr = ca.number_input("Gramos", min_value=0.0, step=1.0)
    hr = cb.number_input("Horas", min_value=0.0, step=0.5)
    mgn = st.select_slider("Margen %", options=[0, 25, 50, 75, 100, 150, 200], value=100)
    total = ((24/1000 * gr) + (hr * 1.0)) * (1 + mgn/100)
    st.markdown(f"### TOTAL: {total:.2f} €")
    nts = st.text_area("Notas")
    if st.button("GUARDAR TRABAJO"):
        if c_nom and p_nom:
            f_h = datetime.now().strftime("%d/%m/%Y")
            id_u = datetime.now().strftime("%y%m%d%H%M%S")
            row = pd.DataFrame([{"ID": id_u, "Fecha": f_h, "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total, "Gramos": gr, "Horas": hr, "Notas": nts}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, row], ignore_index=True))
            conn.update(worksheet="Facturas", data=pd.concat([df_facturas, row.drop(columns=['Estado'])], ignore_index=True))
            st.cache_data.clear(); st.success("Guardado"); st.rerun()

elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Historial de Facturas</p>', unsafe_allow_html=True)
    for i, r in df_facturas.iloc[::-1].iterrows():
        with st.container():
            st.markdown(f'<div class="card-container"><p class="factura-meta">{r["Fecha"]} | ID: {r["ID"]}</p><p class="factura-cliente">{r["Cliente"]}</p><p class="factura-detalle">{r["Pieza"]} - {r["Precio"]} €</p></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                pdf = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), r['Notas'])
                st.download_button("📩 PDF", data=pdf, file_name=f"F_{r['Cliente']}.pdf", key=f"f_dl_btn_{i}")
            with c2:
                if st.button("🗑️", key=f"f_del_btn_{i}"):
                    df_facturas = df_facturas.drop(i)
                    conn.update(worksheet="Facturas", data=df_facturas)
                    st.cache_data.clear(); st.rerun()
            st.divider()

st.markdown('</div>', unsafe_allow_html=True)

# 5. MENÚ FIJO (Obligado a estar en fila)
st.write("") # Espaciador
bot_nav1, bot_nav2, bot_nav3 = st.columns(3)
with bot_nav1:
    if st.button("TRABAJOS", key="f_nav_1"):
        st.session_state.seccion = "TRABAJOS"
        st.rerun()
with bot_nav2:
    if st.button("NUEVO", key="f_nav_2"):
        st.session_state.seccion = "NUEVO TRABAJO"
        st.rerun()
with bot_nav3:
    if st.button("FACTURAS", key="f_nav_3"):
        st.session_state.seccion = "FACTURAS"
        st.rerun()

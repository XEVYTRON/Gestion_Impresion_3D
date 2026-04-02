import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="centered", initial_sidebar_state="collapsed")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
        .titulo-seccion { font-size: 22px; font-weight: bold; text-align: center; text-transform: uppercase; margin-bottom: 20px; }
        .stButton button { width: 100%; height: 3rem; border-radius: 8px; font-weight: 600; text-transform: uppercase; border: 1px solid #ddd; }
        .card-container { background-color: #fff; border-radius: 10px; padding: 12px; border: 1px solid #e0e0e0; border-left: 5px solid #6f42c1; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .trabajo-fecha { font-size: 10px; color: #999; text-transform: uppercase; margin: 0; }
        .trabajo-cliente { font-size: 19px; font-weight: 800; color: #111; text-transform: uppercase; margin: 0; }
        .trabajo-pieza { font-size: 15px; font-weight: 500; color: #555; margin: 0; }
        .trabajo-precio { font-size: 17px; color: #6f42c1; font-weight: bold; margin-top: 3px; }
        .factura-meta { font-size: 11px; color: #777; text-transform: uppercase; margin: 0; }
        .factura-cliente { font-size: 18px; font-weight: bold; color: #111; margin: 0; }
        .factura-detalle { font-size: 16px; color: #6f42c1; font-weight: bold; margin: 0; }
        [data-testid="stDownloadButton"] button { height: 2.8rem; width: 100%; border-radius: 8px; background-color: #f8f9fa; }
        .stExpander > details > summary { background-color: #f8f9fa; border-radius: 8px; border: 1px solid #ddd; height: 2.8rem; display: flex; align-items: center; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN (CON SEGURO DE ERRORES)
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_seguro():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        # Aseguramos que la columna Notas exista
        if 'Notas' not in p.columns: p['Notas'] = ""
        if 'Notas' not in f.columns: f['Notas'] = ""
        return p, f
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df_pedidos, df_facturas = cargar_seguro()

if df_pedidos is None:
    st.warning("⚠️ La app no puede leer tu Google Sheets. Revisa los nombres de las pestañas.")
    st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# 3. LÓGICA PDF
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
    pdf.ln(5)
    pdf.cell(200, 8, txt=f"- Material: {gramos} g | - Tiempo: {horas} h", ln=True)
    if notas:
        pdf.ln(5)
        pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(200, 8, txt=f"Notas: {notas}")
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {total:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 4. NAVEGACIÓN
if 'seccion' not in st.session_state:
    st.session_state.seccion = "TRABAJOS"

nav1, nav2, nav3 = st.columns(3)
if nav1.button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if nav2.button("NUEVO TRABAJO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if nav3.button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
st.divider()

# 5. VISTA: TRABAJOS
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    filtro = st.pills("Estado:", ESTADOS, default="Pendiente", label_visibility="collapsed")
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    for i, r in items.iterrows():
        with st.container():
            col_dat, col_pdf, col_ed = st.columns([2.2, 0.6, 1.2])
            with col_dat:
                st.markdown(f'<div class="card-container"><p class="trabajo-fecha">{r["Fecha"]}</p><p class="trabajo-cliente">{r["Cliente"]}</p><p class="trabajo-pieza">{r["Pieza"]}</p><p class="trabajo-precio">{r["Precio"]} €</p></div>', unsafe_allow_html=True)
            with col_pdf:
                n_v = r['Notas'] if pd.notna(r['Notas']) else ""
                pdf = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), n_v)
                st.download_button("📄", data=pdf, file_name=f"Fac_{r['Cliente']}.pdf", key=f"p_{r['ID']}")
            with col_ed:
                with st.expander("⚙️"):
                    with st.form(f"e_{r['ID']}"):
                        u_cli = st.text_input("Cliente", value=r['Cliente'])
                        u_pie = st.text_input("Pieza", value=r['Pieza'])
                        u_pre = st.number_input("Precio (€)", value=float(r['Precio']))
                        u_not = st.text_area("Notas", value=r['Notas'] if pd.notna(r['Notas']) else "")
                        if st.form_submit_button("Ok"):
                            df_pedidos.loc[i, ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                            conn.update(worksheet="Pedidos", data=df_pedidos)
                            if not df_facturas.empty:
                                df_facturas.loc[df_facturas['ID'] == r['ID'], ['Cliente', 'Pieza', 'Precio', 'Notas']] = [u_cli, u_pie, u_pre, u_not]
                                conn.update(worksheet="Facturas", data=df_facturas)
                            st.cache_data.clear(); st.rerun()
                    if st.button("🗑️", key=f"d_{r['ID']}", type="primary"):
                        df_pedidos = df_pedidos.drop(i)
                        conn.update(worksheet="Pedidos", data=df_pedidos)
                        st.cache_data.clear(); st.rerun()
            nuevo_e = st.select_slider("Estado:", options=ESTADOS, value=filtro, key=f"s_{r['ID']}", label_visibility="collapsed")
            if nuevo_e != filtro:
                df_pedidos.loc[i, "Estado"] = nuevo_e
                conn.update(worksheet="Pedidos", data=df_pedidos)
                st.cache_data.clear(); st.rerun()
        st.divider()

# 6. VISTA: NUEVO TRABAJO
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
    if st.button("GUARDAR"):
        if c_nom and p_nom:
            f_h = datetime.now().strftime("%d/%m/%Y")
            id_n = int(df_pedidos["ID"].max() + 1 if not df_pedidos.empty else 1)
            row = pd.DataFrame([{"ID": id_n, "Fecha": f_h, "Cliente": c_nom, "Pieza": p_nom, "Estado": "Pendiente", "Precio": total, "Gramos": gr, "Horas": hr, "Notas": nts}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, row], ignore_index=True))
            conn.update(worksheet="Facturas", data=pd.concat([df_facturas, row.drop(columns=['Estado'])], ignore_index=True))
            st.cache_data.clear(); st.success("Guardado"); st.rerun()

# 7. VISTA: FACTURAS
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Facturas</p>', unsafe_allow_html=True)
    for i, r in df_facturas.iloc[::-1].iterrows():
        with st.container():
            st.markdown(f'<div class="card-container"><p class="factura-meta">{r["Fecha"]} | ID: {r["ID"]}</p><p class="factura-cliente">{r["Cliente"]}</p><p class="factura-detalle">{r["Pieza"]} - {r["Precio"]} €</p></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                pdf = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']), r['Notas'])
                st.download_button("📩 PDF", data=pdf, file_name=f"F_{r['Cliente']}.pdf", key=f"df_{i}")
            with c2:
                if st.button("🗑️", key=f"bf_{i}"):
                    df_facturas = df_facturas.drop(i)
                    conn.update(worksheet="Facturas", data=df_facturas)
                    st.cache_data.clear(); st.rerun()
            st.divider()

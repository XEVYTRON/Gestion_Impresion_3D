import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="centered", initial_sidebar_state="collapsed")

# --- ESTILOS CSS UNIFICADOS (MOBILE FIRST) ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        html, body, [class*="css"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        
        .titulo-seccion {
            font-size: 22px; font-weight: bold; color: #333;
            margin-bottom: 20px; text-align: center; text-transform: uppercase;
        }
        
        .stButton button {
            width: 100%; height: 3rem; border-radius: 8px; font-size: 14px;
            font-weight: 600; text-transform: uppercase; border: 1px solid #ddd;
        }
        
        .card-container {
            background-color: #fff; border-radius: 10px; padding: 15px;
            border: 1px solid #e0e0e0; border-left: 5px solid #007bff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 5px;
        }
        .cliente-txt { font-size: 11px; color: #777; text-transform: uppercase; margin: 0; }
        .pieza-txt { font-size: 18px; font-weight: bold; color: #111; margin: 0; }
        .precio-txt { font-size: 16px; color: #28a745; font-weight: bold; margin: 0; }
        
        [data-testid="stDownloadButton"] button {
            height: 2.5rem; padding: 0; border-radius: 5px; background-color: #f8f9fa;
        }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos")
        f = conn.read(worksheet="Facturas")
        return p, f
    except:
        return None, None

df_pedidos, df_facturas = cargar_datos()

if df_pedidos is None:
    st.error("⚠️ Error: Revisa que las pestañas 'Pedidos' y 'Facturas' existan en Google Sheets.")
    st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# 3. LÓGICA DE PDF
def crear_factura_pdf(id_fac, fecha, cliente, pieza, gramos, horas, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FACTURA / PRESUPUESTO XEVYTRON 3D", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, txt=f"ID: {id_fac} | Fecha: {fecha}", ln=True)
    pdf.cell(200, 8, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 8, txt=f"Trabajo: {pieza}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 8, txt=f"- Material: {gramos} gramos", ln=True)
    pdf.cell(200, 8, txt=f"- Tiempo: {horas} horas", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {total:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 4. NAVEGACIÓN
if 'seccion' not in st.session_state:
    st.session_state.seccion = "TRABAJOS"

c1, c2, c3 = st.columns(3)
if c1.button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if c2.button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if c3.button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
st.divider()

# 5. VISTA: TRABAJOS
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos Activos</p>', unsafe_allow_html=True)
    filtro = st.pills("Estado:", ESTADOS, default="Pendiente", label_visibility="collapsed")
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    if items.empty:
        st.info(f"No hay trabajos en {filtro}")
    else:
        for i, r in items.iterrows():
            with st.container():
                col_datos, col_pdf = st.columns([4, 1])
                with col_datos:
                    st.markdown(f"""
                        <div style="padding-left: 5px;">
                            <p class="cliente-txt">{r['Cliente']}</p>
                            <p class="pieza-txt">{r['Pieza']}</p>
                            <p class="precio-txt">{r['Precio']} €</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col_pdf:
                    pdf_b = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']))
                    st.download_button("📄", data=pdf_b, file_name=f"Factura_{r['Cliente']}.pdf", key=f"pdf_{r['ID']}")
                
                nuevo_e = st.select_slider("Estado:", options=ESTADOS, value=filtro, key=f"sl_{r['ID']}", label_visibility="collapsed")
                if nuevo_e != filtro:
                    df_pedidos.loc[i, "Estado"] = nuevo_e
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear(); st.rerun()
                
                with st.expander("Editar / Borrar"):
                    with st.form(f"edit_{r['ID']}"):
                        e_cli = st.text_input("Cliente", value=r['Cliente'])
                        e_pie = st.text_input("Pieza", value=r['Pieza'])
                        e_pre = st.number_input("Precio (€)", value=float(r['Precio']))
                        if st.form_submit_button("Actualizar"):
                            df_pedidos.loc[i, ['Cliente', 'Pieza', 'Precio']] = [e_cli, e_pie, e_pre]
                            conn.update(worksheet="Pedidos", data=df_pedidos)
                            st.cache_data.clear(); st.rerun()
                    if st.button("🗑️ Eliminar Trabajo", key=f"del_{r['ID']}", type="primary"):
                        df_pedidos = df_pedidos.drop(i)
                        conn.update(worksheet="Pedidos", data=df_pedidos)
                        st.cache_data.clear(); st.rerun()
            st.divider()

# 6. VISTA: NUEVO TRABAJO
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    with st.form("crear"):
        cliente = st.text_input("Cliente")
        pieza = st.text_input("Pieza")
        c_a, c_b = st.columns(2)
        gramos = c_a.number_input("Gramos", min_value=0.0)
        horas = c_b.number_input("Horas", min_value=0.0)
        margen = st.select_slider("Margen %", options=[0, 50, 100, 150, 200], value=100)
        
        precio_calc = ((24/1000 * gramos) + (horas * 1.0)) * (1 + margen/100)
        p_final = st.number_input("Precio Final (€)", value=float(round(precio_calc, 2)))
        
        if st.form_submit_button("GUARDAR TRABAJO Y FACTURA"):
            if cliente and pieza:
                f_hoy = datetime.now().strftime("%d/%m/%Y")
                id_n = int(df_pedidos["ID"].max() + 1 if not df_pedidos.empty else 1)
                
                nuevo_p = pd.DataFrame([{"ID": id_n, "Fecha": f_hoy, "Cliente": cliente, "Pieza": pieza, "Estado": "Pendiente", "Precio": p_final, "Gramos": gramos, "Horas": horas, "Notas": ""}])
                nueva_f = pd.DataFrame([{"ID": id_n, "Fecha": f_hoy, "Cliente": cliente, "Pieza": pieza, "Precio": p_final, "Gramos": gramos, "Horas": horas}])
                
                conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_p], ignore_index=True))
                conn.update(worksheet="Facturas", data=pd.concat([df_facturas, nueva_f], ignore_index=True))
                st.cache_data.clear(); st.success("¡Guardado!")
            else: st.warning("Faltan datos.")

# 7. VISTA: FACTURAS (CON OPCIÓN DE BORRAR)
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Registro de Facturas</p>', unsafe_allow_html=True)
    if df_facturas.empty:
        st.info("No hay facturas registradas.")
    else:
        # Mostramos las facturas de más reciente a más antigua
        df_inv = df_facturas.iloc[::-1]
        for i, r in df_inv.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="card-container" style="border-left-color: #6f42c1;">
                    <p class="cliente-txt">{r['Fecha']} | ID: {r['ID']}</p>
                    <p class="pieza-txt">{r['Cliente']}</p>
                    <p class="precio-txt" style="color: #6f42c1;">{r['Pieza']} - {r['Precio']} €</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Botón de Descarga
                pdf_bytes = crear_factura_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Gramos'], r['Horas'], float(r['Precio']))
                st.download_button("📩 Descargar PDF", data=pdf_bytes, file_name=f"Factura_{r['Cliente']}.pdf", key=f"dl_f_{i}")
                
                # NUEVO: Botón de Borrar Factura
                if st.button("🗑️ Borrar esta Factura", key=f"del_f_{i}", type="secondary"):
                    # Eliminamos la fila por su índice original
                    df_facturas = df_facturas.drop(i)
                    conn.update(worksheet="Facturas", data=df_facturas)
                    st.cache_data.clear()
                    st.success("Factura eliminada.")
                    st.rerun()
                
                st.divider()

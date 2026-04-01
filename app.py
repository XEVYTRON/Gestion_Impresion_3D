import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="wide", initial_sidebar_state="collapsed")

# Estilos CSS corregidos para asegurar visibilidad
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {display:none;}
        .main-content {margin-bottom: 120px;}
        .nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            padding: 10px 0;
            display: flex;
            justify-content: space-around;
            border-top: 1px solid #ddd;
            z-index: 9999;
        }
        .stButton button { width: 100%; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN INTELIGENTE
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def cargar_todo():
    try:
        # Intentamos leer la hoja completa y luego separamos por pestañas
        # Esto es más seguro que buscarlas por nombre individual
        peds = conn.read(worksheet="Pedidos")
        pres = conn.read(worksheet="Presupuestos")
        return peds, pres
    except:
        return None, None

df_pedidos, df_presus = cargar_todo()

# Si falla la carga, mostramos un aviso claro
if df_pedidos is None:
    st.error("⚠️ Error de conexión. Revisa que en Google Sheets las pestañas se llamen 'Pedidos' y 'Presupuestos'.")
    st.info("Si los nombres están bien, ve a Streamlit Cloud > Settings > Secrets y pega de nuevo tus claves.")
    st.stop()

# 3. LÓGICA PDF
def crear_pdf(cliente, pieza, coste_mat, coste_tiem, precio_fin):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="PRESUPUESTO 3D", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 10, txt=f"Pieza: {pieza}", ln=True)
    pdf.cell(200, 10, txt=f"Precio: {precio_fin:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 4. NAVEGACIÓN (ESTADO DE SESIÓN)
if 'menu' not in st.session_state:
    st.session_state.menu = "Producción"

# 5. CONTENIDO
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.title("🛠️ Xevytron 3D")

if st.session_state.menu == "Calculadora":
    st.header("🧮 Calcular")
    c_n = st.text_input("Cliente")
    p_n = st.text_input("Pieza")
    g = st.number_input("Gramos", 0.0)
    h = st.number_input("Horas", 0.0)
    if st.button("✅ GUARDAR"):
        precio = ((24/1000*g) + (h*1.5)) * 2
        new_ped = pd.DataFrame([{"ID": len(df_pedidos)+1, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": c_n, "Pieza": p_n, "Estado": "Pendiente", "Precio": precio, "Gramos": g, "Horas": h, "Notas": ""}])
        updated = pd.concat([df_pedidos, new_ped], ignore_index=True)
        conn.update(worksheet="Pedidos", data=updated)
        st.success("¡Guardado!")
        st.cache_data.clear()
        st.rerun()

elif st.session_state.menu == "Historial":
    st.header("📂 Presupuestos")
    st.write("Aquí verás tus presupuestos guardados.")
    st.dataframe(df_presus)

else: # Producción
    st.header("📊 Producción")
    for est in ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]:
        with st.expander(f"📍 {est}", expanded=True):
            items = df_pedidos[df_pedidos["Estado"] == est]
            for i, r in items.iterrows():
                st.write(f"**{r['Pieza']}** ({r['Cliente']})")
                new_state = st.selectbox("Mover a:", ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"], index=["Pendiente", "En Preparación", "En Ejecución", "Finalizado"].index(est), key=f"s{i}")
                if new_state != est:
                    df_pedidos.loc[i, "Estado"] = new_state
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear()
                    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# 6. MENÚ INFERIOR FIJO (BOTONES REPRODUCIDOS)
st.markdown('<div class="nav-bar">', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📊 Tablero"):
        st.session_state.menu = "Producción"
        st.rerun()
with c2:
    if st.button("🧮 Calcular"):
        st.session_state.menu = "Calculadora"
        st.rerun()
with c3:
    if st.button("📂 Historial"):
        st.session_state.menu = "Historial"
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

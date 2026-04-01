import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="wide", initial_sidebar_state="collapsed")

# --- DISEÑO CSS PARA INTERFAZ MÓVIL LIMPIA Y BOTONES FIJOS ---
st.markdown("""
    <style>
        /* Ocultar menús de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {display:none;}

        /* Margen inferior para que el contenido no quede tapado por los botones */
        .main-content {
            margin-bottom: 120px;
        }

        /* BARRA INFERIOR FIJA (ESTILO APP) */
        .fixed-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            z-index: 9999;
            padding: 15px 10px;
            border-top: 1px solid #ddd;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }
        
        /* Botones grandes para el pulgar */
        .stButton button {
            width: 100%;
            border-radius: 12px;
            height: 3.5rem;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos")
        h = conn.read(worksheet="Presupuestos")
        return p, h
    except:
        return None, None

df_pedidos, df_presus = cargar_datos()

if df_pedidos is None:
    st.error("⚠️ Error de conexión. Revisa que las pestañas se llamen 'Pedidos' y 'Presupuestos'.")
    st.stop()

# 3. GESTIÓN DE NAVEGACIÓN
if 'seccion' not in st.session_state:
    st.session_state.seccion = "Tablero"

# 4. CONTENIDO PRINCIPAL
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.title("🛠️ Xevytron 3D")

if st.session_state.seccion == "Tablero":
    st.header("📊 Producción")
    estados = ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]
    for est in estados:
        with st.expander(f"📍 {est}", expanded=True):
            items = df_pedidos[df_pedidos["Estado"] == est]
            if items.empty:
                st.caption("Vacío")
            for i, r in items.iterrows():
                st.write(f"**{r['Pieza']}** ({r['Cliente']})")
                nuevo_e = st.selectbox("Cambiar estado:", estados, index=estados.index(est), key=f"sel_{r['ID']}")
                if nuevo_e != est:
                    df_pedidos.loc[df_pedidos["ID"] == r["ID"], "Estado"] = nuevo_e
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear()
                    st.rerun()

elif st.session_state.seccion == "Calculadora":
    st.header("🧮 Calcular")
    with st.form("calc_form"):
        cli = st.text_input("Cliente")
        pie = st.text_input("Pieza")
        gr = st.number_input("Gramos", value=0.0)
        hr = st.number_input("Horas", value=0.0)
        if st.form_submit_button("✅ GUARDAR"):
            precio = ((24/1000*gr) + (hr*1.5)) * 2
            nuevo_p = pd.DataFrame([{"ID": len(df_pedidos)+1, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": cli, "Pieza": pie, "Estado": "Pendiente", "Precio": precio, "Gramos": gr, "Horas": hr, "Notas": ""}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_p], ignore_index=True))
            st.success("Guardado")
            st.cache_data.clear()

elif st.session_state.seccion == "Historial":
    st.header("📂 Historial")
    st.dataframe(df_presus, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# 5. BARRA DE NAVEGACIÓN INFERIOR (CORREGIDA)
# Creamos nuevas columnas específicas para los botones finales
st.markdown('---') 
btn_col1, btn_col2, btn_col3 = st.columns(3)

with btn_col1:
    if st.button("📊 Tablero", key="nav_tab"):
        st.session_state.seccion = "Tablero"
        st.rerun()
with btn_col2:
    if st.button("🧮 Calcular", key="nav_calc"):
        st.session_state.seccion = "Calculadora"
        st.rerun()
with btn_col3:
    if st.button("📂 Historial", key="nav_hist"):
        st.session_state.seccion = "Historial"
        st.rerun()

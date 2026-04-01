import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="wide", initial_sidebar_state="collapsed")

# --- DISEÑO DE INTERFAZ FIJA (CSS AVANZADO) ---
st.markdown("""
    <style>
        /* Ocultar elementos de sistema */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {display:none;}

        /* Contenedor principal con margen inferior para que no tape el último pedido */
        .main-content {
            margin-bottom: 120px;
        }

        /* BARRA INFERIOR FIJA */
        div[data-testid="stVerticalBlock"] > div:last-child {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            z-index: 999999;
            padding: 10px 20px;
            border-top: 2px solid #f0f2f6;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }

        /* Estilo de los botones para que parezcan de App */
        .stButton button {
            width: 100%;
            border-radius: 12px;
            height: 3.5rem;
            font-weight: bold;
            border: 1px solid #d1d5db;
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
    st.error("⚠️ Error de conexión con Google Sheets.")
    st.stop()

# 3. NAVEGACIÓN
if 'menu' not in st.session_state:
    st.session_state.menu = "Producción"

# 4. CUERPO DE LA APP (DENTRO DE UN DIV PARA EL SCROLL)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

st.title("🛠️ Xevytron 3D")

if st.session_state.menu == "Calculadora":
    st.header("🧮 Calcular")
    c_n = st.text_input("Cliente")
    p_n = st.text_input("Pieza")
    col1, col2 = st.columns(2)
    g = col1.number_input("Gramos", 0.0)
    h = col2.number_input("Horas", 0.0)
    m = st.slider("Beneficio %", 0, 200, 100)
    
    precio = ((24/1000*g) + (h*1.5)) * (1 + m/100)
    st.metric("PRECIO RECOMENDADO", f"{precio:.2f} €")
    
    if st.button("✅ GUARDAR"):
        new_ped = pd.DataFrame([{"ID": len(df_pedidos)+1, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": c_n, "Pieza": p_n, "Estado": "Pendiente", "Precio": precio, "Gramos": g, "Horas": h, "Notas": ""}])
        conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, new_ped], ignore_index=True))
        st.success("¡Pedido enviado al tablero!")
        st.cache_data.clear()
        st.rerun()

elif st.session_state.menu == "Historial":
    st.header("📂 Presupuestos")
    st.dataframe(df_presus, use_container_width=True)

else: # Tablero de Producción
    st.header("📊 Producción")
    for est in ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]:
        with st.expander(f"📍 {est}", expanded=True):
            items = df_pedidos[df_pedidos["Estado"] == est]
            for i, r in items.iterrows():
                st.write(f"**{r['Pieza']}** - {r['Cliente']}")
                new_state = st.selectbox("Estado:", ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"], 
                                         index=["Pendiente", "En Preparación", "En Ejecución", "Finalizado"].index(est), 
                                         key=f"item_{r['ID']}")
                if new_state != est:
                    df_pedidos.loc[df_pedidos["ID"] == r["ID"], "Estado"] = new_state
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear()
                    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# 5. MENÚ INFERIOR (ESTE BLOQUE SIEMPRE VA AL FINAL DEL CÓDIGO)
# Las columnas se meten en el último div generado, que el CSS fijará abajo.
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📊 Tablero", key="nav_p"):
        st.session_state.menu = "Producción"
        st.rerun()
with c2:
    if st.button("🧮 Calcular", key="nav_c"):
        st.session_state.menu = "Calculadora"
        st.rerun()
with c3:
    if st.button("📂 Historial", key="nav_h"):
        st.session_state.menu = "Historial"
        st.rerun()

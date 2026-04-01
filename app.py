import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Xevytron 3D", layout="wide", initial_sidebar_state="collapsed")

# --- DISEÑO CSS PARA FIJAR BOTONES ABAJO ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Margen para que el contenido no choque con los botones */
        .main-content { margin-bottom: 150px; }

        /* ESTILO BARRA INFERIOR FIJA */
        .fixed-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            padding: 15px 10px;
            border-top: 2px solid #edeff2;
            z-index: 9999;
            display: flex;
            justify-content: space-around;
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
    st.error("⚠️ Error al conectar con Google Sheets. Revisa los nombres de las pestañas.")
    st.stop()

# 3. GESTIÓN DE NAVEGACIÓN (Estado de sesión)
if 'seccion' not in st.session_state:
    st.session_state.seccion = "Tablero"

# 4. CONTENIDO DE LA APP
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.title("🛠️ Xevytron 3D")

if st.session_state.seccion == "Tablero":
    st.header("📊 Tablero de Producción")
    estados = ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]
    for est in estados:
        with st.expander(f"📍 {est}", expanded=True):
            items = df_pedidos[df_pedidos["Estado"] == est]
            if items.empty:
                st.caption("No hay pedidos aquí.")
            for i, r in items.iterrows():
                st.write(f"**{r['Pieza']}** — {r['Cliente']}")
                # Selector para mover de estado
                nuevo = st.selectbox("Mover a:", estados, index=estados.index(est), key=f"move_{r['ID']}")
                if nuevo != est:
                    df_pedidos.loc[df_pedidos["ID"] == r["ID"], "Estado"] = nuevo
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear()
                    st.rerun()

elif st.session_state.seccion == "Calculadora":
    st.header("🧮 Nueva Calculadora")
    with st.form("form_calc"):
        cliente = st.text_input("Cliente")
        pieza = st.text_input("Pieza")
        gramos = st.number_input("Gramos", value=0.0)
        horas = st.number_input("Horas", value=0.0)
        enviar = st.form_submit_button("✅ Guardar Pedido")
        
        if enviar:
            precio = ((24/1000*gramos) + (horas*1.5)) * 2 # Cálculo rápido
            nuevo_p = pd.DataFrame([{"ID": len(df_pedidos)+1, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": cliente, "Pieza": pieza, "Estado": "Pendiente", "Precio": precio, "Gramos": gramos, "Horas": horas, "Notas": ""}])
            conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_p], ignore_index=True))
            st.success("¡Pedido guardado!")
            st.cache_data.clear()

elif st.session_state.seccion == "Historial":
    st.header("📂 Historial")
    st.write("Lista de presupuestos realizados:")
    st.dataframe(df_presus, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# 5. BOTONES DE NAVEGACIÓN FIJOS (Al final para que floten)
# Creamos un contenedor de columnas que Streamlit renderizará
st.markdown('---') # Separador visual
c1, c2

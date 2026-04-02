import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN MÓVIL
st.set_page_config(
    page_title="Xevytron 3D", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PARA APP MÓVIL ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {display:none;}

        .block-container {
            padding-top: 1rem;
            padding-bottom: 5rem;
        }

        .stButton button {
            width: 100%;
            height: 3.5rem;
            border-radius: 15px;
            font-size: 16px;
            font-weight: bold;
        }

        .order-card {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 15px;
            border-left: 6px solid #007bff;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos")
        return p
    except:
        return None

df_pedidos = cargar_datos()

if df_pedidos is None:
    st.error("❌ Error de conexión. Revisa tus Secrets.")
    st.stop()

# Definición Global de Estados
ESTADOS_LISTA = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# 3. NAVEGACIÓN SUPERIOR
st.title("🛠️ Xevytron 3D")
col_nav1, col_nav2 = st.columns(2)

if 'vista' not in st.session_state:
    st.session_state.vista = "Trabajos"

with col_nav1:
    if st.button("📋 TRABAJOS"):
        st.session_state.vista = "Trabajos"
        st.rerun()
with col_nav2:
    if st.button("➕ NUEVO"):
        st.session_state.vista = "Nuevo"
        st.rerun()

st.divider()

# 4. VISTA: TRABAJOS
if st.session_state.vista == "Trabajos":
    st.subheader("Estado de los Trabajos")
    
    # Filtro de estado para el móvil
    filtro = st.pills("Filtrar por:", ESTADOS_LISTA, default="Pendiente")
    
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    if items.empty:
        st.info(f"No hay trabajos en estado: {filtro}")
    else:
        for i, r in items.iterrows():
            with st.container():
                # Tarjeta visual
                st.markdown(f"""
                <div class="order-card">
                    <p style="margin:0; font-size:12px; color:#777;">Cliente: {r['Cliente']}</p>
                    <h3 style="margin:0; font-size:20px;">{r['Pieza']}</h3>
                    <p style="margin:0; font-weight:bold; color:#28a745;">{r['Precio']} €</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Deslizador táctil para cambiar estado
                nuevo_e = st.select_slider(
                    "Mover proceso:",
                    options=ESTADOS_LISTA,
                    value=filtro,
                    key=f"sl_{r['ID']}_{i}"
                )
                
                if nuevo_e != filtro:
                    df_pedidos.loc[df_pedidos["ID"] == r["ID"], "Estado"] = nuevo_e
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear()
                    st.toast(f"✅ {r['Pieza']} movida a {nuevo_e}")
                    st.rerun()
            st.divider()

# 5. VISTA: NUEVO PEDIDO
elif st.session_state.vista == "Nuevo":
    st.subheader("Añadir Nuevo Trabajo")
    
    with st.form("form_nuevo"):
        cli = st.text_input("Nombre del Cliente")
        pie = st.text_input("Nombre de la Pieza")
        
        c1, c2 = st.columns(2)
        gr = c1.number_input("Gramos", min_value=0.0, step=10.0)
        hr = c2.number_input("Horas", min_value=0.0, step=1.0)
        
        margen = st.select_slider("Margen de Beneficio %", options=[0, 50, 100, 150, 200], value=100)
        
        # Cálculo: (Material + Tiempo) * Margen
        coste_base = (24/1000 * gr) + (hr * 1.0)
        total = coste_base * (1 + margen/100)
        
        st.write(f"### PRECIO TOTAL: {total:.2f} €")
        
        if st.form_submit_button("💾 GUARDAR TRABAJO"):
            if cli and pie:
                nuevo_row = pd.DataFrame([{
                    "ID": int(df_pedidos["ID"].max() + 1 if not df_pedidos.empty else 1),
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Cliente": cli,
                    "Pieza": pie,
                    "Estado": "Pendiente",
                    "Precio": round(total, 2),
                    "Gramos": gr,
                    "Horas": hr,
                    "Notas": ""
                }])
                conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_row], ignore_index=True))
                st.cache_data.clear()
                st.success("¡Trabajo guardado en Pendientes!")
            else:
                st.warning("Rellena el nombre del cliente y la pieza.")

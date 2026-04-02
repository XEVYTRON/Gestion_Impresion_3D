import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN TÉCNICA (MODO MÓVIL)
st.set_page_config(
    page_title="Xevytron 3D", 
    layout="centered", # Centrado es mejor para móviles que "wide"
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PARA QUE PAREZCA UNA APP NATIVA ---
st.markdown("""
    <style>
        /* Ocultar elementos innecesarios de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stStatusWidget"] {display:none;}

        /* Ajuste de márgenes para móviles */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 5rem;
        }

        /* Botones grandes y cómodos */
        .stButton button {
            width: 100%;
            height: 3.5rem;
            border-radius: 15px;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        /* Tarjetas de pedidos */
        .order-card {
            background-color: #f8f9fa;
            border-radius: 15px;
            padding: 15px;
            border-left: 5px solid #007bff;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A LOS DATOS
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
    st.error("❌ Error de conexión. Revisa tus Secrets y pestañas.")
    st.stop()

# 3. NAVEGACIÓN SIMPLIFICADA (BOTONES ARRIBA)
# En móvil, tener los botones arriba es más estable en Streamlit
st.title("🛠️ Xevytron 3D")
col_nav1, col_nav2 = st.columns(2)

if 'vista' not in st.session_state:
    st.session_state.vista = "Tablero"

with col_nav1:
    if st.button("📊 TABLERO"):
        st.session_state.vista = "Tablero"
        st.rerun()
with col_nav2:
    if st.button("🧮 NUEVO"):
        st.session_state.vista = "Nuevo"
        st.rerun()

st.divider()

# 4. VISTA: TABLERO DE PRODUCCIÓN
if st.session_state.vista == "Tablero":
    st.subheader("Estado de Producción")
    
    # Selector de filtro rápido para no saturar la pantalla
    filtro = st.selectbox("Ver estado:", ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"])
    
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    if items.empty:
        st.info(f"No hay nada en {filtro}")
    else:
        for i, r in items.iterrows():
            # Diseño de Tarjeta
            with st.container():
                st.markdown(f"""
                <div class="order-card">
                    <p style="margin:0; font-size:14px; color:#666;">Cliente: {r['Cliente']}</p>
                    <h3 style="margin:0; color:#1f1f1f;">{r['Pieza']}</h3>
                    <p style="margin:0; font-weight:bold; color:#28a745;">{r['Precio']} €</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Botón de cambio de estado justo debajo de la tarjeta
                estados = ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]
                nuevo_e = st.select_slider(
                    "Mover a:",
                    options=estados,
                    value=filtro,
                    key=f"slider_{r['ID']}"
                )
                
                if nuevo_e != filtro:
                    df_pedidos.loc[df_pedidos["ID"] == r["ID"], "Estado"] = nuevo_e
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear()
                    st.success(f"¡{r['Pieza']} movida!")
                    st.rerun()
            st.divider()

# 5. VISTA: NUEVA CALCULADORA / PEDIDO
elif st.session_state.vista == "Nuevo":
    st.subheader("Crear Nuevo Pedido")
    
    with st.form("form_movil"):
        cli = st.text_input("Nombre del Cliente")
        pie = st.text_input("Nombre de la Pieza")
        
        c1, c2 = st.columns(2)
        gr = c1.number_input("Gramos", value=0.0, step=1.0)
        hr = c2.number_input("Horas", value=0.0, step=0.5)
        
        margen = st.select_slider("Beneficio %", options=[0, 25, 50, 75, 100, 150, 200], value=100)
        
        # Cálculo en tiempo real (Tarifas fijas: 24€/kg y 1€/h)
        coste = (24/1000 * gr) + (hr * 1.0)
        total = coste * (1 + margen/100)
        
        st.write(f"### TOTAL: {total:.2f} €")
        
        if st.form_submit_button("✅ GUARDAR E IMPRIMIR"):
            if cli and pie:
                nuevo_p = pd.DataFrame([{
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
                conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_p], ignore_index=True))
                st.cache_data.clear()
                st.success("¡Pedido guardado correctamente!")
            else:
                st.warning("Por favor, rellena cliente y pieza.")

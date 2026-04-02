import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Xevytron 3D", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS UNIFICADOS (TIPOGRAFÍA Y TAMAÑOS) ---
st.markdown("""
    <style>
        /* Ocultar elementos de sistema */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* Unificar Tipografía y Colores */
        html, body, [class*="css"] {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Títulos de sección iguales */
        .titulo-seccion {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
            text-transform: uppercase;
        }

        /* Botones de menú iguales */
        .stButton button {
            width: 100%;
            height: 3rem;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            border: 1px solid #ddd;
            background-color: #ffffff;
            color: #333;
        }

        /* Tarjetas de trabajos */
        .order-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 15px;
            border: 1px solid #eee;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXIÓN A DATOS
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def cargar_datos():
    try:
        p = conn.read(worksheet="Pedidos")
        # Asumimos que tienes una pestaña llamada "Facturas" en tu Drive
        f = conn.read(worksheet="Facturas") 
        return p, f
    except:
        return None, None

df_pedidos, df_facturas = cargar_datos()

if df_pedidos is None:
    st.error("Error de conexión. Asegúrate de tener las pestañas 'Pedidos' y 'Facturas' en tu Google Sheets.")
    st.stop()

# Estados oficiales
ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]

# 3. NAVEGACIÓN (SIN SÍMBOLOS)
if 'seccion' not in st.session_state:
    st.session_state.seccion = "TRABAJOS"

# Fila de botones de menú (Tipografía y tamaño unificados)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("TRABAJOS"):
        st.session_state.seccion = "TRABAJOS"
        st.rerun()
with c2:
    if st.button("NUEVO TRABAJO"):
        st.session_state.seccion = "NUEVO TRABAJO"
        st.rerun()
with c3:
    if st.button("FACTURAS"):
        st.session_state.seccion = "FACTURAS"
        st.rerun()

st.divider()

# 4. VISTA: TRABAJOS
if st.session_state.seccion == "TRABAJOS":
    st.markdown('<p class="titulo-seccion">Trabajos</p>', unsafe_allow_html=True)
    
    filtro = st.pills("Estado:", ESTADOS, default="Pendiente", label_visibility="collapsed")
    
    items = df_pedidos[df_pedidos["Estado"] == filtro]
    
    if items.empty:
        st.info(f"No hay registros en {filtro}")
    else:
        for i, r in items.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="order-card">
                    <p style="margin:0; font-size:11px; color:#999; text-transform:uppercase;">{r['Cliente']}</p>
                    <p style="margin:0; font-size:18px; font-weight:bold; color:#222;">{r['Pieza']}</p>
                    <p style="margin:0; font-size:15px; color:#28a745; font-weight:600;">{r['Precio']} €</p>
                </div>
                """, unsafe_allow_html=True)
                
                nuevo_e = st.select_slider(
                    "Cambiar proceso",
                    options=ESTADOS,
                    value=filtro,
                    key=f"sl_{r['ID']}",
                    label_visibility="collapsed"
                )
                
                if nuevo_e != filtro:
                    df_pedidos.loc[df_pedidos["ID"] == r["ID"], "Estado"] = nuevo_e
                    conn.update(worksheet="Pedidos", data=df_pedidos)
                    st.cache_data.clear()
                    st.rerun()
            st.divider()

# 5. VISTA: NUEVO TRABAJO
elif st.session_state.seccion == "NUEVO TRABAJO":
    st.markdown('<p class="titulo-seccion">Nuevo Trabajo</p>', unsafe_allow_html=True)
    
    with st.form("nuevo_t_form"):
        cliente = st.text_input("Cliente")
        pieza = st.text_input("Pieza")
        
        col_a, col_b = st.columns(2)
        gramos = col_a.number_input("Gramos", min_value=0.0)
        horas = col_b.number_input("Horas", min_value=0.0)
        
        margen = st.select_slider("Margen %", options=[0, 50, 100, 150, 200], value=100)
        
        precio = ((24/1000 * gramos) + (horas * 1.0)) * (1 + margen/100)
        st.subheader(f"Precio: {precio:.2f} €")
        
        if st.form_submit_button("GUARDAR TRABAJO"):
            if cliente and pieza:
                nuevo_row = pd.DataFrame([{
                    "ID": int(df_pedidos["ID"].max() + 1 if not df_pedidos.empty else 1),
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Cliente": cliente,
                    "Pieza": pieza,
                    "Estado": "Pendiente",
                    "Precio": round(precio, 2),
                    "Gramos": gramos,
                    "Horas": horas,
                    "Notas": ""
                }])
                conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_row], ignore_index=True))
                st.cache_data.clear()
                st.success("Trabajo añadido.")
            else:
                st.warning("Completa los datos.")

# 6. VISTA: FACTURAS
elif st.session_state.seccion == "FACTURAS":
    st.markdown('<p class="titulo-seccion">Facturas</p>', unsafe_allow_html=True)
    
    if df_facturas.empty:
        st.info("No hay facturas registradas.")
    else:
        # Aquí puedes listar las facturas o añadir un buscador
        st.dataframe(df_facturas, use_container_width=True)
    
    st.button("GENERAR NUEVA FACTURA (PRÓXIMAMENTE)")

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="3D Print Manager", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

st.title("🛠️ Control de Pedidos 3D")

menu = st.sidebar.selectbox("Menú", ["Tablero de Pedidos", "Nuevo Pedido", "Calculadora"])

if menu == "Calculadora":
    st.header("🧮 Calculadora de Presupuesto")
    col1, col2 = st.columns(2)
    with col1:
        precio_kilo = st.number_input("Precio Filamento (€/kg)", value=20.0)
        gramos = st.number_input("Gramos necesarios", value=0)
    with col2:
        horas = st.number_input("Horas de impresión", value=0.0)
        margen = st.slider("Margen de beneficio %", 0, 200, 100)

    costo_material = (precio_kilo / 1000) * gramos
    costo_luz = (300 / 1000) * horas * 0.15 
    total_base = costo_material + costo_luz
    precio_final = total_base * (1 + margen / 100)
    st.metric("PRECIO RECOMENDADO", f"{precio_final:.2f} €")

elif menu == "Nuevo Pedido":
    st.header("📝 Registrar Nuevo Trabajo")
    with st.form("nuevo_form"):
        cliente = st.text_input("Nombre del Cliente")
        pieza = st.text_input("Nombre de la Pieza")
        gramos_p = st.number_input("Gramos", value=0)
        horas_p = st.number_input("Horas", value=0.0)
        precio_p = st.number_input("Precio Pactado (€)", value=0.0)
        notas = st.text_area("Notas")
        
        if st.form_submit_button("Guardar Pedido"):
            nuevo_dato = pd.DataFrame([{
                "ID": len(df) + 1 if not df.empty else 1,
                "Fecha": datetime.now().strftime("%d/%m/%Y"),
                "Cliente": cliente,
                "Pieza": pieza,
                "Estado": "Pendiente",
                "Precio": precio_p,
                "Gramos": gramos_p,
                "Horas": horas_p,
                "Notas": notas
            }])
            updated_df = pd.concat([df, nuevo_dato], ignore_index=True)
            conn.update(data=updated_df)
            st.success("¡Pedido guardado en la nube!")
            st.cache_data.clear()

elif menu == "Tablero de Pedidos":
    st.header("📊 Tablero de Producción")
    
    if df.empty:
        st.warning("Aún no hay pedidos registrados. Ve a 'Nuevo Pedido' para empezar.")
    else:
        # Definir los estados y crear 4 columnas
        estados = ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]
        columnas = st.columns(4)
        
        # Llenar cada columna con sus tarjetas correspondientes
        for idx, estado in enumerate(estados):
            with columnas[idx]:
                st.subheader(estado)
                
                # Filtrar pedidos por este estado
                pedidos_estado = df[df["Estado"] == estado]
                
                for _, row in pedidos_estado.iterrows():
                    # Crear una "tarjeta" para cada pedido
                    with st.container(border=True):
                        st.markdown(f"**{row['Pieza']}**")
                        st.caption(f"👤 {row['Cliente']} | 💰 {row['Precio']}€")
                        
                        # Selector para mover la tarjeta a otro estado
                        nuevo_estado = st.selectbox(
                            "Mover a:", 
                            estados, 
                            index=estados.index(estado), 
                            key=f"sel_{row['ID']}",
                            label_visibility="collapsed"
                        )
                        
                        # Si se selecciona un estado diferente, actualizar la base de datos
                        if nuevo_estado != estado:
                            df.loc[df["ID"] == row["ID"], "Estado"] = nuevo_estado
                            conn.update(data=df)
                            st.cache_data.clear()
                            st.rerun() # Recarga la página al instante para ver el cambio

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="3D Print Manager PRO", layout="wide")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer ambas hojas (ajusta los nombres en worksheet si los tienes en mayúsculas en el Excel)
try:
    df_pedidos = conn.read(worksheet="Pedidos", ttl=0) 
    df_presus = conn.read(worksheet="Presupuestos", ttl=0) 
except Exception as e:
    st.error(f"Error técnico al leer las hojas: {e}")
    st.stop()

st.title("🚀 Gestión 3D: Pedidos y Presupuestos")

menu = st.sidebar.selectbox("Menú", ["Tablero de Producción", "Gestión de Presupuestos", "Nueva Calculadora"])

# --- FUNCIÓN PDF ---
def crear_pdf(cliente, pieza, coste_mat, coste_tiem, precio_fin):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="PRESUPUESTO DE IMPRESIÓN 3D", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(200, 10, txt=f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 10, txt=f"Pieza: {pieza}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Desglose:", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"- Material: {coste_mat:.2f} Euros", ln=True)
    pdf.cell(200, 10, txt=f"- Tiempo de máquina: {coste_tiem:.2f} Euros", ln=True)
    pdf.ln(10)
    
    # AQUÍ ESTABA EL ERROR. ¡Ya está corregido a 'B'!
    pdf.set_font("Arial", 'B', 14) 
    pdf.cell(200, 10, txt=f"TOTAL: {precio_fin:.2f} Euros", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- LÓGICA DE MENÚS ---

if menu == "Nueva Calculadora":
    st.header("🧮 Calculadora y Nuevo Presupuesto")
    with st.expander("Datos del Cliente", expanded=True):
        c1, c2 = st.columns(2)
        cliente_n = c1.text_input("Nombre del Cliente")
        pieza_n = c2.text_input("Nombre de la Pieza")
    
    col1, col2 = st.columns(2)
    with col1:
        precio_kilo = st.number_input("Precio Filamento (€/kg)", value=24.0)
        gramos = st.number_input("Gramos (Slicer)", value=0.0)
    with col2:
        horas = st.number_input("Horas (Slicer)", value=0.0)
        precio_hora = st.number_input("Precio/Hora (€)", value=1.0)
        margen = st.slider("Beneficio %", 0, 300, 100)

    c_mat = (precio_kilo / 1000) * gramos
    c_tiem = horas * precio_hora
    p_final = (c_mat + c_tiem) * (1 + margen / 100)

    st.metric("PRECIO FINAL", f"{p_final:.2f} €")

    if st.button("✅ Guardar Presupuesto y Crear Pedido"):
        # 1. Guardar en Presupuestos
        nuevo_presu = pd.DataFrame([{
            "ID": len(df_presus) + 1, "Fecha": datetime.now().strftime("%d/%m/%Y"),
            "Cliente": cliente_n, "Pieza": pieza_n, "Coste_Material": c_mat,
            "Coste_Tiempo": c_tiem, "Precio_Final": p_final, "Notas": ""
        }])
        # 2. Guardar en Pedidos automáticamente
        nuevo_ped = pd.DataFrame([{
            "ID": len(df_pedidos) + 1, "Fecha": datetime.now().strftime("%d/%m/%Y"),
            "Cliente": cliente_n, "Pieza": pieza_n, "Estado": "Pendiente",
            "Precio": p_final, "Gramos": gramos, "Horas": horas, "Notas": "Viene de presupuesto"
        }])
        
        conn.update(worksheet="Presupuestos", data=pd.concat([df_presus, nuevo_presu], ignore_index=True))
        conn.update(worksheet="Pedidos", data=pd.concat([df_pedidos, nuevo_ped], ignore_index=True))
        st.success("Presupuesto guardado y pedido enviado al tablero.")
        st.cache_data.clear()

elif menu == "Gestión de Presupuestos":
    st.header("📂 Historial de Presupuestos")
    busqueda = st.text_input("🔍 Buscar por cliente o pieza")
    
    # Filtrado
    df_f = df_presus[df_presus.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)] if not df_presus.empty else df_presus

    for i, row in df_f.iterrows():
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2, 2, 1])
            col_a.write(f"**{row['Pieza']}** ({row['Fecha']})")
            col_a.caption(f"👤 Cliente: {row['Cliente']}")
            col_b.write(f"💰 Total: {row['Precio_Final']:.2f} €")
            
            # Botones
            pdf_b = crear_pdf(row['Cliente'], row['Pieza'], row['Coste_Material'], row['Coste_Tiempo'], row['Precio_Final'])
            col_c.download_button("📩 PDF", pdf_b, f"Presu_{row['Cliente']}.pdf", key=f"dl_{i}")
            if col_c.button("🗑️ Borrar", key=f"del_{i}"):
                df_presus = df_presus.drop(i)
                conn.update(worksheet="Presupuestos", data=df_presus)
                st.cache_data.clear()
                st.rerun()

elif menu == "Tablero de Producción":
    st.header("📊 Tablero de Trabajo")
    estados = ["Pendiente", "En Preparación", "En Ejecución", "Finalizado"]
    columnas = st.columns(4)
    
    for

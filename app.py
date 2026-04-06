import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
from PIL import Image
from io import BytesIO
import urllib.parse

# --- 1. SEGURIDAD ---
try:
    PASSWORD_APP = st.secrets["password"]
except:
    PASSWORD_APP = "xevy2024"

# --- 2. UTILIDADES DE PDF ---
def crear_pdf(id_factura, fecha, cliente, pieza, total, notas="", gramos=0, horas=0):
    pdf = FPDF()
    pdf.add_page()
    r_corp, g_corp, b_corp = 111, 66, 193
    try:
        pdf.image("image_7.png", 10, 8, 22)
        pdf.set_x(35)
    except:
        pdf.set_font("Arial", 'B', 22)
        pdf.set_text_color(r_corp, g_corp, b_corp)
        pdf.cell(30, 20, "VYE")
        pdf.set_text_color(0); pdf.set_x(35)

    pdf.set_font("Arial", 'B', 18)
    pdf.cell(100, 10, "VYE 3D - SERVICIOS", ln=False)
    pdf.set_font("Arial", 'B', 10); pdf.set_text_color(100)
    pdf.cell(0, 10, f"FACTURA: #{id_factura}", ln=True, align='R')
    pdf.set_text_color(0)
    pdf.set_draw_color(r_corp, g_corp, b_corp); pdf.set_line_width(0.8)
    pdf.line(10, 32, 200, 32)
    pdf.set_y(38) 

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 6, "PARA:", ln=False); pdf.cell(0, 6, "DETALLES DE FECHA:", ln=True)
    pdf.set_font("Arial", 'B', 11) 
    def format_es(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 6, format_es(cliente), ln=False); pdf.cell(0, 6, f"{fecha}", ln=True); pdf.ln(6) 

    pdf.set_fill_color(r_corp, g_corp, b_corp); pdf.set_text_color(255); pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 7, " CONCEPTO / PIEZA", border=0, fill=True)
    pdf.cell(30, 7, " GRAMOS", border=0, fill=True, align='C')
    pdf.cell(30, 7, " HORAS", border=0, fill=True, align='C')
    pdf.cell(40, 7, " TOTAL", border=0, fill=True, align='R'); pdf.ln(7)

    pdf.set_text_color(0); pdf.set_font("Arial", 'B', 10); pdf.set_draw_color(220)
    pdf.cell(90, 9, format_es(f" {pieza}"), border='B')
    pdf.cell(30, 9, f" {gramos} g", border='B', align='C')
    pdf.cell(30, 9, f" {horas} h", border='B', align='C')
    pdf.cell(40, 9, f" {total:.2f} EUR ", border='B', align='R'); pdf.ln(10)

    nota_limpia = str(notas).strip()
    if nota_limpia and nota_limpia.lower() != 'nan':
        pdf.set_font("Arial", 'B', 10); pdf.set_text_color(r_corp, g_corp, b_corp)
        pdf.cell(0, 7, "OBSERVACIONES:", ln=True)
        pdf.set_font("Arial", 'B', 10); pdf.set_text_color(50)
        pdf.multi_cell(0, 5, format_es(nota_limpia)); pdf.ln(6)

    pdf.ln(5); pdf.set_font("Arial", 'B', 13); pdf.set_fill_color(245, 245, 245)
    pdf.cell(125, 10, "", border=0); pdf.cell(65, 10, format_es(f" TOTAL A PAGAR: {total:.2f} EUR "), border=0, fill=True, align='R')

    pdf.set_y(-38); pdf.set_font("Arial", 'B', 8); pdf.set_text_color(120)
    pdf.cell(0, 4, format_es("Gracias por confiar en VYE 3D para tus proyectos de fabricación aditiva."), align='C', ln=True)
    pdf.set_text_color(r_corp, g_corp, b_corp)
    pdf.cell(0, 4, "Instagram: @vye3d  |  Email: vye3d@hotmail.com", align='C', ln=True)
    pdf.cell(0, 4, "Contacto: 660211456 / 625375222", align='C')
    return pdf.output(dest="S").encode("latin-1")

# --- 3. CONFIGURACIÓN ---
st.set_page_config(page_title="VYE 3D", layout="centered")

# --- 4. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso VYE 3D</h1>", unsafe_allow_html=True)
    pass_input = st.text_input("Contraseña", type="password")
    if st.button("ENTRAR"):
        if pass_input == PASSWORD_APP: st.session_state.autenticado = True; st.rerun()
    st.stop()

# --- 5. ESTILOS CSS (Añadido efecto para Urgentes) ---
st.markdown("""<style>
@keyframes blinker { 50% { border-color: #ff0000; box-shadow: 0 0 10px #ff0000; } }
.card-urgente { border-left: 10px solid #ff0000 !important; animation: blinker 1.5s linear infinite; }
.card-alta { border-left: 10px solid #fd7e14 !important; }
.card-media { border-left: 10px solid #6f42c1 !important; }
.card-baja { border-left: 10px solid #20c997 !important; }
.card-container { background-color: #ffffff; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; margin-bottom: 10px; }
.card-nombre { font-size: 18px; font-weight: 800; color: #343a40; text-transform: uppercase; margin: 0; }
.card-entrega { font-size: 12px; font-weight: 700; color: #d63384; margin-bottom: 5px; }
</style>""", unsafe_allow_html=True)

# --- 6. DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_df(df, con_estado=False):
    cols = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas', 'Prioridad', 'Entrega', 'Telefono']
    if con_estado: cols.append('Estado')
    for c in cols:
        if c not in df.columns: df[c] = "Normal" if c == "Prioridad" else ""
    df = df[cols].copy()
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
    for n in ['Precio', 'Gramos', 'Horas']: df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=2)
def cargar_todo():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0); f = conn.read(worksheet="Facturas", ttl=0)
        return limpiar_df(p, True), limpiar_df(f, False)
    except: return None, None

if 'df_pedidos' not in st.session_state: st.session_state.df_pedidos, st.session_state.df_facturas = cargar_todo()
df_p, df_f = st.session_state.df_pedidos, st.session_state.df_facturas

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]
PRIORIDADES = ["Baja", "Media", "Alta", "URGENTE"]

def card_html(r):
    prio_class = f"card-{r['Prioridad'].lower()}"
    entrega_txt = f"<p class='card-entrega'>⏱️ ENTREGA: {r['Entrega']}</p>" if r['Entrega'] else ""
    return f"""<div class="card-container {prio_class}">
        {entrega_txt}
        <p class="card-nombre">{r['Cliente']}</p>
        <p style='margin:0; font-weight:600;'>Pieza: {r['Pieza']}</p>
        <p style='margin:0; font-size:16px; font-weight:bold;'>{r['Precio']:.2f} €</p>
    </div>"""

st.markdown("<h1 style='text-align: center; color: #6f42c1; text-transform: uppercase; font-size: 50px; font-weight: 900;'>VYE 3D</h1>", unsafe_allow_html=True)

# --- 7. NAVEGACIÓN ---
if 'seccion' not in st.session_state: st.session_state.seccion = "TRABAJOS"
n_cols = st.columns(4)
if n_cols[0].button("TRABAJOS"): st.session_state.seccion = "TRABAJOS"; st.rerun()
if n_cols[1].button("NUEVO"): st.session_state.seccion = "NUEVO TRABAJO"; st.rerun()
if n_cols[2].button("FACTURAS"): st.session_state.seccion = "FACTURAS"; st.rerun()
if n_cols[3].button("📊"): st.session_state.seccion = "ESTADISTICAS"; st.rerun()
st.divider()

# --- 8. VISTA: TRABAJOS ---
if st.session_state.seccion == "TRABAJOS":
    texto_buscar = st.text_input("🔍 Buscar Cliente o Pieza...", value="").lower().strip()
    if texto_buscar:
        items = df_p[df_p['Cliente'].str.lower().str.contains(texto_buscar) | df_p['Pieza'].str.lower().str.contains(texto_buscar)]
    else:
        est_sel = st.selectbox("Filtrar por Estado:", ESTADOS)
        items = df_p[df_p["Estado"] == est_sel]
    
    for idx, r in items.sort_values(by="Prioridad", ascending=False).iterrows():
        st.markdown(card_html(r), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        upd_est = col1.selectbox("Cambiar Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"est_{r['ID']}")
        if upd_est != r['Estado']:
            df_p.at[idx, "Estado"] = upd_est
            conn.update(worksheet="Pedidos", data=df_p); st.rerun()
        
        # BOTÓN WHATSAPP
        if r['Telefono']:
            msg = urllib.parse.quote(f"¡Hola {r['Cliente']}! Tu pieza '{r['Pieza']}' de VYE 3D ya está lista. Puedes pasar a recogerla.")
            col2.link_button("🟢 AVISAR WHATSAPP", f"https://wa.me/{r['Telefono']}?text={msg}")
        
        with st.expander("MODIFICAR / PDF"):
            pdf_b = crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], float(r['Precio']), r['Notas'], r['Gramos'], r['Horas'])
            st.download_button("📩 Descargar Factura", data=pdf_b, file_name=f"VYE_{r['Cliente']}.pdf", key=f"pdf_{r['ID']}")
            if st.button("🗑️ Eliminar", key=f"del_{r['ID']}"):
                df_p = df_p[df_p['ID'] != r['ID']]; conn.update(worksheet="Pedidos", data=df_p); st.rerun()
        st.divider()

# --- 9. VISTA: NUEVO TRABAJO ---
elif st.session_state.seccion == "NUEVO TRABAJO":
    with st.form("nuevo_p"):
        c1, c2 = st.columns(2)
        nc = c1.text_input("Cliente")
        ntel = c2.text_input("Teléfono (Ej: 34660211456)")
        np = st.text_input("Pieza")
        c3, c4, c5 = st.columns(3)
        gms = c3.number_input("Gramos", min_value=0.0)
        hrs = c4.number_input("Horas", min_value=0.0)
        prio = c5.selectbox("Prioridad", PRIORIDADES, index=1)
        entrega = st.date_input("Fecha de Entrega", value=datetime.now() + timedelta(days=2))
        mgn = st.select_slider("Margen %", options=[0, 50, 100, 150, 200], value=100)
        pf = ((0.024 * gms) + (hrs * 1.0)) * (1 + mgn / 100)
        nn = st.text_area("Notas")
        if st.form_submit_button("GUARDAR TRABAJO"):
            id_n = datetime.now().strftime("%y%m%d%H%M%S")
            nueva_fila = pd.DataFrame([{"ID": id_n, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": nc, "Pieza": np, "Estado": "Pendiente", "Precio": pf, "Gramos": gms, "Horas": hrs, "Notas": nn, "Prioridad": prio, "Entrega": entrega.strftime("%d/%m/%Y"), "Telefono": ntel}])
            df_p = pd.concat([df_p, nueva_fila], ignore_index=True)
            df_f = pd.concat([df_f, nueva_fila.drop(columns=['Estado'])], ignore_index=True)
            conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f)
            st.success("¡Trabajo guardado!"); st.rerun()

# --- 10. ESTADÍSTICAS ---
elif st.session_state.seccion == "ESTADISTICAS":
    # Alerta de entregas próximas
    hoy = datetime.now()
    entregas_prox = df_p[df_p["Estado"] != "Finalizado"].copy()
    entregas_prox['Entrega_DT'] = pd.to_datetime(entregas_prox['Entrega'], format="%d/%m/%Y", errors='coerce')
    proximas = entregas_prox[(entregas_prox['Entrega_DT'] >= hoy) & (entregas_prox['Entrega_DT'] <= hoy + timedelta(days=3))]
    
    if not proximas.empty:
        st.warning(f"⚠️ ¡Atención! Tienes {len(proximas)} entregas para los próximos 3 días.")

    st.markdown("### 💰 Finanzas Reales")
    total_v = df_f['Precio'].sum()
    total_g, total_h = df_f['Gramos'].sum(), df_f['Horas'].sum()
    beneficio = total_v - (total_g * 0.024 + total_h * 0.20)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingresos", f"{total_v:.2f} €")
    m2.metric("Beneficio Neto", f"{beneficio:.2f} €")
    m3.metric("Trabajos", len(df_f))

    st.divider(); st.markdown("**Evolución de Ventas**")
    df_f['Fecha_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y", errors='coerce')
    vm = df_f.dropna(subset=['Fecha_DT']).set_index('Fecha_DT').resample('ME')['Precio'].sum()
    st.bar_chart(vm)

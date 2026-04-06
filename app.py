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

# --- 2. MOTOR DE PDF (DISEÑO ROBUSTO Y HOJA ÚNICA) ---
def crear_pdf(id_factura, fecha, cliente, pieza, total, notas="", gramos=0, horas=0):
    pdf = FPDF()
    pdf.add_page()
    r_corp, g_corp, b_corp = 111, 66, 193
    try:
        pdf.image("image_7.png", 10, 8, 22)
        pdf.set_x(35)
    except:
        pdf.set_font("Arial", 'B', 22); pdf.set_text_color(r_corp, g_corp, b_corp)
        pdf.cell(30, 20, "VYE"); pdf.set_text_color(0); pdf.set_x(35)
    pdf.set_font("Arial", 'B', 18); pdf.cell(100, 10, "VYE 3D - SERVICIOS", ln=False)
    pdf.set_font("Arial", 'B', 10); pdf.set_text_color(100); pdf.cell(0, 10, f"FACTURA: #{id_factura}", ln=True, align='R')
    pdf.set_text_color(0); pdf.set_draw_color(r_corp, g_corp, b_corp); pdf.set_line_width(0.8); pdf.line(10, 32, 200, 32)
    pdf.set_y(38); pdf.set_font("Arial", 'B', 10); pdf.cell(100, 6, "PARA:", ln=False); pdf.cell(0, 6, "DETALLES DE FECHA:", ln=True)
    def format_es(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("Arial", 'B', 11); pdf.cell(100, 6, format_es(cliente), ln=False); pdf.cell(0, 6, f"{fecha}", ln=True); pdf.ln(6) 
    pdf.set_fill_color(r_corp, g_corp, b_corp); pdf.set_text_color(255); pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 7, " CONCEPTO / PIEZA", border=0, fill=True); pdf.cell(30, 7, " GRAMOS", border=0, fill=True, align='C')
    pdf.cell(30, 7, " HORAS", border=0, fill=True, align='C'); pdf.cell(40, 7, " TOTAL", border=0, fill=True, align='R'); pdf.ln(7)
    pdf.set_text_color(0); pdf.set_font("Arial", 'B', 10); pdf.set_draw_color(220)
    pdf.cell(90, 9, format_es(f" {pieza}"), border='B'); pdf.cell(30, 9, f" {gramos} g", border='B', align='C')
    pdf.cell(30, 9, f" {horas} h", border='B', align='C'); pdf.cell(40, 9, f" {total:.2f} EUR ", border='B', align='R'); pdf.ln(10)
    if notas and str(notas).lower() != 'nan' and str(notas).strip() != "":
        pdf.set_font("Arial", 'B', 10); pdf.set_text_color(r_corp, g_corp, b_corp); pdf.cell(0, 7, "OBSERVACIONES:", ln=True)
        pdf.set_font("Arial", 'B', 10); pdf.set_text_color(50); pdf.multi_cell(0, 5, format_es(notas)); pdf.ln(6)
    pdf.ln(5); pdf.set_font("Arial", 'B', 13); pdf.set_fill_color(245, 245, 245)
    pdf.cell(125, 10, "", border=0); pdf.cell(65, 10, format_es(f" TOTAL A PAGAR: {total:.2f} EUR "), border=0, fill=True, align='R')
    pdf.set_y(-38); pdf.set_font("Arial", 'B', 8); pdf.set_text_color(120)
    pdf.cell(0, 4, format_es("Gracias por confiar en VYE 3D para tus proyectos de fabricación aditiva."), align='C', ln=True)
    pdf.set_text_color(r_corp, g_corp, b_corp); pdf.cell(0, 4, "Instagram: @vye3d  |  Email: vye3d@hotmail.com", align='C', ln=True)
    pdf.cell(0, 4, "Contacto: 660211456 / 625375222", align='C')
    return pdf.output(dest="S").encode("latin-1")

# --- 3. CONFIGURACIÓN ---
st.set_page_config(page_title="VYE 3D", layout="centered")

# --- 4. ESTILOS CSS ---
st.markdown("""<style>
@keyframes blinker { 50% { border-color: #ff0000; box-shadow: 0 0 10px #ff0000; } }
.card-urgente { border-left: 10px solid #ff0000 !important; animation: blinker 1.5s linear infinite; }
.card-alta { border-left: 10px solid #fd7e14 !important; }
.card-media { border-left: 10px solid #6f42c1 !important; }
.card-baja { border-left: 10px solid #20c997 !important; }
.card-container { background-color: #ffffff !important; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; color: #333; }
.card-fecha { font-size: 10px; color: #777 !important; margin-bottom: 2px; text-transform: uppercase; }
.card-nombre { font-size: 18px; font-weight: 800; color: #6f42c1 !important; margin: 0; text-transform: uppercase; }
.card-pieza { font-size: 15px; color: #333 !important; font-weight: 600; margin-top: 4px; }
.card-nota { font-size: 13px; color: #555 !important; font-style: italic; margin-top: 2px; line-height: 1.2; }
.card-precio { font-size: 17px; color: #111 !important; font-weight: 900; margin-top: 8px; border-top: 1px solid #eee; padding-top: 5px; }
.card-entrega { font-size: 11px; font-weight: 700; color: #d63384; margin-bottom: 5px; text-transform: uppercase; }
.badge-estado { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; background-color: #f1f3f5; color: #6f42c1; border: 1px solid #6f42c1; margin-bottom: 5px; }
.stButton button { width: 100%; font-weight: 600; }
</style>""", unsafe_allow_html=True)

# --- 5. DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_df(df, con_estado=False):
    cols_base = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas', 'Prioridad', 'Entrega', 'Telefono']
    if con_estado: cols_base.append('Estado')
    for c in cols_base:
        if c not in df.columns: df[c] = ""
    df = df[cols_base].copy()
    df['Prioridad'] = df['Prioridad'].fillna('Media').replace('', 'Media').astype(str)
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False)
    # Limpiamos el texto "nan" de las entregas
    df['Entrega'] = df['Entrega'].astype(str).replace(['nan', 'NaN', 'None', ''], '')
    for n in ['Precio', 'Gramos', 'Horas']: df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=1)
def cargar_todo():
    p = conn.read(worksheet="Pedidos", ttl=0); f = conn.read(worksheet="Facturas", ttl=0)
    return limpiar_df(p, True), limpiar_df(f, False)

if 'df_p' not in st.session_state: st.session_state.df_p, st.session_state.df_f = cargar_todo()
df_p, df_f = st.session_state.df_p, st.session_state.df_f

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]
PRIORIDADES = ["Baja", "Media", "Alta", "URGENTE"]

def card_html(r, badge=""):
    prio = str(r['Prioridad']).lower()
    # Evitamos mostrar "NAN" en la entrega
    e_str = str(r['Entrega']).strip()
    ent = f"<p class='card-entrega'>⏱️ ENTREGA: {e_str}</p>" if e_str and e_str.lower() != 'nan' else ""
    nt = f"<p class='card-nota'>Notas: {r['Notas']}</p>" if r['Notas'] and str(r['Notas']).lower() != 'nan' else ""
    bdg = f"<div class='badge-estado'>{badge}</div>" if badge else ""
    return f'<div class="card-container card-{prio}">{bdg}{ent}<p class="card-fecha">{r["Fecha"]} | ID: {r["ID"]}</p><p class="card-nombre">{r["Cliente"]}</p><p class="card-pieza">Pieza: {r["Pieza"]}</p>{nt}<p class="card-precio">{r["Precio"]:.2f} €</p></div>'

# --- 6. ACCESO (RESTAURADO BOTÓN ENTRAR) ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso VYE 3D</h1>", unsafe_allow_html=True)
    pass_input = st.text_input("Contraseña", type="password")
    if st.button("ENTRAR"):
        if pass_input == PASSWORD_APP:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

st.markdown("<h1 style='text-align: center; color: #6f42c1; text-transform: uppercase; font-size: 50px; font-weight: 900;'>VYE 3D</h1>", unsafe_allow_html=True)

# --- 7. NAVEGACIÓN ---
if 'sec' not in st.session_state: st.session_state.sec = "TRABAJOS"
n_cols = st.columns(4)
if n_cols[0].button("TRABAJOS"): st.session_state.sec = "TRABAJOS"; st.rerun()
if n_cols[1].button("NUEVO"): st.session_state.sec = "NUEVO"; st.rerun()
if n_cols[2].button("FACTURAS"): st.session_state.sec = "FACTURAS"; st.rerun()
if n_cols[3].button("📊"): st.session_state.sec = "STATS"; st.rerun()
st.divider()

# --- 8. VISTA: TRABAJOS ---
if st.session_state.sec == "TRABAJOS":
    busc = st.text_input("🔍 Buscar...").lower().strip()
    items = df_p[df_p['Cliente'].str.lower().str.contains(busc) | df_p['Pieza'].str.lower().str.contains(busc)] if busc else df_p[df_p["Estado"] == st.selectbox("Estado:", ESTADOS)]
    
    items['pv'] = items['Prioridad'].map({"Baja":1, "Media":2, "Alta":3, "URGENTE":4}).fillna(2)
    for idx, r in items.sort_values(by="pv", ascending=False).iterrows():
        st.markdown(card_html(r, r['Estado'] if busc else ""), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        upd = c1.selectbox("Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"e_{r['ID']}")
        if upd != r['Estado']: df_p.at[idx, "Estado"] = upd; conn.update(worksheet="Pedidos", data=df_p); st.rerun()
        if r['Telefono']:
            url = f"https://wa.me/{r['Telefono']}?text=" + urllib.parse.quote(f"Hola {r['Cliente']}, tu pedido {r['Pieza']} ya esta listo!")
            c2.link_button("🟢 WHATSAPP", url)
        
        with st.expander("MODIFICAR / PDF ⚙️"):
            with st.form(f"f_{r['ID']}"):
                ec, ep = st.text_input("Cliente", r['Cliente']), st.text_input("Pieza", r['Pieza'])
                c3, c4, c5 = st.columns(3)
                eg, eh, epr = c3.number_input("Gramos", value=float(r['Gramos'])), c4.number_input("Horas", value=float(r['Horas'])), c5.number_input("Precio (€)", value=float(r['Precio']))
                c6, c7, c8 = st.columns(3)
                eprio = c6.selectbox("Prioridad", PRIORIDADES, index=PRIORIDADES.index(r['Prioridad']))
                
                # REPARACIÓN DE FECHA: Evita el TypeError
                e_str = str(r['Entrega']).strip()
                try:
                    ent_val = datetime.strptime(e_str, "%d/%m/%Y")
                except:
                    ent_val = datetime.now() # Fallback si no hay fecha válida
                
                eent = c7.date_input("Entrega", value=ent_val)
                etel = c8.text_input("Tel.", r['Telefono'])
                en = st.text_area("Notas", r['Notas'])
                if st.form_submit_button("Guardar"):
                    vals = [ec, ep, epr, str(en).strip(), eg, eh, eprio, eent.strftime("%d/%m/%Y"), etel]
                    df_p.loc[df_p['ID'] == r['ID'], ['Cliente', 'Pieza', 'Precio', 'Notas', 'Gramos', 'Horas', 'Prioridad', 'Entrega', 'Telefono']] = vals
                    df_f.loc[df_f['ID'] == r['ID'], ['Cliente', 'Pieza', 'Precio', 'Notas', 'Gramos', 'Horas', 'Prioridad', 'Entrega', 'Telefono']] = vals
                    conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f); st.rerun()
            st.download_button("📩 PDF", data=crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Precio'], r['Notas'], r['Gramos'], r['Horas']), file_name=f"VYE_{r['Cliente']}.pdf", key=f"p_{r['ID']}")
            if st.button("🗑️ Eliminar", key=f"d_{r['ID']}"): df_p = df_p[df_p['ID'] != r['ID']]; conn.update(worksheet="Pedidos", data=df_p); st.rerun()
        st.divider()

# --- 9. VISTA: NUEVO ---
elif st.session_state.sec == "NUEVO":
    with st.form("n"):
        c1, c2 = st.columns(2)
        nc, ntel = c1.text_input("Cliente"), c2.text_input("WhatsApp (34...)")
        np = st.text_input("Pieza")
        c3, c4, c5 = st.columns(3)
        gms, hrs, prio = c3.number_input("Gramos", 0.0), c4.number_input("Horas", 0.0), c5.selectbox("Prioridad", PRIORIDADES, index=1)
        
        # EL USUARIO ELIGE LA FECHA LIBREMENTE
        ent = st.date_input("Fecha de Entrega", value=datetime.now()) 
        
        mgn = st.select_slider("Margen %", options=[0, 50, 100, 150, 200], value=100)
        pf = ((0.024 * gms) + (hrs * 1.0)) * (1 + mgn / 100)
        st.write(f"### TOTAL: {pf:.2f} €")
        nn = st.text_area("Notas")
        if st.form_submit_button("GUARDAR"):
            id_n = datetime.now().strftime("%y%m%d%H%M%S")
            nueva = pd.DataFrame([{"ID": id_n, "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": nc, "Pieza": np, "Estado": "Pendiente", "Precio": pf, "Gramos": gms, "Horas": hrs, "Notas": nn, "Prioridad": prio, "Entrega": ent.strftime("%d/%m/%Y"), "Telefono": ntel}])
            df_p = pd.concat([df_p, nueva], ignore_index=True); df_f = pd.concat([df_f, nueva.drop(columns=['Estado'])], ignore_index=True)
            conn.update(worksheet="Pedidos", data=df_p); conn.update(worksheet="Facturas", data=df_f); st.rerun()

# --- 10. FACTURAS ---
elif st.session_state.sec == "FACTURAS":
    busc = st.text_input("🔍 Buscar...").lower().strip()
    items = df_f[df_f['Cliente'].str.lower().str.contains(busc) | df_f['Pieza'].str.lower().str.contains(busc)] if busc else df_f
    for _, r in items.sort_values(by="ID", ascending=False).iterrows():
        st.markdown(card_html(r), unsafe_allow_html=True)
        st.download_button("📩 PDF", data=crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Precio'], r['Notas'], r['Gramos'], r['Horas']), file_name=f"VYE_{r['Cliente']}.pdf", key=f"f_{r['ID']}")
        st.divider()

# --- 11. STATS ---
elif st.session_state.sec == "STATS":
    total_v = df_f['Precio'].sum(); total_g, total_h = df_f['Gramos'].sum(), df_f['Horas'].sum()
    beneficio = total_v - (total_g * 0.024 + total_h * 0.20)
    c1, c2, c3 = st.columns(3); c1.metric("Ingresos", f"{total_v:.2f} €"); c2.metric("Beneficio Neto", f"{beneficio:.2f} €"); c3.metric("Trabajos", len(df_f))
    st.divider(); df_f['F_DT'] = pd.to_datetime(df_f['Fecha'], format="%d/%m/%Y", errors='coerce')
    vm = df_f.dropna(subset=['F_DT']).set_index('F_DT').resample('ME')['Precio'].sum()
    st.bar_chart(vm)

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

# --- 2. MOTOR DE PDF ---
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
.card-urgente-alerta { border-left: 10px solid #ff0000 !important; animation: blinker 1.5s linear infinite; }
.card-alta { border-left: 10px solid #fd7e14 !important; }
.card-media { border-left: 10px solid #6f42c1 !important; }
.card-baja { border-left: 10px solid #20c997 !important; }
.card-container { background-color: #ffffff !important; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; color: #333; }
.card-fecha { font-size: 10px; color: #777 !important; margin-bottom: 2px; text-transform: uppercase; }
.card-nombre { font-size: 18px; font-weight: 800; color: #6f42c1 !important; margin: 0; text-transform: uppercase; }
.card-pieza { font-size: 15px; color: #333 !important; font-weight: 600; margin-top: 4px; }
.card-nota { font-size: 13px; color: #555 !important; font-style: italic; margin-top: 2px; line-height: 1.2; }
.card-precio { font-size: 17px; color: #111 !important; font-weight: 900; margin-top: 8px; border-top: 1px solid #eee; padding-top: 5px; }
.badge-estado { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; background-color: #f1f3f5; color: #6f42c1; border: 1px solid #6f42c1; margin-bottom: 5px; }
.stat-card { background-color: #f8f9fa; border-radius: 10px; padding: 12px 16px; border-left: 5px solid #6f42c1; margin-bottom: 8px; }
</style>""", unsafe_allow_html=True)

# --- 5. DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_df(df, con_estado=False):
    cols_base = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas', 'Prioridad', 'Entrega', 'Telefono']
    if con_estado: cols_base.append('Estado')
    for c in cols_base:
        if c not in df.columns: df[c] = ""
    df = df[cols_base].copy()
    df['Prioridad'] = df['Prioridad'].fillna('Media').replace(['', 'nan', 'NaN'], 'Media').astype(str)
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False)
    df['Entrega'] = df['Entrega'].astype(str).replace(['nan', 'NaN', 'None', ''], '')
    df['Notas'] = df['Notas'].astype(str).replace(['nan', 'NaN', 'None'], '')
    for n in ['Precio', 'Gramos', 'Horas']: df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=1)
def cargar_todo():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        return limpiar_df(p, True)
    except: return None

if 'df_p' not in st.session_state: st.session_state.df_p = cargar_todo()
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]
PRIORIDADES = ["Baja", "Media", "Alta", "URGENTE"]

def card_html(r, badge=""):
    prio_class = f"card-{r['Prioridad'].lower()}"
    e_str = str(r['Entrega']).strip()
    if e_str and e_str != "":
        try:
            dias = (datetime.strptime(e_str, "%d/%m/%Y") - datetime.now()).days
            if dias <= 7 or r['Prioridad'] == "URGENTE": prio_class = "card-urgente-alerta"
        except: pass
    ent = f"<p style='color:#d63384; font-size:11px; font-weight:700;'>⏱️ ENTREGA: {e_str}</p>" if e_str else ""
    nt = f"<p class='card-nota'>Notas: {r['Notas']}</p>" if r['Notas'] else ""
    bdg = f"<div class='badge-estado'>{badge}</div>" if badge else ""
    return f'<div class="card-container {prio_class}">{bdg}{ent}<p class="card-fecha">{r["Fecha"]} | ID: {r["ID"]}</p><p class="card-nombre">{r["Cliente"]}</p><p class="card-pieza">Pieza: {r["Pieza"]}</p>{nt}<p class="card-precio">{r["Precio"]:.2f} €</p></div>'

# --- 6. ACCESO (BOTÓN ENTRAR FIX) ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso VYE 3D</h1>", unsafe_allow_html=True)
    p_in = st.text_input("Contraseña", type="password")
    if st.button("ENTRAR"):
        if p_in == PASSWORD_APP: st.session_state.auth = True; st.rerun()
        else: st.error("Contraseña incorrecta")
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

df_p = st.session_state.df_p

# --- 8. VISTA: TRABAJOS ---
if st.session_state.sec == "TRABAJOS":
    busc = st.text_input("🔍 Buscar...").lower().strip()
    items = df_p[df_p['Cliente'].str.lower().str.contains(busc, na=False) | df_p['Pieza'].str.lower().str.contains(busc, na=False)] if busc else df_p[df_p["Estado"] == st.selectbox("Estado:", ESTADOS)]
    for idx, r in items.iterrows():
        st.markdown(card_html(r, r['Estado']), unsafe_allow_html=True)
        upd = st.selectbox("Cambiar Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"up_{r['ID']}")
        if upd != r['Estado']:
            df_p.at[idx, "Estado"] = upd
            conn.update(worksheet="Pedidos", data=df_p); st.session_state.df_p = df_p; st.rerun()
        if r['Telefono'] and str(r['Telefono']) != "":
            url = f"https://wa.me/{r['Telefono']}?text=" + urllib.parse.quote(f"Hola {r['Cliente']}, tu pedido {r['Pieza']} de VYE 3D ya esta listo!")
            st.link_button("🟢 AVISAR POR WHATSAPP", url)
        with st.expander("EDITAR / PDF"):
            with st.form(f"fm_{r['ID']}"):
                ec, ep = st.text_input("Cliente", r['Cliente']), st.text_input("Pieza", r['Pieza'])
                eg, eh, epr = st.number_input("Gramos", value=float(r['Gramos'])), st.number_input("Horas", value=float(r['Horas'])), st.number_input("Precio (€)", value=float(r['Precio']))
                eprio = st.selectbox("Prioridad", PRIORIDADES, index=PRIORIDADES.index(r['Prioridad']))
                usar_f = st.checkbox("Tiene entrega", value=(r['Entrega'] != ""))
                eent = st.date_input("Fecha", value=datetime.now()) if usar_f else None
                etel, en = st.text_input("Tel", r['Telefono']), st.text_area("Notas", r['Notas'])
                if st.form_submit_button("Guardar Cambios"):
                    f_val = eent.strftime("%d/%m/%Y") if usar_f else ""
                    df_p.loc[df_p['ID'] == r['ID'], ['Cliente','Pieza','Precio','Notas','Gramos','Horas','Prioridad','Entrega','Telefono']] = [ec, ep, epr, en, eg, eh, eprio, f_val, etel]
                    conn.update(worksheet="Pedidos", data=df_p); st.session_state.df_p = df_p; st.rerun()
            st.download_button("📩 PDF", data=crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Precio'], r['Notas'], r['Gramos'], r['Horas']), file_name=f"VYE_{r['Cliente']}.pdf", key=f"pdf_{r['ID']}")
            if st.button("🗑️ Eliminar", key=f"dl_{r['ID']}"):
                df_p = df_p[df_p['ID'] != r['ID']]; conn.update(worksheet="Pedidos", data=df_p); st.session_state.df_p = df_p; st.rerun()

# --- 9. VISTA: NUEVO ---
elif st.session_state.sec == "NUEVO":
    with st.container(key=f"cont_{st.session_state.reset_key}"):
        with st.form("n_f", clear_on_submit=True):
            nc, ntel, np = st.text_input("Cliente"), st.text_input("WhatsApp (34...)"), st.text_input("Pieza")
            gms, hrs, prio = st.number_input("Gramos", 0.0), st.number_input("Horas", 0.0), st.selectbox("Prioridad", PRIORIDADES, index=1)
            usar_f = st.checkbox("Poner fecha de entrega")
            ent = st.date_input("Entrega") if usar_f else None
            pf = ((0.024 * gms) + (hrs * 1.0)) * (1 + (st.select_slider("Margen %", options=[0,50,100,150,200], value=100)/100))
            st.write(f"### TOTAL: {pf:.2f} €"); nn = st.text_area("Notas")
            if st.form_submit_button("GUARDAR TRABAJO"):
                f_e = ent.strftime("%d/%m/%Y") if usar_f else ""
                nueva = pd.DataFrame([{"ID": datetime.now().strftime("%y%m%d%H%M%S"), "Fecha": datetime.now().strftime("%d/%m/%Y"), "Cliente": nc, "Pieza": np, "Estado": "Pendiente", "Precio": pf, "Gramos": gms, "Horas": hrs, "Notas": nn, "Prioridad": prio, "Entrega": f_e, "Telefono": ntel}])
                df_p = pd.concat([df_p, nueva], ignore_index=True); conn.update(worksheet="Pedidos", data=df_p); st.session_state.df_p = df_p; st.session_state.reset_key +=1; st.rerun()

# --- 10. VISTA: FACTURAS (Historial Unificado) ---
elif st.session_state.sec == "FACTURAS":
    st.markdown("### 📜 Historial de Facturas")
    busc_f = st.text_input("🔍 Buscar por Cliente o Pieza...").lower().strip()
    
    # Usamos df_p para mostrar todo el historial de trabajos creados
    items_f = df_p[df_p['Cliente'].str.lower().str.contains(busc_f, na=False) | df_p['Pieza'].str.lower().str.contains(busc_f, na=False)] if busc_f else df_p
    
    for _, r in items_f.sort_values(by="ID", ascending=False).iterrows():
        # Usamos el diseño de tarjeta original
        st.markdown(card_html(r, r['Estado']), unsafe_allow_html=True)
        # Botón de descarga de PDF para esta factura
        st.download_button(
            "📩 Descargar PDF", 
            data=crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Precio'], r['Notas'], r['Gramos'], r['Horas']), 
            file_name=f"VYE_{r['Cliente']}.pdf", 
            key=f"fct_{r['ID']}"
        )
        st.divider()

# --- 11. STATS ---
elif st.session_state.sec == "STATS":
    st.markdown("## 📊 Centro de Control VYE 3D")
    df_p['F_DT'] = pd.to_datetime(df_p['Fecha'], format="%d/%m/%Y", errors='coerce')
    
    st.markdown("### ⏳ Pendientes y Proyecciones")
    df_pend = df_p[df_p["Estado"] != "Finalizado"]
    if not df_pend.empty:
        p_v, p_g, p_h = df_pend['Precio'].sum(), df_pend['Gramos'].sum(), df_pend['Horas'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas en Espera", f"{p_v:.2f} €")
        c2.metric("Plástico Necesario", f"{p_g/1000:.2f} kg")
        c3.metric("Horas de Luz", f"{p_h:.1f} h")
    else: st.info("No hay trabajos pendientes.")

    st.divider()

    st.markdown("### 📜 Historial de Caja Real")
    df_f_final = df_p[df_p["Estado"] == "Finalizado"].copy()
    if not df_f_final.empty:
        df_f_final['Mes_Año'] = df_f_final['F_DT'].dt.strftime('%m/%Y')
        meses = sorted(df_f_final['Mes_Año'].unique(), reverse=True)
        mes_sel = st.selectbox("Selecciona mes:", meses)
        df_mes_real = df_f_final[df_f_final['Mes_Año'] == mes_sel]
        t_v = df_mes_real['Precio'].sum(); t_g = df_mes_real['Gramos'].sum(); t_h = df_mes_real['Horas'].sum()
        beneficio = t_v - (t_g * 0.024 + t_h * 0.20)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric(f"Ingresos {mes_sel}", f"{t_v:.2f} €")
        col_b.metric("Beneficio Neto", f"{beneficio:.2f} €")
        col_c.metric("Material Gastado", f"{t_g/1000:.2f} kg")
        st.dataframe(df_mes_real[['Fecha', 'Cliente', 'Pieza', 'Precio']], use_container_width=True)
    else: st.info("No hay trabajos finalizados.")

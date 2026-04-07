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
        pdf.set_font("Arial", 'B', 22)
        pdf.set_text_color(r_corp, g_corp, b_corp)
        pdf.cell(30, 20, "VYE")
        pdf.set_text_color(0)
        pdf.set_x(35)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(100, 10, "VYE 3D - SERVICIOS", ln=False)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(100)
    pdf.cell(0, 10, f"FACTURA: #{id_factura}", ln=True, align='R')
    pdf.set_text_color(0)
    pdf.set_draw_color(r_corp, g_corp, b_corp)
    pdf.set_line_width(0.8)
    pdf.line(10, 32, 200, 32)
    pdf.set_y(38)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 6, "PARA:", ln=False)
    pdf.cell(0, 6, "DETALLES DE FECHA:", ln=True)

    def format_es(texto):
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 6, format_es(cliente), ln=False)
    pdf.cell(0, 6, f"{fecha}", ln=True)
    pdf.ln(6)
    pdf.set_fill_color(r_corp, g_corp, b_corp)
    pdf.set_text_color(255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 7, " CONCEPTO / PIEZA", border=0, fill=True)
    pdf.cell(30, 7, " GRAMOS", border=0, fill=True, align='C')
    pdf.cell(30, 7, " HORAS", border=0, fill=True, align='C')
    pdf.cell(40, 7, " TOTAL", border=0, fill=True, align='R')
    pdf.ln(7)
    pdf.set_text_color(0)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_draw_color(220)
    pdf.cell(90, 9, format_es(f" {pieza}"), border='B')
    pdf.cell(30, 9, f" {gramos} g", border='B', align='C')
    pdf.cell(30, 9, f" {horas} h", border='B', align='C')
    pdf.cell(40, 9, f" {total:.2f} EUR ", border='B', align='R')
    pdf.ln(10)
    if notas and str(notas).lower() != 'nan' and str(notas).strip() != "":
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(r_corp, g_corp, b_corp)
        pdf.cell(0, 7, "OBSERVACIONES:", ln=True)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(50)
        pdf.multi_cell(0, 5, format_es(notas))
        pdf.ln(6)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(125, 10, "", border=0)
    pdf.cell(65, 10, format_es(f" TOTAL A PAGAR: {total:.2f} EUR "), border=0, fill=True, align='R')
    pdf.set_y(-38)
    pdf.set_font("Arial", 'B', 8)
    pdf.set_text_color(120)
    pdf.cell(0, 4, format_es("Gracias por confiar en VYE 3D para tus proyectos de fabricación aditiva."), align='C', ln=True)
    pdf.set_text_color(r_corp, g_corp, b_corp)
    pdf.cell(0, 4, "Instagram: @vye3d  |  Email: vye3d@hotmail.com", align='C', ln=True)
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
.stat-card { background-color: #f8f9fa; border-radius: 10px; padding: 12px 16px; border-left: 5px solid #6f42c1; margin-bottom: 8px; }
.stat-cliente { font-size: 15px; font-weight: 700; color: #343a40; }
.stat-detalle { font-size: 13px; color: #666; margin-top: 2px; }
.stat-total { font-size: 16px; font-weight: 900; color: #6f42c1; margin-top: 4px; }
</style>""", unsafe_allow_html=True)

# --- 5. DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def limpiar_df(df, con_estado=False):
    cols_base = ['ID', 'Fecha', 'Cliente', 'Pieza', 'Precio', 'Gramos', 'Horas', 'Notas', 'Prioridad', 'Entrega', 'Telefono']
    if con_estado:
        cols_base.append('Estado')
    for c in cols_base:
        if c not in df.columns:
            df[c] = ""
    df = df[cols_base].copy()
    df['Prioridad'] = df['Prioridad'].fillna('Media').replace(['', 'nan', 'NaN'], 'Media').astype(str)
    df['ID'] = df['ID'].astype(str).str.replace('.0', '', regex=False)
    df['Cliente'] = df['Cliente'].astype(str).replace(['nan', 'NaN'], '')
    df['Pieza'] = df['Pieza'].astype(str).replace(['nan', 'NaN'], '')
    df['Notas'] = df['Notas'].astype(str).replace(['nan', 'NaN'], '')
    df['Telefono'] = df['Telefono'].astype(str).replace(['nan', 'NaN'], '')
    df['Entrega'] = df['Entrega'].astype(str).replace(['nan', 'NaN', 'None', ''], '')
    for n in ['Precio', 'Gramos', 'Horas']:
        df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0.0)
    return df

@st.cache_data(ttl=1)
def cargar_todo():
    try:
        p = conn.read(worksheet="Pedidos", ttl=0)
        f = conn.read(worksheet="Facturas", ttl=0)
        return limpiar_df(p, True), limpiar_df(f, False)
    except:
        return None, None

if 'df_p' not in st.session_state:
    st.session_state.df_p, st.session_state.df_f = cargar_todo()
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

# FIX 3: Guardia contra None si la conexión falla
if st.session_state.df_p is None:
    st.error("⚠️ Error de conexión con Google Sheets. Revisa tus credenciales.")
    if st.button("Reintentar"):
        st.cache_data.clear()
        st.session_state.df_p = None
        st.rerun()
    st.stop()

ESTADOS = ["Pendiente", "Diseñando", "Imprimiendo / Posprocesando", "Finalizado"]
PRIORIDADES = ["Baja", "Media", "Alta", "URGENTE"]

def card_html(r, badge=""):
    prio = str(r['Prioridad']).lower()
    e_str = str(r['Entrega']).strip()
    ent = f"<p class='card-entrega'>⏱️ ENTREGA: {e_str}</p>" if e_str and e_str.lower() != 'nan' else ""
    nt = f"<p class='card-nota'>Notas: {r['Notas']}</p>" if r['Notas'] and str(r['Notas']).lower() != 'nan' and str(r['Notas']).strip() != "" else ""
    bdg = f"<div class='badge-estado'>{badge}</div>" if badge else ""
    return f'<div class="card-container card-{prio}">{bdg}{ent}<p class="card-fecha">{r["Fecha"]} | ID: {r["ID"]}</p><p class="card-nombre">{r["Cliente"]}</p><p class="card-pieza">Pieza: {r["Pieza"]}</p>{nt}<p class="card-precio">{r["Precio"]:.2f} €</p></div>'

# --- 6. ACCESO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso VYE 3D</h1>", unsafe_allow_html=True)
    pass_input = st.text_input("Contraseña", type="password", key="login_pass")
    if st.button("ENTRAR"):
        if pass_input == PASSWORD_APP:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

st.markdown("<h1 style='text-align: center; color: #6f42c1; text-transform: uppercase; font-size: 50px; font-weight: 900;'>VYE 3D</h1>", unsafe_allow_html=True)

# --- 7. NAVEGACIÓN ---
if 'sec' not in st.session_state:
    st.session_state.sec = "TRABAJOS"
n_cols = st.columns(4)
if n_cols[0].button("TRABAJOS"): st.session_state.sec = "TRABAJOS"; st.rerun()
if n_cols[1].button("NUEVO"): st.session_state.sec = "NUEVO"; st.rerun()
if n_cols[2].button("FACTURAS"): st.session_state.sec = "FACTURAS"; st.rerun()
if n_cols[3].button("📊"): st.session_state.sec = "STATS"; st.rerun()
st.divider()

df_p, df_f = st.session_state.df_p, st.session_state.df_f

# --- 8. VISTA: TRABAJOS ---
if st.session_state.sec == "TRABAJOS":
    busc = st.text_input("🔍 Buscar Cliente o Pieza...").lower().strip()
    if busc:
        items = df_p[
            df_p['Cliente'].str.lower().str.contains(busc, na=False) |
            df_p['Pieza'].str.lower().str.contains(busc, na=False)
        ]
    else:
        est_sel = st.selectbox("Estado:", ESTADOS)
        items = df_p[df_p["Estado"] == est_sel]

    items = items.copy()
    items['pv'] = items['Prioridad'].map({"Baja": 1, "Media": 2, "Alta": 3, "URGENTE": 4}).fillna(2)

    for idx, r in items.sort_values(by="pv", ascending=False).iterrows():
        st.markdown(card_html(r, r['Estado'] if busc else ""), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        upd = c1.selectbox("Cambiar Estado:", ESTADOS, index=ESTADOS.index(r['Estado']), key=f"upd_{r['ID']}")
        if upd != r['Estado']:
            df_p.at[idx, "Estado"] = upd
            conn.update(worksheet="Pedidos", data=df_p)
            st.session_state.df_p = df_p
            st.rerun()

        if r['Telefono'] and str(r['Telefono']).lower() != 'nan' and r['Telefono'] != "":
            url = f"https://wa.me/{r['Telefono']}?text=" + urllib.parse.quote(f"Hola {r['Cliente']}, tu pedido {r['Pieza']} de VYE 3D ya está listo!")
            c2.link_button("🟢 WHATSAPP", url)

        with st.expander("MODIFICAR / PDF ⚙️"):
            with st.form(f"form_mod_{r['ID']}"):
                ec = st.text_input("Cliente", str(r['Cliente']))
                ep = st.text_input("Pieza", str(r['Pieza']))
                c3, c4, c5 = st.columns(3)
                eg = c3.number_input("Gramos", value=float(r['Gramos']))
                eh = c4.number_input("Horas", value=float(r['Horas']))
                epr = c5.number_input("Precio (€)", value=float(r['Precio']))
                c6, c7, c8 = st.columns(3)
                eprio = c6.selectbox("Prioridad", PRIORIDADES, index=PRIORIDADES.index(r['Prioridad']))
                try:
                    ent_val = datetime.strptime(str(r['Entrega']), "%d/%m/%Y")
                except:
                    ent_val = datetime.now()
                eent = c7.date_input("Entrega", value=ent_val)
                etel = c8.text_input("Tel.", str(r['Telefono']))
                en = st.text_area("Notas", str(r['Notas']))

                if st.form_submit_button("Guardar"):
                    cols_to_upd = {
                        'Cliente': ec, 'Pieza': ep, 'Precio': epr, 'Notas': str(en).strip(),
                        'Gramos': eg, 'Horas': eh, 'Prioridad': eprio,
                        'Entrega': eent.strftime("%d/%m/%Y"), 'Telefono': etel
                    }
                    for col, val in cols_to_upd.items():
                        df_p.at[idx, col] = val
                        idx_f = df_f[df_f['ID'] == r['ID']].index
                        if not idx_f.empty:
                            df_f.at[idx_f[0], col] = val
                    conn.update(worksheet="Pedidos", data=df_p)
                    conn.update(worksheet="Facturas", data=df_f)
                    st.session_state.df_p, st.session_state.df_f = df_p, df_f
                    # FIX 1: Mensaje genérico sin nombre hardcodeado
                    st.success("¡Datos actualizados correctamente!")
                    st.rerun()

            st.download_button(
                "📩 PDF",
                data=crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Precio'], r['Notas'], r['Gramos'], r['Horas']),
                file_name=f"VYE_{r['Cliente']}.pdf",
                key=f"pdf_{r['ID']}"
            )

            # FIX 2: Borrado con confirmación doble
            ck = f"dk_{r['ID']}"
            if ck not in st.session_state:
                st.session_state[ck] = False
            if not st.session_state[ck]:
                if st.button("🗑️ Eliminar Trabajo", key=f"del_{r['ID']}"):
                    st.session_state[ck] = True
                    st.rerun()
            else:
                st.warning("¿Seguro que quieres borrar este trabajo?")
                b1, b2 = st.columns(2)
                if b1.button("SÍ, BORRAR ✅", key=f"si_{r['ID']}"):
                    df_p = df_p[df_p['ID'] != r['ID']]
                    df_f = df_f[df_f['ID'] != r['ID']]
                    conn.update(worksheet="Pedidos", data=df_p)
                    conn.update(worksheet="Facturas", data=df_f)
                    st.session_state.df_p, st.session_state.df_f = df_p, df_f
                    st.session_state[ck] = False
                    st.rerun()
                if b2.button("CANCELAR ❌", key=f"no_{r['ID']}"):
                    st.session_state[ck] = False
                    st.rerun()
        st.divider()

# --- 9. VISTA: NUEVO ---
elif st.session_state.sec == "NUEVO":
    st.markdown("### Crear Nuevo Trabajo")
    with st.container(key=f"container_nuevo_{st.session_state.reset_key}"):
        with st.form("form_nuevo_trabajo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nc = c1.text_input("Nombre del Cliente")
            ntel = c2.text_input("WhatsApp (con 34 delante)")
            nueva_pieza = st.text_input("Nombre de la Pieza")
            c3, c4, c5 = st.columns(3)
            gms = c3.number_input("Gramos", 0.0)
            hrs = c4.number_input("Horas", 0.0)
            prio = c5.selectbox("Prioridad", PRIORIDADES, index=1)
            ent = st.date_input("Fecha de Entrega", value=datetime.now())
            mgn = st.select_slider("Margen %", options=[0, 50, 100, 150, 200], value=100)
            pf = ((0.024 * gms) + (hrs * 1.0)) * (1 + mgn / 100)
            st.write(f"### TOTAL ESTIMADO: {pf:.2f} €")
            nn = st.text_area("Notas / Detalles")
            if st.form_submit_button("GUARDAR EN BASE DE DATOS"):
                if nc and nueva_pieza:
                    id_n = datetime.now().strftime("%y%m%d%H%M%S")
                    nueva = pd.DataFrame([{
                        "ID": id_n, "Fecha": datetime.now().strftime("%d/%m/%Y"),
                        "Cliente": nc, "Pieza": nueva_pieza, "Estado": "Pendiente",
                        "Precio": pf, "Gramos": gms, "Horas": hrs, "Notas": nn,
                        "Prioridad": prio, "Entrega": ent.strftime("%d/%m/%Y"), "Telefono": ntel
                    }])
                    df_p_new = pd.concat([df_p, nueva], ignore_index=True)
                    df_f_new = pd.concat([df_f, nueva.drop(columns=['Estado'])], ignore_index=True)
                    conn.update(worksheet="Pedidos", data=df_p_new)
                    conn.update(worksheet="Facturas", data=df_f_new)
                    st.session_state.df_p, st.session_state.df_f = df_p_new, df_f_new
                    st.session_state.reset_key += 1
                    st.success("¡Trabajo guardado correctamente!")
                    st.rerun()
                else:
                    st.error("Por favor, rellena el Cliente y la Pieza.")

# --- 10. FACTURAS ---
elif st.session_state.sec == "FACTURAS":
    busc = st.text_input("🔍 Buscar Factura...").lower().strip()
    # FIX 4: na=False para evitar errores con celdas vacías
    if busc:
        items = df_f[
            df_f['Cliente'].str.lower().str.contains(busc, na=False) |
            df_f['Pieza'].str.lower().str.contains(busc, na=False)
        ]
    else:
        items = df_f
    for _, r in items.sort_values(by="ID", ascending=False).iterrows():
        st.markdown(card_html(r), unsafe_allow_html=True)
        st.download_button(
            "📩 Descargar PDF",
            data=crear_pdf(r['ID'], r['Fecha'], r['Cliente'], r['Pieza'], r['Precio'], r['Notas'], r['Gramos'], r['Horas']),
            file_name=f"VYE_{r['Cliente']}.pdf",
            key=f"fct_{r['ID']}"
        )
        st.divider()

# --- 11. DASHBOARD ---
elif st.session_state.sec == "STATS":
    st.markdown('<p class="titulo-seccion">Dashboard Ejecutivo VYE 3D</p>', unsafe_allow_html=True)
    if not df_f.empty:
        df_s = df_f.copy()
        df_s['Precio'] = pd.to_numeric(df_s['Precio'], errors='coerce').fillna(0.0)
        df_s['Gramos'] = pd.to_numeric(df_s['Gramos'], errors='coerce').fillna(0.0)
        df_s['Horas'] = pd.to_numeric(df_s['Horas'], errors='coerce').fillna(0.0)

        total_v = df_s['Precio'].sum()
        total_g = df_s['Gramos'].sum()
        total_h = df_s['Horas'].sum()
        coste_m = total_g * 0.024
        coste_maquina = total_h * 0.20
        beneficio_n = total_v - (coste_m + coste_maquina)

        st.markdown("### 💰 Finanzas Reales")
        m1, m2, m3 = st.columns(3)
        m1.metric("Ingresos Totales", f"{total_v:.2f} €")
        m2.metric("Beneficio Neto Est.", f"{beneficio_n:.2f} €", delta=f"{((beneficio_n/total_v)*100) if total_v > 0 else 0:.1f}% Margen")
        m3.metric("Ticket Medio", f"{(total_v/len(df_s)):.2f} €")

        st.markdown("### ⚙️ Rendimiento Taller")
        m4, m5, m6 = st.columns(3)
        m4.metric("Filamento Gastado", f"{total_g/1000:.2f} kg")
        m5.metric("Tiempo de Vuelo", f"{total_h:.1f} h")
        m6.metric("Trabajos", len(df_s))

        st.divider()
        st.markdown("**Evolución Mensual**")
        df_s['F_DT'] = pd.to_datetime(df_s['Fecha'], format="%d/%m/%Y", errors='coerce')
        df_chart = df_s.dropna(subset=['F_DT'])
        if not df_chart.empty:
            try:
                vm = df_chart.set_index('F_DT').resample('ME')['Precio'].sum()
            except Exception:
                vm = df_chart.set_index('F_DT').resample('M')['Precio'].sum()
            st.bar_chart(vm)

        st.divider()
        st.markdown("**🏆 Ranking de Clientes (Top 5)**")
        ranking = (
            df_s.groupby('Cliente')
            .agg(Total=('Precio', 'sum'), Trabajos=('Precio', 'count'))
            .sort_values('Total', ascending=False)
            .head(5)
            .reset_index()
        )
        for i, r in ranking.iterrows():
            st.markdown(f'<div class="stat-card"><p class="stat-cliente">#{i+1} 👤 {r["Cliente"]}</p><p class="stat-detalle">{int(r["Trabajos"])} trabajos realizados</p><p class="stat-total">Total Facturado: {r["Total"]:.2f} €</p></div>', unsafe_allow_html=True)
    else:
        st.info("No hay datos para mostrar.")

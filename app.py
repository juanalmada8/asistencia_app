import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from pytz import timezone

# Configuración general
st.set_page_config(page_title="Registro de Asistencia", page_icon="📋", layout="centered")

st.markdown("""<link rel="shortcut icon" href="favicon.png">""", unsafe_allow_html=True)

# 🔐 Autenticación con clave
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("### 🔐 Ingreso de entrenador")
    pwd = st.text_input("Clave de acceso", type="password")
    if pwd == st.secrets["app"]["password"]:
        st.session_state.logged_in = True
        st.rerun()
    elif pwd != "":
        st.error("❌ Clave incorrecta")
    st.stop()

# Mostrar logo
logo = Image.open("icon.jpg")
st.image(logo, width=120)

# 📌 Zona horaria
ARG_TZ = timezone("America/Argentina/Buenos_Aires")

# 📌 Cargar jugadoras
@st.cache_data(ttl=300)
def cargar_jugadoras():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["credentials"], scope)
    client = gspread.authorize(creds)
    hoja = client.open("Asistencia Hockey").worksheet("Jugadoras")
    return hoja.col_values(1)[1:]  # sin encabezado

# 📌 Obtener asistencia previa (último registro por jugadora y fecha)
@st.cache_data(ttl=300)
def obtener_asistencias_previas(fecha):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["credentials"], scope)
    client = gspread.authorize(creds)

    hoja = client.open("Asistencia Hockey").worksheet("Asistencias")
    datos = hoja.get_all_values()
    encabezados = datos[0]
    idx_fecha = encabezados.index("Fecha")
    idx_jugadora = encabezados.index("Jugadora")
    idx_asistio = encabezados.index("Asistió")

    fecha_str = fecha.strftime("%Y-%m-%d")
    ultimos_registros = {}

    for fila in datos[1:]:
        if len(fila) <= max(idx_fecha, idx_jugadora, idx_asistio):
            continue
        f_fecha = fila[idx_fecha].strip()
        f_jugadora = fila[idx_jugadora].strip()
        f_asistio = fila[idx_asistio].strip().upper()
        if f_fecha == fecha_str:
            ultimos_registros[f_jugadora] = f_asistio

    jugadoras_presentes = [j for j, estado in ultimos_registros.items() if estado == "SÍ"]
    return jugadoras_presentes

# 📌 Upsert: actualiza si existe, agrega si no
def upsert_asistencias(sheet_id, hoja_nombre, nuevas_filas):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["credentials"], scope)
    client = gspread.authorize(creds)

    hoja = client.open_by_key(sheet_id).worksheet(hoja_nombre)
    datos = hoja.get_all_values()
    encabezados = datos[0]

    idx_fecha = encabezados.index("Fecha")
    idx_jugadora = encabezados.index("Jugadora")

    nuevas_dict = {(f[0], f[1]): f for f in nuevas_filas}
    filas_existentes = datos[1:]
    filas_actualizadas = set()
    nuevas_para_agregar = []

    for i, fila in enumerate(filas_existentes):
        if len(fila) < max(idx_fecha, idx_jugadora) + 1:
            continue
        clave = (fila[idx_fecha].strip(), fila[idx_jugadora].strip())
        if clave in nuevas_dict:
            hoja.update(f"A{i+2}", [nuevas_dict[clave]])
            filas_actualizadas.add(clave)

    for clave, fila in nuevas_dict.items():
        if clave not in filas_actualizadas:
            nuevas_para_agregar.append(fila)

    if nuevas_para_agregar:
        hoja.append_rows(nuevas_para_agregar, value_input_option="USER_ENTERED")

# 🏑 UI principal
st.title("Registro de Asistencia 🏑")
st.markdown("### 🗓️ Fecha del entrenamiento")
fecha = st.date_input("Seleccioná la fecha", value=datetime.now(ARG_TZ).date())

# Cargar jugadoras y asistencias previas
jugadoras = cargar_jugadoras()
jugadoras_presentes = obtener_asistencias_previas(fecha)
jugadoras_faltantes = [j for j in jugadoras if j not in jugadoras_presentes]

if not jugadoras_faltantes:
    st.success("✅ Todas las jugadoras ya tienen registrada la asistencia para esta fecha.")
    st.stop()

st.markdown("### Jugadoras")
datos_asistencia = []

for jugadora in jugadoras_faltantes:
    st.markdown(f"**{jugadora}**")
    asistio = st.checkbox("Asistió", key=f"asistio_{jugadora}")
    tarde = False
    comentario = ""

    if asistio:
        tarde = st.checkbox("Llegó tarde", key=f"tarde_{jugadora}")
    comentario = st.text_input("Comentario (opcional)", key=f"comentario_{jugadora}")

    datos_asistencia.append({
        "jugadora": jugadora,
        "asistio": "SÍ" if asistio else "NO",
        "llego_tarde": "SÍ" if asistio and tarde else "NO",
        "comentario": comentario.upper() if comentario else ""
    })

st.markdown("---")

if st.button("✅ Guardar asistencia"):
    nuevas_filas = [
        [
            fecha.strftime("%Y-%m-%d"),
            d["jugadora"],
            d["asistio"],
            d["llego_tarde"],
            d["comentario"]
        ] for d in datos_asistencia
    ]
    try:
        upsert_asistencias(
            sheet_id="1MIzfkUB9kOsHyvNKVfBcS0VzmGbJnE4w8ufnvxHd5Po",
            hoja_nombre="Asistencias",
            nuevas_filas=nuevas_filas
        )
        total_asistieron = sum(1 for d in datos_asistencia if d["asistio"] == "SÍ")
        st.success(f"✅ ¡Asistencia guardada con éxito! 🟢 {total_asistieron} jugadoras asistieron.")
    except Exception as e:
        st.error("❌ Error al guardar la asistencia.")
        st.exception(e)

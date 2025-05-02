import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from PIL import Image
import json
from time import sleep

st.set_page_config(page_title="Registro de Asistencia", page_icon="📋", layout="centered")

st.markdown(
    """
    <link rel="shortcut icon" href="favicon.png">
    """,
    unsafe_allow_html=True
)

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

# 🧠 CACHE: agrupar conexión + lecturas en 1 sola función
@st.cache_data(ttl=300)
def cargar_datos():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = st.secrets["credentials"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("Asistencia Hockey")
    jugadoras_ws = spreadsheet.worksheet("Jugadoras")
    asistencias_ws = spreadsheet.worksheet("Asistencias")
    jugadoras = jugadoras_ws.col_values(1)[1:]  # sin encabezado

    return jugadoras, asistencias_ws

jugadoras, asistencias_ws = cargar_datos()

# UI
st.title("Registro de Asistencia 🏑")
st.markdown("### 🗓️ Fecha del entrenamiento")
fecha = st.date_input("", value=datetime.today())

st.markdown("### Jugadoras")
datos_asistencia = []

for jugadora in jugadoras:
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
    nuevas_filas = []
    for d in datos_asistencia:
        nuevas_filas.append([
            str(fecha),
            d["jugadora"],
            d["asistio"],
            d["llego_tarde"],
            d["comentario"]
        ])
    try:
        for fila in nuevas_filas:
            asistencias_ws.append_row(fila)
        st.success("✅ ¡Asistencia guardada con éxito!")
    except Exception as e:
        st.error("❌ Error al guardar la asistencia.")
        st.exception(e)

        
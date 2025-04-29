import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from PIL import Image
import json

# ✅ Esto tiene que ir antes que cualquier otro st.*
st.set_page_config(page_title="Registro de Asistencia", page_icon="📋", layout="centered")

# 🔐 Login simple
st.markdown("### 🔐 Ingreso de entrenador")
pwd = st.text_input("Clave de acceso", type="password")

if pwd != st.secrets["app"]["password"]:
    st.warning("⚠️ Ingresá la clave correcta para continuar.")
    st.stop()

# Mostrar logo del club
logo = Image.open("icon.jpg")
st.image(logo, width=120)


# Autenticación
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = st.secrets["credentials"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)

client = gspread.authorize(creds)

spreadsheet = client.open("Asistencia Hockey")
jugadoras_ws = spreadsheet.worksheet("Jugadoras")
asistencias_ws = spreadsheet.worksheet("Asistencias")

@st.cache_data(ttl=300)
def obtener_jugadoras():
    return jugadoras_ws.col_values(1)[1:]

jugadoras = obtener_jugadoras()

# UI
st.title("Registro de Asistencia 🏑")
st.markdown("### 📅 Fecha del entrenamiento")
fecha = st.date_input("", value=datetime.today())

st.markdown("### Jugadoras")
datos_asistencia = []

# Mobile-friendly: todo en un bloque por jugadora
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
    asistencias_ws.append_rows(nuevas_filas)
    st.success("✅ ¡Asistencia guardada con éxito!")

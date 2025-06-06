# app.py
import streamlit as st
from datetime import datetime
from config import SHEET_ID, ARG_TZ
from services.google_sheets import cargar_jugadoras, obtener_asistencias_previas, upsert_asistencias
from services.asistencia import generar_resumen
from ui.login import login
from ui.registro import mostrar_formulario_asistencia
from ui.resumen import mostrar_boton_resumen

# Configuración general
st.set_page_config(page_title="Registro de Asistencia", page_icon="📋", layout="centered")

# 🔐 Login
if not login():
    st.stop()

# 🏑 UI principal
st.title("Registro de Asistencia 🏑")

# Fecha de entrenamiento
fecha = st.date_input("Seleccioná la fecha", value=datetime.now(ARG_TZ).date())

# ⚡ Cache manual en session_state para jugadoras
if "jugadoras" not in st.session_state:
    st.session_state.jugadoras = cargar_jugadoras()

# ⚡ Cache manual en session_state para asistencias previas (por fecha)
if "asistencias_previas" not in st.session_state or st.session_state.get("asistencia_fecha") != fecha:
    st.session_state.asistencias_previas = obtener_asistencias_previas(fecha)
    st.session_state.asistencia_fecha = fecha

# Cargar desde cache
jugadoras = st.session_state.jugadoras
jugadoras_presentes = st.session_state.asistencias_previas
jugadoras_faltantes = [j for j in jugadoras if j not in jugadoras_presentes]

if not jugadoras_faltantes:
    st.success("✅ Todas las jugadoras ya tienen registrada la asistencia para esta fecha.")
else:
    nuevas_filas = mostrar_formulario_asistencia(jugadoras_faltantes, fecha)
    if nuevas_filas:
        try:
            upsert_asistencias(SHEET_ID, "Asistencias", nuevas_filas)
            total = sum(1 for fila in nuevas_filas if fila[2] == "SÍ")
            st.success(f"✅ ¡Asistencia guardada! {total} jugadoras asistieron.")
            # Invalidar cache para fecha actual, para forzar nueva lectura si se repite
            del st.session_state["asistencias_previas"]
        except Exception as e:
            st.error("❌ Error al guardar la asistencia.")
            st.exception(e)

# 📊 Botón de resumen
mostrar_boton_resumen(SHEET_ID)

# main.py
import streamlit as st
from datetime import datetime
from config import SHEET_ID, ARG_TZ
from services.google_sheets import cargar_jugadoras, obtener_asistencias_previas, upsert_asistencias
from services.asistencia import generar_resumen
from ui.login import login
from ui.registro import mostrar_formulario_asistencia
from ui.resumen import mostrar_boton_resumen

# Configuracion inicial
st.set_page_config(page_title="Registro de Asistencia", page_icon="📋", layout="centered")

# Login
if not login():
    st.stop()

# UI principal
st.title("Registro de Asistencia 🏑")
fecha = st.date_input("Seleccioná la fecha", value=datetime.now(ARG_TZ).date())

jugadoras = cargar_jugadoras()
jugadoras_presentes = obtener_asistencias_previas(fecha)
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
        except Exception as e:
            st.error("❌ Error al guardar la asistencia.")
            st.exception(e)

# Boton de resumen
mostrar_boton_resumen(SHEET_ID)

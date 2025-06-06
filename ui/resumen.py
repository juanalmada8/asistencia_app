# ui/resumen.py
import streamlit as st
from services.asistencia import generar_resumen

def mostrar_boton_resumen(sheet_id):
    st.markdown("---")
    if st.button("📊 Generar resumen de asistencia"):
        generar_resumen(sheet_id)

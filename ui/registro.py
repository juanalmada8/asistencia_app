# ui/registro.py
import streamlit as st
from utils.helpers import normalizar_asistio, normalizar_tarde, limpiar_texto, to_str_fecha

def mostrar_formulario_asistencia(jugadoras_faltantes, fecha):
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
            "asistio": normalizar_asistio("SÍ" if asistio else "NO"),
            "llego_tarde": normalizar_tarde("SÍ" if asistio and tarde else "NO"),
            "comentario": limpiar_texto(comentario)
        })

    st.markdown("---")

    if st.button("✅ Guardar asistencia"):
        nuevas_filas = [
            [
                to_str_fecha(fecha),
                d["jugadora"],
                d["asistio"],
                d["llego_tarde"],
                d["comentario"]
            ] for d in datos_asistencia
        ]
        return nuevas_filas

    return []

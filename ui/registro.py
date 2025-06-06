# ui/registro.py
import streamlit as st

def mostrar_formulario_asistencia(jugadoras, fecha):
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
        return [
            [
                fecha.strftime("%Y-%m-%d"),
                d["jugadora"],
                d["asistio"],
                d["llego_tarde"],
                d["comentario"]
            ] for d in datos_asistencia
        ]

    return None

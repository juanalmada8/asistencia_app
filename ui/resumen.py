import streamlit as st
import pandas as pd
from services.google_sheets import get_dataframe_from_sheet, exportar_df_a_hoja
from config import ARG_TZ

def generar_resumen(sheet_id):
    df = get_dataframe_from_sheet(sheet_id, "Asistencias")
    if df.empty:
        st.warning("❗ No hay suficientes datos para generar el resumen.")
        return

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Asistió"] = df["Asistió"].str.strip().str.upper()
    df["Llegó tarde"] = df["Llegó tarde"].str.strip().str.upper()
    df["Mes"] = df["Fecha"].dt.to_period("M")

    # Métricas
    entrenamientos_por_mes = df.groupby("Mes")["Fecha"].nunique().reset_index(name="Entrenamientos del mes")
    presencias_por_jugadora_mes = (
        df[df["Asistió"] == "SÍ"]
        .groupby(["Mes", "Jugadora"])
        .size()
        .reset_index(name="Presencias")
    )
    llegadas_tarde_mes = (
        df[(df["Asistió"] == "SÍ") & (df["Llegó tarde"] == "SÍ")]
        .groupby(["Mes", "Jugadora"])
        .size()
        .reset_index(name="Tardanzas")
    )
    ranking = (
        df[df["Asistió"] == "SÍ"]
        .groupby("Jugadora")
        .size()
        .reset_index(name="Total presencias")
        .sort_values("Total presencias", ascending=False)
    )

    # Mostrar en pantalla
    st.subheader("📊 Entrenamientos por mes")
    st.dataframe(entrenamientos_por_mes)

    st.subheader("📈 Presencias por jugadora por mes")
    st.dataframe(presencias_por_jugadora_mes)

    st.subheader("⏱️ Tardanzas por jugadora por mes")
    st.dataframe(llegadas_tarde_mes)

    st.subheader("🏆 Ranking de asistencia")
    st.dataframe(ranking)

    # Exportar al Google Sheet en hoja "Resumen"
    spreadsheet = get_dataframe_from_sheet(sheet_id, "Asistencias", return_client=True)
    try:
        resumen_ws = spreadsheet.worksheet("Resumen")
        spreadsheet.del_worksheet(resumen_ws)
    except:
        pass
    resumen_ws = spreadsheet.add_worksheet(title="Resumen", rows="100", cols="20")

    fila = 1
    fila = exportar_df_a_hoja(resumen_ws, entrenamientos_por_mes, fila)
    fila = exportar_df_a_hoja(resumen_ws, presencias_por_jugadora_mes, fila)
    fila = exportar_df_a_hoja(resumen_ws, llegadas_tarde_mes, fila)
    fila = exportar_df_a_hoja(resumen_ws, ranking, fila)

    st.success("✅ Resumen exportado a hoja 'Resumen'")

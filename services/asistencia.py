# services/asistencia.py
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st


def generar_resumen(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["credentials"], scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    ws = spreadsheet.worksheet("Asistencias")
    raw_data = ws.get_all_values()

    if not raw_data or len(raw_data) < 2:
        st.warning("❗ No hay suficientes datos para generar el resumen.")
        return

    df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Asistió"] = df["Asistió"].str.strip().str.upper()
    df["Llegó tarde"] = df["Llegó tarde"].str.strip().str.upper()
    df["Mes"] = df["Fecha"].dt.to_period("M")

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

    try:
        resumen_ws = spreadsheet.worksheet("Resumen")
        spreadsheet.del_worksheet(resumen_ws)
    except gspread.exceptions.WorksheetNotFound:
        pass
    resumen_ws = spreadsheet.add_worksheet(title="Resumen", rows="100", cols="20")

    def exportar_df(ws, df, fila_inicio):
        ws.update(f"A{fila_inicio}", [df.columns.tolist()] + df.astype(str).values.tolist())
        return fila_inicio + len(df) + 2

    fila = 1
    fila = exportar_df(resumen_ws, entrenamientos_por_mes, fila)
    fila = exportar_df(resumen_ws, presencias_por_jugadora_mes, fila)
    fila = exportar_df(resumen_ws, llegadas_tarde_mes, fila)
    fila = exportar_df(resumen_ws, ranking, fila)

    st.success("✅ Resumen generado en la hoja 'Resumen'")

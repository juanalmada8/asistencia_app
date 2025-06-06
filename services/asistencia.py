# services/google_sheets.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st

# 📌 Autenticación
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["credentials"], scope)
    return gspread.authorize(creds)

# 📌 Leer jugadoras
@st.cache_data(ttl=300)
def cargar_jugadoras():
    client = get_client()
    hoja = client.open("Asistencia Hockey").worksheet("Jugadoras")
    return hoja.col_values(1)[1:]  # sin encabezado

# 📌 Leer asistencias existentes por fecha
@st.cache_data(ttl=300)
def obtener_asistencias_previas(fecha):
    client = get_client()
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

# 📌 Upsert eficiente (batch update + append)
def upsert_asistencias(sheet_id, hoja_nombre, nuevas_filas):
    client = get_client()
    hoja = client.open_by_key(sheet_id).worksheet(hoja_nombre)
    datos = hoja.get_all_values()
    encabezados = datos[0]

    idx_fecha = encabezados.index("Fecha")
    idx_jugadora = encabezados.index("Jugadora")

    existentes = {(fila[idx_fecha], fila[idx_jugadora]): i+2 for i, fila in enumerate(datos[1:]) if len(fila) > max(idx_fecha, idx_jugadora)}
    nuevas_dict = {(f[0], f[1]): f for f in nuevas_filas}

    updates = []
    inserts = []

    for clave, fila in nuevas_dict.items():
        if clave in existentes:
            fila_idx = existentes[clave]
            updates.append((fila_idx, fila))
        else:
            inserts.append(fila)

    # Actualizar filas existentes
    if updates:
        batch_data = []
        for fila_idx, fila in updates:
            batch_data.append({
                "range": f"A{fila_idx}:E{fila_idx}",
                "values": [fila]
            })
        hoja.batch_update(batch_data)

    # Agregar nuevas filas
    if inserts:
        hoja.append_rows(inserts, value_input_option="USER_ENTERED")

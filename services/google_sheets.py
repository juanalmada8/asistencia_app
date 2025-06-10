import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CREDENTIALS_DICT

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_DICT, SCOPE)
    return gspread.authorize(creds)


def cargar_jugadoras():
    client = get_client()
    hoja = client.open_by_key(SHEET_ID).worksheet("Jugadoras")
    return hoja.col_values(1)[1:]  # sin encabezado


def obtener_asistencias_previas(fecha):
    client = get_client()
    hoja = client.open_by_key(SHEET_ID).worksheet("Asistencias")
    datos = hoja.get_all_values()
    encabezados = datos[0]
    idx_fecha = encabezados.index("Fecha")
    idx_jugadora = encabezados.index("Jugadora")
    idx_asistio = encabezados.index("Asist\u00f3")

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

    return [j for j, estado in ultimos_registros.items() if estado == "S\u00cd"]


def upsert_asistencias(sheet_id, hoja_nombre, nuevas_filas):
    client = get_client()
    hoja = client.open_by_key(sheet_id).worksheet(hoja_nombre)
    datos = hoja.get_all_values()
    encabezados = datos[0]

    idx_fecha = encabezados.index("Fecha")
    idx_jugadora = encabezados.index("Jugadora")

    nuevas_dict = {(f[0], f[1]): f for f in nuevas_filas}
    filas_existentes = datos[1:]
    filas_actualizadas = set()
    nuevas_para_agregar = []

    for i, fila in enumerate(filas_existentes):
        if len(fila) < max(idx_fecha, idx_jugadora) + 1:
            continue
        clave = (fila[idx_fecha].strip(), fila[idx_jugadora].strip())
        if clave in nuevas_dict:
            hoja.update(f"A{i+2}", [nuevas_dict[clave]])
            filas_actualizadas.add(clave)

    for clave, fila in nuevas_dict.items():
        if clave not in filas_actualizadas:
            nuevas_para_agregar.append(fila)

    if nuevas_para_agregar:
        hoja.append_rows(nuevas_para_agregar, value_input_option="USER_ENTERED")

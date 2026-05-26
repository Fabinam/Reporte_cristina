import re
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Reportes WhatsApp", layout="wide")

SHEET_NAME = "respaldo_reportes_whatsapp"
WORKSHEET_NAME = "reportes"

COLUMNAS = [
    "fecha_envio",
    "hora_envio",
    "tipo_reporte",
    "equipo",
    "unidad",
    "hora_inicio_actividades",
    "equipo_completo_excavadores",
    "disponibilidad_sombra",
    "estado_harneros",
    "estado_baldes",
    "estado_mesa_harnero",
    "observaciones",
    "texto_original",
    "fecha_registro_app",
]


def conectar_google_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope,
    )

    client = gspread.authorize(credentials)

    try:
        sheet = client.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sheet = client.create(SHEET_NAME)
        sheet.share(st.secrets["google_sheet_user"], perm_type="user", role="writer")

    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=30)
        worksheet.append_row(COLUMNAS)

    return worksheet


def limpiar_texto(texto):
    texto = texto.replace("⁠", "")
    texto = texto.replace("\u200e", "")
    texto = texto.replace("\u200f", "")
    texto = texto.replace("\xa0", " ")
    return texto.strip()


def extraer_campo(texto, patrones):
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def separar_reportes(texto):
    bloques = re.split(r"(?=\[\d{1,2}:\d{2},\s*\d{1,2}/\d{1,2}/\d{4}\])", texto)
    return [b.strip() for b in bloques if b.strip()]


def procesar_reporte(texto):
    texto = limpiar_texto(texto)

    encabezado = re.search(
        r"\[(\d{1,2}:\d{2}),\s*(\d{1,2}/\d{1,2}/\d{4})\]",
        texto,
    )

    hora_envio = encabezado.group(1) if encabezado else ""
    fecha_envio = encabezado.group(2) if encabezado else ""

    tipo_reporte = "Inicio jornada" if "inicio jornada" in texto.lower() else ""

    equipo = extraer_campo(texto, [
        r"Equipo\s*:\s*(.+)",
    ])

    unidad = extraer_campo(texto, [
        r"Unidad\s*:\s*(.+)",
    ])

    hora_inicio = extraer_campo(texto, [
        r"Hora de inicio de actividades\s*:\s*(.+)",
    ])

    equipo_completo = extraer_campo(texto, [
        r"Equipo completo excavadores.*?:\s*(.+)",
    ])

    sombra = extraer_campo(texto, [
        r"Disponibilidad de sombra.*?:\s*(.+)",
    ])

    harneros = extraer_campo(texto, [
        r"Estado de harneros\s*:\s*(.+)",
    ])

    baldes = extraer_campo(texto, [
        r"Estado de baldes\s*:\s*(.+)",
    ])

    mesa = extraer_campo(texto, [
        r"Estado de mesa harnero\s*:\s*(.+)",
    ])

    observaciones = extraer_campo(texto, [
        r"Observaciones\s*:\s*(.+)",
    ])

    return {
        "fecha_envio": fecha_envio,
        "hora_envio": hora_envio,
        "tipo_reporte": tipo_reporte,
        "equipo": equipo,
        "unidad": unidad,
        "hora_inicio_actividades": hora_inicio,
        "equipo_completo_excavadores": equipo_completo,
        "disponibilidad_sombra": sombra,
        "estado_harneros": harneros,
        "estado_baldes": baldes,
        "estado_mesa_harnero": mesa,
        "observaciones": observaciones,
        "texto_original": texto,
        "fecha_registro_app": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def guardar_en_google_sheets(df):
    worksheet = conectar_google_sheets()
    filas = df[COLUMNAS].fillna("").values.tolist()
    worksheet.append_rows(filas)


def cargar_respaldo():
    worksheet = conectar_google_sheets()
    data = worksheet.get_all_records()
    return pd.DataFrame(data)


st.title("Consolidador de reportes WhatsApp")
st.write("Pega uno o varios reportes de WhatsApp. La app los ordena y los guarda en Google Sheets.")

texto = st.text_area("Pegar reportes aquí", height=300)

col1, col2, col3 = st.columns(3)

with col1:
    procesar = st.button("Procesar reportes")

with col2:
    ver_respaldo = st.button("Ver respaldo completo")

with col3:
    limpiar = st.button("Limpiar pantalla")

if limpiar:
    st.rerun()

if procesar:
    if not texto.strip():
        st.warning("Debes pegar al menos un reporte.")
    else:
        reportes = separar_reportes(texto)
        datos = [procesar_reporte(r) for r in reportes]
        df = pd.DataFrame(datos)

        st.subheader("Reportes procesados")
        st.dataframe(df, use_container_width=True)

        guardar_en_google_sheets(df)

        st.success(f"Se guardaron {len(df)} reporte(s) en Google Sheets.")

        excel = df.to_excel("reportes_procesados.xlsx", index=False)

        with open("reportes_procesados.xlsx", "rb") as file:
            st.download_button(
                "Descargar Excel de esta carga",
                file,
                file_name="reportes_procesados.xlsx",
            )

if ver_respaldo:
    df_respaldo = cargar_respaldo()

    if df_respaldo.empty:
        st.info("Todavía no hay reportes guardados.")
    else:
        st.subheader("Respaldo completo")
        st.dataframe(df_respaldo, use_container_width=True)

        archivo = "respaldo_completo_reportes.xlsx"
        df_respaldo.to_excel(archivo, index=False)

        with open(archivo, "rb") as file:
            st.download_button(
                "Descargar respaldo completo",
                file,
                file_name=archivo,
            )

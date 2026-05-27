import re
import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Reportes WhatsApp", layout="wide")

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
    "fecha_procesamiento",
]


def limpiar_texto(texto):
    texto = texto.replace("⁠", "")
    texto = texto.replace("\u200e", "")
    texto = texto.replace("\u200f", "")
    texto = texto.replace("\xa0", " ")
    return texto.strip()


def separar_reportes(texto):
    bloques = re.split(
        r"(?=\[\d{1,2}:\d{2},\s*\d{1,2}/\d{1,2}/\d{4}\])",
        texto
    )
    return [b.strip() for b in bloques if b.strip()]


def extraer_campo(texto, patron):
    match = re.search(patron, texto, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def procesar_reporte(texto):
    texto = limpiar_texto(texto)

    encabezado = re.search(
        r"\[(\d{1,2}:\d{2}),\s*(\d{1,2}/\d{1,2}/\d{4})\]",
        texto
    )

    return {
        "fecha_envio": encabezado.group(2) if encabezado else "",
        "hora_envio": encabezado.group(1) if encabezado else "",
        "tipo_reporte": "Inicio jornada" if "inicio jornada" in texto.lower() else "",
        "equipo": extraer_campo(texto, r"Equipo\s*:\s*(.+)"),
        "unidad": extraer_campo(texto, r"Unidad\s*:\s*(.+)"),
        "hora_inicio_actividades": extraer_campo(texto, r"Hora de inicio de actividades\s*:\s*(.+)"),
        "equipo_completo_excavadores": extraer_campo(texto, r"Equipo completo excavadores.*?:\s*(.+)"),
        "disponibilidad_sombra": extraer_campo(texto, r"Disponibilidad de sombra.*?:\s*(.+)"),
        "estado_harneros": extraer_campo(texto, r"Estado de harneros\s*:\s*(.+)"),
        "estado_baldes": extraer_campo(texto, r"Estado de baldes\s*:\s*(.+)"),
        "estado_mesa_harnero": extraer_campo(texto, r"Estado de mesa harnero\s*:\s*(.+)"),
        "observaciones": extraer_campo(texto, r"Observaciones\s*:\s*(.+)"),
        "texto_original": texto,
        "fecha_procesamiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reportes")
    output.seek(0)
    return output


st.title("Consolidador de reportes WhatsApp")

st.write("Pega uno o varios reportes. La app los ordena en una tabla y permite descargar un Excel.")

texto = st.text_area("Pegar reportes aquí", height=300)

col1, col2 = st.columns(2)

with col1:
    procesar = st.button("Procesar reportes")

with col2:
    limpiar = st.button("Limpiar pantalla")

if limpiar:
    st.rerun()

if procesar:
    if not texto.strip():
        st.warning("Debes pegar al menos un reporte.")
    else:
        reportes = separar_reportes(texto)
        datos = [procesar_reporte(r) for r in reportes]
        df = pd.DataFrame(datos, columns=COLUMNAS)

        st.subheader("Reportes procesados")
        st.dataframe(df, use_container_width=True)

        excel = generar_excel(df)

        st.download_button(
            label="Descargar Excel",
            data=excel,
            file_name="reportes_whatsapp.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

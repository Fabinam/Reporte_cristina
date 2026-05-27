import re
import hashlib
from io import BytesIO
from datetime import datetime, date

import pandas as pd
import streamlit as st
from dateutil import parser


st.set_page_config(page_title="Consolidador de reportes WhatsApp", layout="wide")

COLUMNAS_REPORTE = [
    "id_reporte", "fecha_reporte", "fecha_usada_por_defecto", "tipo_reporte",
    "equipo", "unidad", "hora_inicio_actividades",
    "equipo_completo_excavadores", "disponibilidad_sombra",
    "estado_harneros", "estado_baldes", "estado_mesa_harnero",
    "observaciones", "estado_validacion", "campos_faltantes",
    "fecha_procesamiento",
]

COLUMNAS_ORIGINAL = ["id_reporte", "fecha_procesamiento", "texto_original"]

COLUMNAS_FALTANTES = [
    "id_reporte", "campo", "valor_final", "fue_completado_manual"
]

CAMPOS_OBLIGATORIOS = [
    "fecha_reporte", "equipo", "unidad", "hora_inicio_actividades",
    "equipo_completo_excavadores", "disponibilidad_sombra",
    "estado_harneros", "estado_baldes", "estado_mesa_harnero",
    "observaciones",
]

ETIQUETAS = {
    "fecha_reporte": "Fecha",
    "equipo": "Equipo",
    "unidad": "Unidad",
    "hora_inicio_actividades": "Hora de inicio de actividades",
    "equipo_completo_excavadores": "Equipo completo excavadores",
    "disponibilidad_sombra": "Disponibilidad de sombra",
    "estado_harneros": "Estado de harneros",
    "estado_baldes": "Estado de baldes",
    "estado_mesa_harnero": "Estado de mesa harnero",
    "observaciones": "Observaciones",
}


def iniciar_estado():
    if "datos_originales" not in st.session_state:
        st.session_state["datos_originales"] = []
    if "respaldos" not in st.session_state:
        st.session_state["respaldos"] = []
    if "faltantes_por_reporte" not in st.session_state:
        st.session_state["faltantes_por_reporte"] = {}


def limpiar_texto(texto):
    texto = texto.replace("⁠", "")
    texto = texto.replace("\u200e", "")
    texto = texto.replace("\u200f", "")
    texto = texto.replace("\xa0", " ")
    texto = texto.replace("\t", " ")
    texto = re.sub(r"[•●▪◦]", "\n", texto)
    texto = re.sub(r"(?m)^\s*[-*]\s*", "", texto)

    etiquetas = [
        "fecha", "equipo", "unidad", "hora de inicio de actividades",
        "equipo completo excavadores", "disponibilidad de sombra",
        "estado de harneros", "estado de baldes",
        "estado de mesa harnero", "observaciones",
    ]

    for etiqueta in etiquetas:
        texto = re.sub(rf"(?i)\b({etiqueta})\s*:", rf"\n\1:", texto)

    texto = re.sub(r"\n{2,}", "\n", texto)
    return texto.strip()


def separar_reportes(texto):
    bloques = re.split(r"(?i)(?=Reporte\s+de\s+inicio\s+Jornada)", texto.strip())
    bloques = [b.strip() for b in bloques if b.strip()]

    if len(bloques) <= 1:
        bloques = re.split(
            r"(?=\[\d{1,2}:\d{2},\s*\d{1,2}/\d{1,2}/\d{2,4}\])",
            texto.strip()
        )
        bloques = [b.strip() for b in bloques if b.strip()]

    return bloques


def generar_id_reporte(texto):
    return hashlib.md5(texto.strip().encode("utf-8")).hexdigest()[:10]


def extraer_campo(texto, etiqueta):
    patron = (
        rf"(?i){etiqueta}\s*:\s*"
        rf"(.*?)"
        rf"(?=\n(?:fecha|equipo|unidad|hora de inicio de actividades|"
        rf"equipo completo excavadores|disponibilidad de sombra|"
        rf"estado de harneros|estado de baldes|estado de mesa harnero|"
        rf"observaciones)\s*:|\Z)"
    )
    match = re.search(patron, texto, flags=re.DOTALL)
    if not match:
        return ""

    valor = match.group(1).strip()
    valor = re.sub(r"\s+", " ", valor)
    return valor


def normalizar_fecha(valor_fecha):
    if not valor_fecha or not str(valor_fecha).strip():
        return date.today().strftime("%d/%m/%Y"), True

    valor = str(valor_fecha).strip().lower().replace(" de ", " ")

    meses = {
        "enero": "january", "febrero": "february", "marzo": "march",
        "abril": "april", "mayo": "may", "junio": "june",
        "julio": "july", "agosto": "august", "septiembre": "september",
        "setiembre": "september", "octubre": "october",
        "noviembre": "november", "diciembre": "december",
    }

    for esp, eng in meses.items():
        valor = valor.replace(esp, eng)

    try:
        fecha = parser.parse(valor, dayfirst=True, fuzzy=True)
        return fecha.strftime("%d/%m/%Y"), False
    except Exception:
        return date.today().strftime("%d/%m/%Y"), True


def normalizar_texto_simple(valor):
    if not valor:
        return ""

    valor = re.sub(r"\s+", " ", str(valor).strip())

    if valor.lower() in [
        "ninguna", "sin observaciones", "sin observación",
        "no hay", "n/a", "na", "no aplica"
    ]:
        return "Sin observaciones"

    return valor


def detectar_tipo_reporte(texto):
    if "inicio jornada" in texto.lower():
        return "Inicio jornada"
    return "No identificado"


def procesar_reporte(texto_original):
    texto_limpio = limpiar_texto(texto_original)
    id_reporte = generar_id_reporte(texto_original)

    fecha_raw = extraer_campo(texto_limpio, "fecha")
    fecha_reporte, fecha_default = normalizar_fecha(fecha_raw)

    datos = {
        "id_reporte": id_reporte,
        "fecha_reporte": fecha_reporte,
        "fecha_usada_por_defecto": "Sí" if fecha_default else "No",
        "tipo_reporte": detectar_tipo_reporte(texto_limpio),
        "equipo": normalizar_texto_simple(extraer_campo(texto_limpio, "equipo")),
        "unidad": normalizar_texto_simple(extraer_campo(texto_limpio, "unidad")),
        "hora_inicio_actividades": normalizar_texto_simple(extraer_campo(texto_limpio, "hora de inicio de actividades")),
        "equipo_completo_excavadores": normalizar_texto_simple(extraer_campo(texto_limpio, "equipo completo excavadores")),
        "disponibilidad_sombra": normalizar_texto_simple(extraer_campo(texto_limpio, "disponibilidad de sombra")),
        "estado_harneros": normalizar_texto_simple(extraer_campo(texto_limpio, "estado de harneros")),
        "estado_baldes": normalizar_texto_simple(extraer_campo(texto_limpio, "estado de baldes")),
        "estado_mesa_harnero": normalizar_texto_simple(extraer_campo(texto_limpio, "estado de mesa harnero")),
        "observaciones": normalizar_texto_simple(extraer_campo(texto_limpio, "observaciones")),
        "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    faltantes = []

    for campo in CAMPOS_OBLIGATORIOS:
        if not datos.get(campo):
            faltantes.append(campo)

    if fecha_default and not fecha_raw:
        faltantes.append("fecha_reporte")

    faltantes = list(dict.fromkeys(faltantes))

    datos["estado_validacion"] = "Completo" if not faltantes else "Incompleto"
    datos["campos_faltantes"] = ", ".join([ETIQUETAS[c] for c in faltantes])

    respaldo = {
        "id_reporte": id_reporte,
        "fecha_procesamiento": datos["fecha_procesamiento"],
        "texto_original": texto_original.strip(),
    }

    return datos, respaldo, faltantes


def aplicar_correcciones(datos, correcciones, no_completar):
    datos_corregidos = datos.copy()
    registros_faltantes = []

    for campo in CAMPOS_OBLIGATORIOS:
        valor_original = datos_corregidos.get(campo, "")
        fue_manual = "No"

        if campo in correcciones and correcciones[campo].strip():
            datos_corregidos[campo] = correcciones[campo].strip()
            fue_manual = "Sí"
        elif campo in no_completar and not valor_original:
            datos_corregidos[campo] = "No informado"

        if campo in correcciones or campo in no_completar:
            registros_faltantes.append({
                "id_reporte": datos_corregidos["id_reporte"],
                "campo": ETIQUETAS[campo],
                "valor_final": datos_corregidos.get(campo, ""),
                "fue_completado_manual": fue_manual,
            })

    faltantes_finales = [
        campo for campo in CAMPOS_OBLIGATORIOS
        if not datos_corregidos.get(campo)
    ]

    datos_corregidos["estado_validacion"] = "Completo" if not faltantes_finales else "Incompleto"
    datos_corregidos["campos_faltantes"] = ", ".join([ETIQUETAS[c] for c in faltantes_finales])

    return datos_corregidos, registros_faltantes


def generar_excel(df_reportes, df_originales, df_faltantes):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_reportes.to_excel(writer, index=False, sheet_name="Reporte estructurado")
        df_originales.to_excel(writer, index=False, sheet_name="Mensajes originales")
        df_faltantes.to_excel(writer, index=False, sheet_name="Faltantes corregidos")
    output.seek(0)
    return output


def generar_txt(df_originales):
    partes = []

    for i, row in df_originales.iterrows():
        partes.append("=" * 70)
        partes.append(f"REPORTE {i + 1}")
        partes.append(f"ID: {row['id_reporte']}")
        partes.append(f"Fecha procesamiento: {row['fecha_procesamiento']}")
        partes.append("=" * 70)
        partes.append(row["texto_original"])
        partes.append("")

    return "\n".join(partes).encode("utf-8")


def detectar_duplicados(df):
    if df.empty:
        return pd.DataFrame()

    columnas = ["fecha_reporte", "equipo", "unidad", "hora_inicio_actividades"]
    return df[df.duplicated(subset=columnas, keep=False)].sort_values(columnas)


iniciar_estado()

st.title("Consolidador de reportes WhatsApp")

st.markdown("""
Esta app permite pegar reportes de WhatsApp, convertirlos en una tabla ordenada
y descargar un Excel consolidado.

### Formas de uso

Puedes usarla de dos maneras:

1. **Carga masiva:** pegar varios reportes juntos y presionar **Agregar al consolidado**.
2. **Carga individual:** pegar un reporte, agregarlo, luego pegar otro y volver a agregarlo.

Los reportes agregados se acumulan en pantalla hasta que presiones **Vaciar consolidado**.

### Qué hace la app

- Reconoce distintos formatos de fecha.
- Si no hay fecha, usa la fecha del día.
- Detecta campos faltantes.
- Permite completar campos debajo de cada reporte.
- Descarga un Excel con:
  - reporte estructurado,
  - mensajes originales,
  - faltantes corregidos.
- Descarga un TXT con respaldo de los mensajes originales.
""")

texto = st.text_area(
    "Pega aquí uno o varios reportes nuevos",
    height=300,
    placeholder="Pega aquí el reporte recién recibido o varios reportes juntos..."
)

col1, col2, col3 = st.columns(3)

with col1:
    agregar = st.button("Agregar al consolidado", type="primary")

with col2:
    limpiar_caja = st.button("Limpiar caja de texto")

with col3:
    vaciar = st.button("Vaciar consolidado")

if limpiar_caja:
    st.rerun()

if vaciar:
    st.session_state.clear()
    st.rerun()

if agregar:
    if not texto.strip():
        st.warning("Debes pegar al menos un reporte.")
    else:
        reportes = separar_reportes(texto)
        existentes = {r["id_reporte"] for r in st.session_state["datos_originales"]}

        nuevos = 0
        duplicados = 0

        for reporte in reportes:
            datos, respaldo, faltantes = procesar_reporte(reporte)

            if datos["id_reporte"] in existentes:
                duplicados += 1
                continue

            st.session_state["datos_originales"].append(datos)
            st.session_state["respaldos"].append(respaldo)
            st.session_state["faltantes_por_reporte"][datos["id_reporte"]] = faltantes
            existentes.add(datos["id_reporte"])
            nuevos += 1

        st.success(f"Se agregaron {nuevos} reporte(s) al consolidado.")

        if duplicados:
            st.warning(f"Se omitieron {duplicados} reporte(s) duplicado(s).")

if st.session_state["datos_originales"]:
    datos_finales = []
    registros_faltantes = []

    st.subheader("Consolidado en curso")

    for i, datos in enumerate(st.session_state["datos_originales"], start=1):
        id_reporte = datos["id_reporte"]
        faltantes = st.session_state["faltantes_por_reporte"].get(id_reporte, [])

        with st.container(border=True):
            st.markdown(f"### Reporte {i}")
            st.write(f"**ID:** {id_reporte}")
            st.write(f"**Equipo detectado:** {datos.get('equipo') or 'No detectado'}")
            st.write(f"**Unidad detectada:** {datos.get('unidad') or 'No detectada'}")
            st.write(f"**Fecha detectada:** {datos.get('fecha_reporte')}")

            correcciones = {}
            no_completar = set()

            if faltantes:
                st.warning(
                    "Campos faltantes: "
                    + ", ".join([ETIQUETAS[c] for c in faltantes])
                )

                decision = st.radio(
                    "¿Quieres completar manualmente los campos faltantes?",
                    ["Sí, completar ahora", "No completar este reporte"],
                    key=f"decision_{id_reporte}",
                    horizontal=True,
                )

                if decision == "Sí, completar ahora":
                    for campo in faltantes:
                        correcciones[campo] = st.text_input(
                            ETIQUETAS[campo],
                            key=f"{id_reporte}_{campo}"
                        )
                else:
                    no_completar = set(faltantes)
            else:
                st.success("Reporte completo.")

            datos_corregidos, registros = aplicar_correcciones(
                datos, correcciones, no_completar
            )

            datos_finales.append(datos_corregidos)
            registros_faltantes.extend(registros)

    df_reportes = pd.DataFrame(datos_finales, columns=COLUMNAS_REPORTE)
    df_originales = pd.DataFrame(st.session_state["respaldos"], columns=COLUMNAS_ORIGINAL)
    df_faltantes = pd.DataFrame(registros_faltantes, columns=COLUMNAS_FALTANTES)

    st.subheader("Tabla estructurada final")
    st.dataframe(df_reportes, use_container_width=True)

    total = len(df_reportes)
    completos = len(df_reportes[df_reportes["estado_validacion"] == "Completo"])
    incompletos = total - completos
    equipos_unicos = df_reportes["equipo"].replace("", pd.NA).dropna().nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total reportes", total)
    c2.metric("Completos", completos)
    c3.metric("Incompletos", incompletos)
    c4.metric("Equipos únicos", equipos_unicos)

    duplicados_df = detectar_duplicados(df_reportes)

    if not duplicados_df.empty:
        st.warning("Se detectaron posibles duplicados por fecha, equipo, unidad y hora.")
        st.dataframe(duplicados_df, use_container_width=True)

    excel = generar_excel(df_reportes, df_originales, df_faltantes)
    txt = generar_txt(df_originales)

    st.download_button(
        label="Descargar Excel consolidado",
        data=excel,
        file_name="reportes_whatsapp_consolidado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.download_button(
        label="Descargar respaldo TXT",
        data=txt,
        file_name="respaldo_mensajes_originales.txt",
        mime="text/plain",
    )
else:
    st.info("Aún no hay reportes agregados al consolidado.")

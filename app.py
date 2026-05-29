import re
import hashlib
import unicodedata
from io import BytesIO
from datetime import datetime, date

import pandas as pd
import streamlit as st
from dateutil import parser


st.set_page_config(
    page_title="Consolidador reportes prevención de riesgos",
    layout="wide"
)

COLUMNAS_REPORTE = [
    "id_reporte",
    "fecha_reporte",
    "fecha_usada_por_defecto",
    "tipo_reporte",
    "unidad",
    "equipo",
    "inicio_jornada",
    "actividad",
    "numero_excavadores",
    "cantidad_toldos",
    "estado_sombra_toldos",
    "cantidad_harneros",
    "estado_harneros",
    "cantidad_baldes",
    "estado_baldes",
    "mesa_gabinete",
    "estado_mesa",
    "observaciones",
    "estado_validacion",
    "campos_faltantes",
    "campos_no_reconocidos",
    "campos_esperados_no_detectados",
    "fecha_procesamiento",
]

COLUMNAS_ORIGINAL = [
    "id_reporte",
    "fecha_procesamiento",
    "texto_original",
]

COLUMNAS_FALTANTES = [
    "id_reporte",
    "campo",
    "valor_final",
    "fue_completado_manual",
]

COLUMNAS_CAMBIOS = [
    "id_reporte",
    "tipo_alerta",
    "detalle",
]

CAMPOS_OBLIGATORIOS = [
    "fecha_reporte",
    "unidad",
    "equipo",
    "inicio_jornada",
    "actividad",
    "numero_excavadores",
    "cantidad_toldos",
    "estado_sombra_toldos",
    "cantidad_harneros",
    "estado_harneros",
    "cantidad_baldes",
    "estado_baldes",
    "mesa_gabinete",
    "estado_mesa",
    "observaciones",
]

ETIQUETAS = {
    "fecha_reporte": "Fecha",
    "unidad": "Unidad",
    "equipo": "Equipo",
    "inicio_jornada": "Inicio jornada",
    "actividad": "Actividad",
    "numero_excavadores": "N° excavadores",
    "cantidad_toldos": "Cantidad toldos",
    "estado_sombra_toldos": "Estado sombra (toldos)",
    "cantidad_harneros": "Cantidad harneros",
    "estado_harneros": "Estado harneros",
    "cantidad_baldes": "Cantidad baldes",
    "estado_baldes": "Estado baldes",
    "mesa_gabinete": "Mesa gabinete",
    "estado_mesa": "Estado mesa",
    "observaciones": "Observaciones",
}

ALIAS_CAMPOS = {
    "fecha_reporte": ["fecha", "dia", "día", "fecha reporte"],
    "unidad": ["unidad", "cuadro", "sector"],
    "equipo": ["equipo", "responsables"],
    "inicio_jornada": [
        "inicio jornada",
        "hora inicio",
        "hora de inicio",
        "inicio de jornada",
        "inicio actividades",
        "hora inicio jornada",
    ],
    "actividad": ["actividad", "actividad realizada", "trabajo", "tarea", "labor"],
    "numero_excavadores": [
        "n excavadores",
        "n° excavadores",
        "nº excavadores",
        "numero excavadores",
        "número excavadores",
        "cantidad excavadores",
        "excavadores presentes",
    ],
    "cantidad_toldos": [
        "cantidad toldos",
        "n toldos",
        "n° toldos",
        "nº toldos",
        "numero toldos",
        "número toldos",
        "toldos",
    ],
    "estado_sombra_toldos": [
        "estado sombra",
        "estado sombra toldos",
        "estado de sombra",
        "estado de toldos",
        "estado toldos",
        "sombra",
        "estado sombra (toldos)",
    ],
    "cantidad_harneros": [
        "cantidad harneros",
        "n harneros",
        "n° harneros",
        "nº harneros",
        "numero harneros",
        "número harneros",
        "harneros cantidad",
    ],
    "estado_harneros": [
        "estado harneros",
        "estado de harneros",
        "harneros estado",
    ],
    "cantidad_baldes": [
        "cantidad baldes",
        "n baldes",
        "n° baldes",
        "nº baldes",
        "numero baldes",
        "número baldes",
        "baldes cantidad",
    ],
    "estado_baldes": [
        "estado baldes",
        "estado de baldes",
        "baldes estado",
    ],
    "mesa_gabinete": [
        "mesa gabinete",
        "mesa de gabinete",
        "gabinete",
        "mesa",
    ],
    "estado_mesa": [
        "estado mesa",
        "estado de mesa",
        "estado mesa gabinete",
        "estado de mesa gabinete",
    ],
    "observaciones": [
        "observaciones",
        "observación",
        "observacion",
        "obs",
        "comentarios",
        "comentario",
        "nota",
        "notas",
    ],
}


def iniciar_estado():
    st.session_state.setdefault("datos_originales", [])
    st.session_state.setdefault("respaldos", [])
    st.session_state.setdefault("faltantes_por_reporte", {})
    st.session_state.setdefault("cambios_por_reporte", {})
    st.session_state.setdefault("texto_input", "")


def limpiar_solo_caja():
    st.session_state["texto_input"] = ""


def normalizar_clave(texto):
    texto = str(texto).strip().lower()
    texto = texto.replace("°", "")
    texto = texto.replace("º", "")
    texto = texto.replace("n°", "n")
    texto = texto.replace("nº", "n")
    texto = texto.replace("n.", "n")
    texto = texto.replace("nro", "numero")
    texto = texto.replace("número", "numero")

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    texto = re.sub(r"\([^)]*\)", "", texto)
    texto = re.sub(r"[^a-z0-9ñ\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


ALIAS_NORMALIZADOS = {}
for campo, alias_list in ALIAS_CAMPOS.items():
    for alias in alias_list:
        ALIAS_NORMALIZADOS[normalizar_clave(alias)] = campo


def campo_desde_etiqueta(etiqueta):
    etiqueta_norm = normalizar_clave(etiqueta)

    if etiqueta_norm in ALIAS_NORMALIZADOS:
        return ALIAS_NORMALIZADOS[etiqueta_norm]

    for alias_norm, campo in ALIAS_NORMALIZADOS.items():
        if len(alias_norm) >= 5 and alias_norm in etiqueta_norm:
            return campo
        if len(etiqueta_norm) >= 5 and etiqueta_norm in alias_norm:
            return campo

    return None


def limpiar_texto(texto):
    texto = texto.replace("⁠", "")
    texto = texto.replace("\u200e", "")
    texto = texto.replace("\u200f", "")
    texto = texto.replace("\xa0", " ")
    texto = texto.replace("\t", " ")
    texto = texto.replace("–", "-")
    texto = texto.replace("—", "-")
    texto = re.sub(r"[•●▪◦]", "\n", texto)
    texto = re.sub(r"\r\n?", "\n", texto)
    texto = re.sub(r"\n{2,}", "\n", texto)
    return texto.strip()


def separar_reportes(texto):
    texto = texto.strip()

    bloques = re.split(
        r"(?i)(?=Reporte\s+prevenci[oó]n\s+de\s+riesgos)",
        texto
    )
    bloques = [b.strip() for b in bloques if b.strip()]

    if len(bloques) <= 1:
        bloques = re.split(
            r"(?i)(?=Reporte\s+de\s+prevenci[oó]n\s+de\s+riesgos)",
            texto
        )
        bloques = [b.strip() for b in bloques if b.strip()]

    if len(bloques) <= 1:
        bloques = re.split(
            r"(?=\[\d{1,2}:\d{2},\s*\d{1,2}/\d{1,2}/\d{2,4}\])",
            texto
        )
        bloques = [b.strip() for b in bloques if b.strip()]

    return bloques if bloques else [texto]


def generar_id_reporte(texto):
    return hashlib.md5(texto.strip().encode("utf-8")).hexdigest()[:10]


def detectar_tipo_reporte(texto):
    texto_norm = normalizar_clave(texto)

    if "prevencion de riesgos" in texto_norm:
        return "Prevención de riesgos"

    return "No identificado"


def extraer_lineas_candidatas(texto):
    texto = limpiar_texto(texto)
    lineas = []

    for linea in texto.split("\n"):
        linea = linea.strip()
        linea = re.sub(r"^\s*[-*]+\s*", "", linea).strip()

        if not linea:
            continue

        if re.search(r"(?i)^reporte\s+", linea):
            continue

        lineas.append(linea)

    return lineas


def extraer_campos(texto):
    lineas = extraer_lineas_candidatas(texto)

    campos = {campo: "" for campo in CAMPOS_OBLIGATORIOS}
    campos_detectados = []
    campos_no_reconocidos = []

    alias_posibles = sorted(
        set(sum(ALIAS_CAMPOS.values(), [])),
        key=len,
        reverse=True
    )

    alias_regex = "|".join(re.escape(alias) for alias in alias_posibles)

    for linea in lineas:
        linea_original = linea.strip()

        etiqueta = ""
        valor = ""

        if ":" in linea_original:
            partes = linea_original.split(":", 1)
            etiqueta = partes[0].strip()
            valor = partes[1].strip()

        elif re.search(r"\s+-\s+", linea_original):
            partes = re.split(r"\s+-\s+", linea_original, maxsplit=1)
            etiqueta = partes[0].strip()
            valor = partes[1].strip() if len(partes) > 1 else ""

        else:
            match = re.match(
                rf"(?i)^\s*(?P<etiqueta>{alias_regex})\s+(?P<valor>.*)$",
                linea_original
            )

            if match:
                etiqueta = match.group("etiqueta").strip()
                valor = match.group("valor").strip()
            else:
                campos_no_reconocidos.append(linea_original)
                continue

        campo = campo_desde_etiqueta(etiqueta)

        if campo:
            campos[campo] = normalizar_texto_simple(valor)
            campos_detectados.append(campo)
        else:
            campos_no_reconocidos.append(linea_original)

    campos_esperados_no_detectados = [
        campo for campo in CAMPOS_OBLIGATORIOS
        if campo not in campos_detectados
    ]

    return campos, campos_no_reconocidos, campos_esperados_no_detectados


def normalizar_fecha(valor_fecha):
    if not valor_fecha or not str(valor_fecha).strip():
        return date.today().strftime("%d/%m/%Y"), True

    valor = str(valor_fecha).strip().lower()
    valor = valor.replace(" de ", " ")

    meses = {
        "enero": "january",
        "febrero": "february",
        "marzo": "march",
        "abril": "april",
        "mayo": "may",
        "junio": "june",
        "julio": "july",
        "agosto": "august",
        "septiembre": "september",
        "setiembre": "september",
        "octubre": "october",
        "noviembre": "november",
        "diciembre": "december",
    }

    for esp, eng in meses.items():
        valor = valor.replace(esp, eng)

    try:
        fecha = parser.parse(valor, dayfirst=True, fuzzy=True)
        return fecha.strftime("%d/%m/%Y"), False
    except Exception:
        return date.today().strftime("%d/%m/%Y"), True


def normalizar_texto_simple(valor):
    if valor is None:
        return ""

    valor = str(valor).strip()
    valor = re.sub(r"\s+", " ", valor)

    if valor.lower() in [
        "ninguna",
        "sin observaciones",
        "sin observación",
        "sin observacion",
        "no hay",
        "n/a",
        "na",
        "no aplica",
    ]:
        return "Sin observaciones"

    return valor


def procesar_reporte(texto_original):
    texto_limpio = limpiar_texto(texto_original)
    id_reporte = generar_id_reporte(texto_original)

    campos, campos_no_reconocidos, campos_esperados_no_detectados = extraer_campos(texto_limpio)

    fecha_raw = campos.get("fecha_reporte", "")
    fecha_reporte, fecha_default = normalizar_fecha(fecha_raw)

    datos = {
        "id_reporte": id_reporte,
        "fecha_reporte": fecha_reporte,
        "fecha_usada_por_defecto": "Sí" if fecha_default else "No",
        "tipo_reporte": detectar_tipo_reporte(texto_limpio),
        "unidad": campos.get("unidad", ""),
        "equipo": campos.get("equipo", ""),
        "inicio_jornada": campos.get("inicio_jornada", ""),
        "actividad": campos.get("actividad", ""),
        "numero_excavadores": campos.get("numero_excavadores", ""),
        "cantidad_toldos": campos.get("cantidad_toldos", ""),
        "estado_sombra_toldos": campos.get("estado_sombra_toldos", ""),
        "cantidad_harneros": campos.get("cantidad_harneros", ""),
        "estado_harneros": campos.get("estado_harneros", ""),
        "cantidad_baldes": campos.get("cantidad_baldes", ""),
        "estado_baldes": campos.get("estado_baldes", ""),
        "mesa_gabinete": campos.get("mesa_gabinete", ""),
        "estado_mesa": campos.get("estado_mesa", ""),
        "observaciones": campos.get("observaciones", ""),
        "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    faltantes = []

    for campo in CAMPOS_OBLIGATORIOS:
        if campo == "fecha_reporte":
            if fecha_default and not fecha_raw:
                faltantes.append(campo)
        elif not datos.get(campo):
            faltantes.append(campo)

    faltantes = list(dict.fromkeys(faltantes))

    datos["estado_validacion"] = "Completo" if not faltantes else "Incompleto"
    datos["campos_faltantes"] = ", ".join([ETIQUETAS[c] for c in faltantes])
    datos["campos_no_reconocidos"] = " | ".join(campos_no_reconocidos)
    datos["campos_esperados_no_detectados"] = ", ".join(
        [ETIQUETAS.get(c, c) for c in campos_esperados_no_detectados]
    )

    respaldo = {
        "id_reporte": id_reporte,
        "fecha_procesamiento": datos["fecha_procesamiento"],
        "texto_original": texto_original.strip(),
    }

    alertas = []

    if campos_no_reconocidos:
        alertas.append({
            "id_reporte": id_reporte,
            "tipo_alerta": "Campo no reconocido o nuevo formato",
            "detalle": " | ".join(campos_no_reconocidos),
        })

    if campos_esperados_no_detectados:
        alertas.append({
            "id_reporte": id_reporte,
            "tipo_alerta": "Campo esperado no detectado",
            "detalle": ", ".join([ETIQUETAS.get(c, c) for c in campos_esperados_no_detectados]),
        })

    return datos, respaldo, faltantes, alertas


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

    datos_corregidos["estado_validacion"] = (
        "Completo" if not faltantes_finales else "Incompleto"
    )
    datos_corregidos["campos_faltantes"] = ", ".join(
        [ETIQUETAS[c] for c in faltantes_finales]
    )

    return datos_corregidos, registros_faltantes


def generar_excel(df_reportes, df_originales, df_faltantes, df_alertas):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_reportes.to_excel(writer, index=False, sheet_name="Reporte estructurado")
        df_originales.to_excel(writer, index=False, sheet_name="Mensajes originales")
        df_faltantes.to_excel(writer, index=False, sheet_name="Faltantes corregidos")
        df_alertas.to_excel(writer, index=False, sheet_name="Alertas formato")

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

    columnas = ["fecha_reporte", "unidad", "equipo", "inicio_jornada"]

    return df[df.duplicated(subset=columnas, keep=False)].sort_values(columnas)


iniciar_estado()

st.title("Consolidador de reportes de prevención de riesgos")

st.markdown("""
Esta app permite pegar reportes de prevención de riesgos enviados por WhatsApp,
convertirlos en una tabla ordenada y descargar un Excel consolidado.

### Formato esperado

```text
Reporte prevención de riesgos.
- Fecha:
- Unidad:
- Equipo:
- Inicio jornada:
- Actividad:
- N° excavadores:
- Cantidad toldos:
- Estado sombra (toldos):
- Cantidad harneros:
- Estado harneros:
- Cantidad baldes:
- Estado baldes:
- Mesa gabinete:
- Estado mesa:
- Observaciones:

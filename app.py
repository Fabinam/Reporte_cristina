import re
import hashlib
import unicodedata
from io import BytesIO
from datetime import datetime, date

import pandas as pd
import streamlit as st
from dateutil import parser
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


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
    "sombra_toldo_malla",
    "cantidad_sombra_toldo_malla",
    "calidad_sombra",
    "cantidad_harneros",
    "estado_harneros",
    "cantidad_baldes",
    "estado_baldes",
    "mesa_gabinete",
    "estado_mesa",
    "observaciones",
    "estado_validacion",
    "campos_faltantes",
    "valores_invalidos",
    "campos_no_reconocidos",
    "campos_esperados_no_detectados",
    "fecha_procesamiento",
]

COLUMNAS_REPORTE_LIMPIO = [
    "fecha_reporte",
    "tipo_reporte",
    "unidad",
    "equipo",
    "inicio_jornada",
    "actividad",
    "numero_excavadores",
    "sombra_toldo_malla",
    "cantidad_sombra_toldo_malla",
    "calidad_sombra",
    "cantidad_harneros",
    "estado_harneros",
    "cantidad_baldes",
    "estado_baldes",
    "mesa_gabinete",
    "estado_mesa",
    "observaciones",
]

COLUMNAS_VALIDACIONES = [
    "id_reporte",
    "estado_validacion",
    "fecha_usada_por_defecto",
    "campos_faltantes",
    "valores_invalidos",
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

COLUMNAS_ALERTAS = [
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
    "sombra_toldo_malla",
    "cantidad_sombra_toldo_malla",
    "calidad_sombra",
    "cantidad_harneros",
    "estado_harneros",
    "cantidad_baldes",
    "estado_baldes",
    "mesa_gabinete",
    "estado_mesa",
    "observaciones",
]

CAMPOS_CANTIDAD = [
    "numero_excavadores",
    "cantidad_sombra_toldo_malla",
    "cantidad_harneros",
    "cantidad_baldes",
]

CAMPO_HORA = "inicio_jornada"

ETIQUETAS = {
    "fecha_reporte": "Fecha",
    "unidad": "Unidad",
    "equipo": "Equipo",
    "inicio_jornada": "Inicio jornada",
    "actividad": "Actividad",
    "numero_excavadores": "N° excavadores",
    "sombra_toldo_malla": "Sombra (Toldo/Malla)",
    "cantidad_sombra_toldo_malla": "Cantidad sombra (Toldo/Malla)",
    "calidad_sombra": "Calidad de sombra",
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
        "hora comienzo",
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
    "sombra_toldo_malla": [
        "sombra",
        "sombra toldo malla",
        "sombra toldo/malla",
        "sombra (toldo/malla)",
        "tipo sombra",
        "tipo de sombra",
        "tipo sombra toldo malla",
        "toldo malla",
        "toldo/malla",
    ],
    "cantidad_sombra_toldo_malla": [
        "cantidad sombra",
        "cantidad sombra toldo malla",
        "cantidad sombra toldo/malla",
        "cantidad sombra (toldo/malla)",
        "cantidad toldos",
        "cantidad mallas",
        "n toldos",
        "n° toldos",
        "nº toldos",
        "numero toldos",
        "número toldos",
        "n mallas",
        "n° mallas",
        "numero mallas",
        "número mallas",
    ],
    "calidad_sombra": [
        "calidad sombra",
        "calidad de sombra",
        "calidad sombra toldo malla",
        "calidad sombra toldo/malla",
        "calidad de sombra (toldo/malla)",
        "estado sombra",
        "estado de sombra",
        "estado sombra toldos",
        "estado sombra (toldos)",
        "estado toldos",
        "estado de toldos",
        "estado malla",
        "estado de malla",
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
    st.session_state.setdefault("alertas_por_reporte", {})
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
for campo_alias, alias_list in ALIAS_CAMPOS.items():
    for alias in alias_list:
        ALIAS_NORMALIZADOS[normalizar_clave(alias)] = campo_alias


def campo_desde_etiqueta(etiqueta):
    etiqueta_norm = normalizar_clave(etiqueta)

    if etiqueta_norm in ALIAS_NORMALIZADOS:
        return ALIAS_NORMALIZADOS[etiqueta_norm]

    for alias_norm, campo_alias in ALIAS_NORMALIZADOS.items():
        if len(alias_norm) >= 5 and alias_norm in etiqueta_norm:
            return campo_alias
        if len(etiqueta_norm) >= 5 and etiqueta_norm in alias_norm:
            return campo_alias

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

    alias_posibles = sorted(set(sum(ALIAS_CAMPOS.values(), [])), key=len, reverse=True)
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

    valor = str(valor_fecha).strip().lower().replace(" de ", " ")

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


def normalizar_hora(valor):
    valor = str(valor).strip()
    if not valor:
        return "", False, ""
    if es_no_informado(valor):
        return valor, True, ""

    patron = r"^(?P<hora>\d{1,2})[:.](?P<minuto>\d{2})$"
    match = re.match(patron, valor)

    if not match:
        return valor, False, "Debe usar formato HH:MM o HH.MM, por ejemplo 09:00 o 09.00."

    hora = int(match.group("hora"))
    minuto = int(match.group("minuto"))

    if hora < 0 or hora > 23 or minuto < 0 or minuto > 59:
        return valor, False, "La hora debe estar entre 00:00 y 23:59."

    return f"{hora:02d}:{minuto:02d}", True, ""


def normalizar_cantidad(valor):
    valor = str(valor).strip()
    if not valor:
        return "", False, ""
    if es_no_informado(valor):
        return valor, True, ""

    if not re.match(r"^\d+$", valor):
        return valor, False, "Debe ser un número entero mayor a 0. No se aceptan negativos, decimales ni texto."

    numero = int(valor)
    if numero <= 0:
        return valor, False, "Debe ser un número mayor a 0."

    return str(numero), True, ""


def validar_y_normalizar_datos(datos):
    datos = datos.copy()
    alertas = []

    hora_normalizada, hora_valida, mensaje_hora = normalizar_hora(datos.get(CAMPO_HORA, ""))
    if datos.get(CAMPO_HORA, ""):
        datos[CAMPO_HORA] = hora_normalizada
        if not hora_valida:
            alertas.append({
                "tipo_alerta": "Hora inválida",
                "detalle": f"{ETIQUETAS[CAMPO_HORA]}: '{datos.get(CAMPO_HORA, '')}'. {mensaje_hora}",
            })

    for campo in CAMPOS_CANTIDAD:
        valor_original = datos.get(campo, "")
        valor_normalizado, valido, mensaje = normalizar_cantidad(valor_original)
        if valor_original:
            datos[campo] = valor_normalizado
            if not valido:
                alertas.append({
                    "tipo_alerta": "Cantidad inválida",
                    "detalle": f"{ETIQUETAS[campo]}: '{valor_original}'. {mensaje}",
                })

    return datos, alertas


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
        "sombra_toldo_malla": campos.get("sombra_toldo_malla", ""),
        "cantidad_sombra_toldo_malla": campos.get("cantidad_sombra_toldo_malla", ""),
        "calidad_sombra": campos.get("calidad_sombra", ""),
        "cantidad_harneros": campos.get("cantidad_harneros", ""),
        "estado_harneros": campos.get("estado_harneros", ""),
        "cantidad_baldes": campos.get("cantidad_baldes", ""),
        "estado_baldes": campos.get("estado_baldes", ""),
        "mesa_gabinete": campos.get("mesa_gabinete", ""),
        "estado_mesa": campos.get("estado_mesa", ""),
        "observaciones": campos.get("observaciones", ""),
        "fecha_procesamiento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    datos, alertas_validacion_base = validar_y_normalizar_datos(datos)

    faltantes = []
    for campo in CAMPOS_OBLIGATORIOS:
        if campo == "fecha_reporte":
            if fecha_default and not fecha_raw:
                faltantes.append(campo)
        elif not datos.get(campo):
            faltantes.append(campo)

    valores_invalidos = []
    for alerta in alertas_validacion_base:
        valores_invalidos.append(alerta["detalle"])

    faltantes = list(dict.fromkeys(faltantes))

    datos["estado_validacion"] = "Completo" if not faltantes and not valores_invalidos else "Revisar"
    datos["campos_faltantes"] = ", ".join([ETIQUETAS[c] for c in faltantes])
    datos["valores_invalidos"] = " | ".join(valores_invalidos)
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

    for alerta in alertas_validacion_base:
        alerta["id_reporte"] = id_reporte
        alertas.append(alerta)

    return datos, respaldo, faltantes, alertas


def es_no_informado(valor):
    return str(valor).strip().lower() == "no informado"


def validar_fecha_manual(valor):
    valor = str(valor).strip()
    if not valor:
        return "", False, ""

    if es_no_informado(valor):
        return valor, True, ""

    fecha_normalizada, uso_default = normalizar_fecha(valor)

    if uso_default:
        return valor, False, "Debe ingresar una fecha válida, por ejemplo 09/02/2026, 09-02-2026 o 09.02.2026."

    return fecha_normalizada, True, ""


def aplicar_correcciones(datos, correcciones, no_completar):
    datos_corregidos = datos.copy()
    registros_faltantes = []
    alertas_validacion = []
    campos_no_completados = set(no_completar)
    campos_corregidos = set()

    for campo in CAMPOS_OBLIGATORIOS:
        valor_original = datos_corregidos.get(campo, "")
        fue_manual = "No"
        decision_no_completar = campo in campos_no_completados

        if campo in correcciones and correcciones[campo].strip():
            valor_manual = correcciones[campo].strip()

            if campo == "fecha_reporte":
                fecha_normalizada, fecha_valida, mensaje_fecha = validar_fecha_manual(valor_manual)
                datos_corregidos[campo] = fecha_normalizada
                datos_corregidos["fecha_usada_por_defecto"] = "No" if fecha_valida else datos_corregidos.get("fecha_usada_por_defecto", "")
                if not fecha_valida:
                    alertas_validacion.append({
                        "id_reporte": datos_corregidos["id_reporte"],
                        "tipo_alerta": "Fecha inválida",
                        "detalle": f"{ETIQUETAS[campo]}: '{valor_manual}'. {mensaje_fecha}",
                    })
            else:
                datos_corregidos[campo] = valor_manual

            fue_manual = "Sí"
            campos_corregidos.add(campo)

        elif decision_no_completar:
            datos_corregidos[campo] = "No informado"

        if campo in correcciones or decision_no_completar:
            registros_faltantes.append({
                "id_reporte": datos_corregidos["id_reporte"],
                "campo": ETIQUETAS[campo],
                "valor_final": datos_corregidos.get(campo, ""),
                "fue_completado_manual": fue_manual if not decision_no_completar else "No completado por usuario",
            })

    datos_corregidos, alertas_base = validar_y_normalizar_datos(datos_corregidos)
    for alerta in alertas_base:
        alerta["id_reporte"] = datos_corregidos["id_reporte"]
        alertas_validacion.append(alerta)

    faltantes_finales = []

    for campo in CAMPOS_OBLIGATORIOS:
        valor = datos_corregidos.get(campo, "")

        if campo in campos_no_completados:
            faltantes_finales.append(campo)
        elif not valor:
            faltantes_finales.append(campo)
        elif es_no_informado(valor):
            faltantes_finales.append(campo)

    faltantes_finales = list(dict.fromkeys(faltantes_finales))
    valores_invalidos = [alerta["detalle"] for alerta in alertas_validacion]

    datos_corregidos["estado_validacion"] = (
        "Completo" if not faltantes_finales and not valores_invalidos else "Revisar"
    )
    datos_corregidos["campos_faltantes"] = ", ".join(
        [ETIQUETAS[c] for c in faltantes_finales]
    )
    datos_corregidos["valores_invalidos"] = " | ".join(valores_invalidos)

    return datos_corregidos, registros_faltantes, alertas_validacion


def formatear_hoja_reporte_estructurado(workbook):
    ws = workbook["Reporte estructurado"]

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    for column_cells in ws.columns:
        column_letter = get_column_letter(column_cells[0].column)
        header = str(column_cells[0].value or "")
        max_length = len(header)

        for cell in column_cells[1:]:
            value = "" if cell.value is None else str(cell.value)
            longest_line = max([len(line) for line in value.split("\n")], default=0)
            max_length = max(max_length, longest_line)

        adjusted_width = min(max(max_length + 2, 12), 45)

        if header in ["observaciones"]:
            adjusted_width = min(max(adjusted_width, 35), 60)

        ws.column_dimensions[column_letter].width = adjusted_width

    for row in ws.iter_rows(min_row=2):
        row_number = row[0].row
        max_lines = 1
        for cell in row:
            if cell.value:
                text = str(cell.value)
                estimated_lines = max(1, len(text) // 45 + 1)
                max_lines = max(max_lines, estimated_lines)
        ws.row_dimensions[row_number].height = min(max_lines * 15, 90)


def generar_excel(df_reportes, df_originales, df_faltantes, df_alertas):
    output = BytesIO()

    df_reporte_limpio = df_reportes[COLUMNAS_REPORTE_LIMPIO].copy()
    df_validaciones = df_reportes[[col for col in COLUMNAS_VALIDACIONES if col in df_reportes.columns]].copy()

    if not df_alertas.empty:
        df_alertas_export = df_alertas.copy()
    else:
        df_alertas_export = pd.DataFrame(columns=COLUMNAS_ALERTAS)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_reporte_limpio.to_excel(writer, index=False, sheet_name="Reporte estructurado")
        df_originales.to_excel(writer, index=False, sheet_name="Mensajes originales")
        df_faltantes.to_excel(writer, index=False, sheet_name="Faltantes corregidos")
        df_validaciones.to_excel(writer, index=False, sheet_name="Validaciones por reporte")
        df_alertas_export.to_excel(writer, index=False, sheet_name="Alertas y validaciones")

        formatear_hoja_reporte_estructurado(writer.book)

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



def es_alerta_validacion(alerta):
    return alerta.get("tipo_alerta") in {"Hora inválida", "Cantidad inválida", "Fecha inválida"}


def campo_desde_detalle_alerta(detalle):
    etiqueta = str(detalle).split(":", 1)[0].strip()
    for campo, etiqueta_oficial in ETIQUETAS.items():
        if normalizar_clave(etiqueta) == normalizar_clave(etiqueta_oficial):
            return campo
    return None


def campos_invalidos_desde_alertas(alertas):
    campos = []
    for alerta in alertas:
        if es_alerta_validacion(alerta):
            campo = campo_desde_detalle_alerta(alerta.get("detalle", ""))
            if campo and campo not in campos:
                campos.append(campo)
    return campos


def unir_campos_sin_duplicados(*listas):
    resultado = []
    for lista in listas:
        for campo in lista:
            if campo not in resultado:
                resultado.append(campo)
    return resultado


def deduplicar_alertas(alertas):
    vistas = set()
    resultado = []
    for alerta in alertas:
        clave = (
            alerta.get("id_reporte", ""),
            alerta.get("tipo_alerta", ""),
            alerta.get("detalle", ""),
        )
        if clave not in vistas:
            vistas.add(clave)
            resultado.append(alerta)
    return resultado

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
- Sombra (Toldo/Malla):
- Cantidad sombra (Toldo/Malla):
- Calidad de sombra:
- Cantidad harneros:
- Estado harneros:
- Cantidad baldes:
- Estado baldes:
- Mesa gabinete:
- Estado mesa:
- Observaciones:
```

### Validaciones principales

- **Inicio jornada** debe tener formato de hora válido: `09:00` o `09.00`.
- No se aceptan horas escritas como texto, por ejemplo `nueve de la tarde`.
- Las cantidades deben ser números enteros mayores a 0.
- No se aceptan cantidades negativas, decimales ni texto en campos numéricos.
- Si falta un campo, la app permite completarlo manualmente debajo del reporte.
- Si aparece un campo nuevo o no reconocido, la app genera una alerta sin detener el procesamiento.
- La hoja **Reporte estructurado** queda limpia, sin columnas técnicas de validación.
- Las columnas de control quedan separadas en **Validaciones por reporte** y **Alertas y validaciones**.

### Instrucciones

1. Pega uno o varios reportes en la caja de texto.
2. Presiona **Agregar al consolidado**.
3. Revisa las alertas de campos faltantes o valores inválidos.
4. Corrige manualmente los datos faltantes o inválidos en la misma sección del reporte, o selecciona **No completar este reporte**.
5. Si llega otro reporte después, usa **Limpiar caja de texto** y vuelve a pegar.
6. Descarga el Excel consolidado o el TXT de respaldo.
""")

texto = st.text_area(
    "Pega aquí uno o varios reportes nuevos",
    height=350,
    key="texto_input",
    placeholder="""Reporte prevención de riesgos.
- Fecha:
- Unidad:
- Equipo:
- Inicio jornada:
- Actividad:
- N° excavadores:
- Sombra (Toldo/Malla):
- Cantidad sombra (Toldo/Malla):
- Calidad de sombra:
- Cantidad harneros:
- Estado harneros:
- Cantidad baldes:
- Estado baldes:
- Mesa gabinete:
- Estado mesa:
- Observaciones:"""
)

col1, col2, col3 = st.columns(3)

with col1:
    agregar = st.button("Agregar al consolidado", type="primary")

with col2:
    st.button("Limpiar caja de texto", on_click=limpiar_solo_caja)

with col3:
    vaciar = st.button("Vaciar consolidado")

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
            datos, respaldo, faltantes, alertas = procesar_reporte(reporte)

            if datos["id_reporte"] in existentes:
                duplicados += 1
                continue

            st.session_state["datos_originales"].append(datos)
            st.session_state["respaldos"].append(respaldo)
            st.session_state["faltantes_por_reporte"][datos["id_reporte"]] = faltantes
            st.session_state["alertas_por_reporte"][datos["id_reporte"]] = alertas

            existentes.add(datos["id_reporte"])
            nuevos += 1

        st.success(f"Se agregaron {nuevos} reporte(s) al consolidado.")

        if duplicados:
            st.warning(f"Se omitieron {duplicados} reporte(s) duplicado(s).")

if st.session_state["datos_originales"]:
    datos_finales = []
    registros_faltantes = []
    registros_alertas = []

    st.subheader("Consolidado en curso")

    for i, datos in enumerate(st.session_state["datos_originales"], start=1):
        id_reporte = datos["id_reporte"]
        faltantes = st.session_state["faltantes_por_reporte"].get(id_reporte, [])
        alertas = st.session_state["alertas_por_reporte"].get(id_reporte, [])

        with st.container(border=True):
            st.markdown(f"### Reporte {i}")
            st.write(f"**ID:** {id_reporte}")
            st.write(f"**Unidad detectada:** {datos.get('unidad') or 'No detectada'}")
            st.write(f"**Equipo detectado:** {datos.get('equipo') or 'No detectado'}")
            st.write(f"**Fecha detectada:** {datos.get('fecha_reporte')}")

            alertas_formato = [alerta for alerta in alertas if not es_alerta_validacion(alerta)]
            alertas_validacion_inicial = [alerta for alerta in alertas if es_alerta_validacion(alerta)]
            campos_invalidos = campos_invalidos_desde_alertas(alertas_validacion_inicial)
            campos_para_revisar = unir_campos_sin_duplicados(faltantes, campos_invalidos)

            if alertas_formato:
                for alerta in alertas_formato:
                    st.warning(f"{alerta['tipo_alerta']}: {alerta['detalle']}")
                    registros_alertas.append(alerta)

            if alertas_validacion_inicial:
                for alerta in alertas_validacion_inicial:
                    st.warning(f"{alerta['tipo_alerta']}: {alerta['detalle']}")

            correcciones = {}
            no_completar = set()

            if campos_para_revisar:
                if faltantes:
                    st.warning("Campos faltantes: " + ", ".join([ETIQUETAS[c] for c in faltantes]))
                if campos_invalidos:
                    st.warning("Campos con valores inválidos: " + ", ".join([ETIQUETAS[c] for c in campos_invalidos]))

                decision = st.radio(
                    "¿Quieres corregir manualmente los campos observados?",
                    ["Sí, corregir ahora", "No completar este reporte"],
                    key=f"decision_{id_reporte}",
                    horizontal=True,
                )

                if decision == "Sí, corregir ahora":
                    for campo in campos_para_revisar:
                        valor_actual = datos.get(campo, "") if campo in campos_invalidos else ""
                        correcciones[campo] = st.text_input(
                            ETIQUETAS[campo],
                            value=valor_actual,
                            key=f"{id_reporte}_{campo}",
                            help="Corrige este campo. Se aplicarán las mismas validaciones del reporte original."
                        )
                else:
                    no_completar = set(campos_para_revisar)
            else:
                st.success("Reporte sin campos vacíos ni valores inválidos.")

            datos_corregidos, registros, alertas_correccion = aplicar_correcciones(
                datos,
                correcciones,
                no_completar
            )

            if alertas_correccion:
                for alerta in alertas_correccion:
                    st.error(f"Sigue pendiente: {alerta['tipo_alerta']}: {alerta['detalle']}")
            elif campos_para_revisar and correcciones:
                st.success("Correcciones validadas correctamente.")

            datos_finales.append(datos_corregidos)
            registros_faltantes.extend(registros)
            registros_alertas.extend(alertas_correccion)

    df_reportes = pd.DataFrame(datos_finales, columns=COLUMNAS_REPORTE)
    df_originales = pd.DataFrame(st.session_state["respaldos"], columns=COLUMNAS_ORIGINAL)
    df_faltantes = pd.DataFrame(registros_faltantes, columns=COLUMNAS_FALTANTES)
    registros_alertas = deduplicar_alertas(registros_alertas)
    df_alertas = pd.DataFrame(registros_alertas, columns=COLUMNAS_ALERTAS)

    df_reporte_limpio = df_reportes[COLUMNAS_REPORTE_LIMPIO].copy()
    df_validaciones = df_reportes[[col for col in COLUMNAS_VALIDACIONES if col in df_reportes.columns]].copy()

    st.subheader("Tabla estructurada final")
    st.dataframe(df_reporte_limpio, use_container_width=True)

    with st.expander("Ver validaciones por reporte"):
        st.dataframe(df_validaciones, use_container_width=True)

    total = len(df_reportes)
    completos = len(df_reportes[df_reportes["estado_validacion"] == "Completo"])
    revisar = total - completos
    equipos_unicos = df_reportes["equipo"].replace("", pd.NA).dropna().nunique()
    alertas_total = len(df_alertas)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total reportes", total)
    c2.metric("Completos", completos)
    c3.metric("Por revisar", revisar)
    c4.metric("Equipos únicos", equipos_unicos)
    c5.metric("Alertas", alertas_total)

    duplicados_df = detectar_duplicados(df_reportes)
    if not duplicados_df.empty:
        st.warning("Se detectaron posibles duplicados por fecha, unidad, equipo e inicio de jornada.")
        st.dataframe(duplicados_df, use_container_width=True)

    if not df_alertas.empty:
        st.subheader("Alertas y validaciones")
        st.dataframe(df_alertas, use_container_width=True)

    excel = generar_excel(df_reportes, df_originales, df_faltantes, df_alertas)
    txt = generar_txt(df_originales)

    st.download_button(
        label="Descargar Excel consolidado",
        data=excel,
        file_name="reportes_prevencion_riesgos_consolidado.xlsx",
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

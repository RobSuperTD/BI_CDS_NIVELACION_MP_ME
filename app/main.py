"""Tablero Nivelacion y Ventas Internas Materias Primas y Material Empaque."""

import base64
import html as html_lib
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from styles import GLOBAL_CSS, CLASIFICACION_COLORES
from components import (
    render_combinado_table,
    render_card,
    render_count_badges,
)
from data import cargar_inventario_necesidad
from logic_inventario import (
    construir_filas_combinadas,
    exportar_excel,
    CENTROS_MP,
    CENTROS_ME,
)

st.set_page_config(page_title="Nivelacion y Ventas Internas MP y ME", page_icon="📦", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ---------- Header ----------
fecha_actualizacion = ""  # Deja vacío si no necesitas la fecha
semana_actual = None

_semana_txt = f" &nbsp;·&nbsp; Semana <b>{semana_actual}</b>" if semana_actual else ""
sello_fecha = (
    f"<div class='updated'>Datos actualizados al <b>{html_lib.escape(fecha_actualizacion)}</b>"
    f"{_semana_txt}</div>"
    if fecha_actualizacion
    else ""
)

# Cargar el logo
logo_path = Path(__file__).resolve().parent / "static" / "logo_super.png"
logo_b64 = ""
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

# Renderizar el encabezado completo (Hero)
st.markdown(
    "<div class='hero'>"
    f"<img src='data:image/png;base64,{logo_b64}' style='position: absolute; left: 4%; top: 50%; transform: translateY(-50%); height: 75px; filter: drop-shadow(0px 0px 8px rgba(255,219,0,0.6)) drop-shadow(0px 4px 12px rgba(0,51,160,0.7));'>"
    "<h1>NIVELACIÓN Y VENTAS INTERNAS MP Y ME</h1>"
    "<div class='bar'></div>"
    f"{sello_fecha}</div>",
    unsafe_allow_html=True,
)

with st.spinner("Cargando datos desde Snowflake..."):
    df_consolidado = cargar_inventario_necesidad()

# ================= Filtros =================

# --- Grupo (necesario primero para saber que centros ofrecer en IdCentro) ---
GRUPOS = {"Materia Prima": "MP", "Material de Empaque": "ME", "Ambos": "AMBOS"}


def _centros_de_grupo(grupo_valor: str) -> list[str]:
    if grupo_valor == "MP":
        return list(CENTROS_MP)
    if grupo_valor == "ME":
        return list(CENTROS_ME)
    return list(CENTROS_MP) + list(CENTROS_ME)


col_idcentro, col_semana, col_grupo, col_modo = st.columns(4)

with col_grupo:
    st.markdown("**Grupo**")
    grupo_label = st.radio(
        "grupo", list(GRUPOS.keys()),
        horizontal=True, label_visibility="collapsed", key="grupo",
    )
grupo = GRUPOS[grupo_label]
centros_grupo = _centros_de_grupo(grupo)
opciones_idcentro = ["Todos"] + centros_grupo

def _sincronizar_filtro_todos(key_ms: str):
    seleccion = st.session_state.get(key_ms, [])
    if not seleccion:
        st.session_state[key_ms] = ["Todos"]
        return
    if "Todos" in seleccion:
        if len(seleccion) > 1:
            if seleccion[-1] == "Todos":
                st.session_state[key_ms] = ["Todos"]
            else:
                st.session_state[key_ms] = [x for x in seleccion if x != "Todos"]


def _marcar_todos_idcentro():
    _sincronizar_filtro_todos("idcentro_ms")


with col_idcentro:
    st.markdown("**IdCentro**")
    if "idcentro_ms" not in st.session_state or not set(st.session_state["idcentro_ms"]) <= set(opciones_idcentro):
        st.session_state["idcentro_ms"] = ["Todos"]

    seleccion_idcentro = st.multiselect(
        "idcentro_filtro", opciones_idcentro,
        label_visibility="collapsed", key="idcentro_ms",
        on_change=_marcar_todos_idcentro,
    )

if "Todos" in seleccion_idcentro or not seleccion_idcentro:
    idcentro_filtro = None
else:
    idcentro_filtro = tuple(seleccion_idcentro)

with col_semana:
    st.markdown("**Semana**")
    semana_label = st.radio(
        "semana", ["Semana actual", "Próxima semana", "Semana actual + 2"],
        horizontal=True, label_visibility="collapsed", key="semana",
    )
semana = {"Semana actual": 0, "Próxima semana": 1, "Semana actual + 2": 2}[semana_label]

AYUDA_INVENTARIO = (
    "<b>Actual:</b> muestra el inventario tal como va hoy. Para la semana siguiente "
    "toma lo que hay en bodega y le resta lo que se va a consumir. No cuenta pedidos "
    "que estén por llegar ni movimientos entre centros.<br><br>"
    "<b>Simulado:</b> muestra cómo quedaría el inventario si se hacen los movimientos "
    "sugeridos. Para la semana siguiente toma lo que hay en bodega, le resta lo que se "
    "va a consumir, le suma los pedidos que llegan esta semana y aplica los traslados "
    "recomendados entre centros."
)

with col_modo:
    st.markdown(
        "<div style='font-weight:600; margin-bottom:0.25rem;'>Inventario"
        f"<span class='info-tip'>i<span class='info-tip-text'>{AYUDA_INVENTARIO}</span></span></div>",
        unsafe_allow_html=True,
    )
    modo_label = st.radio(
        "modo", ["Actual", "Simulado"],
        horizontal=True, label_visibility="collapsed", key="modo",
    )
modo = "actual" if modo_label == "Actual" else "simulado"

# --- Filtros de nivelacion/venta interna ---
prefijo_filtro = ("13",) if grupo == "MP" else (("14",) if grupo == "ME" else ("13", "14"))
df_grupo_mats = df_consolidado[df_consolidado["IDMATERIAL"].str.startswith(prefijo_filtro)]
mats_unicos = (
    df_grupo_mats[["IDMATERIAL", "MATERIAL"]]
    .dropna(subset=["IDMATERIAL"])
    .drop_duplicates()
    .sort_values("IDMATERIAL")
)
opciones_materiales = [
    f"{row['IDMATERIAL']} - {row['MATERIAL']}"
    for _, row in mats_unicos.iterrows()
]

if "busqueda_ms" in st.session_state:
    st.session_state["busqueda_ms"] = [
        m for m in st.session_state["busqueda_ms"]
        if any(str(m).startswith(p) for p in prefijo_filtro)
    ]

col_busqueda, col_clasif, col_destino = st.columns(3)
with col_busqueda:
    st.markdown("**🔍 Buscar Material**")
    materiales_busqueda = st.multiselect(
        "busqueda", options=opciones_materiales, default=[],
        placeholder="Código o nombre para autocompletar...",
        label_visibility="collapsed", key="busqueda_ms",
    )
with col_clasif:
    st.markdown("**Clasificación**")
    clasificacion_label = st.radio(
        "clasificacion_filtro", ["Todas", "Nivelacion", "Venta Interna"],
        horizontal=True, label_visibility="collapsed", key="clasificacion_filtro",
    )
opciones_centro_destino = ["Todos"] + centros_grupo

def _marcar_todos_centro_destino():
    _sincronizar_filtro_todos("centro_destino_ms")


with col_destino:
    st.markdown("**Centro Destino**")
    if "centro_destino_ms" not in st.session_state or not set(st.session_state["centro_destino_ms"]) <= set(opciones_centro_destino):
        st.session_state["centro_destino_ms"] = ["Todos"]

    seleccion_centro_destino = st.multiselect(
        "centro_destino_filtro", opciones_centro_destino,
        label_visibility="collapsed", key="centro_destino_ms",
        on_change=_marcar_todos_centro_destino,
    )

clasificacion_filtro = None if clasificacion_label == "Todas" else clasificacion_label
if "Todos" in seleccion_centro_destino or not seleccion_centro_destino:
    centro_destino_filtro = None
else:
    centro_destino_filtro = tuple(seleccion_centro_destino)

filas_combinadas = construir_filas_combinadas(
    df_consolidado, grupo=grupo, semana=semana, modo=modo,
    idcentro_filtro=idcentro_filtro,
    centro_destino_filtro=centro_destino_filtro, clasificacion_filtro=clasificacion_filtro,
)

if materiales_busqueda:
    terminos_id = {m.split(" - ")[0].strip() for m in materiales_busqueda if " - " in m}
    terminos_texto = [m.lower().strip() for m in materiales_busqueda if " - " not in m]
    filas_combinadas = [
        f for f in filas_combinadas
        if (
            str(f.get("IdMaterial", "")) in terminos_id
            or any(
                t in str(f.get("IdMaterial", "")).lower() or t in str(f.get("Material", "")).lower()
                for t in terminos_texto
            )
        )
    ]

total_nivelacion = sum(1 for f in filas_combinadas if f.get("ClasificacionNivelar") == "Nivelacion")
total_venta_interna = sum(1 for f in filas_combinadas if f.get("ClasificacionNivelar") == "Venta Interna")

st.markdown(
    render_count_badges([
        ("TOTAL TRASLADOS", str(total_nivelacion + total_venta_interna), "#013066"),
        ("NIVELACION", str(total_nivelacion), CLASIFICACION_COLORES["Nivelacion"]),
        ("VENTA INTERNA", str(total_venta_interna), CLASIFICACION_COLORES["Venta Interna"]),
    ]),
    unsafe_allow_html=True,
)

if not filas_combinadas:
    st.info("No hay datos para los filtros seleccionados.")
else:
    st.download_button(
        "📥 Generar Excel",
        data=exportar_excel(filas_combinadas),
        file_name="nivelacion_ventas_internas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.markdown(render_card(render_combinado_table(filas_combinadas)), unsafe_allow_html=True)

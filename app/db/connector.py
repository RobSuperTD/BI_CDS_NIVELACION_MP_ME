"""
Conexion a Snowflake (dual: local secrets.toml o sesion activa en SiS).
"""

import threading
import time

import pandas as pd
import streamlit as st

from app.config.settings import get_snowflake_config

# Codigo de error de Snowflake para "token de autenticacion vencido".
_CODIGO_TOKEN_EXPIRADO = 390114


def _es_token_expirado(e: Exception) -> bool:
    """Detecta el error 390114 de forma robusta: primero por el codigo
    estructurado que expone SnowparkSQLException (`sql_error_code`), y si no
    esta disponible cae de vuelta a buscar el codigo en el texto del mensaje."""
    if getattr(e, "sql_error_code", None) == _CODIGO_TOKEN_EXPIRADO:
        return True
    return str(_CODIGO_TOKEN_EXPIRADO) in str(e)


# Reintentos adicionales de reconexion si la primera reconexion tambien falla
# (ej. inestabilidad de red/reloj justo despues de que el servidor se reinicio).
_MAX_REINTENTOS_RECONEXION = 2
_ESPERA_ENTRE_REINTENTOS_SEG = 2

# Protege la reconexion: si varios usuarios (hilos) chocan con el token
# vencido al mismo tiempo, solo el primero crea la sesion nueva; los demas
# reutilizan esa misma sesion en vez de crear cada uno la suya.
_reconnect_lock = threading.Lock()


@st.cache_resource(show_spinner="Conectando a Snowflake...")
def get_session():
    """Orden de resolucion:
    1. Streamlit in Snowflake (desplegado) -> sesion activa del contenedor.
    2. Local / servidor BI -> credenciales en .streamlit/secrets.toml ([snowflake])."""
    from snowflake.snowpark import Session

    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        pass

    try:
        cfg = get_snowflake_config()
        # Mantiene el token de sesion vivo mientras el proceso siga corriendo,
        # en vez de dejarlo expirar por inactividad (causa mas comun del 390114
        # en una sesion cacheada por horas via st.cache_resource).
        cfg.setdefault("client_session_keep_alive", True)
        return Session.builder.configs(cfg).create()
    except Exception as e:
        st.error(f"No se pudo conectar a Snowflake: {e}")
        st.info("Configura tus credenciales en `.streamlit/secrets.toml` bajo la seccion `[snowflake]`.")
        st.stop()


def _reconnect(stale):
    with _reconnect_lock:
        actual = get_session()
        if actual is not stale:
            return actual
        get_session.clear()
        return get_session()


def run_query(sql: str) -> pd.DataFrame:
    session = get_session()
    for intento in range(_MAX_REINTENTOS_RECONEXION + 1):
        try:
            return session.sql(sql).to_pandas()
        except Exception as e:
            if not _es_token_expirado(e):
                raise
            if intento == _MAX_REINTENTOS_RECONEXION:
                raise
            time.sleep(_ESPERA_ENTRE_REINTENTOS_SEG)
            session = _reconnect(session)

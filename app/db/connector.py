"""Conexion singleton a Snowflake con reconexion automatica ante expiracion."""

import decimal
import threading
import time

import pandas as pd
import snowflake.connector as sc
import streamlit as st
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from app.config.settings import (
    PRIV_KEY_PASSPHRASE,
    PRIV_KEY_PATH,
    SNOWFLAKE_CONFIG,
)

_MAX_REINTENTOS_RECONEXION = 2
_ESPERA_ENTRE_REINTENTOS_SEG = 2
_reconnect_lock = threading.Lock()


def _get_private_key_bytes() -> bytes:
    with open(PRIV_KEY_PATH, "rb") as f:
        pk = serialization.load_pem_private_key(
            f.read(), password=PRIV_KEY_PASSPHRASE, backend=default_backend()
        )
    return pk.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


@st.cache_resource(show_spinner=False)
def get_conn():
    """Conexion singleton a Snowflake, reutilizada en toda la sesion."""
    return sc.connect(
        private_key=_get_private_key_bytes(),
        **SNOWFLAKE_CONFIG,
    )


def _coerce_decimal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas Decimal a float64 para compatibilidad con Arrow/Streamlit."""
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna()
            if not sample.empty and isinstance(sample.iloc[0], decimal.Decimal):
                df[col] = df[col].astype(float)
    return df


def _cursor_to_df(cursor) -> pd.DataFrame:
    try:
        df = cursor.fetch_pandas_all()
    except Exception:
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []
        df = pd.DataFrame(rows, columns=cols)
    return _coerce_decimal_columns(df)


def _reconnect(stale) -> "sc.SnowflakeConnection":
    with _reconnect_lock:
        actual = get_conn()
        if actual is not stale:
            return actual
        get_conn.clear()
        return get_conn()


def _ejecutar(conn, sql: str, params: tuple | None = None) -> pd.DataFrame:
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return _cursor_to_df(cursor)
    finally:
        cursor.close()


def run_query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    """Ejecuta una consulta SQL sobre la conexion cacheada y reconecta si expiro."""
    conn = get_conn()
    for intento in range(_MAX_REINTENTOS_RECONEXION + 1):
        try:
            return _ejecutar(conn, sql, params)
        except sc.errors.DatabaseError:
            if intento == _MAX_REINTENTOS_RECONEXION:
                raise
            time.sleep(_ESPERA_ENTRE_REINTENTOS_SEG)
            conn = _reconnect(conn)
        except Exception as exc:
            st.error(f"Error al ejecutar la consulta: {exc}")
            raise

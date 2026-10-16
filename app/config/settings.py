"""Configuracion de conexion a Snowflake.

Lee las credenciales desde st.secrets["snowflake"] (seccion [snowflake] de
.streamlit/secrets.toml). En local vive en .streamlit/secrets.toml en la raiz
del repo; en el servidor BI (Docker) se monta en runtime como
/app/.streamlit/secrets.toml desde /opt/config/BI_CDS_NIVELACION_MP_ME/.
"""

import os
import certifi
import streamlit as st

os.environ["SSL_CERT_FILE"] = certifi.where()

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_sf_secrets = st.secrets["snowflake"]

SNOWFLAKE_CONFIG = {
    "account": _sf_secrets["account"],
    "user": _sf_secrets["user"],
    "warehouse": _sf_secrets["warehouse"],
    "client_session_keep_alive": True,
}

_role = _sf_secrets.get("role", "")
if _role:
    SNOWFLAKE_CONFIG["role"] = _role

_raw_key_path = _sf_secrets.get("priv_key_path") or _sf_secrets.get("private_key_file")
if _raw_key_path and not os.path.isabs(_raw_key_path):
    PRIV_KEY_PATH = os.path.join(_REPO_ROOT, _raw_key_path)
else:
    PRIV_KEY_PATH = _raw_key_path

_passphrase = _sf_secrets.get("priv_key_passphrase", "")
PRIV_KEY_PASSPHRASE: bytes | None = _passphrase.encode() if _passphrase else None

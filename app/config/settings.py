import os
import streamlit as st

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_snowflake_config() -> dict:
    cfg = dict(st.secrets["snowflake"])

    priv_key_path = cfg.pop("priv_key_path", None)
    if priv_key_path:
        if not os.path.isabs(priv_key_path):
            priv_key_path = os.path.join(_REPO_ROOT, priv_key_path)
        cfg["private_key_file"] = priv_key_path

    passphrase = cfg.pop("priv_key_passphrase", None)
    if passphrase:
        cfg["private_key_file_pwd"] = passphrase

    return cfg

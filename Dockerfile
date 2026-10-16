FROM python:3.12-slim

WORKDIR /app

# Solo curl (para el HEALTHCHECK). NO agregar gcc: pandas/numpy/pyarrow/
# cryptography/snowflake-connector-python ya traen ruedas manylinux precompiladas
# para python:3.12-slim (linux/amd64).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /usr/local/lib/python3.12/site-packages/pandas/tests \
              /usr/local/lib/python3.12/site-packages/pyarrow/tests \
              /usr/local/lib/python3.12/site-packages/pyarrow/include \
              /usr/local/lib/python3.12/site-packages/plotly/labextension

COPY . .

EXPOSE 8501

# --- Config de producción de Streamlit ---
# Evita el prompt de email y la telemetría en el contenedor.
# CORS/XSRF off: va detrás de Nginx + gate de auth; sin esto el websocket
# (_stcore/stream) se rechaza por origen y el tablero "carga eternamente".
# MALLOC_ARENA_MAX=2: limita la retención de memoria por hilo en glibc.
ENV MALLOC_ARENA_MAX=2

ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_SERVER_BASE_URL_PATH=""

# El subpath (baseUrlPath) se inyecta por entorno en `docker run`
# (STREAMLIT_SERVER_BASE_URL_PATH). El healthcheck respeta ese path.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fs "http://localhost:8501/${STREAMLIT_SERVER_BASE_URL_PATH}/_stcore/health" || exit 1

CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]

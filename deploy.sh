#!/usr/bin/env bash
# =====================================================================
#  deploy.sh — Despliegue estandarizado de dashboards Streamlit
#
#  Uso (en el servidor, dentro de la carpeta del proyecto):
#      ./deploy.sh
#  o indicando la ruta del proyecto:
#      ./deploy.sh /opt/apps/BI_CDS_NIVELACION_MP_ME
#
#  Requisitos por dashboard:
#    - deploy.conf en la raíz del proyecto (APP_NAME, BASE_PATH, HOST_PORT)
#    - /opt/config/<APP_NAME>/secrets.toml      (config Snowflake)
#    - /opt/config/<APP_NAME>/<llave>.p8        (referenciada en secrets.toml)
# =====================================================================
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
cd "$PROJECT_DIR"

# ── 1. Cargar configuración ──────────────────────────────────────────
if [[ ! -f deploy.conf ]]; then
    echo "ERROR: no se encontró deploy.conf en $PROJECT_DIR" >&2
    exit 1
fi
# shellcheck disable=SC1091
source ./deploy.conf

: "${APP_NAME:?Falta APP_NAME en deploy.conf}"
: "${BASE_PATH:?Falta BASE_PATH en deploy.conf}"
: "${HOST_PORT:?Falta HOST_PORT en deploy.conf}"

IMAGE_NAME="$(printf '%s' "$APP_NAME" | tr '[:upper:]' '[:lower:]')"
CONTAINER_NAME="$IMAGE_NAME"
CONFIG_DIR="/opt/config/${APP_NAME}"
SECRETS_FILE="${CONFIG_DIR}/secrets.toml"

echo "════════════════════════════════════════════════"
echo "  Desplegando : $APP_NAME"
echo "  Imagen      : $IMAGE_NAME"
echo "  Puerto      : 127.0.0.1:${HOST_PORT} -> 8501"
echo "  Subpath     : /${BASE_PATH}"
echo "  Config dir  : $CONFIG_DIR"
echo "════════════════════════════════════════════════"

# ── 2. Validaciones previas ──────────────────────────────────────────
if [[ ! -f Dockerfile ]]; then
    echo "ERROR: no hay Dockerfile en $PROJECT_DIR" >&2
    exit 1
fi
if [[ ! -f "$SECRETS_FILE" ]]; then
    echo "ERROR: falta $SECRETS_FILE" >&2
    echo "       Crea la carpeta y el secrets.toml antes de desplegar." >&2
    exit 1
fi

# El puerto no puede estar ocupado por OTRO contenedor
in_use="$(docker ps --filter "publish=${HOST_PORT}" --format '{{.Names}}' \
          | grep -vx "${CONTAINER_NAME}" || true)"
if [[ -n "$in_use" ]]; then
    echo "ERROR: el puerto ${HOST_PORT} ya lo usa el contenedor: ${in_use}" >&2
    echo "       Cambia HOST_PORT en deploy.conf." >&2
    exit 1
fi

# ── 3. Construir imagen ──────────────────────────────────────────────
echo "→ Construyendo imagen ${IMAGE_NAME}..."
docker build -t "$IMAGE_NAME" .

# ── 4. Recrear contenedor ────────────────────────────────────────────
echo "→ Recreando contenedor ${CONTAINER_NAME}..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm   "$CONTAINER_NAME" >/dev/null 2>&1 || true

# Publicado SOLO en loopback (127.0.0.1) detrás de Nginx local.
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "127.0.0.1:${HOST_PORT}:8501" \
    -e "STREAMLIT_SERVER_BASE_URL_PATH=${BASE_PATH}" \
    -v "${CONFIG_DIR}:/app/.streamlit:ro" \
    --restart unless-stopped \
    --label autoheal=true \
    --memory="${MEM_LIMIT:-512m}" \
    --memory-swap="${MEM_LIMIT:-512m}" \
    "$IMAGE_NAME" >/dev/null

# ── 5. Healthcheck ───────────────────────────────────────────────────
URL="http://localhost:${HOST_PORT}/${BASE_PATH}/_stcore/health"
echo -n "→ Esperando respuesta en ${URL}"
code=""
for i in $(seq 1 20); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$URL" || true)"
    [[ "$code" == "200" ]] && { echo " OK (200)"; break; }
    echo -n "."
    sleep 2
done
if [[ "$code" != "200" ]]; then
    echo " FALLÓ (último código: ${code:-sin respuesta})"
    echo "   Diagnóstico: docker logs --tail 40 ${CONTAINER_NAME}" >&2
    exit 1
fi

# ── 5.1 Limpieza automática de la imagen anterior ────────────────────
echo "→ Limpiando imágenes huérfanas..."
docker image prune -f

# ── 6. Bloque Nginx sugerido ─────────────────────────────────────────
cat <<EOF

✔ ${APP_NAME} desplegado correctamente.
    Local   : ${URL}
    Público : https://app.administracionsuper.com:8443/${BASE_PATH}/

Si el bloque de Nginx para /${BASE_PATH}/ AÚN NO existe, agrega esto
dentro del server { listen 443 ... } de /etc/nginx/conf.d/bi-backend.conf :

    location = /${BASE_PATH} { return 301 /${BASE_PATH}/; }
    location /${BASE_PATH}/ {
        auth_request /_authcheck;
        error_page 401 = /__login.html;
        error_page 403 /__forbidden.html;

        proxy_pass http://127.0.0.1:${HOST_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade           \$http_upgrade;
        proxy_set_header Connection         "upgrade";
        proxy_set_header Host               \$host;
        proxy_set_header X-Real-IP          \$remote_addr;
        proxy_set_header X-Forwarded-For    \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto  \$scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

Luego:  sudo nginx -t && sudo systemctl reload nginx
EOF

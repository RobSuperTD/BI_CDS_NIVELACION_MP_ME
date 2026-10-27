"""CSS global del tablero: paleta, header, tarjetas, pildoras y tabla."""

# Paleta de marca
COLOR_AZUL_CORP = "#013066"
COLOR_TEXTO = "#2C2C2C"
COLOR_FONDO_PAGINA = "#F2F4F7"

# Colores por compania (pildoras)
COLOR_GLOBAL = "#0B4DA2"
COLOR_SUPER = "#013066"
COLOR_TRULULU = "#E6007E"
COLOR_BIANCHI = "#F5821F"

COMPANIA_COLORES = {
    "Global": COLOR_GLOBAL,
    "Super": COLOR_SUPER,
    "Trululu": COLOR_TRULULU,
    "Bianchi": COLOR_BIANCHI,
}

# Colores de pastilla para la columna "Centro" del Cuadro 1
COLOR_OKA_LOKA = "#7E57C2"
COLOR_COMERCIALIZADORA = "#6B7280"
COLOR_CENTRO_ROBOTIZADO = "#546E7A"

CENTRO_COLORES = {
    **COMPANIA_COLORES,
    "Oka Loka": COLOR_OKA_LOKA,
    "Comercializadora": COLOR_COMERCIALIZADORA,
    "Centro robotizado": COLOR_CENTRO_ROBOTIZADO,
}

# Colores de estado de inventario vs politicas MRP
COLOR_STOCK_MINIMO = "#E53935"
COLOR_STOCK_MAXIMO = "#F5A623"
COLOR_DENTRO_RANGO = "#4CAF50"
COLOR_SIN_MRP_CON_INV = "#2196F3"
COLOR_QUIEBRE_INVENTARIO = "#9C27B0"

CLASIFICACION_COLORES = {
    "Nivelacion": COLOR_DENTRO_RANGO,
    "Venta Interna": COLOR_SIN_MRP_CON_INV,
}

ESTADO_COLORES = {
    "Stock minimo": COLOR_STOCK_MINIMO,
    "Stock maximo": COLOR_STOCK_MAXIMO,
    "Dentro de rango": COLOR_DENTRO_RANGO,
    "Sin MRP con Inv": COLOR_SIN_MRP_CON_INV,
    "Quiebre inventario": COLOR_QUIEBRE_INVENTARIO,
}

GLOBAL_CSS = f"""
<style>
    :root {{
      --azul:#0033a0; --azul-claro:#0093d9; --amarillo:#ffdb00; --verde:#76b62a;
      --naranja:#ea6608; --magenta:#a51680; --ambar:#f5a404; --tinta:#1c2b4a;
    }}
    /* Fondo general */
    .stApp {{ background: linear-gradient(180deg, #f6f9fe 0%, #eef3fb 100%); }}
    .block-container {{ padding-top: 1.6rem; max-width: 1400px; padding-bottom: 2rem; }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* ---------- Hero header ---------- */
    .hero {{
      background: linear-gradient(110deg, #0033a0 0%, #0093d9 100%);
      border-radius: 18px; padding: 18px 24px; margin: 0 0 14px;
      box-shadow: 0 10px 26px rgba(0,51,160,0.28); position: relative;
      overflow: hidden;
      container-type: inline-size;
      container-name: herosection;
    }}
    .hero::after {{
      content:""; position:absolute; right:-40px; top:-40px; width:160px; height:160px;
      background: radial-gradient(circle, rgba(255,219,0,0.35) 0%, rgba(255,219,0,0) 70%);
      pointer-events: none;
    }}
    .hero-container {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      position: relative;
      z-index: 1;
      width: 100%;
    }}
    .hero-logo-box, .hero-logo-spacer {{
      flex: 0 0 150px;
      width: 150px;
      display: flex;
      align-items: center;
      justify-content: flex-start;
    }}
    .hero-logo-spacer {{
      visibility: hidden;
    }}
    .hero-logo-img {{
      height: 65px;
      max-width: 150px;
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0px 0px 8px rgba(255,219,0,0.6)) drop-shadow(0px 4px 12px rgba(0,51,160,0.7));
      transition: height 0.2s ease, max-width 0.2s ease;
    }}
    .hero-text-box {{
      flex: 1 1 auto;
      text-align: center;
      min-width: 0;
    }}
    .hero h1 {{
      color:#fff;
      font-size: clamp(1.2rem, 2.2vw, 1.85rem);
      font-weight: 800;
      margin: 0;
      letter-spacing: .3px;
      text-shadow: 0 2px 10px rgba(0,0,0,.18);
      line-height: 1.25;
      word-wrap: break-word;
    }}
    .hero .bar {{
      height: 4px;
      width: 110px;
      margin: 8px auto 0;
      background: linear-gradient(90deg,#ffdb00,#f5a404,#ea6608);
      border-radius: 4px;
    }}
    .hero .updated {{
      position: relative;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      margin: 10px auto 0;
      padding: 4px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.28);
      color: #eef6ff;
      font-size: 0.84rem;
      font-weight: 600;
      backdrop-filter: blur(2px);
    }}
    .hero .updated::before {{
      content:""; width:8px; height:8px; border-radius:50%; background:#76b62a;
      box-shadow:0 0 0 3px rgba(118,182,42,0.35);
    }}
    .hero .updated b {{ color:#fff; font-weight:800; }}

    /* Responsive: viewport query (iframe / window) */
    @media (max-width: 992px) {{
      .hero {{ padding: 16px 18px; }}
      .hero-container {{
        flex-direction: column;
        justify-content: center;
        gap: 10px;
      }}
      .hero-logo-box {{
        flex: 0 0 auto;
        width: 100%;
        justify-content: center;
      }}
      .hero-logo-spacer {{
        display: none;
      }}
      .hero-logo-img {{
        height: 52px;
      }}
      .hero h1 {{
        font-size: clamp(1.15rem, 4vw, 1.45rem);
      }}
    }}

    @media (max-width: 576px) {{
      .hero {{ padding: 12px 14px; }}
      .hero-logo-img {{ height: 42px; }}
      .hero h1 {{ font-size: 1.15rem; }}
      .hero .bar {{ width: 80px; height: 3px; margin: 6px auto 0; }}
      .hero .updated {{ font-size: 0.75rem; padding: 3px 10px; }}
    }}

    /* Responsive: container query (en caso de incrustacion flexible) */
    @container herosection (max-width: 950px) {{
      .hero-container {{
        flex-direction: column;
        justify-content: center;
        gap: 10px;
      }}
      .hero-logo-box {{
        flex: 0 0 auto;
        width: 100%;
        justify-content: center;
      }}
      .hero-logo-spacer {{
        display: none;
      }}
      .hero-logo-img {{
        height: 52px;
      }}
      .hero h1 {{
        font-size: 1.35rem;
      }}
    }}
    /* Ocultar el menú superior nativo de Streamlit */
    header[data-testid="stHeader"] {{
      display: none !important;
    }}


    /* ---------- Tarjetas blancas ---------- */
    .card {{
        background: #FFFFFF;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(16, 24, 40, 0.18), 0 2px 6px rgba(16, 24, 40, 0.10);
    }}
    .card-title {{
        color: {COLOR_AZUL_CORP};
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 10px;
    }}
    .section-title {{
        text-align: center;
        color: {COLOR_AZUL_CORP};
        font-weight: 700;
        font-size: 1.05rem;
        margin: 6px 0 16px 0;
    }}
    .section-title .rule {{
        width: 60px;
        height: 3px;
        background: {COLOR_AZUL_CORP};
        margin: 6px auto 0 auto;
        border-radius: 3px;
    }}

    /* ---------- Pildoras de compania ---------- */
    .pill {{
        display: inline-block;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 6px 22px;
        border-radius: 20px;
        text-align: center;
    }}

    /* ---------- Tabla resumen (metricas por compania) ---------- */
    table.metric-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    table.metric-table th {{
        text-align: center;
        padding: 10px 8px;
        border-bottom: 1px solid #EEF1F5;
    }}
    table.metric-table td {{
        text-align: center;
        padding: 10px 8px;
        border-bottom: 1px solid #EEF1F5;
        color: {COLOR_TEXTO};
    }}
    table.metric-table td:first-child, table.metric-table th:first-child {{
        text-align: left;
        color: {COLOR_AZUL_CORP};
        font-weight: 600;
    }}
    table.metric-table tr.metric-total td {{
        font-weight: 700;
        font-size: 1.05rem;
        color: {COLOR_AZUL_CORP};
    }}

    /* ---------- Franja de estados (Stock minimo, etc) ---------- */
    .status-strip {{
        display: flex;
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 4px;
    }}
    .status-strip .seg {{
        flex: 1;
        color: #FFFFFF;
        text-align: center;
        font-weight: 700;
        font-size: 0.8rem;
        padding: 8px 4px;
    }}

    /* ---------- Badge de estado dentro de tabla detalle ---------- */
    .status-dot-cell {{
        display: inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        margin-right: 6px;
    }}

    /* ---------- Filtros (sidebar) ---------- */
    .filtro-label {{
        background: {COLOR_AZUL_CORP};
        color: #FFFFFF;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 6px 6px 0 0;
        display: inline-block;
    }}

    /* ---------- Tabla de detalle con borde degradado ---------- */
    /* Separado en 2 capas: el borde/padding va en el contenedor EXTERIOR
       (sin scroll), y el interior (con scroll) queda sin padding para que
       el thead sticky quede pegado al borde superior visible sin hueco. */
    .detail-table-outer {{
        border: 2px solid transparent;
        border-radius: 12px;
        background:
            linear-gradient(#fff, #fff) padding-box,
            linear-gradient(120deg, #1E8FD6, #4CAF50, #F5A623, #E6007E) border-box;
        padding: 4px;
        margin-bottom: 10px;
    }}
    .detail-table-wrap {{
        max-height: 900px;
        overflow: auto;
        border-radius: 9px;
    }}
    table.detail-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
    }}
    table.detail-table thead th {{
        position: sticky;
        top: 0;
        background: {COLOR_AZUL_CORP};
        color: #FFFFFF;
        padding: 8px 6px;
        text-align: center;
        z-index: 1;
    }}
    table.detail-table tbody td {{
        padding: 7px 8px;
        text-align: center;
        border-bottom: 1px solid #F0F2F5;
        white-space: nowrap;
    }}
    table.detail-table tbody tr:hover {{
        background: #F7F9FC;
    }}
    table.detail-table tbody tr.grupo-material-fin td {{
        border-bottom: 2px solid {COLOR_AZUL_CORP};
    }}

    /* ---------- Badges de conteo (Materias primas / Material empaque) ---------- */
    .count-badge {{
        display: inline-block;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 0.8rem;
        padding: 6px 16px;
        border-radius: 20px;
        margin-right: 10px;
    }}

    /* ---------- Radio horizontal estilizado como pildoras (para secciones) ---------- */
    div[role="radiogroup"] {{
        gap: 6px;
    }}

    /* ---------- Fila de pastillas de filtro (Centro) ---------- */
    .st-key-fila_pills_centro {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap;
        gap: 8px;
    }}
    .st-key-fila_pills_centro > div {{
        width: auto !important;
        flex: 0 0 auto !important;
    }}

    /* ---------- Icono de informacion (i) con mensaje al pasar el mouse ---------- */
    .info-tip {{
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 17px;
        height: 17px;
        margin-left: 6px;
        border-radius: 50%;
        background: {COLOR_AZUL_CORP};
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 700;
        cursor: help;
        vertical-align: middle;
    }}
    .info-tip .info-tip-text {{
        visibility: hidden;
        opacity: 0;
        position: absolute;
        top: 24px;
        right: -8px;
        width: 340px;
        padding: 12px 14px;
        border-radius: 10px;
        background: #FFFFFF;
        color: #2C2C2C;
        border: 1px solid {COLOR_AZUL_CORP};
        box-shadow: 0 8px 20px rgba(16, 24, 40, 0.18);
        font-weight: 400;
        font-size: 0.85rem;
        line-height: 1.4;
        text-align: left;
        z-index: 1000;
        transition: opacity .15s;
    }}
    .info-tip:hover .info-tip-text {{
        visibility: visible;
        opacity: 1;
    }}
    .info-tip-text b {{
        color: {COLOR_AZUL_CORP};
    }}
</style>
"""

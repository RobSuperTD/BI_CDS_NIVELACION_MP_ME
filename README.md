# 📦 Tablero de Nivelación y Ventas Internas (MP y ME)

Aplicación web interactiva desarrollada en **Streamlit** para la gestión, simulación y optimización del balance de inventario de **Materias Primas (MP)** y **Material de Empaque (ME)** entre los diferentes centros productivos y razones sociales del grupo.

El tablero cruza en tiempo real el inventario disponible en piso y almacenes contra las reservas actuales, los requerimientos del **MRP** y las **Entregas Pendientes de Órdenes de Compra (OC)** en **Snowflake**, sugiriendo automáticamente los traslados óptimos entre centros y clasificándolos en **Nivelaciones** o **Ventas Internas**.

---

## 🚀 Características Principales

- **Vista Unificada de Balance y Traslados:** Integra en una sola tabla jerárquica el estado de cada centro (`Inventario`, `Necesidad`, `Entrega Pendiente`, `Fecha Entrega`, `Bloqueado`) junto con el plan de despacho sugerido (`Centro a Nivelar`, `Cantidad a Nivelar`, `Clasificación`) y una fila de **Subtotal** consolidado por material.
- **Enfoque Accionable:** Filtra y muestra exclusivamente aquellos materiales que presentan al menos una oportunidad de traslado (Nivelación o Venta Interna) en la semana y modo seleccionados.
- **Motor de Simulación Semanal (Actual vs. Simulado):**
  - **Modo Actual:** Proyecta el inventario de las próximas semanas descontando únicamente el consumo ($\text{Inventario} - \text{Necesidad}$), sin considerar recepciones de OC ni traslados entre centros.
  - **Modo Simulado:** Proyecta cómo evolucionaría el inventario si se reciben a tiempo las entregas pendientes de OC de la semana previa y se ejecutan los traslados recomendados semana a semana. Incluye un tooltip informativo `(i)` en la interfaz.
- **Filtros Avanzados y Búsqueda Múltiple:**
  - Filtro de **Grupo** (*Materia Prima*, *Material de Empaque* o *Ambos*).
  - Selección múltiple de **IdCentro** (origen/visualización) y **Centro Destino** con sincronización automática de la opción `"Todos"`.
  - **Buscador por Pastillas (Tags):** Permite ingresar y combinar múltiples códigos `ID` o nombres de materiales simultáneamente.
  - Filtro por **Clasificación** (*Todas*, *Nivelación*, *Venta Interna*) y horizonte de **Semana** (*Semana actual*, *Próxima semana*, *Semana actual + 2*).
- **Exportación a Excel (`.xlsx`):** Descarga inmediata en memoria (`openpyxl`) de la vista filtrada lista para gestión operativa.
- **Alto Rendimiento:** Consultas y simulaciones optimizadas con `@st.cache_data` y renderizado HTML vectorizado mediante listas (sin uso de `iterrows` en el dibujado).

---

## 🧠 Reglas de Negocio y Lógica de Cálculo

### 1. Centros y Grupos de Materiales
| Grupo | Prefijo Material | Centros Habilitados (`IdCentroFase2`) |
| :--- | :---: | :--- |
| **Materia Prima (MP)** | `13%` | `CPS1`, `CPS2`, `CPT2`, `CPB2`, `CPB1` |
| **Material de Empaque (ME)** | `14%` | `CPS9`, `CPT9`, `CPB9`, `CPE9`, `CPK9`, `CPO9` |

### 2. Composición del Inventario (Semana 0)
A partir de la vista `TDS_VW_CDS_INVENTARIOMATERIALMMDIAACTUAL`:
- **Inventario Libre + Calidad (`inv_libre_calidad`):** Suma de `CantidadLibreUtilizacion + CantidadControlCalidad` excluyendo los almacenes de excepción (`0003`, `0004`, `0005`, `0006`, `0017`, `0018`, `0038`, `0039`). **Es el único inventario elegible para ser trasladado a otros centros.**
- **Inventario de Producción (`InventarioProduccion`):** Equivale al **85%** de `(Libre + Calidad)` ubicado en los almacenes de excepción mencionados. Sirve para cubrir la necesidad del propio centro, pero **nunca se despacha en traslados**.
- **Inventario Total (`inv_total`):** `inv_libre_calidad + InventarioProduccion`.
- **Inventario Bloqueado (`CantidadBloqueado`):** Se muestra como alerta visual (píldora amarilla) al final de la fila; no participa en el cálculo de disponibilidad ni en la cascada semanal.

### 3. Necesidades por Horizonte Semanal
- **Semana 0 (Semana Actual):** Corresponde a la columna `CantidadReservado` de la vista de inventario actual, calculada de forma global por centro (**sin** excluir almacenes).
- **Semana 1 (Próxima) y Semana 2 (Actual + 2):** Provienen de los requerimientos activos (`MRP_Estado = 'Activo'`) en `EEO_RequerimientoMaterialMRP` para materiales `ZMPR` y `ZEMP`.

### 4. Entregas Pendientes de Órdenes de Compra (OC)
Extraídas de `TDS_VW_CDS_ORDENCOMPRA` bajo las siguientes condiciones:
- Cantidad pendiente: `CantidadOrdenCompra - CantidadEntregada`.
- Solo posiciones con entrega abierta (`IndicadorEntregaFinal = FALSE`) y tipos `ZMPR` / `ZEMP`.
- **Exclusión de compras intercompañía:** Se descartan las órdenes cuya `RazonSocial` pertenece a empresas internas del grupo:
  - `C.I. SUPER S.A.S.`
  - `SUPER DE ALIMENTOS S.A.S`
  - `GOLOSINAS TRULULU S.A.`
  - `GOLOSINAS SUPER DE COSTA RICA`
  - `MUNDO SUPER GUATEMALA SOCIEDAD ANÓN`
- Se agrupan por semana (`0`, `1`, `2`) según `FechaEntregaPosicion` y se registra la fecha mínima programada (`DD/MM`).

### 5. Algoritmo de Asignación de Traslados (`calcular_traslados_semana`)
Para cada material y semana:
1. Se calcula el balance neto de cada centro:
   $$\text{Superávit}(c) = \text{InvTotal}(c) - \text{Necesidad}(c)$$
2. **Centros Origen ($\text{Superávit} > 0$):**
   - Lo máximo que pueden enviar sin quedar en déficit y sin tocar piso de producción es:
     $$\text{Capacidad}(c) = \min\big(\text{Superávit}(c),\ \text{InvLibreCalidad}(c)\big)$$
   - Se priorizan de **mayor a menor superávit**.
3. **Centros Destino ($\text{Superávit} < 0$):**
   - Se priorizan de **menor a mayor déficit** con el objetivo de cubrir por completo la mayor cantidad de plantas posible.
4. **Clasificación del Movimiento:**
   - 🟢 **Nivelación:** Origen y Destino comparten el **mismo último dígito** en su código de centro (misma razón social, ej. `CPS1` → `CPB1` o `CPS9` → `CPT9`).
   - 🔵 **Venta Interna:** Origen y Destino tienen **diferente último dígito** (distinta razón social, ej. `CPS1` → `CPS2`).

---

## 📁 Estructura del Proyecto

```text
/
├── app/
│   ├── main.py               # Punto de entrada Streamlit: layout, filtros, KPIs y descarga Excel
│   ├── data.py               # Consulta SQL CTE y caché de datos
│   ├── logic_inventario.py   # Motor de simulación semanal, algoritmo de traslados y exportación .xlsx
│   ├── components.py         # Generadores de tablas HTML con rowspan, subtotales, tarjetas y badges
│   ├── styles.py             # Sistema de diseño CSS, paleta corporativa, Hero Header y tooltips
│   ├── config/
│   │   └── settings.py       # Lectura de credenciales Snowflake desde .streamlit/secrets.toml
│   ├── db/
│   │   └── connector.py      # Conexión singleton a Snowflake (.p8) con reconexión automática
│   └── static/               # Recursos gráficos (logo_super.png)
├── .streamlit/
│   ├── config.toml           # Tema corporativo y configuración del servidor Streamlit
│   └── secrets.toml.example  # Plantilla de configuración de credenciales Snowflake
├── Dockerfile                # Imagen de producción (python:3.12-slim)
├── deploy.conf               # Parámetros del contenedor (APP_NAME, BASE_PATH, HOST_PORT, MEM_LIMIT)
├── deploy.sh                 # Script estandarizado de despliegue en el servidor BI
├── requirements.txt          # Dependencias del entorno Python
├── .dockerignore             # Exclusiones de contexto Docker
├── .gitignore                # Reglas de exclusión de Git (secrets.toml, llaves .p8, caché)
└── README.md                 # Documentación general y técnica del proyecto
```

---

## ⚙️ Requisitos e Instalación Local

1. **Clonar el repositorio y ubicarse en el directorio raíz:**
   ```bash
   git clone https://github.com/juanfernandopatino/BI_CDS_NIVELACION_MP_ME.git
   cd BI_CDS_NIVELACION_MP_ME
   ```

2. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar las credenciales de Snowflake (`.streamlit/secrets.toml`):**
   Copiar `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y completar las credenciales y la ruta hacia la llave privada `.p8`:
   ```toml
   [snowflake]
   account = "nsauztq-gf69991"
   user = "USR_TABLEAU"
   role = "TABLEAU"
   warehouse = "COMPUTE_WH"
   priv_key_path = ".streamlit/Privada_USR_TABLEAU.p8"
   priv_key_passphrase = ""
   ```

---

## ▶️ Ejecución

Para levantar el servidor local de Streamlit:

```bash
python -m streamlit run app/main.py
```

El tablero estará disponible en tu navegador en `http://localhost:8501`.

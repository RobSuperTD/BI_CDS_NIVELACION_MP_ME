"""Capa de acceso a datos (Snowflake) para el tablero Nivelacion y Ventas Internas MP y ME.

Conexion por llave privada .p8 leida desde .streamlit/secrets.toml ([snowflake])
mediante app/db/connector.py y app/config/settings.py, igual que el resto de
tableros del servidor de BI.

Fuentes:
  - Inventario: DB_EXCELENCIAYEFECTIVIDADORGANIZACIONAL.PUBLIC."EEO_InventarioMaterialMM" (a la maxima fecha presente)
  - Necesidad MRP: DB_EXCELENCIAYEFECTIVIDADORGANIZACIONAL.PUBLIC."EEO_RequerimientoMaterialMRP"
  - Entregas pendientes de OC: DB_TABLEAUDATASOURCE.CADENASUMINISTRO.TDS_VW_CDS_ORDENCOMPRA
  - Maestra de materiales: DB_TABLEAUDATASOURCE.CADENASUMINISTRO.TDS_VW_CDS_MAESTRAMATERIALES
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.db.connector import run_query


def _query(sql: str) -> pd.DataFrame:
    return run_query(sql)


QUERY_INVENTARIO_NECESIDAD = """
-- Inventario + Produccion + Entregas Pendientes de OC + Necesidad MRP (semana 0,1,2), una fila por Material + Centro.
-- Centros materia prima (material inicia por '13'): CPS1, CPS2, CPT2, CPB2, CPB1
-- Centros empaque (material inicia por '14'): CPS9, CPT9, CPB9, CPE9, CPK9, CPO9
-- Excluye los almacenes: 0003, 0004, 0005, 0006, 0017, 0018, 0038, 0039 (solo aplica a inventario normal, InventarioProduccion es el 85% de esos almacenes)
-- FechaReferencia = Maxima fecha presente en EEO_InventarioMaterialMM (resiliente ante desfases o fallos del ETL diario).
-- Semana 0 = semana de corte (lunes a domingo), Semana 1 = siguiente semana, Semana 2 = la que sigue.
-- Entrega Pendiente: ordenes de compra no entregadas totalmente (IndicadorEntregaFinal = FALSE), sumando
-- todos los almacenes, discriminadas por el centro real (IdCentroFase2) de TDS_VW_CDS_ORDENCOMPRA.
-- Excluye ordenes cuya RazonSocial sea una de las razones sociales internas del grupo (no son compras
-- a terceros).
-- Necesidad Semana 0 (actual) = CantidadReservado de EEO_InventarioMaterialMM a la fecha de corte,
-- SIN filtro de almacen (a diferencia del inventario normal, que si excluye los almacenes de excepcion).
-- Necesidad Semana 1 y 2 siguen viniendo del MRP (EEO_RequerimientoMaterialMRP).

WITH FECHA_CORTE AS (
    SELECT COALESCE(MAX(DATE("IMM_FechaInsercion")), CURRENT_DATE()) AS FechaReferencia
    FROM DB_EXCELENCIAYEFECTIVIDADORGANIZACIONAL.PUBLIC."EEO_InventarioMaterialMM"
),
INV_BASE AS (
    SELECT
        i."IMM_IdMaterial"                as IdMaterial,
        i.IMM_ID_CENTRO_CF2              as Centro,
        i."IMM_UnidadMedidaBase"          as Unidad,
        i."IMM_CantidadLibreUtilizacion"  as Libre,
        i."IMM_CantidadControlCalidad"   as Calidad,
        i."IMM_CantidadBloqueado"        as Bloqueado
    FROM DB_EXCELENCIAYEFECTIVIDADORGANIZACIONAL.PUBLIC."EEO_InventarioMaterialMM" i
    CROSS JOIN FECHA_CORTE fc
    WHERE DATE(i."IMM_FechaInsercion") = fc.FechaReferencia
      AND (
            (i."IMM_IdMaterial" LIKE '13%' AND i.IMM_ID_CENTRO_CF2 IN ('CPS1','CPS2','CPT2','CPB2','CPB1'))
         OR (i."IMM_IdMaterial" LIKE '14%' AND i.IMM_ID_CENTRO_CF2 IN ('CPS9','CPT9','CPB9','CPE9','CPK9','CPO9'))
          )
      AND (i."IMM_IdAlmacen" IS NULL OR i."IMM_IdAlmacen" NOT IN ('0003','0004','0005','0006','0017','0018','0038','0039'))
),
RESERVADO_BASE AS (
    -- CantidadReservado (Necesidad Semana 0) NO se filtra por almacen, a diferencia del inventario normal
    SELECT
        i."IMM_IdMaterial"           as IdMaterial,
        i.IMM_ID_CENTRO_CF2         as Centro,
        i."IMM_CantidadReservado"    as Reservado
    FROM DB_EXCELENCIAYEFECTIVIDADORGANIZACIONAL.PUBLIC."EEO_InventarioMaterialMM" i
    CROSS JOIN FECHA_CORTE fc
    WHERE DATE(i."IMM_FechaInsercion") = fc.FechaReferencia
      AND (
            (i."IMM_IdMaterial" LIKE '13%' AND i.IMM_ID_CENTRO_CF2 IN ('CPS1','CPS2','CPT2','CPB2','CPB1'))
         OR (i."IMM_IdMaterial" LIKE '14%' AND i.IMM_ID_CENTRO_CF2 IN ('CPS9','CPT9','CPB9','CPE9','CPK9','CPO9'))
          )
),
PROD_BASE AS (
    -- Inventario en los almacenes de excepcion (0003,0004,0005,0006,0017,0018,0038,0039)
    SELECT
        i."IMM_IdMaterial"                as IdMaterial,
        i.IMM_ID_CENTRO_CF2             as Centro,
        i."IMM_CantidadLibreUtilizacion"  as Libre,
        i."IMM_CantidadControlCalidad"   as Calidad
    FROM DB_EXCELENCIAYEFECTIVIDADORGANIZACIONAL.PUBLIC."EEO_InventarioMaterialMM" i
    CROSS JOIN FECHA_CORTE fc
    WHERE DATE(i."IMM_FechaInsercion") = fc.FechaReferencia
      AND (
            (i."IMM_IdMaterial" LIKE '13%' AND i.IMM_ID_CENTRO_CF2 IN ('CPS1','CPS2','CPT2','CPB2','CPB1'))
         OR (i."IMM_IdMaterial" LIKE '14%' AND i.IMM_ID_CENTRO_CF2 IN ('CPS9','CPT9','CPB9','CPE9','CPK9','CPO9'))
          )
      AND i."IMM_IdAlmacen" IN ('0003','0004','0005','0006','0017','0018','0038','0039')
),
MRP_BASE AS (
    SELECT
        "MRP_IdMaterial"     as IdMaterial,
        "MRP_ID_CENTRO_CF2"  as Centro,
        "MRP_UnidadMedidaBase" as Unidad,
        "MRP_CantidadNecesaria" as Cantidad,
        DATEDIFF('WEEK', DATE_TRUNC('WEEK', fc.FechaReferencia), DATE_TRUNC('WEEK', "MRP_FechaNecesidad")) as Semana
    FROM DB_EXCELENCIAYEFECTIVIDADORGANIZACIONAL.PUBLIC."EEO_RequerimientoMaterialMRP"
    CROSS JOIN FECHA_CORTE fc
    WHERE "MRP_Estado" = 'Activo'
      AND "MRP_TipoMaterial" IN ('ZMPR','ZEMP')
      AND (
            ("MRP_IdMaterial" LIKE '13%' AND "MRP_ID_CENTRO_CF2" IN ('CPS1','CPS2','CPT2','CPB2','CPB1'))
         OR ("MRP_IdMaterial" LIKE '14%' AND "MRP_ID_CENTRO_CF2" IN ('CPS9','CPT9','CPB9','CPE9','CPK9','CPO9'))
          )
),
PO_BASE AS (
    -- Entregas pendientes de ordenes de compra (no entregadas totalmente), sumando todos los almacenes,
    -- discriminadas por el centro real (IdCentroFase2)
    SELECT
        "IdMaterial"           as IdMaterial,
        "IdCentroFase2"        as Centro,
        ("CantidadOrdenCompra" - "CantidadEntregada") as Cantidad,
        "FechaEntregaPosicion" as FechaEntrega,
        DATEDIFF('WEEK', DATE_TRUNC('WEEK', fc.FechaReferencia), DATE_TRUNC('WEEK', "FechaEntregaPosicion")) as Semana
    FROM DB_TABLEAUDATASOURCE.CADENASUMINISTRO.TDS_VW_CDS_ORDENCOMPRA
    CROSS JOIN FECHA_CORTE fc
    WHERE "IndicadorEntregaFinal" = FALSE
      AND "TipoMaterial" IN ('ZMPR','ZEMP')
      AND "RazonSocial" NOT IN (
            'C.I. SUPER S.A.S.',
            'SUPER DE ALIMENTOS S.A.S',
            'GOLOSINAS TRULULU S.A.',
            'GOLOSINAS SUPER DE COSTA RICA',
            'MUNDO SUPER GUATEMALA SOCIEDAD ANÓN'
          )
      AND (
            ("IdMaterial" LIKE '13%' AND "IdCentroFase2" IN ('CPS1','CPS2','CPT2','CPB2','CPB1'))
         OR ("IdMaterial" LIKE '14%' AND "IdCentroFase2" IN ('CPS9','CPT9','CPB9','CPE9','CPK9','CPO9'))
          )
),
PO_AGG AS (
    SELECT
        IdMaterial, Centro,
        SUM(CASE WHEN Semana = 0 THEN Cantidad ELSE 0 END) as EntregaPendienteS0,
        MIN(CASE WHEN Semana = 0 THEN FechaEntrega END)    as FechaEntregaProgramadaS0,
        SUM(CASE WHEN Semana = 1 THEN Cantidad ELSE 0 END) as EntregaPendienteS1,
        MIN(CASE WHEN Semana = 1 THEN FechaEntrega END)    as FechaEntregaProgramadaS1,
        SUM(CASE WHEN Semana = 2 THEN Cantidad ELSE 0 END) as EntregaPendienteS2,
        MIN(CASE WHEN Semana = 2 THEN FechaEntrega END)    as FechaEntregaProgramadaS2
    FROM PO_BASE
    WHERE Semana IN (0, 1, 2)
    GROUP BY IdMaterial, Centro
),
UNIDAD_BASE AS (
    SELECT IdMaterial, Unidad FROM INV_BASE WHERE Unidad IS NOT NULL
    UNION
    SELECT IdMaterial, Unidad FROM MRP_BASE WHERE Unidad IS NOT NULL
),
UNIDAD_AGG AS (
    SELECT
        IdMaterial,
        LISTAGG(DISTINCT Unidad, ', ') as UnidadMedida
    FROM UNIDAD_BASE
    GROUP BY IdMaterial
),
MATERIALES_ALL AS (
    SELECT DISTINCT IdMaterial FROM INV_BASE
    UNION SELECT DISTINCT IdMaterial FROM RESERVADO_BASE
    UNION SELECT DISTINCT IdMaterial FROM PROD_BASE
    UNION SELECT DISTINCT IdMaterial FROM MRP_BASE
    UNION SELECT DISTINCT IdMaterial FROM PO_BASE
),
CENTROS_RAW AS (
    SELECT 'CPS1' as Centro UNION ALL SELECT 'CPS2' UNION ALL SELECT 'CPT2' UNION ALL SELECT 'CPB2' UNION ALL SELECT 'CPB1'
),
CENTROS_EMP AS (
    SELECT 'CPS9' as Centro UNION ALL SELECT 'CPT9' UNION ALL SELECT 'CPB9' UNION ALL SELECT 'CPE9' UNION ALL SELECT 'CPK9' UNION ALL SELECT 'CPO9'
),
MATERIAL_CENTRO AS (
    SELECT MA.IdMaterial, C.Centro FROM MATERIALES_ALL MA CROSS JOIN CENTROS_RAW C WHERE MA.IdMaterial LIKE '13%'
    UNION ALL
    SELECT MA.IdMaterial, C.Centro FROM MATERIALES_ALL MA CROSS JOIN CENTROS_EMP C WHERE MA.IdMaterial LIKE '14%'
),
INV_AGG AS (
    SELECT
        IdMaterial, Centro,
        SUM(Libre)                as InventarioLibreUtilizacion,
        SUM(Calidad)              as InventarioCalidad,
        SUM(Bloqueado)            as InventarioBloqueado
    FROM INV_BASE
    GROUP BY IdMaterial, Centro
),
RESERVADO_AGG AS (
    SELECT
        IdMaterial, Centro,
        SUM(Reservado) as CantidadReservado
    FROM RESERVADO_BASE
    GROUP BY IdMaterial, Centro
),
PROD_AGG AS (
    SELECT
        IdMaterial, Centro,
        (SUM(Libre) + SUM(Calidad)) * 0.85 as InventarioProduccion
    FROM PROD_BASE
    GROUP BY IdMaterial, Centro
),
MRP_AGG AS (
    -- NecesidadSemana0 ya no se calcula aqui: la Necesidad de la semana actual
    -- viene de CantidadReservado (RESERVADO_AGG), no del MRP.
    SELECT
        IdMaterial, Centro,
        SUM(CASE WHEN Semana = 1 THEN Cantidad ELSE 0 END) as NecesidadSemana1,
        SUM(CASE WHEN Semana = 2 THEN Cantidad ELSE 0 END) as NecesidadSemana2
    FROM MRP_BASE
    WHERE Semana IN (1, 2)
    GROUP BY IdMaterial, Centro
)
SELECT
    MC.IdMaterial                                             as IdMaterial,
    MM."Material"                                             as Material,
    MC.Centro                                                 as IdCentro,
    COALESCE(U.UnidadMedida, MM."UnidadMedidaBase")            as UnidadMedida,
    COALESCE(I.InventarioLibreUtilizacion, 0)                  as InventarioLibreUtilizacion,
    COALESCE(I.InventarioCalidad, 0)                           as InventarioCalidad,
    COALESCE(I.InventarioBloqueado, 0)                         as CantidadBloqueado,
    COALESCE(P.InventarioProduccion, 0)                        as InventarioProduccion,
    COALESCE(PO.EntregaPendienteS0, 0)                         as "Entrega Pendiente S0",
    PO.FechaEntregaProgramadaS0                                as "Fecha Entrega Programada S0",
    COALESCE(PO.EntregaPendienteS1, 0)                         as "Entrega Pendiente S1",
    PO.FechaEntregaProgramadaS1                                as "Fecha Entrega Programada S1",
    COALESCE(PO.EntregaPendienteS2, 0)                         as "Entrega Pendiente S2",
    PO.FechaEntregaProgramadaS2                                as "Fecha Entrega Programada S2",
    COALESCE(RES.CantidadReservado, 0)                         as NecesidadSemana0,
    COALESCE(R.NecesidadSemana1, 0)                            as NecesidadSemana1,
    COALESCE(R.NecesidadSemana2, 0)                            as NecesidadSemana2,
    FC.FechaReferencia                                         as FechaReferencia
FROM MATERIAL_CENTRO MC
CROSS JOIN FECHA_CORTE FC
LEFT JOIN INV_AGG I  ON MC.IdMaterial = I.IdMaterial  AND MC.Centro = I.Centro
LEFT JOIN RESERVADO_AGG RES ON MC.IdMaterial = RES.IdMaterial AND MC.Centro = RES.Centro
LEFT JOIN PROD_AGG P ON MC.IdMaterial = P.IdMaterial  AND MC.Centro = P.Centro
LEFT JOIN MRP_AGG R  ON MC.IdMaterial = R.IdMaterial  AND MC.Centro = R.Centro
LEFT JOIN PO_AGG PO  ON MC.IdMaterial = PO.IdMaterial AND MC.Centro = PO.Centro
LEFT JOIN UNIDAD_AGG U ON MC.IdMaterial = U.IdMaterial
LEFT JOIN DB_TABLEAUDATASOURCE.CADENASUMINISTRO.TDS_VW_CDS_MAESTRAMATERIALES MM ON MC.IdMaterial = MM."IdMaterial"
WHERE COALESCE(I.InventarioLibreUtilizacion, 0) != 0
   OR COALESCE(I.InventarioCalidad, 0) != 0
   OR COALESCE(I.InventarioBloqueado, 0) != 0
   OR COALESCE(RES.CantidadReservado, 0) != 0
   OR COALESCE(P.InventarioProduccion, 0) != 0
   OR COALESCE(PO.EntregaPendienteS0, 0) != 0
   OR COALESCE(PO.EntregaPendienteS1, 0) != 0
   OR COALESCE(PO.EntregaPendienteS2, 0) != 0
   OR COALESCE(R.NecesidadSemana1, 0) != 0
   OR COALESCE(R.NecesidadSemana2, 0) != 0
ORDER BY MC.IdMaterial, MC.Centro
"""


@st.cache_data(ttl=3600, show_spinner=False)
def cargar_inventario_necesidad() -> pd.DataFrame:
    """Columnas tal como las nombra la consulta (alias sin comillas -> MAYUSCULA
    por defecto de Snowflake; alias entre comillas, ej. "CPS1 Inv", conservan su forma)."""
    return _query(QUERY_INVENTARIO_NECESIDAD)

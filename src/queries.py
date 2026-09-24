"""Consultas agregadas e parametrizadas para os dashboards."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Mapping

import pandas as pd
import streamlit as st

from src.database import ReadOnlyViolation, execute_query, validate_read_only_query


TTL_AGREGACAO_SIMPLES = 60
TTL_MULTIPLOS_JOINS = 900


INDICADORES_VENDAS_SQL = """
SELECT
    COALESCE(SUM(v.valor_pago), 0)::numeric(14, 2) AS faturamento_total,
    COUNT(v.id_vendas)::bigint AS quantidade_vendida,
    COALESCE(AVG(v.valor_pago), 0)::numeric(14, 2) AS ticket_medio
FROM vendas AS v
WHERE v.data_venda >= :data_inicio
  AND v.data_venda < :data_fim_exclusiva
"""

EVOLUCAO_VENDAS_SQL = """
SELECT
    DATE_TRUNC('day', v.data_venda)::date AS data,
    SUM(v.valor_pago)::numeric(14, 2) AS faturamento,
    COUNT(v.id_vendas)::bigint AS quantidade
FROM vendas AS v
WHERE v.data_venda >= :data_inicio
  AND v.data_venda < :data_fim_exclusiva
GROUP BY DATE_TRUNC('day', v.data_venda)::date
ORDER BY data
"""

DESEMPENHO_CONCESSIONARIAS_SQL = """
SELECT
    c.id_concessionarias,
    c.concessionaria,
    COALESCE(vp.faturamento, 0)::numeric(14, 2) AS faturamento,
    COALESCE(vp.quantidade, 0)::bigint AS quantidade,
    COALESCE(vp.ticket_medio, 0)::numeric(14, 2) AS ticket_medio
FROM concessionarias AS c
LEFT JOIN (
    SELECT
        v.id_concessionarias,
        SUM(v.valor_pago) AS faturamento,
        COUNT(v.id_vendas) AS quantidade,
        AVG(v.valor_pago) AS ticket_medio
    FROM vendas AS v
    WHERE v.data_venda >= :data_inicio
      AND v.data_venda < :data_fim_exclusiva
      AND (
          CAST(:id_concessionaria AS integer) IS NULL
          OR v.id_concessionarias = CAST(:id_concessionaria AS integer)
      )
    GROUP BY v.id_concessionarias
) AS vp ON vp.id_concessionarias = c.id_concessionarias
ORDER BY faturamento DESC, c.concessionaria
"""

DESEMPENHO_ESTADOS_SQL = """
WITH vendas_periodo AS (
    SELECT
        v.id_concessionarias,
        v.id_vendas,
        v.valor_pago
    FROM vendas AS v
    WHERE v.data_venda >= :data_inicio
      AND v.data_venda < :data_fim_exclusiva
)
SELECT
    e.id_estados,
    e.estado,
    e.sigla,
    COALESCE(SUM(vp.valor_pago), 0)::numeric(14, 2) AS faturamento,
    COUNT(vp.id_vendas)::bigint AS quantidade,
    COALESCE(AVG(vp.valor_pago), 0)::numeric(14, 2) AS ticket_medio
FROM concessionarias AS co
JOIN cidades AS ci ON ci.id_cidades = co.id_cidades
JOIN estados AS e ON e.id_estados = ci.id_estados
LEFT JOIN vendas_periodo AS vp ON vp.id_concessionarias = co.id_concessionarias
GROUP BY e.id_estados, e.estado, e.sigla
ORDER BY faturamento DESC, e.estado
"""

DESEMPENHO_CIDADES_SQL = """
WITH vendas_periodo AS (
    SELECT
        v.id_concessionarias,
        v.id_vendas,
        v.valor_pago
    FROM vendas AS v
    WHERE v.data_venda >= :data_inicio
      AND v.data_venda < :data_fim_exclusiva
)
SELECT
    ci.id_cidades,
    ci.cidade,
    e.id_estados,
    e.estado,
    e.sigla,
    COALESCE(SUM(vp.valor_pago), 0)::numeric(14, 2) AS faturamento,
    COUNT(vp.id_vendas)::bigint AS quantidade,
    COALESCE(AVG(vp.valor_pago), 0)::numeric(14, 2) AS ticket_medio
FROM concessionarias AS co
JOIN cidades AS ci ON ci.id_cidades = co.id_cidades
JOIN estados AS e ON e.id_estados = ci.id_estados
LEFT JOIN vendas_periodo AS vp ON vp.id_concessionarias = co.id_concessionarias
GROUP BY ci.id_cidades, ci.cidade, e.id_estados, e.estado, e.sigla
ORDER BY faturamento DESC, ci.cidade
"""

RANKING_VENDEDORES_SQL = """
SELECT
    ve.id_vendedores,
    ve.nome AS vendedor,
    co.id_concessionarias,
    co.concessionaria,
    SUM(v.valor_pago)::numeric(14, 2) AS faturamento,
    COUNT(v.id_vendas)::bigint AS quantidade,
    AVG(v.valor_pago)::numeric(14, 2) AS ticket_medio
FROM vendas AS v
JOIN vendedores AS ve ON ve.id_vendedores = v.id_vendedores
JOIN concessionarias AS co
  ON co.id_concessionarias = v.id_concessionarias
WHERE v.data_venda >= :data_inicio
  AND v.data_venda < :data_fim_exclusiva
  AND (
      CAST(:id_concessionaria AS integer) IS NULL
      OR v.id_concessionarias = CAST(:id_concessionaria AS integer)
  )
GROUP BY ve.id_vendedores, ve.nome, co.id_concessionarias, co.concessionaria
ORDER BY faturamento DESC, quantidade DESC, ve.nome
"""

MODELOS_MAIS_VENDIDOS_SQL = """
SELECT
    ve.id_veiculos,
    ve.nome AS veiculo,
    ve.tipo,
    COUNT(v.id_vendas)::bigint AS quantidade,
    SUM(v.valor_pago)::numeric(14, 2) AS faturamento
FROM vendas AS v
JOIN veiculos AS ve ON ve.id_veiculos = v.id_veiculos
WHERE v.data_venda >= :data_inicio
  AND v.data_venda < :data_fim_exclusiva
  AND (
      CAST(:id_concessionaria AS integer) IS NULL
      OR v.id_concessionarias = CAST(:id_concessionaria AS integer)
  )
GROUP BY ve.id_veiculos, ve.nome, ve.tipo
ORDER BY quantidade DESC, faturamento DESC, ve.nome
"""

DESCONTOS_POR_VENDEDOR_SQL = """
SELECT
    vend.id_vendedores,
    vend.nome AS vendedor,
    co.id_concessionarias,
    co.concessionaria,
    AVG(ve.valor - v.valor_pago)::numeric(14, 2) AS desconto_medio,
    AVG(
        CASE
            WHEN ve.valor <> 0 THEN (ve.valor - v.valor_pago) / ve.valor * 100
            ELSE NULL
        END
    )::numeric(8, 2) AS desconto_percentual_medio
FROM vendas AS v
JOIN vendedores AS vend ON vend.id_vendedores = v.id_vendedores
JOIN veiculos AS ve ON ve.id_veiculos = v.id_veiculos
JOIN concessionarias AS co
  ON co.id_concessionarias = v.id_concessionarias
WHERE v.data_venda >= :data_inicio
  AND v.data_venda < :data_fim_exclusiva
  AND (
      CAST(:id_concessionaria AS integer) IS NULL
      OR v.id_concessionarias = CAST(:id_concessionaria AS integer)
  )
GROUP BY vend.id_vendedores, vend.nome, co.id_concessionarias, co.concessionaria
ORDER BY desconto_medio DESC, vend.nome
"""

DESCONTOS_POR_CONCESSIONARIA_SQL = """
SELECT
    co.id_concessionarias,
    co.concessionaria,
    AVG(ve.valor - v.valor_pago)::numeric(14, 2) AS desconto_medio,
    AVG(
        CASE
            WHEN ve.valor <> 0 THEN (ve.valor - v.valor_pago) / ve.valor * 100
            ELSE NULL
        END
    )::numeric(8, 2) AS desconto_percentual_medio
FROM vendas AS v
JOIN veiculos AS ve ON ve.id_veiculos = v.id_veiculos
JOIN concessionarias AS co
  ON co.id_concessionarias = v.id_concessionarias
WHERE v.data_venda >= :data_inicio
  AND v.data_venda < :data_fim_exclusiva
  AND (
      CAST(:id_concessionaria AS integer) IS NULL
      OR v.id_concessionarias = CAST(:id_concessionaria AS integer)
  )
GROUP BY co.id_concessionarias, co.concessionaria
ORDER BY desconto_medio DESC, co.concessionaria
"""

LISTAR_CONCESSIONARIAS_SQL = """
SELECT
    c.id_concessionarias,
    c.concessionaria
FROM concessionarias AS c
ORDER BY c.concessionaria
"""


PERIOD_QUERIES = {
    "indicadores_vendas": INDICADORES_VENDAS_SQL,
    "evolucao_vendas": EVOLUCAO_VENDAS_SQL,
    "desempenho_concessionarias": DESEMPENHO_CONCESSIONARIAS_SQL,
    "desempenho_estados": DESEMPENHO_ESTADOS_SQL,
    "desempenho_cidades": DESEMPENHO_CIDADES_SQL,
    "ranking_vendedores": RANKING_VENDEDORES_SQL,
    "modelos_mais_vendidos": MODELOS_MAIS_VENDIDOS_SQL,
    "descontos_por_vendedor": DESCONTOS_POR_VENDEDOR_SQL,
    "descontos_por_concessionaria": DESCONTOS_POR_CONCESSIONARIA_SQL,
}


def _period_params(data_inicio: date, data_fim: date) -> dict[str, datetime]:
    if isinstance(data_inicio, datetime) or isinstance(data_fim, datetime):
        raise TypeError("Use valores date, sem horário, para delimitar o período.")
    if not isinstance(data_inicio, date) or not isinstance(data_fim, date):
        raise TypeError("data_inicio e data_fim devem ser datas.")
    if data_inicio > data_fim:
        raise ValueError("data_inicio não pode ser posterior a data_fim.")
    return {
        "data_inicio": datetime.combine(data_inicio, time.min),
        "data_fim_exclusiva": datetime.combine(data_fim + timedelta(days=1), time.min),
    }


def _validate_sales_period_query(sql: str) -> None:
    validate_read_only_query(sql)
    if "vendas" not in sql.lower():
        raise ReadOnlyViolation("A consulta de período deve acessar a tabela vendas.")
    required = (":data_inicio", ":data_fim_exclusiva", "data_venda")
    if any(token not in sql for token in required):
        raise ReadOnlyViolation("A consulta em vendas deve filtrar data_venda no SQL.")


def execute_period_query(
    sql: str,
    data_inicio: date,
    data_fim: date,
    extra_params: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """Executa SQL de vendas com início inclusivo e fim do dia final inclusivo."""
    _validate_sales_period_query(sql)
    params: dict[str, Any] = _period_params(data_inicio, data_fim)
    params.update(extra_params or {})
    return execute_query(sql, params)


@st.cache_data(ttl=TTL_AGREGACAO_SIMPLES, show_spinner=False)
def buscar_indicadores_vendas(data_inicio: date, data_fim: date) -> pd.DataFrame:
    return execute_period_query(INDICADORES_VENDAS_SQL, data_inicio, data_fim)


@st.cache_data(ttl=TTL_AGREGACAO_SIMPLES, show_spinner=False)
def buscar_evolucao_vendas(data_inicio: date, data_fim: date) -> pd.DataFrame:
    return execute_period_query(EVOLUCAO_VENDAS_SQL, data_inicio, data_fim)


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def buscar_desempenho_concessionarias(
    data_inicio: date,
    data_fim: date,
    id_concessionaria: int | None = None,
) -> pd.DataFrame:
    return execute_period_query(
        DESEMPENHO_CONCESSIONARIAS_SQL,
        data_inicio,
        data_fim,
        {"id_concessionaria": id_concessionaria},
    )


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def buscar_desempenho_estados(data_inicio: date, data_fim: date) -> pd.DataFrame:
    return execute_period_query(DESEMPENHO_ESTADOS_SQL, data_inicio, data_fim)


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def buscar_desempenho_cidades(data_inicio: date, data_fim: date) -> pd.DataFrame:
    return execute_period_query(DESEMPENHO_CIDADES_SQL, data_inicio, data_fim)


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def buscar_ranking_vendedores(
    data_inicio: date,
    data_fim: date,
    id_concessionaria: int | None = None,
) -> pd.DataFrame:
    return execute_period_query(
        RANKING_VENDEDORES_SQL,
        data_inicio,
        data_fim,
        {"id_concessionaria": id_concessionaria},
    )


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def buscar_modelos_mais_vendidos(
    data_inicio: date,
    data_fim: date,
    id_concessionaria: int | None = None,
) -> pd.DataFrame:
    return execute_period_query(
        MODELOS_MAIS_VENDIDOS_SQL,
        data_inicio,
        data_fim,
        {"id_concessionaria": id_concessionaria},
    )


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def buscar_descontos_por_vendedor(
    data_inicio: date,
    data_fim: date,
    id_concessionaria: int | None = None,
) -> pd.DataFrame:
    return execute_period_query(
        DESCONTOS_POR_VENDEDOR_SQL,
        data_inicio,
        data_fim,
        {"id_concessionaria": id_concessionaria},
    )


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def buscar_descontos_por_concessionaria(
    data_inicio: date,
    data_fim: date,
    id_concessionaria: int | None = None,
) -> pd.DataFrame:
    return execute_period_query(
        DESCONTOS_POR_CONCESSIONARIA_SQL,
        data_inicio,
        data_fim,
        {"id_concessionaria": id_concessionaria},
    )


@st.cache_data(ttl=TTL_MULTIPLOS_JOINS, show_spinner=False)
def listar_concessionarias() -> pd.DataFrame:
    return execute_query(LISTAR_CONCESSIONARIAS_SQL)

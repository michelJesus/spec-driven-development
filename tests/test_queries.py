from datetime import date, datetime

import pytest

from src.database import ReadOnlyViolation, validate_read_only_query
from src.queries import (
    DESCONTOS_POR_CONCESSIONARIA_SQL,
    DESCONTOS_POR_VENDEDOR_SQL,
    DESEMPENHO_CONCESSIONARIAS_SQL,
    PERIOD_QUERIES,
    RANKING_VENDEDORES_SQL,
    _period_params,
    _validate_sales_period_query,
)


def test_todas_as_consultas_de_vendas_sao_somente_leitura() -> None:
    for sql in PERIOD_QUERIES.values():
        validate_read_only_query(sql)


def test_todas_as_consultas_de_vendas_filtram_periodo_no_sql() -> None:
    for sql in PERIOD_QUERIES.values():
        _validate_sales_period_query(sql)
        assert ":data_inicio" in sql
        assert ":data_fim_exclusiva" in sql
        assert "data_venda" in sql


def test_periodo_inclui_todo_o_dia_final() -> None:
    params = _period_params(date(2026, 9, 1), date(2026, 9, 30))

    assert params["data_inicio"] == datetime(2026, 9, 1, 0, 0)
    assert params["data_fim_exclusiva"] == datetime(2026, 10, 1, 0, 0)


def test_rejeita_periodo_invertido() -> None:
    with pytest.raises(ValueError):
        _period_params(date(2026, 9, 2), date(2026, 9, 1))


def test_rejeita_consulta_em_vendas_sem_filtro_de_periodo() -> None:
    with pytest.raises(ReadOnlyViolation):
        _validate_sales_period_query("SELECT id_vendas FROM vendas")


def test_comparacao_preserva_concessionarias_sem_vendas() -> None:
    sql_normalizado = " ".join(DESEMPENHO_CONCESSIONARIAS_SQL.upper().split())

    assert "FROM CONCESSIONARIAS AS C LEFT JOIN" in sql_normalizado
    assert "COALESCE(VP.FATURAMENTO, 0)" in sql_normalizado
    assert "COALESCE(VP.QUANTIDADE, 0)" in sql_normalizado
    assert "V.ID_CONCESSIONARIAS = CAST(:ID_CONCESSIONARIA AS INTEGER)" in sql_normalizado


@pytest.mark.parametrize(
    "sql",
    (DESCONTOS_POR_VENDEDOR_SQL, DESCONTOS_POR_CONCESSIONARIA_SQL),
)
def test_desconto_usa_preco_de_tabela_menos_valor_pago(sql: str) -> None:
    sql_normalizado = " ".join(sql.upper().split())

    assert "AVG(VE.VALOR - V.VALOR_PAGO)" in sql_normalizado
    assert "(VE.VALOR - V.VALOR_PAGO) / VE.VALOR * 100" in sql_normalizado
    assert "GREATEST" not in sql_normalizado


def test_ranking_atribui_venda_a_concessionaria_da_venda() -> None:
    sql_normalizado = " ".join(RANKING_VENDEDORES_SQL.upper().split())

    assert (
        "CO.ID_CONCESSIONARIAS = V.ID_CONCESSIONARIAS" in sql_normalizado
    )
    assert (
        "CO.ID_CONCESSIONARIAS = VE.ID_CONCESSIONARIAS" not in sql_normalizado
    )

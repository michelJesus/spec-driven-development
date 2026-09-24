from datetime import date
from decimal import Decimal

import pytest

from src.projecao import (
    calcular_projecao_mes_corrente,
    calcular_run_rate,
    periodo_e_mes_corrente,
)


def test_calcula_run_rate_mensal() -> None:
    resultado = calcular_run_rate(
        Decimal("15000"), dias_decorridos=15, dias_no_mes=30
    )

    assert resultado == Decimal("30000")


def test_projecao_considera_quantidade_real_de_dias_do_mes() -> None:
    resultado = calcular_projecao_mes_corrente(
        Decimal("29000"),
        date(2024, 2, 1),
        date(2024, 2, 29),
        hoje=date(2024, 2, 10),
    )

    assert resultado == Decimal("84100")


@pytest.mark.parametrize(
    ("inicio", "fim"),
    [
        (date(2026, 8, 1), date(2026, 8, 31)),
        (date(2026, 9, 2), date(2026, 9, 24)),
        (date(2026, 9, 1), date(2026, 9, 23)),
    ],
)
def test_nao_projeta_periodo_que_nao_cobre_mes_corrente(
    inicio: date, fim: date
) -> None:
    assert (
        calcular_projecao_mes_corrente(
            1000,
            inicio,
            fim,
            hoje=date(2026, 9, 24),
        )
        is None
    )


def test_reconhece_mes_corrente_ate_hoje() -> None:
    assert periodo_e_mes_corrente(
        date(2026, 9, 1),
        date(2026, 9, 24),
        hoje=date(2026, 9, 24),
    )


def test_rejeita_dias_invalidos() -> None:
    with pytest.raises(ValueError):
        calcular_run_rate(1000, dias_decorridos=0, dias_no_mes=30)

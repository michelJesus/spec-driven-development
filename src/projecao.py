"""Cálculo puro da projeção simples de fechamento do mês."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal


def periodo_e_mes_corrente(
    data_inicio: date,
    data_fim: date,
    *,
    hoje: date | None = None,
) -> bool:
    """Indica se o período cobre o mês atual desde seu primeiro dia até hoje."""
    referencia = hoje or date.today()
    primeiro_dia = referencia.replace(day=1)
    ultimo_dia = referencia.replace(
        day=calendar.monthrange(referencia.year, referencia.month)[1]
    )
    return data_inicio == primeiro_dia and referencia <= data_fim <= ultimo_dia


def calcular_run_rate(
    valor_vendido: Decimal | int | float,
    *,
    dias_decorridos: int,
    dias_no_mes: int,
) -> Decimal:
    """Projeta o total mensal mantendo constante o ritmo médio diário."""
    if dias_decorridos <= 0:
        raise ValueError("dias_decorridos deve ser maior que zero.")
    if dias_no_mes < dias_decorridos:
        raise ValueError("dias_no_mes não pode ser menor que dias_decorridos.")

    valor = Decimal(str(valor_vendido))
    return valor / Decimal(dias_decorridos) * Decimal(dias_no_mes)


def calcular_projecao_mes_corrente(
    valor_vendido: Decimal | int | float,
    data_inicio: date,
    data_fim: date,
    *,
    hoje: date | None = None,
) -> Decimal | None:
    """Retorna o run-rate apenas quando o período representa o mês corrente."""
    referencia = hoje or date.today()
    if not periodo_e_mes_corrente(data_inicio, data_fim, hoje=referencia):
        return None

    dias_no_mes = calendar.monthrange(referencia.year, referencia.month)[1]
    return calcular_run_rate(
        valor_vendido,
        dias_decorridos=referencia.day,
        dias_no_mes=dias_no_mes,
    )

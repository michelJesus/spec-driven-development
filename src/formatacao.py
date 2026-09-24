"""Formatação de valores para a interface em português do Brasil."""

from decimal import Decimal


def formatar_moeda_brl(valor: Decimal | int | float) -> str:
    formatado = f"{Decimal(str(valor)):,.2f}"
    formatado = formatado.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatado}"


def formatar_inteiro(valor: int | float | Decimal) -> str:
    return f"{int(valor):,}".replace(",", ".")

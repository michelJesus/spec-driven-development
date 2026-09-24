from decimal import Decimal

from src.formatacao import formatar_inteiro, formatar_moeda_brl


def test_formata_moeda_em_portugues_brasileiro() -> None:
    assert formatar_moeda_brl(Decimal("1234567.8")) == "R$ 1.234.567,80"


def test_formata_inteiro_com_separador_de_milhar() -> None:
    assert formatar_inteiro(1234567) == "1.234.567"

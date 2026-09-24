from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import src.queries as queries


def test_dashboard_renderiza_com_dados_agregados(monkeypatch) -> None:
    monkeypatch.setattr(
        queries,
        "buscar_indicadores_vendas",
        lambda *_: pd.DataFrame(
            [
                {
                    "faturamento_total": Decimal("250000.00"),
                    "quantidade_vendida": 10,
                    "ticket_medio": Decimal("25000.00"),
                }
            ]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_evolucao_vendas",
        lambda *_: pd.DataFrame(
            [{"data": date.today(), "faturamento": 250000, "quantidade": 10}]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_desempenho_concessionarias",
        lambda *_: pd.DataFrame(
            [
                {
                    "concessionaria": "Unidade Centro",
                    "faturamento": 250000,
                    "quantidade": 10,
                    "ticket_medio": 25000,
                },
                {
                    "concessionaria": "Unidade sem vendas",
                    "faturamento": 0,
                    "quantidade": 0,
                    "ticket_medio": 0,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_desempenho_estados",
        lambda *_: pd.DataFrame(
            [
                {
                    "estado": "São Paulo",
                    "sigla": "SP",
                    "faturamento": 250000,
                    "quantidade": 10,
                    "ticket_medio": 25000,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_desempenho_cidades",
        lambda *_: pd.DataFrame(
            [
                {
                    "cidade": "São Paulo",
                    "sigla": "SP",
                    "faturamento": 250000,
                    "quantidade": 10,
                    "ticket_medio": 25000,
                }
            ]
        ),
    )

    pagina = Path(__file__).parents[1] / "pages" / "1_Dashboard_Executivo.py"
    app = AppTest.from_file(pagina).run()

    assert not app.exception
    assert app.title[0].value == "Dashboard Executivo"
    assert [metric.label for metric in app.metric[:3]] == [
        "Faturamento",
        "Veículos vendidos",
        "Ticket médio",
    ]
    assert app.metric[0].value == "R$ 250.000,00"
    assert any("estimativa simples" in caption.value.lower() for caption in app.caption)

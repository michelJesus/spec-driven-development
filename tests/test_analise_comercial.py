from decimal import Decimal
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import src.queries as queries


PAGINA = Path(__file__).parents[1] / "pages" / "2_Analise_Comercial.py"


def _configurar_consultas(monkeypatch, *, com_vendas: bool) -> None:
    monkeypatch.setattr(
        queries,
        "listar_concessionarias",
        lambda: pd.DataFrame(
            [
                {"id_concessionarias": 1, "concessionaria": "Rio"},
                {"id_concessionarias": 2, "concessionaria": "Porto Alegre"},
            ]
        ),
    )

    if not com_vendas:
        vazio = lambda *_: pd.DataFrame()
        monkeypatch.setattr(queries, "buscar_ranking_vendedores", vazio)
        monkeypatch.setattr(queries, "buscar_modelos_mais_vendidos", vazio)
        monkeypatch.setattr(queries, "buscar_descontos_por_vendedor", vazio)
        monkeypatch.setattr(queries, "buscar_descontos_por_concessionaria", vazio)
        monkeypatch.setattr(
            queries,
            "buscar_desempenho_concessionarias",
            lambda *_: pd.DataFrame(
                [
                    {
                        "concessionaria": "Rio",
                        "faturamento": 0,
                        "quantidade": 0,
                        "ticket_medio": 0,
                    }
                ]
            ),
        )
        return

    monkeypatch.setattr(
        queries,
        "buscar_ranking_vendedores",
        lambda *_: pd.DataFrame(
            [
                {
                    "vendedor": "Ana",
                    "concessionaria": "Rio",
                    "faturamento": Decimal("150000.00"),
                    "quantidade": 5,
                    "ticket_medio": Decimal("30000.00"),
                },
                {
                    "vendedor": "Bruno",
                    "concessionaria": "Porto Alegre",
                    "faturamento": Decimal("100000.00"),
                    "quantidade": 5,
                    "ticket_medio": Decimal("20000.00"),
                },
            ]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_modelos_mais_vendidos",
        lambda *_: pd.DataFrame(
            [
                {
                    "veiculo": "Modelo A",
                    "tipo": "SUV",
                    "quantidade": 6,
                    "faturamento": 160000,
                },
                {
                    "veiculo": "Modelo B",
                    "tipo": "Sedan",
                    "quantidade": 4,
                    "faturamento": 90000,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_descontos_por_vendedor",
        lambda *_: pd.DataFrame(
            [
                {
                    "vendedor": "Ana",
                    "concessionaria": "Rio",
                    "desconto_medio": 1200,
                    "desconto_percentual_medio": 4,
                },
                {
                    "vendedor": "Bruno",
                    "concessionaria": "Porto Alegre",
                    "desconto_medio": -500,
                    "desconto_percentual_medio": -2,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_descontos_por_concessionaria",
        lambda *_: pd.DataFrame(
            [
                {
                    "concessionaria": "Rio",
                    "desconto_medio": 1200,
                    "desconto_percentual_medio": 4,
                },
                {
                    "concessionaria": "Porto Alegre",
                    "desconto_medio": -500,
                    "desconto_percentual_medio": -2,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        queries,
        "buscar_desempenho_concessionarias",
        lambda *_: pd.DataFrame(
            [
                {
                    "concessionaria": "Rio",
                    "faturamento": 150000,
                    "quantidade": 5,
                    "ticket_medio": 30000,
                },
                {
                    "concessionaria": "Porto Alegre",
                    "faturamento": 100000,
                    "quantidade": 5,
                    "ticket_medio": 20000,
                },
            ]
        ),
    )


def test_analise_comercial_renderiza_indicadores_e_limitacoes(monkeypatch) -> None:
    _configurar_consultas(monkeypatch, com_vendas=True)

    app = AppTest.from_file(PAGINA).run()

    assert not app.exception
    assert app.title[0].value == "Análise Comercial"
    assert [metric.label for metric in app.metric[:3]] == [
        "Faturamento",
        "Veículos vendidos",
        "Ticket médio",
    ]
    assert app.metric[0].value == "R$ 250.000,00"
    assert app.metric[1].value == "10"
    assert app.metric[2].value == "R$ 25.000,00"
    textos_limitacoes = " ".join(caption.value.lower() for caption in app.caption)
    assert "funil de conversão" in textos_limitacoes
    assert "inventário" in textos_limitacoes
    assert "valores negativos" in textos_limitacoes


def test_analise_comercial_trata_periodo_sem_vendas(monkeypatch) -> None:
    _configurar_consultas(monkeypatch, com_vendas=False)

    app = AppTest.from_file(PAGINA).run()

    assert not app.exception
    assert app.metric[0].value == "R$ 0,00"
    assert app.metric[1].value == "0"
    assert app.metric[2].value == "R$ 0,00"
    mensagens = " ".join(info.value.lower() for info in app.info)
    assert "não houve vendas" in mensagens
    assert "pelo menos duas concessionárias" in mensagens


def test_filtro_de_concessionaria_e_repassado_as_consultas(monkeypatch) -> None:
    _configurar_consultas(monkeypatch, com_vendas=True)
    ids_recebidos: list[int | None] = []

    def buscar_ranking(*argumentos):
        ids_recebidos.append(argumentos[2])
        return pd.DataFrame()

    monkeypatch.setattr(queries, "buscar_ranking_vendedores", buscar_ranking)

    app = AppTest.from_file(PAGINA).run()
    app.selectbox[0].set_value("Rio").run()

    assert not app.exception
    assert ids_recebidos == [None, 1]

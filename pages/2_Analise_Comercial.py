"""Análise operacional de vendas por período e concessionária."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from src.database import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseQueryError,
)
from src.formatacao import formatar_inteiro, formatar_moeda_brl
from src.queries import (
    buscar_descontos_por_concessionaria,
    buscar_descontos_por_vendedor,
    buscar_desempenho_concessionarias,
    buscar_modelos_mais_vendidos,
    buscar_ranking_vendedores,
    listar_concessionarias,
)


st.set_page_config(page_title="Análise Comercial", page_icon="💼", layout="wide")
st.title("Análise Comercial")
st.caption("Desempenho de vendedores, concessionárias, modelos e descontos")


def _numericos(dados: pd.DataFrame, colunas: tuple[str, ...]) -> pd.DataFrame:
    resultado = dados.copy()
    for coluna in colunas:
        if coluna in resultado.columns:
            resultado[coluna] = pd.to_numeric(
                resultado[coluna], errors="coerce"
            ).fillna(0)
    return resultado


def _grafico_barras(
    dados: pd.DataFrame,
    *,
    categoria: str,
    valor: str,
    titulo: str,
    rotulo_valor: str,
) -> None:
    ordenados = dados.sort_values(valor, ascending=True)
    figura = px.bar(
        ordenados,
        x=valor,
        y=categoria,
        orientation="h",
        labels={categoria: "", valor: rotulo_valor},
        title=titulo,
        color=valor,
        color_continuous_scale="Blues",
    )
    figura.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=50, b=10))
    if valor in {"faturamento", "ticket_medio", "desconto_medio"}:
        figura.update_xaxes(tickprefix="R$ ", separatethousands=True)
    st.plotly_chart(figura, use_container_width=True)


hoje = date.today()
inicio_padrao = hoje.replace(day=1)
periodo = st.sidebar.date_input(
    "Período",
    value=(inicio_padrao, hoje),
    max_value=hoje,
    format="DD/MM/YYYY",
)

if not isinstance(periodo, (tuple, list)) or len(periodo) != 2:
    st.info("Selecione as datas inicial e final do período.")
    st.stop()

data_inicio, data_fim = periodo
if data_inicio > data_fim:
    st.error("A data inicial não pode ser posterior à data final.")
    st.stop()

try:
    cadastro_concessionarias = listar_concessionarias()
except (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseQueryError,
) as error:
    st.error(str(error))
    st.stop()

opcoes_concessionarias: dict[str, int | None] = {"Todas": None}
for registro in cadastro_concessionarias.itertuples(index=False):
    opcoes_concessionarias[str(registro.concessionaria)] = int(
        registro.id_concessionarias
    )

concessionaria_selecionada = st.sidebar.selectbox(
    "Concessionária",
    options=list(opcoes_concessionarias),
)
id_concessionaria = opcoes_concessionarias[concessionaria_selecionada]
st.sidebar.caption("Os filtros são aplicados diretamente nas consultas ao banco.")

try:
    ranking = _numericos(
        buscar_ranking_vendedores(data_inicio, data_fim, id_concessionaria),
        ("faturamento", "quantidade", "ticket_medio"),
    )
    modelos = _numericos(
        buscar_modelos_mais_vendidos(data_inicio, data_fim, id_concessionaria),
        ("quantidade", "faturamento"),
    )
    descontos_vendedores = _numericos(
        buscar_descontos_por_vendedor(data_inicio, data_fim, id_concessionaria),
        ("desconto_medio", "desconto_percentual_medio"),
    )
    descontos_concessionarias = _numericos(
        buscar_descontos_por_concessionaria(
            data_inicio, data_fim, id_concessionaria
        ),
        ("desconto_medio", "desconto_percentual_medio"),
    )
    desempenho_concessionarias = _numericos(
        buscar_desempenho_concessionarias(
            data_inicio, data_fim, id_concessionaria
        ),
        ("faturamento", "quantidade", "ticket_medio"),
    )
except (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseQueryError,
) as error:
    st.error(str(error))
    st.stop()

faturamento = Decimal(str(ranking["faturamento"].sum())) if not ranking.empty else Decimal("0")
quantidade = int(ranking["quantidade"].sum()) if not ranking.empty else 0
ticket_medio = faturamento / quantidade if quantidade else Decimal("0")

col_faturamento, col_quantidade, col_ticket = st.columns(3)
col_faturamento.metric("Faturamento", formatar_moeda_brl(faturamento))
col_quantidade.metric("Veículos vendidos", formatar_inteiro(quantidade))
col_ticket.metric("Ticket médio", formatar_moeda_brl(ticket_medio))

st.subheader("Ranking de vendedores")
if ranking.empty:
    st.info("Não houve vendas para os filtros selecionados.")
else:
    metrica_ranking = st.radio(
        "Ordenar ranking por",
        ("Faturamento", "Quantidade vendida"),
        horizontal=True,
    )
    coluna_ranking = (
        "faturamento" if metrica_ranking == "Faturamento" else "quantidade"
    )
    rotulo_ranking = (
        "Faturamento (R$)"
        if coluna_ranking == "faturamento"
        else "Veículos vendidos"
    )
    ranking_ordenado = ranking.sort_values(
        [coluna_ranking, "vendedor"], ascending=[False, True]
    )
    _grafico_barras(
        ranking_ordenado,
        categoria="vendedor",
        valor=coluna_ranking,
        titulo=f"Ranking por {metrica_ranking.lower()}",
        rotulo_valor=rotulo_ranking,
    )
    st.dataframe(
        ranking_ordenado[
            ["vendedor", "concessionaria", "faturamento", "quantidade", "ticket_medio"]
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "vendedor": "Vendedor",
            "concessionaria": "Concessionária",
            "faturamento": st.column_config.NumberColumn("Faturamento", format="R$ %.2f"),
            "quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
            "ticket_medio": st.column_config.NumberColumn("Ticket médio", format="R$ %.2f"),
        },
    )

st.subheader("Modelos mais vendidos")
if modelos.empty:
    st.info("Não há modelos vendidos para exibir.")
else:
    figura_modelos = px.pie(
        modelos,
        names="veiculo",
        values="quantidade",
        title="Participação dos modelos nas vendas",
    )
    figura_modelos.update_traces(textinfo="percent+label")
    figura_modelos.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(figura_modelos, use_container_width=True)

st.subheader("Descontos praticados")
st.caption(
    "Desconto = preço de tabela atual do veículo − valor pago. "
    "Valores negativos indicam venda acima da tabela e permanecem visíveis."
)
aba_vendedores, aba_concessionarias = st.tabs(("Por vendedor", "Por concessionária"))
with aba_vendedores:
    if descontos_vendedores.empty:
        st.info("Não há descontos por vendedor para exibir.")
    else:
        _grafico_barras(
            descontos_vendedores,
            categoria="vendedor",
            valor="desconto_medio",
            titulo="Desconto médio por vendedor",
            rotulo_valor="Desconto médio (R$)",
        )
        st.dataframe(
            descontos_vendedores[
                ["vendedor", "concessionaria", "desconto_medio", "desconto_percentual_medio"]
            ],
            hide_index=True,
            use_container_width=True,
            column_config={
                "vendedor": "Vendedor",
                "concessionaria": "Concessionária",
                "desconto_medio": st.column_config.NumberColumn("Desconto médio", format="R$ %.2f"),
                "desconto_percentual_medio": st.column_config.NumberColumn("Desconto médio (%)", format="%.2f%%"),
            },
        )
with aba_concessionarias:
    if descontos_concessionarias.empty:
        st.info("Não há descontos por concessionária para exibir.")
    else:
        _grafico_barras(
            descontos_concessionarias,
            categoria="concessionaria",
            valor="desconto_medio",
            titulo="Desconto médio por concessionária",
            rotulo_valor="Desconto médio (R$)",
        )
        st.dataframe(
            descontos_concessionarias[
                ["concessionaria", "desconto_medio", "desconto_percentual_medio"]
            ],
            hide_index=True,
            use_container_width=True,
            column_config={
                "concessionaria": "Concessionária",
                "desconto_medio": st.column_config.NumberColumn("Desconto médio", format="R$ %.2f"),
                "desconto_percentual_medio": st.column_config.NumberColumn("Desconto médio (%)", format="%.2f%%"),
            },
        )

st.subheader("Comparação entre concessionárias")
unidades_com_vendas = desempenho_concessionarias[
    desempenho_concessionarias["quantidade"] > 0
]
if len(unidades_com_vendas) < 2:
    st.info("A comparação requer vendas em pelo menos duas concessionárias no período.")
else:
    metrica_comparacao = st.radio(
        "Métrica da comparação",
        ("Faturamento", "Quantidade", "Ticket médio"),
        horizontal=True,
    )
    coluna_comparacao = {
        "Faturamento": "faturamento",
        "Quantidade": "quantidade",
        "Ticket médio": "ticket_medio",
    }[metrica_comparacao]
    _grafico_barras(
        unidades_com_vendas,
        categoria="concessionaria",
        valor=coluna_comparacao,
        titulo=f"{metrica_comparacao} por concessionária",
        rotulo_valor=metrica_comparacao,
    )
    st.dataframe(
        unidades_com_vendas[
            ["concessionaria", "faturamento", "quantidade", "ticket_medio"]
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "concessionaria": "Concessionária",
            "faturamento": st.column_config.NumberColumn("Faturamento", format="R$ %.2f"),
            "quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
            "ticket_medio": st.column_config.NumberColumn("Ticket médio", format="R$ %.2f"),
        },
    )

st.divider()
st.caption(
    "Funil de conversão e veículos parados no pátio não são exibidos: o banco "
    "atual não possui dados de visitas/leads nem de inventário. O preço de tabela "
    "não tem histórico; por isso, descontos antigos usam o valor atual de veiculos.valor."
)

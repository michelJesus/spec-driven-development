"""Dashboard executivo de vendas por período."""

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
from src.projecao import calcular_projecao_mes_corrente
from src.queries import (
    buscar_desempenho_cidades,
    buscar_desempenho_concessionarias,
    buscar_desempenho_estados,
    buscar_evolucao_vendas,
    buscar_indicadores_vendas,
)


st.set_page_config(page_title="Dashboard Executivo", page_icon="📊", layout="wide")
st.title("Dashboard Executivo")
st.caption("Visão consolidada do desempenho da rede de concessionárias")


def _preparar_numeros(dados: pd.DataFrame) -> pd.DataFrame:
    resultado = dados.copy()
    for coluna in ("faturamento", "quantidade", "ticket_medio"):
        if coluna in resultado.columns:
            resultado[coluna] = pd.to_numeric(resultado[coluna], errors="coerce").fillna(0)
    return resultado


def _grafico_comparacao(
    dados: pd.DataFrame,
    *,
    categoria: str,
    titulo: str,
    chave: str,
) -> None:
    if dados.empty:
        st.info(f"Não há dados de {titulo.lower()} para exibir.")
        return

    metrica = st.radio(
        "Métrica",
        ("Faturamento", "Quantidade"),
        horizontal=True,
        key=f"metrica_{chave}",
        label_visibility="collapsed",
    )
    coluna = "faturamento" if metrica == "Faturamento" else "quantidade"
    rotulo = "Faturamento (R$)" if coluna == "faturamento" else "Veículos vendidos"
    ordenados = dados.sort_values(coluna, ascending=True)
    figura = px.bar(
        ordenados,
        x=coluna,
        y=categoria,
        orientation="h",
        title=titulo,
        labels={coluna: rotulo, categoria: ""},
        color=coluna,
        color_continuous_scale="Blues",
    )
    figura.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=50, b=10))
    if coluna == "faturamento":
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

st.sidebar.caption("O período é aplicado diretamente nas consultas ao banco.")

try:
    indicadores = buscar_indicadores_vendas(data_inicio, data_fim)
    evolucao = _preparar_numeros(buscar_evolucao_vendas(data_inicio, data_fim))
    concessionarias = _preparar_numeros(
        buscar_desempenho_concessionarias(data_inicio, data_fim)
    )
    estados = _preparar_numeros(buscar_desempenho_estados(data_inicio, data_fim))
    cidades = _preparar_numeros(buscar_desempenho_cidades(data_inicio, data_fim))
except (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseQueryError,
) as error:
    st.error(str(error))
    st.stop()

if indicadores.empty:
    faturamento = Decimal("0")
    quantidade = 0
    ticket_medio = Decimal("0")
else:
    resumo = indicadores.iloc[0]
    faturamento = Decimal(str(resumo["faturamento_total"] or 0))
    quantidade = int(resumo["quantidade_vendida"] or 0)
    ticket_medio = Decimal(str(resumo["ticket_medio"] or 0))

col_faturamento, col_quantidade, col_ticket = st.columns(3)
col_faturamento.metric("Faturamento", formatar_moeda_brl(faturamento))
col_quantidade.metric("Veículos vendidos", formatar_inteiro(quantidade))
col_ticket.metric("Ticket médio", formatar_moeda_brl(ticket_medio))

projecao = calcular_projecao_mes_corrente(
    faturamento,
    data_inicio,
    data_fim,
    hoje=hoje,
)
if projecao is not None:
    st.metric("Projeção de fechamento do mês", formatar_moeda_brl(projecao))
    st.caption(
        "Estimativa simples (run-rate): mantém o ritmo médio diário observado "
        "até hoje. Não é uma previsão estatística."
    )

st.subheader("Evolução das vendas")
if evolucao.empty:
    st.info("Não houve vendas no período selecionado.")
else:
    metrica_tempo = st.radio(
        "Métrica da evolução",
        ("Faturamento", "Quantidade"),
        horizontal=True,
    )
    coluna_tempo = "faturamento" if metrica_tempo == "Faturamento" else "quantidade"
    rotulo_tempo = (
        "Faturamento (R$)" if coluna_tempo == "faturamento" else "Veículos vendidos"
    )
    figura_tempo = px.line(
        evolucao,
        x="data",
        y=coluna_tempo,
        markers=True,
        labels={"data": "Data", coluna_tempo: rotulo_tempo},
    )
    if coluna_tempo == "faturamento":
        figura_tempo.update_yaxes(tickprefix="R$ ", separatethousands=True)
    figura_tempo.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(figura_tempo, use_container_width=True)

st.subheader("Comparação da rede")
aba_unidades, aba_estados, aba_cidades = st.tabs(
    ("Concessionárias", "Estados", "Cidades")
)
with aba_unidades:
    _grafico_comparacao(
        concessionarias,
        categoria="concessionaria",
        titulo="Desempenho por concessionária",
        chave="concessionaria",
    )
    st.caption("Todas as concessionárias são exibidas, inclusive as sem vendas.")
with aba_estados:
    _grafico_comparacao(
        estados,
        categoria="estado",
        titulo="Desempenho por estado",
        chave="estado",
    )
with aba_cidades:
    cidades_exibicao = cidades.copy()
    if not cidades_exibicao.empty:
        cidades_exibicao["cidade_uf"] = (
            cidades_exibicao["cidade"] + " / " + cidades_exibicao["sigla"]
        )
    _grafico_comparacao(
        cidades_exibicao,
        categoria="cidade_uf",
        titulo="Desempenho por cidade",
        chave="cidade",
    )

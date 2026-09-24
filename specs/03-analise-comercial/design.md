# Design - Análise Comercial

## Visão geral da solução
Página ou seção Streamlit com ranking de vendedores, ticket médio, modelos mais vendidos e desconto médio, todos filtráveis por concessionária e período.

## Dados utilizados
`vendas` unidos a `vendedores`, `veiculos` e `concessionarias`. Desconto = `veiculos.valor - vendas.valor_pago`, agregado com `AVG()`.

## Fluxo
Filtro (concessionária + período) -> queries agregadas (spec `01-acesso-dados`) -> cache (~15 min, múltiplos joins) -> tabelas/gráficos.

## Decisões Técnicas
- Ranking: tabela ordenável (`st.dataframe`) ou gráfico de barras horizontal (Plotly).
- Desconto: exibir também o percentual (`desconto / veiculo.valor`), além do valor absoluto.
- Nenhuma tentativa de estimar funil a partir de proxies.
- Modelos mais vendidos: gráfico de pizza (Plotly `px.pie`), não mais barras, por pedido da Gerente Fernanda para visualizar a particiação de cada modelo.
- Modelos mais vendidos: gráfico de pizza (Plotly `px.pie`), não mais barras, por pedido do Gerente Fernanda para visualizar a participação de cada modelo.

## Riscos / pontos em aberto
- Se `veiculo.valor` mudar ao longo do tempo (sem histórico de preço no modelo atual), o desconto de vendas antigas pode ficar impreciso. Assumir que `veiculos.valor` é o preço vigente, documentar limitação.

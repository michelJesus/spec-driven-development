# Design - Dashboard Executivo

## Visão geral da solução
Página única Streamlit com filtro de período na barra lateral, cartões de indicadores (faturamento, quantidade, ticket médio), gráfico de evolução temporal, comparação entre concessionárias e, quando possível, por estado. Projeção exibida com card adicional com aviso de que é uma estimativa simples.

## Dados utilizados
`vendas` (valor_pago, data_venda) unida a `concessionarias`, `cidades` e `estados`. Filtro de período sempre aplicado no SQL (usa a camada de `01-acesso-dados`).

## Fluxo
Fitro de data (sidebar) -> funções de `queries.py` (da spec 01) -> cache -> agregação final em pandas apenas para formataçao -> gráficos Plotly.

## Decisões Técnicas
- Projeção: `run_rate = valor_vendido_ate_hoje / dias_passados_mes * dia_totais_no_mes`. Simples, sem bibliotecas de séries temporais.
- Gráficos: Plotly (linha de evolução, barra de comparação entre concessionárias).
- Cache: TTL de 5-15 min (consulta com várias junções), conforme regra do CIO.

## Riscos / pontos em aberto
- Run-rate é uma estimativa ingênua e pode enganar em meses com sazonalidade forte. Documentar esta limitação na própria tela (tooltip).

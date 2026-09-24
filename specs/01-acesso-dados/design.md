# Design - Acesso a Dados (camada base, somente leitura)

## Visão geral da solução
Módulo único de conexão e execução de queries somente leitura no PostgreSQL, usando pelas duas specs de dashboard (`02-dashboard-executivo` e `03-analise-comercial`).

## Dados utilizados
Todas as 7 tabelas do modelo (`estados`,`cidades`,`concessionarias`, `veiculos`,`clientes`, `vendedores`, `vendas`) conforme `docs/diagrama-banco-dados.png`. Toda consulta que toca `vendas` recebe filtro de data de período inicial e final.

## Fluxo
`.env`/`st.secrets` -> `database.py` (engine SQLAlchemy + psycopg2, usuário somente leitura), `queries.py` (funções de consulta parametrizadas por perído) -> `st.cache_data` envolvendo cada função de consulta -> páginas Streamlit consomem os dataframes já agregados.

## Decisões Técnicas
- Banco: PostgreSQL. Driver `psycopg2-binary` via SQLAlchemy.
- Cache: `st.cache_data(ttl=900)` (15 min) para consultas com múltiplos joins.
- Nunca usar `SELECT *`; sempre selecionar apenas as colunas necessárias, já agregadas no SQL quando possível.

## Riscos / pontos em aberto
- Se o volume de vendas crescer muito, pode ser necessário paginar ou pré-agregar por dia, fora do escopo do MVP.
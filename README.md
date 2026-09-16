# Dashboard de Concessionárias

Painel somente leitura sobre o banco de dados PostgreSQL de uma rede de concessionárias, construído em Python + Streamlit. Projeto utilizando técnicas de Spec-Driven Development (SDD) com Codex.

## Status do projeto

As 3 specs estão implementadas:

- [x] **`01-acesso-dados`** — camada de conexão e consultas somente leitura (fundação das demais).
- [x] **`02-dashboard-executivo`** — visão executiva de vendas para o CEO.
- [x] **`03-analise-comercial`** — ferramenta operacional para o time comercial.

## Funcionalidades

### Dashboard Executivo (`pages/1_Dashboard_Executivo.py`)
Faturamento total, quantidade vendida e ticket médio no período selecionado; evolução diária (faturamento ou quantidade); comparação entre concessionárias (todas, mesmo sem vendas no período) e por estado; projeção simples de fechamento do mês (run-rate) quando o período selecionado é o mês corrente.

### Análise Comercial (`pages/2_Analise_Comercial.py`)
Ranking de vendedores por faturamento/quantidade (filtrável por concessionária), modelos de veículo mais vendidos, desconto médio por vendedor (`veiculos.valor - vendas.valor_pago`, incluindo vendas acima da tabela) e comparação comercial entre todas as concessionárias. Taxa de conversão de funil e veículos parados no pátio estão fora de escopo — o banco não tem tabela de leads/visitas nem de estoque.

## Estrutura

```
app.py                          # Home / teste de conexão com o banco
pages/                          # Páginas do dashboard (multipage Streamlit)
  1_Dashboard_Executivo.py
  2_Analise_Comercial.py
src/
  database.py                   # Engine SQLAlchemy + psycopg2, guarda de somente-leitura
  queries.py                    # Consultas agregadas parametrizadas por período
  projecao.py                   # Cálculo de run-rate (função pura)
  formatacao.py                 # Formatação de moeda (pt-BR)
tests/                          # Testes automatizados (pytest)
specs/<pasta>/                  # requirements.md, design.md, tasks.md por spec
docs/diagrama-banco-dados.png   # Diagrama do banco de dados
CODEX.md                       # Regras técnicas não-negociáveis do projeto
prompts.md                      # Prompts prontos para implementar cada spec
```

## Como rodar

### Pré-requisitos
- Python 3.11+
- Acesso de rede ao PostgreSQL da rede de concessionárias (usuário somente leitura)

### Instalação

```bash
pip install -r requirements.txt
```

### Configuração

Crie um arquivo `.env` na raiz do projeto com as credenciais do banco (nunca commitar este arquivo — já está no `.gitignore`):

```
DB_HOST=...
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
```

Alternativa: usar `st.secrets` (arquivo `.streamlit/secrets.toml`) com as mesmas chaves — `src/database.py` tenta `st.secrets` primeiro e cai para variáveis de ambiente automaticamente.

### Executar o painel

```bash
streamlit run app.py
```

Abre em `http://localhost:8501`. A navegação entre "Dashboard Executivo" e "Análise Comercial" aparece na barra lateral.

### Rodar os testes

```bash
pytest tests/
```

Cobrem: bloqueio de qualquer SQL de escrita, presença de filtro de período em toda consulta que toca `vendas`, e a fórmula de projeção (run-rate).

## Regras técnicas

Este projeto segue regras não-negociáveis definidas em `CODEX.md`: acesso somente leitura ao banco, credenciais fora do código-fonte, filtro de período sempre na query SQL, cache (`st.cache_data`) com TTL de ~1 min para agregações simples e 15 min para consultas com múltiplos joins, sem autenticação nesta versão (uso interno).

## Como implementar/revisar uma spec

Abra o CODEX Code na raiz desta pasta e use os prompts de `prompts.md`, um por spec, na ordem numérica (`specs/01-acesso-dados`, `specs/02-dashboard-executivo`, `specs/03-analise-comercial`).

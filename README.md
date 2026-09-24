# Dashboard de Concessionárias

Painel multipágina e somente leitura sobre o banco PostgreSQL de uma rede de
concessionárias. A aplicação foi construída com Python, Streamlit, SQLAlchemy,
pandas e Plotly usando práticas de Spec-Driven Development (SDD).

## Status do projeto

As três especificações previstas estão implementadas:

| Spec | Status | Entrega |
| --- | --- | --- |
| `01-acesso-dados` | Concluída | Conexão PostgreSQL e consultas estritamente somente leitura |
| `02-dashboard-executivo` | Concluída | Indicadores e comparações executivas |
| `03-analise-comercial` | Concluída | Análise operacional de vendedores, modelos e descontos |

Última verificação local: **36 testes automatizados aprovados**.

## Funcionalidades

### Dashboard Executivo (`pages/1_Dashboard_Executivo.py`)

- Faturamento total, quantidade vendida e ticket médio por período.
- Evolução diária por faturamento ou quantidade.
- Comparações por concessionária, estado e cidade.
- Exibição de concessionárias sem vendas no período.
- Projeção simples de fechamento do mês (run-rate) para o mês corrente.

### Análise Comercial (`pages/2_Analise_Comercial.py`)

- Filtros por período e concessionária aplicados nas consultas SQL.
- Ranking de vendedores por faturamento ou quantidade vendida.
- Ticket médio geral, por vendedor e por concessionária.
- Participação dos modelos vendidos em gráfico de pizza.
- Desconto médio absoluto e percentual por vendedor e concessionária.
- Comparação de faturamento, quantidade e ticket entre unidades com vendas.
- Vendas acima do preço de tabela preservadas como descontos negativos.

O cálculo de desconto usa `veiculos.valor - vendas.valor_pago`. Como o banco
não mantém histórico do preço de tabela, vendas antigas usam o valor atual do
veículo. Funil de conversão e veículos parados no pátio permanecem fora do
escopo porque não existem dados de leads/visitas ou inventário.

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
  formatacao.py                 # Formatação numérica em pt-BR
tests/                          # Testes automatizados (pytest)
specs/<pasta>/                  # requirements.md, design.md, tasks.md por spec
docs/diagrama-banco-dados.png   # Diagrama do banco de dados
CODEX.md                        # Regras técnicas não negociáveis do projeto
prompts.md                      # Prompts usados para implementar cada spec
```

## Como rodar

### Pré-requisitos

- Python 3.11+
- Acesso ao PostgreSQL com o esquema representado em
  `docs/diagrama-banco-dados.png`
- Usuário de banco com permissão somente de leitura

### 1. Criar e ativar o ambiente virtual

Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 3. Configurar o banco

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell, use `Copy-Item .env.example .env`.

Depois, preencha o `.env` com as credenciais do PostgreSQL:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=concessionarias
DB_USER=usuario_somente_leitura
DB_PASSWORD=substitua_esta_senha
```

O `.env` não deve ser versionado. Como alternativa, configure as mesmas chaves
em `.streamlit/secrets.toml`. A aplicação procura primeiro em `st.secrets` e
depois nas variáveis de ambiente ou no `.env`.

### 4. Executar a aplicação

```bash
python -m streamlit run app.py
```

Abra `http://localhost:8501`. A barra lateral permite navegar entre a página
inicial, o Dashboard Executivo e a Análise Comercial.

### 5. Rodar os testes

```bash
python -m pytest -q
```

Os testes cobrem a proteção contra SQL de escrita, parametrização e filtros das
consultas, cálculos, projeção mensal e renderização das páginas Streamlit.

## Solução de problemas

- **Configuração incompleta:** confirme se todas as cinco variáveis `DB_*`
  estão definidas e se `DB_PORT` é um número válido.
- **Falha de conexão:** verifique host, porta, VPN/rede e permissões do usuário.
- **Página sem dados:** revise o período selecionado e confirme se existem
  vendas para os filtros aplicados.
- **Porta 8501 ocupada:** execute com outra porta, por exemplo
  `python -m streamlit run app.py --server.port 8502`.

## Regras técnicas

Este projeto segue as regras definidas em `CODEX.md`: banco somente leitura,
credenciais fora do código-fonte, filtro de período dentro da SQL, consultas
parametrizadas e cache com aproximadamente 1 minuto para agregações simples e
15 minutos para consultas com múltiplos joins. Não há autenticação nesta versão,
destinada a uso interno.

## Como implementar/revisar uma spec

Consulte `requirements.md`, `design.md` e `tasks.md` dentro da pasta da spec.
As especificações são numeradas porque as funcionalidades posteriores dependem
da camada de acesso a dados. Os prompts utilizados no fluxo estão em
`prompts.md`.

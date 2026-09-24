# Requirements - Análise Comercial

**Stakeholder** Gerente Comercial - Fernanda Alves

## Objetivo
Dar ao time comercial uma ferramenta operacional para acompanhar vendedores, concessionárias, modelos vendidos e desconto praticado.

## Contexto do Pedido
Fernanda quer ranking de vendedores, comparação entre concessionárias, ticket médio, modelo mais vendido vs. parados no pático, taxa de conversão de funil, desconto médio.

## Perguntas de esclarecimento e Respostas
Pergunta: O que é taxa de conversão do funil, exatamente? Resposta: Clientes que entram na loja vs. quantos compraram.
Pergunta: O banco de dados só tem vendas concluídas, sem lead/visita, o que fazer? Resposta: Isso é um problema, mas tudo bem, foca no que for possível, anota isso, vou cobrar na próxima fase.
Pergunta: O que é desconto médio? Resposta: Diferença entre o preço de tabela do carro e o valor realmente pago.
Pergunta: Qual a frequência de atualização? Resposta: Olho todo dia de manhã; não precisa tempo real, hora em hora já ajuda.
Pergunta: Quer comparar concessionárias? Resposta: Sim, ex.: Rio vs. Porto Alegre, e endender por quê.

## User stories
- O sistema deve exibir o ranking de vendedores por faturamento e por quantidade vendida, filtrável por concessionária, quando o painél for carregado.
- O sistema deve exibir o ticket médio geral e por vendedor/concessionária quando um período for selecionado.
- O sistema deve exibir os modelos de veículos mais vendidos no período quando o painél for carregado.
- O sistema deve exibir desconto médio (preço de tabela do veículo menos valor pago) por vendedor e por concessionária quando o painel for carregado.
- O sistema deve comparar o desempenho comercial entre concessionárias quando mais de uma unidade tiver vendas no período.

## Fora do Escopo / decisões negociadas
- **Taxa de conveersão de funil**: fora de escopo nesta versão. O banco de dados não tem tabela de leads/visitas, só vendas concluídas.
- **Veículos parados no pátio**: fora de escopo. Não existe tabela de inventário/estoque.
- **Desconto médio**: **Dentro do escopo**, `veiculos.valor`(preço de tabela) e `vendas.valor_pago` (valor pago) existem e permitem exatamente o cálculo que Fernanda descreveu.

## Critérios de Aceite
- [ ] Ranking e ticket médio respeitam o período selecionado.
- [ ] Nenhum dado de funil é inventado ou estimado a partir de outra tabela.
- [ ] Desconto médio calculado com `veiculos.valor - vendas.valor_pago`; casos de venda acima da tabela são exibidos, não escondidos.
- [ ] Resultados comparáveis entre concessionárias.


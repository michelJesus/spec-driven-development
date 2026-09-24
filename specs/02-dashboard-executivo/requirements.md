# Requirements - Dashboard Executivo

**Stakeholder** CEO - Ricardo Matos

## Objetivo
Dar ao CEO uma visão rápida e executiva do desempenho de vendas entre concessionárias, para decisão ágil e apresentação trimestral ao conselho.

## Contexto do Pedido
Ricardo hoje só sabe como a empresa esta indo pelo relatório de fechamento mensal do financeiro, tarde demais para agir. Quer abrir uma tela e entender rapidamente se está vendendo mais ou menos que antes, quais unidades vão bem ou mal, e se possível uma projeção do mês.

## Perguntas de esclarecimento e Respostas
Pergunta: O que significa performar bem? Qual métrica? Resposta: Faturamento e quantidade de veículos vendidos, as duas são importantes.
Pergunta: Pode detalhar o método de projeção? Resposta: Não precisa ser sofisticado. Pode ficar para depois se for muito complicado agora.
Pergunta: Quer comparar todas as concessionárias e regiões? Resposta: Sim, é o ponto principal, saber qual unidade carrega a empresa e qual pesa.
Pergunta: Qual o prazo? Resposta: O quanto antes, mas prefere esperar mais e receber algo certo do que rápido e errado.

## User stories
- O sistema deve exibir faturamento total e quantidade de veículos vendidos no período selecionado quando o CEO abrir o painel.
- O sistema deve exibir a evolução de vendas ao longo do tempo (faturamento e/ou quantidade) quando um período for selecionado.
- O sistema deve comparar todas as concessionárias por faturamento e quantidade vendida quando o painel for carregado.
- O sistema deve permitir comparação por estado/cidade quando os dados relacionados existirem.
- O sistema deve exibir uma projeção simples do fechamento do mês (run-rate baseado no valor vendido até a data corrente) quando o período selecionado for mês corrente.

## Fora do Escopo / decisões negociadas
- **Projeção**: Ricado autorizou simplificar ou adiar ("pode ficar para depois, mas eu queria"). Decisão do MVP: implementar uma projeção simples de run-rate (regra de três sobre o ritmo atual do mês). Alternativa igualmente válida: registrar como item de fase 2.
- **Geração automática de apresentaão para o conselho**: fora de escopo. Interpretado como necessidade visual limpo (gráficos), não geração de slide.
- **Metas/Orçamento**: fora de escopo, não existe no banco de dados.

## Critérios de Aceite
- [ ] Todos os números respeitam o período selecionado.
- [ ] Todas as concessionárias aparecem na comparação, mesmo sem vendas no período.
- [ ] A projeção deixa explícito que é uma estimativa simples (run-rate), não previsão estatística.
- [ ] Painel utilizável sem exigir leitura de tabela extensa. Visual, não planilha.

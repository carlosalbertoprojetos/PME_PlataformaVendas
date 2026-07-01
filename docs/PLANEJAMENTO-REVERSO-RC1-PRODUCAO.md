# Planejamento Reverso RC1 para Producao Comercial

Data: 2026-06-30

## Premissas

Este planejamento parte do estado atual real: RC1 auditado, hardening P0/P1 concluido, 105 testes passando, sem producao real, sem pilotos ativos, sem gateway de pagamento, sem integracoes externas, sem IA generativa, sem API publica madura, sem analytics avancado de produto e sem observabilidade completa.

O objetivo nao e reescrever o produto. O objetivo e transformar a base Django existente em um SaaS enxuto, vendavel, seguro, operavel e validavel com PMEs reais.

Regras de priorizacao:

- primeiro estabilizar;
- depois validar com pilotos;
- depois cobrar com gateway;
- depois operar comercialmente;
- somente entao evoluir features.

## 1. Objetivo Final

O estado final desejado e uma Plataforma SaaS de Gestao Comercial para PMEs em producao comercial estavel, com:

### Funcionalidades obrigatorias

- Cadastro e gestao de empresas, usuarios, vendedores e permissoes.
- Catalogo de produtos por empresa.
- Clientes, leads, oportunidades, historico comercial e proximas acoes.
- Workspace comercial como tela principal de operacao.
- Criacao real de pedidos, itens, status e historico.
- WhatsApp operacional via links `wa.me`, sem envio automatico nao autorizado.
- Inteligencia comercial deterministica com motivos auditaveis.
- Eventos de dominio e timeline comercial.
- Motor de automacoes simples, auditavel e administravel.
- Dashboard operacional com KPIs, recomendacoes, onboarding, automacoes e saude comercial.
- Billing real com gateway, planos, assinaturas, limites, status e bloqueios suaves.
- Onboarding guiado ate primeiro valor.

### Seguranca obrigatoria

- Multiempresa isolado por tenant em todas as entidades operacionais.
- Permissoes por papel: admin da empresa e vendedor.
- Settings separados por ambiente.
- `DEBUG=False` em producao.
- `ALLOWED_HOSTS` restrito.
- `SECRET_KEY` e credenciais via secrets.
- CSRF ativo em formularios mutaveis.
- HTTPS obrigatorio.
- Backups testados.
- Logs sem vazamento de dados sensiveis.
- Politica minima de LGPD: termos, privacidade, exportacao/retencao e remocao sob solicitacao.

### Desempenho e estabilidade

- Banco PostgreSQL em producao.
- Cache para recomendacoes e calculos caros.
- Indices revisados para queries reais.
- Limites e paginacao em telas de alto volume.
- Testes automatizados em CI.
- Monitoramento de erros, latencia e disponibilidade.
- Plano de rollback.

### Infraestrutura

- Ambiente local, staging e producao separados.
- CI/CD com checks, testes e migracoes controladas.
- Deploy reproduzivel via `requirements.txt` ou manifesto equivalente.
- Storage para arquivos futuros.
- Backups automaticos e restore testado.
- Secrets fora do repositorio.

### Billing

- Integracao com gateway escolhido: Asaas, Mercado Pago ou Pagar.me.
- Webhooks assinados e auditados.
- Estados de assinatura sincronizados.
- Upgrade/downgrade seguro.
- Registro de pagamentos, falhas e tentativas.
- Bloqueios suaves previsiveis.

### Monitoramento, logs e suporte

- Logs estruturados por request, usuario e empresa.
- Error tracking.
- Metricas de app: latencia, 4xx, 5xx, filas futuras, tempo de automacoes.
- Metricas de produto: ativacao, uso de workspace, catalogo compartilhado, oportunidades criadas, pedidos criados, proximas acoes concluidas.
- Processo de suporte com triagem, SLA inicial e base de conhecimento.

### Documentacao e treinamento

- Manual do administrador da empresa.
- Manual do vendedor.
- Guia de onboarding.
- Playbook de suporte.
- Guia de deploy e operacao.
- Guia de incidentes e rollback.
- Treinamento curto para piloto.

### Implantacao e operacao comercial

- Staging homologado.
- Pilotos pagos ou beta fechado com empresas reais.
- Criterios de sucesso de piloto definidos.
- Contrato/termos aceitos.
- Plano comercial simples: Start, Growth, Pro.
- Processo de venda, onboarding, suporte e acompanhamento.

### Pilotos validados

- Pelo menos 3 a 5 PMEs usando fluxo real.
- Pelo menos 2 empresas com uso semanal recorrente.
- Pelo menos 1 ciclo completo: catalogo -> cliente/lead -> oportunidade -> proxima acao -> pedido -> follow-up.
- Evidencia de disposicao de pagamento ou pagamento real.
- Feedback documentado e convertido em backlog.

## 2. Marcos de tras para frente

### Marco Final: Producao Comercial Estavel

Objetivo: operar o SaaS com clientes pagantes, estabilidade, suporte e cobranca real.

Entregaveis:

- Ambiente de producao ativo.
- Gateway de pagamento operando.
- Monitoramento e alertas ativos.
- Suporte operacional.
- Documentacao de cliente e operacao.
- Pilotos convertidos em clientes ou base comercial inicial.

Dependencias:

- Go-live controlado concluido.
- Billing real validado.
- Observabilidade ativa.
- Pilotos validados.
- Segurança e LGPD minimas.

Riscos:

- Incidentes em clientes reais.
- Cobranca incorreta.
- Baixa adocao apos go-live.
- Suporte insuficiente.

Critérios de conclusão:

- 30 dias sem incidente critico.
- 99%+ disponibilidade no periodo inicial.
- Pagamentos processados e conciliados.
- Clientes ativos usando workspace, pedidos e proximas acoes.
- Suporte com SLA inicial cumprido.

### Marco 10: Go-live controlado

Objetivo: liberar producao para grupo restrito com rollback e suporte ativo.

Entregaveis:

- Deploy em producao.
- Dominio, SSL e DNS configurados.
- Runbook de go-live.
- Plano de rollback.
- Checklist final aprovado.
- Monitoramento em tempo real.

Dependencias:

- Staging aprovado.
- Billing real testado.
- Backups e restore testados.
- Pilotos/beta fechados validados.

Riscos:

- Configuracao divergente entre staging e producao.
- Webhook de pagamento falhando.
- Falta de suporte em horario critico.

Critérios de conclusão:

- Go-live executado sem incidentes P0.
- Primeiro cliente real acessa e opera.
- Logs e alertas funcionando.
- Rollback testado antes do deploy.

### Marco 9: Pilotos pagos ou beta fechado validado

Objetivo: provar valor com empresas reais antes de escala comercial.

Entregaveis:

- 3 a 5 empresas em beta fechado ou piloto pago.
- Roteiro de onboarding.
- Critérios de sucesso por empresa.
- Relatorio semanal de uso.
- Backlog priorizado por evidencia.

Dependencias:

- RC2 pronto.
- Staging e producao controlada disponiveis.
- Suporte minimo.
- Fluxo de pedido real.

Riscos:

- Usuario nao entende valor.
- Dados reais revelam gargalos.
- Produto vira consultoria manual.

Critérios de conclusão:

- Pelo menos 2 empresas usando semanalmente.
- Pelo menos 1 empresa paga ou aceita proposta formal.
- Fluxo comercial completo usado com dados reais.
- Decisao clara: continuar, ajustar ou interromper.

### Marco 8: Billing real com gateway

Objetivo: transformar monetizacao interna em cobranca real e auditavel.

Entregaveis:

- Gateway escolhido e integrado.
- Checkout ou fluxo de assinatura.
- Webhooks assinados.
- Estados de pagamento refletidos em `Assinatura`.
- Testes de pagamento aprovado, pendente, falho, cancelado e reembolso quando aplicavel.
- Logs de eventos de billing.

Dependencias:

- Planos e limites internos estaveis.
- Permissao admin no billing.
- Ambiente staging com secrets.

Riscos:

- Webhook duplicado.
- Assinatura bloqueada indevidamente.
- Cobranca em valor/plano errado.

Critérios de conclusão:

- Fluxos sandbox passam.
- Webhooks idempotentes.
- Cliente consegue assinar, alterar plano e cancelar conforme regra definida.

### Marco 7: Observabilidade e suporte

Objetivo: detectar, diagnosticar e responder problemas antes que clientes desistam.

Entregaveis:

- Error tracking.
- Logs estruturados.
- Metricas de disponibilidade, latencia, 4xx, 5xx.
- Metricas de automacoes e eventos.
- Playbook de suporte.
- Base de conhecimento inicial.

Dependencias:

- Ambientes separados.
- Deploy automatizado ou repetivel.
- Identificacao de usuario e empresa nos logs.

Riscos:

- Excesso de logs sem acao.
- Alertas ruidosos.
- Falta de responsavel por suporte.

Critérios de conclusão:

- Incidente simulado gera alerta.
- Erro de app pode ser rastreado por empresa e usuario.
- Suporte sabe reproduzir e escalar problemas.

### Marco 6: Analytics de produto

Objetivo: medir uso real e ativacao sem criar produto inchado.

Entregaveis:

- Eventos de produto essenciais.
- Dashboard interno de ativacao.
- Funil: onboarding -> produto -> cliente/lead -> oportunidade -> proxima acao -> pedido.
- Metricas de retencao inicial.

Dependencias:

- EventLog e automacoes estaveis.
- Definicao de sucesso do piloto.
- Workspace e pedido funcionando.

Riscos:

- Medir tudo e decidir nada.
- Eventos inconsistentes.
- Falta de privacidade/LGPD.

Critérios de conclusão:

- PM/PO acompanha ativacao por empresa.
- Dados ajudam a decidir backlog de piloto.
- Metricas essenciais documentadas.

### Marco 5: Hardening P2/P3

Objetivo: concluir itens desejaveis de estabilidade apos P0/P1 e antes de pilotos reais.

Entregaveis:

- UI segura para `AutomationRule`.
- Indice operacional de docs.
- Melhorias de UX e navegacao.
- Fluxo real de criacao de pedido.
- Testes de query count e smoke de seguranca.
- Plano de outbox/fila futura documentado.
- Politicas de retencao de logs/eventos.

Dependencias:

- P0/P1 concluidos.
- Decisao sobre fluxo minimo de pedido.
- Capacidade de testes de performance.

Riscos:

- Abrir P2/P3 demais e atrasar piloto.
- Transformar produto em ERP.

Critérios de conclusão:

- Somente itens necessarios para piloto entram.
- Nao ha P0/P1 reaberto.
- RC2 pode ser cortado.

### Marco 4: UI de automacoes

Objetivo: permitir administracao controlada de automacoes sem editar JSON manual.

Entregaveis:

- Lista de regras por empresa.
- Criacao/edicao simples de regras.
- Validacao de conditions/actions.
- Ativar/desativar regra.
- Visualizar execucoes e erros.
- Permissao apenas admin.

Dependencias:

- AutomationRule e ExecutionLog estaveis.
- Permissao por papel.
- Definicao de catalogo permitido de condicoes e acoes.

Riscos:

- Usuario criar regra ciclica.
- Automacao virar feature complexa demais.

Critérios de conclusão:

- Regra invalida nao salva.
- Regra valida executa e registra log.
- Vendedor nao acessa configuracao.

### Marco 3: Fluxo real de criacao de pedido

Objetivo: completar o ciclo comercial minimo.

Entregaveis:

- Criar pedido a partir de cliente ou oportunidade.
- Adicionar produtos e quantidades.
- Calcular total.
- Status: pendente, confirmado, cancelado.
- Validar produtos da mesma empresa.
- Gerar eventos de pedido.
- Botao no workspace.

Dependencias:

- Catalogo estavel.
- CRM e workspace estaveis.
- Regras de pedido definidas sem virar ERP.

Riscos:

- Escopo expandir para estoque, fiscal, financeiro.
- Preco divergente entre catalogo e pedido.

Critérios de conclusão:

- Vendedor cria pedido completo.
- Pedido aparece no workspace, dashboard e inteligencia.
- Testes cobrem isolamento e status.

### Marco 2: Preparacao de ambiente staging

Objetivo: ter ambiente realista para homologar sem afetar producao.

Entregaveis:

- Staging com PostgreSQL.
- Variaveis de ambiente.
- Secrets seguros.
- Deploy repetivel.
- Dados seed anonimizados ou controlados.
- SSL e dominio de staging.
- Pipeline rodando testes.

Dependencias:

- Settings hardenizados.
- `requirements.txt`.
- Migrations consistentes.

Riscos:

- Staging divergir da producao.
- Secrets vazarem.

Critérios de conclusão:

- Deploy do zero documentado.
- Migrations executam.
- Testes passam no pipeline.
- Smoke manual passa.

### Marco 1: RC2

Objetivo: gerar release candidate pronto para beta fechado.

Entregaveis:

- Hardening P2/P3 minimo concluido.
- Fluxo de pedido real.
- UI de automacoes minima.
- Staging operacional.
- Testes de regressao passando.
- Checklist de beta.

Dependencias:

- RC1 pos-hardening.
- Priorizacao estrita.

Riscos:

- RC2 virar pacote grande demais.
- Atrasar pilotos por polimento excessivo.

Critérios de conclusão:

- Sem P0/P1 aberto.
- Fluxo comercial completo funcionando.
- Staging pronto.
- Beta fechado pode iniciar.

### Marco 0: Estado atual - RC1 pos-hardening

Objetivo: ponto de partida.

Entregaveis existentes:

- RC1 auditado.
- P0/P1 corrigidos.
- 105 testes passando.
- Multiempresa, catalogo, CRM, workspace, inteligencia, WhatsApp, billing interno, onboarding, eventos e automacoes.

Dependencias pendentes:

- Staging.
- Pedido real.
- UI de automacoes.
- Gateway de pagamento.
- Observabilidade.
- Pilotos.

Riscos:

- Confundir RC1 com produto pronto.
- Implementar features antes de validar estabilidade e billing.

Critérios de conclusão:

- Estado atual documentado.
- Proxima fase limitada a RC2/staging/pedido/automacoes administraveis.

## 3. Quebra das Entregas

### Producao Comercial Estavel

Atividades:

- Operar clientes pagantes.
- Acompanhar incidentes.
- Revisar metricas semanais.
- Ajustar suporte e onboarding.

Subtarefas:

- Revisao semanal de disponibilidade.
- Revisao mensal de churn e ativacao.
- Auditoria de cobranca.
- Atualizacao de base de conhecimento.

Responsaveis sugeridos:

- Product Owner.
- Tech Lead.
- DevOps.
- Suporte.
- Comercial/Customer Success.

Esforco estimado: continuo, apos go-live.

Riscos: baixa retencao, suporte sobrecarregado, incidentes.

Mitigacao: limite de clientes iniciais, SLA simples, rotina semanal de saude.

### Go-live controlado

Atividades:

- Preparar checklist final.
- Congelar release.
- Executar deploy.
- Monitorar primeira semana.

Subtarefas:

- Backup pre-deploy.
- Migracoes em staging.
- Smoke de login, dashboard, workspace, pedido, billing.
- Validar webhooks.
- Abrir canal de suporte.

Responsaveis: Tech Lead, DevOps, QA, PO.

Esforco estimado: 1 a 2 semanas.

Riscos: deploy com variavel errada, webhook falho.

Mitigacao: runbook, rollback, secrets revisados, deploy em janela controlada.

### Pilotos pagos ou beta fechado

Atividades:

- Selecionar empresas.
- Conduzir onboarding.
- Medir sucesso.
- Coletar feedback.

Subtarefas:

- Definir perfil de PME.
- Criar termo de piloto.
- Configurar empresas.
- Treinar admins e vendedores.
- Reuniao semanal de acompanhamento.

Responsaveis: PO, Comercial, Customer Success, Suporte.

Esforco estimado: 4 a 6 semanas.

Riscos: usuario nao adota, uso vira planilha paralela.

Mitigacao: metas por empresa, roteiro de uso, suporte proativo.

### Billing real com gateway

Atividades:

- Escolher gateway.
- Integrar assinatura.
- Tratar webhooks.
- Validar plano e limites.

Subtarefas:

- Definir gateway prioritario.
- Modelar eventos de pagamento.
- Implementar sandbox.
- Criar testes de webhooks idempotentes.
- Documentar falhas de cobranca.

Responsaveis: Backend, QA, PO.

Esforco estimado: 2 a 4 semanas.

Riscos: cobranca duplicada, status errado.

Mitigacao: idempotencia, sandbox, logs, reconciliacao manual inicial.

### Observabilidade e suporte

Atividades:

- Instrumentar app.
- Estruturar suporte.
- Criar playbooks.

Subtarefas:

- Configurar error tracking.
- Padronizar logs.
- Criar dashboards de saude.
- Definir fluxo de incidentes.
- Criar templates de resposta.

Responsaveis: DevOps, Tech Lead, Suporte.

Esforco estimado: 2 semanas.

Riscos: alerta demais, dado de menos.

Mitigacao: comecar com poucos sinais fortes: erro, latencia, 5xx, pagamento, login.

### Analytics de produto

Atividades:

- Definir eventos essenciais.
- Criar visao de ativacao.
- Acompanhar funil de uso.

Subtarefas:

- Mapear eventos no EventLog.
- Criar dashboard interno.
- Definir metricas de sucesso.
- Documentar dicionario de eventos.

Responsaveis: PO, Produto, Backend.

Esforco estimado: 1 a 2 semanas.

Riscos: medir demais.

Mitigacao: limitar a 10 metricas essenciais.

### Hardening P2/P3

Atividades:

- Selecionar itens essenciais para beta.
- Implementar apenas o que reduz risco operacional.

Subtarefas:

- Query count.
- Smoke de seguranca.
- Retencao de logs.
- Indice de documentacao.

Responsaveis: Tech Lead, Backend, QA.

Esforco estimado: 2 semanas.

Riscos: escopo inflar.

Mitigacao: PO aprova somente itens ligados ao piloto.

### UI de automacoes

Atividades:

- Criar administracao simples.
- Validar regras.
- Exibir execucoes.

Subtarefas:

- Form de regra.
- Catalogo fixo de eventos, condicoes e acoes.
- Validacao server-side.
- Lista de logs.
- Testes de permissao.

Responsaveis: Backend, UX/UI, QA.

Esforco estimado: 2 semanas.

Riscos: regra ciclica.

Mitigacao: bloquear combinacoes perigosas e limitar acoes iniciais.

### Fluxo real de criacao de pedido

Atividades:

- Criar pedido no workspace.
- Adicionar itens.
- Confirmar/cancelar.

Subtarefas:

- Form de pedido.
- Formset ou fluxo simples de itens.
- Validacao tenant.
- Calculo total.
- Eventos de pedido.
- Testes de isolamento.

Responsaveis: Backend, UX/UI, QA, PO.

Esforco estimado: 2 a 3 semanas.

Riscos: virar ERP.

Mitigacao: sem estoque, fiscal, comissao ou financeiro nesta fase.

### Preparacao de staging

Atividades:

- Configurar infraestrutura.
- Automatizar deploy.
- Validar smoke.

Subtarefas:

- PostgreSQL.
- Variaveis de ambiente.
- Dominios e SSL.
- CI com testes.
- Backup e restore.

Responsaveis: DevOps, Tech Lead.

Esforco estimado: 1 a 2 semanas.

Riscos: ambiente incompleto.

Mitigacao: checklist e deploy reproducivel.

### RC2

Atividades:

- Fechar pacote de beta.
- Congelar escopo.
- Rodar regressao.

Subtarefas:

- Atualizar docs.
- Rodar testes.
- Revisar permissao multiempresa.
- Revisar checklist de beta.

Responsaveis: PO, Tech Lead, QA.

Esforco estimado: 1 semana.

Riscos: RC2 crescer demais.

Mitigacao: criterio de corte: tudo que nao bloqueia beta fica fora.

## 4. Cronograma Reverso

| Ordem reversa | Marco | Duracao estimada | Dependencias | Responsaveis |
| --- | --- | --- | --- | --- |
| 11 | Producao Comercial Estavel | continuo apos go-live | Go-live, billing, suporte, pilotos | PO, Tech Lead, DevOps, CS |
| 10 | Go-live controlado | 1-2 semanas | Staging aprovado, billing real, backups | Tech Lead, DevOps, QA |
| 9 | Pilotos pagos ou beta fechado | 4-6 semanas | RC2, suporte, fluxo de pedido | PO, Comercial, CS |
| 8 | Billing real com gateway | 2-4 semanas | planos estaveis, staging, secrets | Backend, QA, PO |
| 7 | Observabilidade e suporte | 2 semanas | staging, logs basicos | DevOps, Tech Lead, Suporte |
| 6 | Analytics de produto | 1-2 semanas | EventLog, funil definido | PO, Backend |
| 5 | Hardening P2/P3 | 2 semanas | P0/P1 concluidos | Tech Lead, Backend, QA |
| 4 | UI de automacoes | 2 semanas | automacoes estaveis, permissao admin | Backend, UX, QA |
| 3 | Fluxo real de pedido | 2-3 semanas | catalogo, CRM, workspace | Backend, UX, QA |
| 2 | Staging | 1-2 semanas | settings, requirements, migrations | DevOps, Tech Lead |
| 1 | RC2 | 1 semana | staging, pedido, automacoes, P2/P3 minimo | PO, Tech Lead, QA |
| 0 | RC1 pos-hardening | estado atual | concluido | Codex, Tech Lead |

## 5. Roadmap Cronologico

### Etapa 1: Consolidar RC2

Sequencia:

1. Preparar staging.
2. Implementar fluxo real de pedido.
3. Criar UI minima de automacoes.
4. Executar hardening P2/P3 estritamente necessario.
5. Fechar RC2 com regressao completa.

Resultado esperado: produto pronto para beta fechado.

### Etapa 2: Validar com pilotos

Sequencia:

1. Selecionar PMEs.
2. Configurar empresas.
3. Treinar usuarios.
4. Medir uso semanal.
5. Corrigir apenas bloqueios.

Resultado esperado: evidencia de valor e disposicao de pagamento.

### Etapa 3: Monetizar

Sequencia:

1. Integrar gateway em sandbox.
2. Validar webhooks.
3. Ativar cobranca controlada.
4. Auditar assinaturas e limites.

Resultado esperado: cobranca real confiavel.

### Etapa 4: Operar producao controlada

Sequencia:

1. Ativar observabilidade.
2. Preparar suporte.
3. Executar go-live controlado.
4. Acompanhar primeira carteira.

Resultado esperado: SaaS comercial operavel.

## 6. Backlog Inicial

### Produto

- Definir escopo exato do RC2.
- Definir criterio de sucesso do beta fechado.
- Definir perfil ideal de PME piloto.
- Definir politica minima de planos e limites para piloto.

### UX/UI

- Desenhar fluxo minimo de criacao de pedido.
- Melhorar navegacao entre dashboard, workspace, agenda e catalogo.
- Criar tela simples de automacoes.
- Revisar estados vazios do workspace.

### Backend

- Implementar pedido real.
- Criar forms/views de automacoes com validacao.
- Adicionar eventos de produto para analytics essencial.
- Preparar webhooks de gateway em fase posterior.

### Frontend

- Ajustar templates Django sem SPA.
- Criar componentes simples para pedido e automacoes.
- Melhorar legibilidade do dashboard.

### Banco de Dados

- Preparar migracao para PostgreSQL em staging.
- Revisar indices de EventLog e PedidoItem.
- Definir retencao de EventLog e AutomationExecutionLog.

### DevOps

- Criar staging.
- Configurar secrets.
- Criar pipeline de check/test.
- Automatizar deploy.
- Configurar backups.

### Seguranca

- Revisar settings de producao.
- Validar permissao admin/vendedor.
- Criar checklist LGPD minimo.
- Testar CSRF em formularios mutaveis.

### Testes

- Testes de pedido.
- Testes de automacoes UI.
- Testes de permissao por papel.
- Testes de query count para dashboard/workspace.
- Smoke test de staging.

### Documentacao

- Guia de staging.
- Manual do vendedor.
- Manual do admin.
- Playbook de suporte.
- Termos iniciais de piloto.

### Operacao

- Definir SLA inicial.
- Definir canal de suporte.
- Criar processo de triagem.
- Criar checklist de onboarding de empresa.

### Comercial

- Definir oferta de piloto pago.
- Definir preco inicial validavel.
- Criar roteiro de demonstracao.
- Criar lista de PMEs candidatas.

### Suporte

- Criar FAQ.
- Criar macro de resposta para problemas comuns.
- Criar processo de escalonamento tecnico.

## 7. Arquitetura Recomendada

### Backend

Recomendacao: manter Django monolitico modular.

Justificativa: o produto ainda esta em validacao. O monolito Django com apps por dominio e suficiente, reduz custo operacional e evita complexidade prematura.

### Frontend/templates

Recomendacao: manter Django templates, com melhoria incremental de UX.

Justificativa: o foco e operacao comercial simples. SPA ou frontend separado aumentaria custo antes de validar pilotos.

### Banco de dados

Recomendacao: PostgreSQL em staging/producao.

Justificativa: melhor suporte a concorrencia, indices, integridade e operacao SaaS real que SQLite.

### Cache

Recomendacao: cache Django local no curto prazo; Redis quando houver staging/producao com multiplas instancias.

Justificativa: cache ja reduz recomputacao. Redis vira necessario quando escala ou multiplos processos exigirem consistencia maior.

### Storage

Recomendacao: iniciar sem storage externo se nao houver uploads; preparar S3 compativel quando surgirem arquivos.

Justificativa: nao criar infraestrutura sem uso real.

### Filas futuras

Recomendacao: manter automacoes sincronas ate pilotos; planejar outbox + worker depois.

Justificativa: Celery/fila antes de necessidade real adiciona operacao. Outbox sera importante se automacoes crescerem.

### Logs

Recomendacao: logs estruturados com empresa, usuario, request_id e evento.

Justificativa: suporte multiempresa exige rastreabilidade sem acessar banco manualmente.

### Monitoramento

Recomendacao: error tracking, uptime check, metricas de latencia e 5xx.

Justificativa: primeiro nivel de producao precisa detectar falhas rapidamente.

### CI/CD

Recomendacao: pipeline com install, check, makemigrations dry-run, test e deploy controlado.

Justificativa: ja existe suite de testes forte; deve virar gate de release.

### Hospedagem

Recomendacao: PaaS ou VPS gerenciada inicialmente, com PostgreSQL gerenciado se possivel.

Justificativa: equipe pequena deve reduzir carga operacional.

### Secrets

Recomendacao: variaveis de ambiente ou secret manager da hospedagem.

Justificativa: settings ja foram preparados para isso no hardening.

### Gateway de pagamento

Recomendacao: escolher um gateway inicial e implementar bem. Preferencia pratica para Asaas se foco for PME brasileira com boleto/pix/assinatura.

Justificativa: multiplo gateway antes de tracao aumenta complexidade.

### WhatsApp

Recomendacao: manter `wa.me` ate piloto provar necessidade de API oficial.

Justificativa: API oficial tem custo, politicas e operacao; manual atende validacao inicial.

### Backups

Recomendacao: backup automatico diario e restore testado mensalmente no inicio.

Justificativa: backup nao testado e apenas esperanca bem formatada.

## 8. Matriz de Dependencias

| Entrega | Depende de |
| --- | --- |
| Staging | settings hardenizados, requirements, migrations estaveis |
| Fluxo real de pedido | catalogo, CRM, workspace, events |
| UI de automacoes | AutomationRule, ExecutionLog, permissoes |
| Hardening P2/P3 | P0/P1 concluidos |
| RC2 | staging, pedido real, automacoes UI, P2/P3 minimo |
| Pilotos | RC2, suporte minimo, docs de onboarding |
| Analytics de produto | EventLog, funil definido, pilotos planejados |
| Observabilidade | staging, logs padronizados, deploy |
| Billing real | planos/assinaturas, secrets, staging, gateway escolhido |
| Go-live | pilotos validados, billing real, observabilidade, backups |
| Producao estavel | go-live controlado, suporte, operacao comercial |

## 9. Analise de Riscos

| Risco | Probabilidade | Impacto | Prioridade | Plano de contingencia |
| --- | --- | --- | --- | --- |
| Seguranca multiempresa falhar | Media | Critico | P0 | Testes de isolamento em toda nova feature; code review obrigatorio; logs por empresa |
| Billing incorreto | Media | Critico | P0 | Webhooks idempotentes; reconciliacao manual inicial; sandbox; auditoria de assinatura |
| Baixa adocao no piloto | Alta | Alto | P0 | Piloto guiado, criterio de sucesso, entrevistas semanais, cortar features pouco usadas |
| Performance degradar | Media | Alto | P1 | Query count, cache, limites, monitoramento de latencia |
| Dados inconsistentes | Media | Alto | P1 | Validacoes de model/form, constraints, backups e scripts de auditoria |
| Onboarding fraco | Alta | Alto | P1 | Checklist claro, treinamento, CS acompanhando primeira semana |
| Suporte insuficiente | Media | Alto | P1 | Playbook, SLA simples, canal unico, escalonamento tecnico |
| Excesso de features | Alta | Alto | P0 | Congelar RC2; tudo passa por impacto em piloto/billing/estabilidade |
| Dependencia de WhatsApp manual | Media | Medio | P2 | Medir uso; integrar API oficial apenas se piloto provar necessidade |
| Ausencia de integracoes | Media | Medio | P2 | Validar manualmente; integrar apenas depois de pilotos |
| Automacoes ciclicas | Media | Alto | P1 | Validacao de regras, whitelist de acoes, logs e limites |
| Gateway instavel | Baixa/Media | Alto | P1 | Retry idempotente, conciliacao manual, fallback operacional |
| Falha de backup | Baixa | Critico | P0 | Restore testado e documentado |
| LGPD negligenciada | Media | Alto | P0 | Termos, privacidade, retencao, remocao sob solicitacao |

## 10. Sprint Planning

### Sprint 1 - Staging e release discipline

Objetivo: preparar ambiente realista e pipeline.

Entregas:

- Staging com PostgreSQL.
- Variaveis e secrets.
- Pipeline check/test.
- Smoke test documentado.

Historias:

- Como Tech Lead, quero deploy reproduzivel para homologar RC2.
- Como PO, quero staging estavel para demonstrar sem risco local.

Critérios de aceite:

- Deploy do zero documentado.
- `check` e `test` rodam no pipeline.
- Smoke de login/dashboard/workspace passa.

Testes obrigatorios:

- `manage.py check`
- `manage.py makemigrations --check --dry-run`
- `manage.py test`

Documentacao obrigatoria:

- Guia de staging.
- Runbook de deploy.

### Sprint 2 - Pedido real minimo

Objetivo: completar ciclo comercial.

Entregas:

- Criar pedido.
- Adicionar itens.
- Confirmar/cancelar.
- Integrar ao workspace.

Historias:

- Como vendedor, quero criar pedido a partir do cliente para registrar interesse real.
- Como admin, quero ver pedidos no dashboard.

Critérios de aceite:

- Pedido pertence a empresa.
- Produto de outra empresa nao entra.
- Total calculado.
- Eventos de pedido emitidos.

Testes obrigatorios:

- Criacao de pedido.
- Itens e totais.
- Isolamento tenant.
- Dashboard/workspace.

Documentacao obrigatoria:

- `docs/pedidos.md` ou secao equivalente.

### Sprint 3 - Automacoes administraveis

Objetivo: permitir configuracao segura de automacoes.

Entregas:

- CRUD simples de regra.
- Validacao de condicoes/acoes.
- Lista de execucoes.
- Permissao admin.

Historias:

- Como admin, quero ativar uma automacao simples para padronizar follow-up.
- Como suporte, quero ver por que uma automacao falhou.

Critérios de aceite:

- Vendedor recebe 403.
- JSON invalido nao salva.
- Execucao fica auditada.

Testes obrigatorios:

- Permissao.
- Regra valida/invalida.
- Execucao e logs.

Documentacao obrigatoria:

- Guia de automacoes.

### Sprint 4 - Hardening P2/P3 minimo e RC2

Objetivo: cortar RC2 para beta fechado.

Entregas:

- Query count basico.
- Smoke de seguranca.
- Indice de docs.
- Checklist beta.

Historias:

- Como PO, quero um RC2 congelado para iniciar piloto.
- Como QA, quero regressao clara para aprovar release.

Critérios de aceite:

- Sem P0/P1.
- Testes verdes.
- Checklist beta aprovado.

Testes obrigatorios:

- Suite completa.
- Smoke staging.
- Testes multiempresa principais.

Documentacao obrigatoria:

- Checklist RC2.
- Guia de beta.

### Sprint 5 - Piloto fechado

Objetivo: validar valor com empresas reais.

Entregas:

- 3 empresas configuradas.
- Treinamento.
- Relatorio semanal.
- Backlog por evidencia.

Historias:

- Como dono de PME, quero cadastrar produtos/clientes e gerar pedidos sem planilha.
- Como vendedor, quero saber quem abordar hoje.

Critérios de aceite:

- Pelo menos 2 empresas usam semanalmente.
- Pelo menos 1 ciclo comercial completo.
- Feedback registrado.

Testes obrigatorios:

- Smoke por empresa piloto.
- Verificacao de isolamento.

Documentacao obrigatoria:

- Relatorio de piloto.

### Sprint 6 - Billing real sandbox

Objetivo: preparar cobranca sem expor cliente a erro.

Entregas:

- Gateway sandbox.
- Webhooks idempotentes.
- Estados de assinatura.
- Logs de billing.

Historias:

- Como admin, quero assinar ou alterar plano com seguranca.
- Como suporte, quero auditar uma falha de pagamento.

Critérios de aceite:

- Pagamento aprovado atualiza assinatura.
- Webhook duplicado nao duplica cobranca.
- Falha fica registrada.

Testes obrigatorios:

- Webhook aprovado, falho, duplicado.
- Permissao admin.

Documentacao obrigatoria:

- Guia de billing e reconciliacao.

### Sprint 7 - Observabilidade e suporte

Objetivo: operar beta/producao controlada.

Entregas:

- Error tracking.
- Logs estruturados.
- Dashboards basicos.
- Playbook de suporte.

Historias:

- Como suporte, quero identificar erro por empresa.
- Como Tech Lead, quero alerta em 5xx.

Critérios de aceite:

- Erro simulado gera alerta.
- Suporte consegue abrir incidente.

Testes obrigatorios:

- Smoke de alertas.
- Smoke de logs.

Documentacao obrigatoria:

- Runbook de incidentes.

### Sprint 8 - Go-live controlado

Objetivo: liberar producao com clientes restritos.

Entregas:

- Checklist final.
- Deploy.
- Rollback.
- Monitoramento da primeira semana.

Historias:

- Como cliente piloto, quero acessar ambiente definitivo com meus dados.
- Como PO, quero acompanhar sucesso do go-live.

Critérios de aceite:

- Deploy sem incidente critico.
- Primeiro cliente opera.
- Backup e rollback testados.

Testes obrigatorios:

- Regressao final.
- Smoke producao.

Documentacao obrigatoria:

- Checklist de producao preenchido.

## 11. Estimativa Geral

Tempo total ate beta fechado: **8 a 12 semanas**.

Tempo total ate producao comercial controlada: **16 a 24 semanas**.

Equipe ideal:

- 1 Product Owner / Analista de Negocios.
- 1 Tech Lead / Arquiteto Django.
- 1 Backend Django.
- 1 UX/UI com foco em produto B2B operacional.
- 1 QA.
- 1 DevOps parcial.
- 1 Customer Success / Suporte.
- 1 Comercial consultivo.

Papeis necessarios:

- Produto: priorizacao, pilotos, criterio de sucesso.
- Engenharia: backend, seguranca, performance, billing.
- UX: fluxo operacional, clareza, onboarding.
- QA: regressao, isolamento multiempresa, smoke.
- DevOps: staging, deploy, logs, backups.
- CS/Suporte: treinamento e suporte de piloto.
- Comercial: prospeccao e conversao.

Esforco por area:

- Backend: alto.
- DevOps: medio/alto.
- QA: medio/alto.
- UX/UI: medio.
- Produto/CS: alto durante pilotos.
- Comercial: medio antes do beta, alto no go-live.

Principais gargalos:

- Definir fluxo de pedido sem virar ERP.
- Gateway de pagamento e webhooks.
- Observabilidade real.
- Onboarding e suporte com clientes reais.
- Evitar excesso de features antes de prova de valor.

## 12. Checklist Final de Producao

### Seguranca

- [ ] `DEBUG=False`.
- [ ] `ALLOWED_HOSTS` restrito.
- [ ] `SECRET_KEY` via secret.
- [ ] HTTPS obrigatorio.
- [ ] CSRF validado em formularios mutaveis.
- [ ] Permissoes admin/vendedor revisadas.
- [ ] Testes de isolamento multiempresa passando.
- [ ] Nenhum dado sensivel em logs.

### Billing

- [ ] Gateway em producao configurado.
- [ ] Webhooks assinados.
- [ ] Webhooks idempotentes.
- [ ] Planos e limites revisados.
- [ ] Fluxo de upgrade/downgrade testado.
- [ ] Cancelamento e inadimplencia definidos.
- [ ] Reconciliacao inicial documentada.

### LGPD

- [ ] Termos de uso.
- [ ] Politica de privacidade.
- [ ] Processo de remocao/exportacao.
- [ ] Retencao de logs definida.
- [ ] Consentimento para piloto.

### Backups

- [ ] Backup automatico.
- [ ] Restore testado.
- [ ] Retencao definida.
- [ ] Responsavel definido.

### Logs

- [ ] Logs por request.
- [ ] Usuario e empresa nos logs.
- [ ] Logs de billing.
- [ ] Logs de automacoes.
- [ ] Logs de erro consultaveis.

### Monitoramento

- [ ] Uptime check.
- [ ] Error tracking.
- [ ] Alertas de 5xx.
- [ ] Latencia monitorada.
- [ ] Alertas de webhook/billing.

### CI/CD

- [ ] Pipeline com install.
- [ ] `manage.py check`.
- [ ] `makemigrations --check --dry-run`.
- [ ] Testes completos.
- [ ] Deploy com rollback.

### Dominio e SSL

- [ ] Dominio configurado.
- [ ] SSL valido.
- [ ] Redirecionamento HTTPS.

### Staging

- [ ] Ambiente separado.
- [ ] PostgreSQL.
- [ ] Secrets separados.
- [ ] Smoke test aprovado.

### Rollback

- [ ] Runbook de rollback.
- [ ] Backup pre-deploy.
- [ ] Responsavel em janela de deploy.

### Testes

- [ ] Suite completa verde.
- [ ] Testes de billing.
- [ ] Testes multiempresa.
- [ ] Smoke producao.
- [ ] Testes de permissao por papel.

### Documentacao

- [ ] Manual admin.
- [ ] Manual vendedor.
- [ ] Guia de suporte.
- [ ] Guia de deploy.
- [ ] Runbook de incidentes.

### Suporte

- [ ] Canal definido.
- [ ] SLA inicial.
- [ ] Playbook de triagem.
- [ ] Escalonamento tecnico.

### Onboarding

- [ ] Roteiro de primeira semana.
- [ ] Checklist de ativacao.
- [ ] Treinamento gravado ou documentado.

### Treinamento

- [ ] Treinamento admin.
- [ ] Treinamento vendedor.
- [ ] Material de duvidas frequentes.

### Contrato/termos

- [ ] Termo de piloto.
- [ ] Contrato ou aceite.
- [ ] Politica de cancelamento.
- [ ] Limites de responsabilidade.

### Plano de piloto

- [ ] Empresas selecionadas.
- [ ] Objetivo por empresa.
- [ ] Responsavel por acompanhamento.
- [ ] Relatorio semanal.

### Metricas de sucesso

- [ ] Empresa ativada.
- [ ] Produtos cadastrados.
- [ ] Clientes/leads cadastrados.
- [ ] Oportunidades criadas.
- [ ] Proximas acoes concluidas.
- [ ] Pedidos criados.
- [ ] Catalogo compartilhado.
- [ ] Uso semanal do workspace.
- [ ] Pagamento ou aceite comercial.

## Obrigatorio versus desejavel

Obrigatorio para producao:

- Staging.
- PostgreSQL.
- Billing real.
- Backups.
- Observabilidade minima.
- Suporte.
- LGPD minima.
- Testes verdes.
- Permissoes revisadas.
- Pilotos validados.

Desejavel para evolucao:

- IA generativa.
- API publica madura.
- Integracoes avancadas.
- Marketplace.
- WhatsApp oficial.
- Filas externas.
- BI avancado.

Esses itens desejaveis nao devem entrar antes de validacao comercial.

## Fechamento

Insight mais importante: o produto nao precisa de mais amplitude agora; precisa provar ciclo comercial completo em PMEs reais com cobranca, suporte e seguranca.

Prioridade real: transformar RC1 pos-hardening em RC2 pilotavel, com staging, pedido real, automacoes administraveis e checklist de beta.

Proxima acao de maior impacto: criar o ambiente de staging e implementar o fluxo real minimo de pedido, porque sem isso nao ha piloto confiavel nem prova comercial completa.

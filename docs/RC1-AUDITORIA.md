# Auditoria tecnica MVP RC1

Data: 2026-06-30

## Objetivo

Auditar o MVP RC1 antes da proxima fase de desenvolvimento, sem alterar comportamento do sistema, sem criar dependencias e sem implementar funcionalidades.

## Escopo auditado

- Arquitetura
- Performance
- Seguranca
- Multiempresa
- Billing
- Workspace
- CRM
- Eventos
- Automacoes
- Inteligencia Comercial
- UX
- Cobertura de testes
- Documentacao
- Dependencias
- Codigo morto
- Duplicacoes
- Consultas N+1
- Indices do banco
- Permissoes
- Escalabilidade

## Sumario executivo

O MVP RC1 esta funcional como prototipo SaaS multiempresa e possui uma base tecnica coerente: apps separados por dominio, mixins de tenant, models com `empresa`, testes cobrindo fluxos principais, domain events, automacoes sincronas auditaveis, dashboard, CRM, workspace e billing interno.

O produto, porem, ainda nao esta pronto para operacao real em producao. Existem bloqueios de seguranca e operacao: `DEBUG=True`, `SECRET_KEY` fixa, `ALLOWED_HOSTS=["*"]`, ausencia de manifesto de dependencias, billing administrativo acessivel por qualquer membro da empresa e risco de custo alto por calculos sincronizados em middleware/dashboard/workspace.

Score geral do produto: **74/100**

Leitura do score:

- 80-100: pronto para piloto controlado em ambiente real.
- 65-79: bom RC interno, mas com bloqueios antes de producao.
- 50-64: prototipo funcional com riscos estruturais.
- abaixo de 50: nao recomendado para evolucao sem estabilizacao.

## Evidencias executadas

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Resultados:

- `python manage.py check`: OK, sem issues.
- `python manage.py makemigrations --check --dry-run`: OK, `No changes detected`.
- `python manage.py test`: OK, 100 testes executados em 72.410s.

Observacoes:

- O repositorio possui alteracoes acumuladas nao commitadas de fases anteriores.
- Nao foi encontrado manifesto de dependencias como `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` ou `setup.cfg`.
- Banco local: SQLite (`db.sqlite3`).

## Arquitetura

Apps identificados:

- `core`: tenant helpers e mixins.
- `empresas`: tenant e memberships.
- `catalogo`: produtos e compartilhamento de catalogo.
- `crm`: cliente, lead, oportunidade, historico, proxima acao e workspace.
- `vendas`: pedido e itens.
- `dashboard`: KPIs, recomendacoes e onboarding.
- `whatsapp`: templates e links `wa.me`.
- `billing`: planos, assinatura, limites e middleware.
- `eventos`: domain events, event log, automacoes e execution logs.
- `services`: inteligencia comercial e onboarding.

Pontos fortes:

- Separacao de apps por dominio.
- Escopo multiempresa centralizado em `core.tenant` e `core.mixins`.
- Domain events e automacoes estao no app `eventos`, coerente com a responsabilidade.
- Documentacao incremental cobre as fases principais.

Riscos:

- `services/` global concentra logicas de dominio que poderiam ficar mais proximas dos apps proprietarios.
- `crm.views.WorkspaceAccessMixin` concentra muitas consultas e composicao de tela em uma unica view.
- `billing.services` importa `services.inteligencia_comercial`, criando custo e acoplamento entre monetizacao e recomendacoes.

## Problemas por criticidade

### Criticos

1. **Settings de producao inseguros**
   - Evidencia: `pme_saas/settings.py` usa `SECRET_KEY = "dev-only-change-me"`, `DEBUG = True` e `ALLOWED_HOSTS = ["*"]`.
   - Impacto: vazamento de detalhes internos, configuracao insegura e impossibilidade de liberar ambiente real com seguranca.
   - Area: seguranca, operacao.

2. **Billing administrativo sem restricao de papel**
   - Evidencia: `billing.views.PlanoAdminView` usa apenas `EmpresaRequiredMixin`.
   - Impacto: qualquer usuario com membership ativa, inclusive vendedor, pode acessar/postar alteracao de assinatura da empresa.
   - Area: permissoes, billing.

3. **Ausencia de manifesto de dependencias**
   - Evidencia: nao ha `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` ou equivalente.
   - Impacto: build nao reprodutivel; risco alto para onboarding de ambiente, CI/CD e deploy.
   - Area: dependencias, operacao.

### Altos

4. **Middleware de billing pode executar calculos caros em qualquer view com `empresa_id`**
   - Evidencia: `BillingLimitMiddleware.process_view` chama `avaliar_limites`, que chama `contar_uso`, que chama `contar_recomendacoes_comerciais`, que recalcula inteligencia comercial.
   - Impacto: cada tela tenant pode disparar agregacoes de pedidos, oportunidades, clientes e recomendacoes.
   - Area: performance, escalabilidade.

5. **Automacoes sincronas podem gerar cascatas de eventos**
   - Evidencia: `AutomationRunner` cria `ProximaAcao`, `Oportunidade` e atualiza status; esses models tambem emitem events via receivers.
   - Impacto: risco de cadeia recursiva ou custo imprevisivel se regras forem configuradas de forma ampla.
   - Area: eventos, automacoes, escalabilidade.

6. **Dispatcher global nao impede registro duplicado de handlers**
   - Evidencia: `eventos.receivers` executa `dispatcher.subscribe_all(...)` no `AppConfig.ready`.
   - Impacto: em cenarios de autoreload, import duplicado ou testes futuros, handlers podem ser registrados mais de uma vez e duplicar efeitos.
   - Area: eventos, automacoes.

7. **Rota de compartilhamento de catalogo altera estado via GET**
   - Evidencia: `CatalogoCompartilharView.get` registra `CATALOGO_COMPARTILHADO` e redireciona para `wa.me`.
   - Impacto: bots, prefetchers ou acessos acidentais podem registrar eventos sem acao real do usuario; GET mutavel nao e ideal.
   - Area: seguranca, auditoria, UX.

8. **Workspace concentra muitas consultas sincronas**
   - Evidencia: `get_workspace_context` consulta oportunidades, historicos, pedidos, proximas acoes, inteligencia, produtos, event logs e automacoes.
   - Impacto: tela principal pode degradar rapidamente com volume.
   - Area: performance, workspace, escalabilidade.

9. **Inteligencia comercial possui N+1 conhecido**
   - Evidencia: `listar_clientes_sem_recompra` busca ultimo pedido dentro do loop por cliente; `score_oportunidade` consulta historico por oportunidade.
   - Impacto: crescimento de clientes/oportunidades aumenta consultas de forma linear.
   - Area: performance, inteligencia comercial.

### Medios

10. **Onboarding considera catalogo compartilhado apenas pela existencia de produto**
    - Evidencia: `_etapa_compartilhar_catalogo` marca concluido se existir produto ativo.
    - Impacto: ativacao fica otimista e nao mede acao real de compartilhamento.
    - Area: onboarding, analytics.

11. **UX ainda e funcional, mas pouco polida**
    - Evidencia: templates Django simples, sem navegacao consolidada, sem estados ricos ou agrupamento visual forte.
    - Impacto: bom para validar regra, limitado para usuario final recorrente.
    - Area: UX.

12. **Automacoes configuradas por JSON sem camada de validacao dedicada**
    - Evidencia: `AutomationRule.conditions` e `actions` sao `JSONField` livres.
    - Impacto: regras invalidas viram falhas em runtime; bom para MVP, fraco para administracao real.
    - Area: automacoes, DX, suporte.

13. **EventLog usa IDs soltos para entidades relacionadas**
    - Evidencia: campos `cliente_id`, `pedido_id`, `produto_id`, etc. sao inteiros, nao FKs.
    - Impacto: flexivel e resiliente a delecao, mas perde integridade referencial e dificulta joins consistentes.
    - Area: eventos, banco.

14. **Pedido nao possui fluxo operacional de criacao**
    - Evidencia: `vendas` possui detail view; workspace mostra criacao de pedido como indisponivel.
    - Impacto: produto comercial ainda depende de dados criados por teste/admin/codigo.
    - Area: vendas, workspace, UX.

15. **Nao ha configuracao separada por ambiente**
    - Evidencia: um unico `settings.py`.
    - Impacto: dev, teste e producao ficam misturados.
    - Area: operacao, seguranca.

### Baixos

16. **Duplicidade entre docs e estado historico**
    - Evidencia: docs acumulam fases sucessivas e algumas secoes sao evolucoes de decisoes anteriores.
    - Impacto: leitura exige contexto; risco de confusao para novo desenvolvedor.
    - Area: documentacao.

17. **Templates simples repetem estruturas de listas e secoes**
    - Evidencia: varias partials renderizam listas semelhantes.
    - Impacto: baixo agora, pode gerar manutencao repetitiva.
    - Area: UX, manutencao.

18. **Sem ferramenta declarada de lint/format**
    - Evidencia: nao ha configuracao de ruff/black/isort/flake8.
    - Impacto: padrao depende da disciplina manual.
    - Area: qualidade.

## Avaliacao por area

### 1. Arquitetura

Status: bom para RC1.

O sistema esta modularizado por apps Django tradicionais. A arquitetura esta apropriada para MVP, com baixo uso de dependencias e boa rastreabilidade. A proxima evolucao deve separar settings por ambiente e extrair services grandes em unidades menores.

### 2. Performance

Status: funcional, mas com riscos claros de escala.

Principais pontos:

- Recomendacoes sao recalculadas em dashboard, workspace e billing.
- `BillingLimitMiddleware` executa avaliacao pesada por request tenant.
- Workspace monta contexto amplo em uma unica view.
- Inteligencia comercial tem loops com consultas por item.

### 3. Seguranca

Status: bloqueador para producao.

Pontos positivos:

- CSRF middleware esta ativo.
- LoginRequiredMixin com `raise_exception=True` evita acesso anonimo a views tenant.
- Templates Django escapam conteudo por padrao.

Bloqueios:

- `DEBUG=True`.
- `SECRET_KEY` fixa.
- `ALLOWED_HOSTS=["*"]`.
- Falta configuracao de ambiente.
- GET mutavel no compartilhamento de catalogo.

### 4. Multiempresa

Status: bom.

Pontos fortes:

- Entidades principais possuem `empresa`.
- Mixins e querysets filtram por tenant.
- Forms filtram relacionamentos por empresa.
- Testes cobrem vazamento entre empresas.

Riscos:

- EventLog usa IDs soltos; a seguranca depende das consultas filtradas por empresa.
- Automacoes precisam continuar sempre partindo do `event.empresa`.

### 5. Billing

Status: estruturalmente presente, mas permissao precisa correcao.

Pontos fortes:

- Plano, Assinatura e limites existem.
- Middleware exibe avisos e bloqueios suaves.
- Limites cobrem usuarios, vendedores, clientes/leads, produtos, oportunidades, pedidos, recomendacoes e workspace.

Riscos:

- Tela administrativa de plano nao exige papel admin.
- Limites recalculam recomendacoes em runtime.
- Nao ha gateway nem ciclo financeiro real, conforme escopo atual.

### 6. Workspace

Status: forte como tela operacional, com risco de custo.

Pontos fortes:

- Reune cliente, oportunidade, pedidos, produtos, inteligencia, timeline e automacoes.
- Acesso por objeto valida membership e retorna 404 quando fora do tenant.

Riscos:

- Muitas consultas sincronas.
- Sem paginação interna para timeline, historicos e pedidos.
- Mistura composicao de tela, metricas e filtragem em uma view grande.

### 7. CRM

Status: adequado ao objetivo de CRM leve.

Pontos fortes:

- Cliente, Lead, Oportunidade, HistoricoContato e ProximaAcao existem.
- ProximaAcao e central e vinculavel a cliente, oportunidade e pedido.
- Forms filtram por empresa.

Riscos:

- Sem workflow sofisticado de pipeline, intencional no escopo.
- Vendedor selecionavel vem dos memberships ativos; nao ha segregacao fina por papel em todos os fluxos.

### 8. Eventos

Status: boa fundacao.

Pontos fortes:

- DomainEvent e EventLog persistente.
- Eventos principais registrados.
- Timeline usa eventos.

Riscos:

- Handlers globais sem deduplicacao.
- EventLog nao tem FKs para entidades de negocio.
- Sem mecanismo de replay ou outbox, aceitavel por enquanto.

### 9. Automacoes

Status: funcional e auditavel para MVP.

Pontos fortes:

- AutomationRule e AutomationExecutionLog existem.
- Toda execucao registra sucesso, falha ou ignorada.
- Idempotencia por evento + regra.

Riscos:

- Execucao sincrona pode impactar request.
- Acoes podem gerar novos eventos.
- JSON livre precisa validacao antes de virar UI administrativa.

### 10. Inteligencia Comercial

Status: boa para regras deterministicas.

Pontos fortes:

- Regras auditaveis.
- Sem IA externa.
- Motivos explicitos nas recomendacoes.

Riscos:

- Sem cache.
- N+1 em clientes sem recompra e score de oportunidade.
- Sem limites de volume por query em alguns calculos.

### 11. UX

Status: suficiente para MVP tecnico, fraca para venda assistida real.

Pontos fortes:

- Telas simples e compreensiveis.
- Workspace centraliza contexto.
- Dashboard mostra KPIs, onboarding, recomendacoes e automacoes.

Riscos:

- Visual muito basico.
- Navegacao e hierarquia ainda rudimentares.
- Fluxo de pedido incompleto.

### 12. Cobertura de testes

Status: bom.

Evidencia: 100 testes passando.

Cobertura qualitativa:

- Multiempresa: boa.
- CRM: boa.
- Dashboard/KPIs/onboarding: boa.
- WhatsApp: boa.
- Eventos/automações: boa.
- Billing: boa.

Gaps:

- Sem testes de carga/query count.
- Sem testes de seguranca de settings.
- Sem testes de papel admin para billing, pois regra ainda nao existe.
- Sem testes de UI visual.

### 13. Documentacao

Status: boa, mas precisa consolidacao.

Docs existentes cobrem auditoria inicial, multiempresa, CRM, workspace, KPIs, WhatsApp, monetizacao, onboarding, eventos, automacoes e inteligencia.

Risco: documentacao esta incremental; recomenda-se um indice operacional e um decision log consolidado.

### 14. Dependencias

Status: bloqueio operacional.

Nao ha arquivo de dependencias. Isso impede ambiente reprodutivel, CI confiavel e deploy previsivel.

### 15. Codigo morto

Status: baixo risco.

Nao foram encontrados `TODO`, `FIXME`, `pass` soltos, `print` ou uso de raw SQL. Existem pontos de escopo intencionalmente incompletos, como criacao de pedido e automacao externa de WhatsApp.

### 16. Duplicacoes

Status: moderado.

Duplicacoes aceitaveis para MVP:

- Agrupamento de acoes/listas em templates.
- Padrões parecidos de forms e mixins.
- Geração de links de ação em inteligencia e workspace.

Recomendacao: consolidar somente apos estabilizar o produto, para nao criar abstração prematura.

### 17. Consultas N+1

Status: risco alto em dados reais.

Principais pontos:

- `listar_clientes_sem_recompra`: busca ultimo pedido dentro do loop.
- `score_oportunidade`: consulta historico por oportunidade.
- Workspace pode agregar muitos blocos em uma request.
- Billing middleware recalcula inteligencia comercial indiretamente.

### 18. Indices do banco

Status: bom para queries principais, incompleto para eventos genericos.

Indices existentes:

- Produto: empresa/ativo/nome.
- CRM: cliente, lead, oportunidade, historico, proxima acao por empresa/status/datas.
- Pedido: empresa/status/data e empresa/vendedor/status.
- EventLog: empresa/tipo/data, empresa/cliente/data, empresa/oportunidade/data, empresa/pedido/data.
- AutomationRule: empresa/ativa/evento/prioridade.
- AutomationExecutionLog: empresa/resultado/data.

Gaps:

- EventLog por `entidade_tipo` + `entidade_id`.
- EventLog por `produto_id` e `proxima_acao_id`, se analytics usarem esses campos.
- PedidoItem por pedido/produto combinado, se analises de produto crescerem.

### 19. Permissoes

Status: bom no tenant, incompleto por papel.

Pontos fortes:

- Usuario sem membership recebe 403.
- Objetos fora do tenant retornam 404 quando apropriado.
- Superuser/staff nao sao bypass silencioso nas views de negocio.

Riscos:

- Billing admin sem exigencia de papel admin.
- Criacao de CRM e catalogo aparentemente disponivel para qualquer membro ativo.
- Futuras telas de automacao devem exigir admin.

### 20. Escalabilidade

Status: suficiente para piloto pequeno, nao para operacao ampla.

Principais limitadores:

- SQLite local.
- Recalculos sincronizados e sem cache.
- Automacoes dentro do request.
- Falta de paginacao/limites em algumas telas e services.
- Sem fila/outbox, por restricao de escopo.

## Melhorias recomendadas

### Prioridade P0 - antes de qualquer producao

1. Criar settings por ambiente e mover segredo/config para variaveis de ambiente.
2. Definir `DEBUG=False` e `ALLOWED_HOSTS` restrito em producao.
3. Criar manifesto de dependencias.
4. Restringir `PlanoAdminView` a admin da empresa.
5. Remover recomendacoes comerciais do caminho quente do middleware de billing.

### Prioridade P1 - antes de piloto com clientes reais

6. Adicionar cache ou precomputacao para inteligencia comercial.
7. Otimizar N+1 em clientes sem recompra e score de oportunidade.
8. Adicionar protecao contra registro duplicado de handlers no dispatcher.
9. Trocar registro de compartilhamento de catalogo para POST ou confirmar explicitamente a acao.
10. Criar paginacao/limites claros para workspace e timeline.

### Prioridade P2 - evolucao controlada

11. Criar UI segura para `AutomationRule`, com validacao de JSON/actions.
12. Criar indice operacional de docs e decision log.
13. Melhorar UX visual e navegacao.
14. Implementar fluxo real de criacao de pedido.
15. Adicionar testes de query count e smoke de seguranca.

### Prioridade P3 - escala futura

16. Avaliar outbox/fila para automacoes.
17. Migrar para banco de producao com plano de indices.
18. Adicionar observabilidade de tempo de services e automacoes.
19. Separar services grandes por dominio.
20. Criar politicas de retencao para EventLog e AutomationExecutionLog.

## Plano de correcao priorizado

### Fase 1 - Hardening RC1

Objetivo: tornar o MVP seguro para ambiente controlado.

Tarefas:

- Ajustar settings por ambiente.
- Criar dependencia reprodutivel.
- Proteger billing admin por papel.
- Reduzir custo do middleware de billing.
- Adicionar testes para permissao de billing admin.

Critério de aceite:

- `manage.py check` OK.
- `manage.py test` OK.
- Vendedor nao altera plano.
- Settings de producao nao expõem debug ou segredo fixo.

### Fase 2 - Performance baseline

Objetivo: remover riscos de N+1 e custo repetido.

Tarefas:

- Medir query count do dashboard e workspace.
- Otimizar inteligencia comercial.
- Cachear/precomputar recomendacoes por empresa.
- Limitar timeline e automacoes por pagina ou janela.

Critério de aceite:

- Dashboard e workspace com limites de consulta documentados.
- Services sem loops com consulta por item nos fluxos principais.

### Fase 3 - Automacoes administraveis

Objetivo: permitir configuracao segura sem quebrar auditabilidade.

Tarefas:

- Criar forms/admin interno para AutomationRule.
- Validar conditions/actions antes de salvar.
- Bloquear regras perigosas/ciclicas.
- Melhorar logs de erro e causa.

Critério de aceite:

- Toda regra invalida falha no form, nao em runtime.
- Nenhuma regra cria cascata nao controlada.

### Fase 4 - UX operacional

Objetivo: transformar a base tecnica em produto usavel.

Tarefas:

- Melhorar navegacao entre dashboard, workspace, agenda e catalogo.
- Implementar criacao de pedido.
- Refinar estados vazios e CTAs.
- Consolidar componentes visuais.

Critério de aceite:

- Usuario comercial consegue executar ciclo cliente -> oportunidade -> proxima acao -> pedido -> follow-up.

## Score detalhado

- Arquitetura: 8/10
- Performance: 5/10
- Seguranca: 4/10
- Multiempresa: 8/10
- Billing: 6/10
- Workspace: 7/10
- CRM: 8/10
- Eventos: 7/10
- Automacoes: 7/10
- Inteligencia Comercial: 7/10
- UX: 5/10
- Testes: 8/10
- Documentacao: 8/10
- Dependencias: 3/10
- Codigo morto: 8/10
- Duplicacoes: 7/10
- N+1: 5/10
- Indices: 7/10
- Permissoes: 6/10
- Escalabilidade: 5/10

Score geral ponderado: **74/100**

## Conclusao

O MVP RC1 esta em bom estado para continuidade tecnica e validacao interna. Ele demonstra uma arquitetura coerente, boa disciplina multiempresa e cobertura de testes saudavel.

Nao deve ser colocado em producao antes de corrigir os itens P0. O maior risco nao esta nas regras comerciais, mas em hardening operacional, permissao de billing, dependencia reprodutivel e custo de calculos sincronizados.

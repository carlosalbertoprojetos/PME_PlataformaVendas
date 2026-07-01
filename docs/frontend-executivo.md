# Frontend executivo

## Objetivo

O frontend executivo organiza a experiencia do dono ou gestor da empresa em uma tela de decisao diaria, sem alterar regras de negocio e sem transformar o sistema em SPA.

A camada visual usa Django tradicional, templates server-side e componentes reutilizaveis em `templates/components`.

## Escopo entregue

- Sidebar limpa com acesso a Dashboard, Workspace, CRM, Pedidos, Agenda, Produtos, Catalogo, Automacoes e Plano.
- Header com empresa, plano/status quando disponivel e usuario autenticado.
- Dashboard da empresa com visao executiva acima da dobra.
- Cards de metricas comerciais.
- Recomendacoes acionaveis com motivo auditavel, prioridade, entidade e botoes.
- Proximas acoes pendentes.
- Automacoes comerciais executadas no dia.
- Onboarding operacional compacto.
- Plano atual e limites de uso.
- CTA de plano apenas para usuario com papel `admin`.
- Estados vazios para componentes sem dados.

## Componentes criados

- `templates/components/_metric_card.html`
- `templates/components/_status_badge.html`
- `templates/components/_empty_state.html`
- `templates/components/_section_header.html`
- `templates/components/_action_button.html`
- `templates/components/_limit_usage.html`

Os componentes sao simples e sem dependencia externa. Eles foram criados para evitar duplicacao visual entre dashboard e billing.

## Dashboard executivo

Arquivo principal:

- `templates/dashboard/empresa.html`

Dados usados:

- KPIs: `dashboard.services.calcular_kpis_comerciais`
- Onboarding: `services.onboarding.gerar_onboarding_empresa`
- Recomendacoes: `services.inteligencia_comercial.listar_recomendacoes_acionaveis`
- Automacoes: `eventos.automation.metricas_automacoes_empresa`
- Billing: `billing.services.get_assinatura_empresa` e `billing.services.avaliar_limites`
- Proximas acoes: `crm.models.ProximaAcao.objects.da_empresa(empresa)`

Nao foram criadas novas regras de score, automacao, billing ou CRM.

## Navegacao e permissoes

A navegacao usa apenas rotas ja existentes. O item `Pedidos` aponta para a area de KPIs do dashboard porque ainda nao existe tela de listagem de pedidos no projeto.

O link `Plano` aparece apenas quando o usuario possui membership com papel `admin`.

O backend continua protegido por:

- `EmpresaRequiredMixin`
- `EmpresaRoleRequiredMixin`
- Querysets `da_empresa`
- Middleware de billing para avisos e bloqueios suaves

## Responsividade

O layout e desktop-first, com quebra para tablets e mobile usando CSS simples no `base.html`.

Decisoes:

- Sem Bootstrap novo via CDN.
- Sem React/Vue.
- Sem SPA.
- Sem dependencia externa.
- Cards com raio maximo visual de 8px, exceto badges/progresso por serem elementos de status.

## Seguranca

Cuidados aplicados:

- Dados do dashboard continuam filtrados por `empresa`.
- Links administrativos de plano nao aparecem para vendedores.
- Nenhum endpoint novo foi criado para a camada visual.
- O comando demo foi isolado em management command e bloqueado em producao.
- O dashboard nao renderiza dados de outra empresa nos testes de isolamento.

## Testes relacionados

Testes adicionados ou ampliados:

- Renderizacao dos blocos principais do dashboard executivo.
- Estados vazios.
- CTA de upgrade quando limite esta atingido.
- Navegacao sem link administrativo indevido para vendedor.
- Isolamento por empresa preservado pelos testes existentes.

Comandos usados na fase:

```powershell
python manage.py check
python manage.py test dashboard.tests empresas.tests
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Limites conhecidos

- Ainda nao existe tela de listagem de pedidos; o item de navegacao `Pedidos` ancora nos indicadores de pedidos do dashboard.
- Ainda nao existe UI administrativa completa de automacoes; o item `Automacoes` ancora nas metricas do dashboard.
- A tela continua sendo uma camada executiva sobre capacidades existentes, nao uma reformulacao total do produto.

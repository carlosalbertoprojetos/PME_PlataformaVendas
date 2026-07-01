# Modelo multiempresa

Data: 2026-06-30

## Objetivo

Garantir que dados operacionais do SaaS sejam sempre acessados dentro do escopo de uma empresa. Nenhum usuario, vendedor ou administrador de uma empresa pode listar, consultar, criar ou alterar dados pertencentes a outra empresa.

## Entidades

### Empresa

`empresas.Empresa` representa o tenant. Dados de negocio devem possuir uma chave estrangeira obrigatoria para `Empresa`.

Campos principais:

- `nome`
- `ativa`
- timestamps de criacao e atualizacao

### EmpresaMembership

`empresas.EmpresaMembership` liga usuario e empresa.

Campos principais:

- `empresa`
- `usuario`
- `papel`: `admin` ou `vendedor`
- `ativo`

Regras:

- A combinacao `empresa + usuario` e unica.
- Membership inativa nao autoriza acesso.
- `is_staff` e `is_superuser` nao sao atalhos de tenant nas views de negocio.

### Produto

`catalogo.Produto` pertence obrigatoriamente a uma empresa.

Regras:

- `empresa` e obrigatoria.
- `nome` e unico dentro da empresa, nao globalmente.
- Consultas operacionais devem filtrar por empresa.
- Indice composto por `empresa`, `ativo` e `nome` apoia listagens do catalogo.

### CRM leve

Os models `crm.Cliente`, `crm.Lead`, `crm.Oportunidade`, `crm.HistoricoContato` e `crm.ProximaAcao` tambem pertencem obrigatoriamente a uma empresa.

Regras:

- clientes e leads sao listados e detalhados apenas dentro da empresa ativa;
- conversao de lead cria cliente na mesma empresa;
- oportunidades vinculam empresa, cliente e vendedor;
- historicos apontam para cliente ou lead da mesma empresa;
- proximas acoes apontam para cliente, oportunidade ou pedido da mesma empresa;
- formularios filtram relacionamentos pela empresa atual.

### Vendas e KPIs

Os models `vendas.Pedido` e `vendas.PedidoItem` suportam os dashboards comerciais.

Regras:

- pedido pertence obrigatoriamente a uma empresa;
- cliente do pedido deve pertencer a mesma empresa;
- oportunidade do pedido, quando informada, deve pertencer a mesma empresa;
- item de pedido deve usar produto da mesma empresa do pedido;
- dashboards comerciais filtram por empresa antes de agregar qualquer metrica.

### WhatsApp leve

O model `whatsapp.WhatsAppTemplateConfig` armazena mensagens configuraveis por empresa para links `wa.me`.

Regras:

- configuracao de WhatsApp pertence a uma unica empresa;
- links de catalogo/produto/cliente/pedido sao gerados a partir de objetos ja escopados;
- nao ha envio automatico nem integracao com API oficial;
- o usuario revisa a mensagem no WhatsApp antes do envio.

### Monetizacao

Os models `billing.Plano` e `billing.Assinatura` preparam monetizacao interna por empresa.

Regras:

- assinatura pertence a uma unica empresa;
- limites sao calculados apenas com dados da propria empresa;
- middleware de billing so carrega limites quando o usuario tem membership ativa na empresa;
- bloqueios por limite sao suaves e aplicados nos pontos de criacao existentes;
- nao ha integracao com gateway nesta fase.

### Eventos comerciais

Os models `eventos.EventLog`, `eventos.AutomationRule` e `eventos.AutomationExecutionLog` registram eventos e automacoes por empresa.

Regras:

- todo evento persistido pertence obrigatoriamente a uma empresa;
- toda regra e toda execucao de automacao pertencem obrigatoriamente a uma empresa;
- timeline e analytics devem consultar eventos com filtro de empresa antes de filtrar entidade relacionada;
- eventos nao substituem validacao de permissao nas views;
- nao ha fila externa nesta fase, apenas dispatcher sincrono.

### Inteligencia comercial

O servico `services/inteligencia_comercial.py` calcula recomendacoes deterministicas por empresa.

Regras:

- recomendacoes filtram dados da empresa antes de qualquer calculo;
- cada recomendacao inclui motivo auditavel;
- nao ha chamada para API de IA;
- dashboard de recomendacoes usa `EmpresaRequiredMixin`.

## Resolucao de tenant

Nesta fundacao, a empresa ativa vem da URL:

`/empresas/<empresa_id>/...`

Excecao controlada: as rotas de workspace comercial (`/workspace/<cliente_id>/` e `/workspace/oportunidade/<id>/`) derivam a empresa do proprio objeto e validam membership ativa antes de renderizar. Quando o usuario nao tem acesso ao objeto, retornam `404`.

Antes de executar a view, `EmpresaRequiredMixin` valida:

1. usuario autenticado;
2. empresa existente e ativa;
3. membership ativa do usuario naquela empresa.

Se qualquer condicao falhar, o acesso retorna `403`.

## Escopo de queries

Helpers centrais:

- `core.tenant.get_membership(usuario, empresa)`
- `core.tenant.user_can_access_empresa(usuario, empresa)`
- `core.tenant.get_empresa_for_user_or_403(usuario, empresa_id)`
- `core.tenant.scoped_queryset_for_user(queryset, usuario, empresa)`

Mixins centrais:

- `core.mixins.EmpresaRequiredMixin`
- `core.mixins.EmpresaScopedQuerysetMixin`
- `core.mixins.EmpresaRoleRequiredMixin`

Views que expõem dados empresariais devem usar esses helpers/mixins ou uma camada equivalente aprovada. Querysets diretos como `Produto.objects.all()` nao devem ser usados em endpoints de negocio.

## Politica de retorno

Casos de acesso indevido devem retornar:

- `403` quando o usuario tenta acessar uma empresa sem membership ativa;
- `404` quando o usuario acessa uma empresa permitida, mas referencia um objeto que nao pertence a ela.

Esse comportamento evita confirmar a existencia de dados de outro tenant quando o usuario ja esta dentro de um escopo permitido.

## Cobertura de testes

Os testes de isolamento ficam em `catalogo/tests.py` e cobrem:

- admin listando apenas produtos da propria empresa;
- admin bloqueado ao listar outra empresa;
- vendedor bloqueado ao listar outra empresa;
- usuario sem empresa bloqueado;
- produto de outra empresa retornando `404` mesmo com ID valido;
- criacao de produto sempre associada a empresa da URL;
- criacao bloqueada em empresa sem membership;
- membership inativa bloqueando acesso.

Os testes de CRM ficam em `crm/tests.py` e cobrem cadastro, conversao de lead, oportunidades, historicos, proximas acoes e bloqueios de acesso cruzado entre empresas.

Os testes de dashboard ficam em `dashboard/tests.py` e cobrem calculo de KPIs, renderizacao e bloqueios de acesso por empresa.

Os testes de WhatsApp ficam em `whatsapp/tests.py` e cobrem geracao de links `wa.me`, mensagens por empresa e renderizacao de botoes.

Os testes de monetizacao ficam em `billing/tests.py` e cobrem planos, assinatura, limites, middleware e tela administrativa.

Os testes de inteligencia comercial ficam em `dashboard/test_inteligencia_comercial.py` e cobrem regras auditaveis, isolamento por empresa e renderizacao do dashboard.

## Regras para novas features

1. Todo model de dado empresarial deve ter `empresa = ForeignKey(Empresa, ...)`.
2. Toda listagem deve filtrar por empresa antes de aplicar filtros de negocio.
3. Todo detalhe/edicao/exclusao deve buscar objeto pelo queryset ja escopado.
4. Payloads de criacao nao podem escolher livremente a empresa quando a empresa ja vem do tenant resolvido.
5. Testes de acesso cruzado devem ser criados junto com cada novo modulo.
6. Administradores de empresa nao recebem permissao global automaticamente.
7. Superusuarios de plataforma exigem fluxo separado e auditavel, nao bypass silencioso nos endpoints de negocio.

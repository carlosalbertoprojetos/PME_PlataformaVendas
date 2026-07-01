# Workspace comercial

Data: 2026-06-30

## Objetivo

Criar uma tela unica de operacao comercial por cliente ou oportunidade. A workspace passa a ser a principal tela operacional do sistema, reunindo cliente, oportunidade, proximas acoes, pedidos, produtos, inteligencia comercial, WhatsApp e timeline sem criar nova regra de negocio.

## Rotas

Rotas entregues:

- `/workspace/<cliente_id>/`
- `/workspace/oportunidade/<id>/`

As rotas nao recebem `empresa_id` porque o tenant e derivado do proprio cliente ou oportunidade. Antes de renderizar, a view valida se o usuario autenticado possui membership ativa na empresa do objeto. Sem acesso, a resposta e `404` para evitar vazamento de existencia de dados de outro tenant. Usuario anonimo recebe `403`.

## Conteudo da tela

### Cliente

Exibe:

- nome;
- telefone;
- empresa;
- ultimo contato;
- ultima compra;
- ticket medio;
- botao WhatsApp via `wa.me`.

### Oportunidade

Exibe:

- status;
- valor;
- probabilidade como `Nao definida`, pois ainda nao ha regra aprovada para esse calculo;
- dias parada pela data de atualizacao;
- score comercial reaproveitando `services.inteligencia_comercial.score_oportunidade`;
- recomendacoes relacionadas ao cliente ou oportunidade.

### Proxima acao

Exibe:

- hoje;
- atrasada;
- agendada;
- concluir;
- editar;
- criar.

Rotas reutilizadas/adicionadas:

- `/empresas/<empresa_id>/crm/proximas-acoes/novo/`;
- `/empresas/<empresa_id>/crm/proximas-acoes/<id>/editar/`;
- `/empresas/<empresa_id>/crm/proximas-acoes/<id>/concluir/`.

### Pedidos

Exibe:

- ultimos pedidos;
- status;
- valor;
- abrir pedido;
- indicacao de que criar pedido ainda nao esta disponivel nesta fase.

### Produtos

Exibe:

- produtos mais comprados pelo cliente;
- sugestoes vindas da inteligencia comercial deterministica existente;
- produtos relacionados, definidos como produtos ativos da empresa.

### Inteligencia

Exibe:

- alertas relacionados ao cliente ou oportunidade;
- motivos auditaveis;
- prioridade.

### Timeline

Usa `eventos.EventLog` como fonte principal da timeline comercial e complementa dados transicionais ainda nao registrados como eventos.

Combina:

- historico de contato;
- pedidos;
- follow-ups/proximas acoes;
- disponibilidade de WhatsApp;
- status atual da oportunidade.
- eventos de dominio como cliente criado, pedido confirmado, proxima acao criada/concluida e catalogo compartilhado.

### Automacoes

Exibe automacoes executadas para o cliente ou oportunidade atual, usando `AutomationExecutionLog` filtrado por empresa e por eventos relacionados ao cliente.

## Componentes reutilizaveis

Template principal:

- `templates/crm/workspace.html`

Parciais:

- `templates/crm/workspace/_cliente.html`
- `templates/crm/workspace/_oportunidade.html`
- `templates/crm/workspace/_proxima_acao.html`
- `templates/crm/workspace/_proxima_acao_grupo.html`
- `templates/crm/workspace/_pedidos.html`
- `templates/crm/workspace/_produtos.html`
- `templates/crm/workspace/_inteligencia.html`
- `templates/crm/workspace/_timeline.html`

## Decisoes de escopo

- Nao foi criado carrinho.
- Nao foi criada tela de criacao de pedido.
- Nao foi criada regra nova de recomendacao de produto, score ou probabilidade.
- Produtos relacionados significam produtos ativos da empresa, ate existir uma regra explicita de relacionamento.
- Sugestoes de produto reutilizam a inteligencia comercial deterministica existente.
- Botoes de WhatsApp apenas abrem links `wa.me`; nao enviam mensagens automaticamente.
- Nao ha JavaScript customizado nem frontend complexo.

## Implementacao

Views:

- `crm.views.ClienteWorkspaceView`
- `crm.views.OportunidadeWorkspaceView`
- `crm.views.ProximaAcaoUpdateView`
- `crm.views.ProximaAcaoConcluirView`

Services reutilizados:

- `services.inteligencia_comercial.gerar_recomendacoes_comerciais`
- `services.inteligencia_comercial.score_oportunidade`
- helpers e template tags de `whatsapp`

Testes:

- acesso a workspace por cliente;
- acesso a workspace por oportunidade;
- renderizacao dos componentes principais;
- isolamento entre empresas;
- bloqueio de usuario anonimo;
- edicao e conclusao de proxima acao.

## Validacao

Comandos esperados:

```powershell
python manage.py check
python manage.py test
```

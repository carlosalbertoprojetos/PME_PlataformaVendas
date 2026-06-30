# Workspace comercial

Data: 2026-06-30

## Objetivo

Criar uma tela unica de operacao comercial por cliente ou oportunidade, com leitura rapida do contexto necessario para uma acao de venda. A tela e propositalmente simples e reutiliza os models ja existentes de catalogo e CRM leve.

## Rotas

Rotas entregues:

- `/workspace/<cliente_id>/`
- `/workspace/oportunidade/<id>/`

As rotas nao recebem `empresa_id` porque o tenant e derivado do proprio cliente ou oportunidade. Antes de renderizar, a view valida se o usuario autenticado possui membership ativa na empresa do objeto. Sem acesso, a resposta e `404` para evitar vazamento de existencia de dados de outro tenant. Usuario anonimo recebe `403`.

## Conteudo da tela

A tela exibe:

1. Dados do cliente.
2. Produtos relacionados: produtos ativos da mesma empresa.
3. Carrinho/pedido: estado vazio nesta tela, pois ainda nao ha fluxo de carrinho ou checkout.
4. Historico comercial: contatos vinculados ao cliente.
5. Proxima acao: acoes pendentes vinculadas a oportunidade atual ou oportunidades do cliente.
6. Pedidos anteriores: estado vazio nesta tela; pedidos foram modelados depois apenas como fonte de KPIs.
7. Status da oportunidade: oportunidade aberta do cliente ou a oportunidade acessada pela rota.

Na fase de WhatsApp leve, a workspace tambem passou a exibir:

- mensagem pronta para cliente;
- mensagem pronta de follow-up;
- compartilhamento de produto via `wa.me`.

## Decisoes de escopo

- O model minimo de pedido foi criado depois desta fase para dashboards/KPIs, mas a workspace continua sem fluxo de carrinho, checkout ou pedidos anteriores.
- Nao foi criado carrinho.
- Nao foi criada regra nova de recomendacao de produto.
- Produtos relacionados significam produtos ativos da empresa, ate existir uma regra explicita de relacionamento.
- A workspace e somente leitura nesta fase.
- Nao ha JavaScript customizado nem frontend complexo.
- Botoes de WhatsApp apenas abrem links `wa.me`; nao enviam mensagens automaticamente.

## Implementacao

Views:

- `crm.views.ClienteWorkspaceView`
- `crm.views.OportunidadeWorkspaceView`

Template:

- `templates/crm/workspace.html`

Testes:

- renderizacao da workspace por cliente;
- renderizacao da workspace por oportunidade;
- bloqueio de cliente de outra empresa;
- bloqueio de oportunidade de outra empresa;
- bloqueio de usuario anonimo.

## Validacao

Comandos esperados:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

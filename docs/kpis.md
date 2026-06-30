# KPIs comerciais

Data: 2026-06-30

## Objetivo

Substituir um dashboard generico por paineis comerciais orientados a decisao, com indicadores simples para empresa e vendedor.

## Rotas

- Dashboard empresa: `/empresas/<empresa_id>/dashboard/`
- Dashboard vendedor: `/empresas/<empresa_id>/dashboard/vendedor/`
- Dashboard de recomendacoes: `/empresas/<empresa_id>/dashboard/recomendacoes/`

As duas rotas usam `EmpresaRequiredMixin`: usuario anonimo recebe `403`, usuario sem membership ativa na empresa recebe `403`.

O dashboard de recomendacoes tambem usa `EmpresaRequiredMixin` e segue o mesmo contrato de tenant.

## Fonte dos dados

Foi criado o app `vendas` com modelos minimos para suportar KPIs:

- `vendas.Pedido`
- `vendas.PedidoItem`

Essa criacao nao implementa fluxo completo de venda, carrinho ou checkout. O objetivo e registrar fatos suficientes para leitura de indicadores:

- empresa;
- cliente;
- oportunidade opcional;
- vendedor;
- status;
- valor total;
- data;
- itens por produto.

Na fase de WhatsApp leve, a tela de detalhe de pedido passou a exibir um botao de compartilhamento `wa.me`, sem alterar a regra de KPI.

## Definicao dos indicadores

### Pedidos do dia

Quantidade de pedidos confirmados da empresa no dia atual.

No dashboard do vendedor, conta apenas pedidos confirmados do usuario logado.

### Receita do mes

Soma de `valor_total` dos pedidos confirmados da empresa no mes atual.

No dashboard do vendedor, soma apenas pedidos confirmados do usuario logado.

### Ticket medio

Media de `valor_total` dos pedidos confirmados no mes atual.

No dashboard do vendedor, considera apenas pedidos confirmados do usuario logado.

### Produtos mais vendidos

Ranking dos 5 produtos com maior quantidade vendida em itens de pedidos confirmados no mes atual.

No dashboard do vendedor, considera apenas itens dos pedidos confirmados do usuario logado.

### Pedidos pendentes

Quantidade de pedidos com status `pendente`.

No dashboard do vendedor, conta apenas pedidos pendentes do usuario logado.

### Clientes ativos

Quantidade de clientes ativos da empresa.

Esse indicador permanece no escopo da empresa mesmo no dashboard do vendedor, pois representa base comercial disponivel.

### Oportunidades abertas

Quantidade de oportunidades com status `aberta`.

No dashboard do vendedor, conta apenas oportunidades abertas do usuario logado.

### Vendedores com maior receita

Ranking dos 5 vendedores com maior receita confirmada no mes atual.

No dashboard do vendedor, o ranking e filtrado para o usuario logado, evitando expor desempenho de outros vendedores em uma tela individual.

## Status de pedido

Status disponiveis:

- `pendente`
- `confirmado`
- `cancelado`

Somente pedidos `confirmado` entram em receita, ticket medio, pedidos do dia, produtos mais vendidos e ranking de vendedores.

## Isolamento multiempresa

Todos os pedidos pertencem a uma empresa.

Regras:

- pedido deve ter cliente da mesma empresa;
- oportunidade, quando informada, deve pertencer a mesma empresa;
- item de pedido deve usar produto da mesma empresa do pedido;
- dashboards filtram por empresa antes de qualquer agregacao;
- dashboards nao usam `is_staff` ou `is_superuser` como bypass.

## Testes

Arquivo: `dashboard/tests.py`

Cobertura:

- calculo de KPIs da empresa sem vazamento de outro tenant;
- renderizacao do dashboard empresa;
- renderizacao do dashboard vendedor com recorte do usuario;
- bloqueio de usuario sem membership;
- bloqueio de usuario tentando acessar dashboard de outra empresa;
- bloqueio de usuario anonimo.

## Validacao

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

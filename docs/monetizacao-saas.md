# Monetizacao SaaS

Data: 2026-06-30

## Objetivo

Implementar a base de monetizacao SaaS com planos, assinatura, limites e controle de acesso, sem integrar gateway de pagamento nesta fase.

## App

App reaproveitado:

`billing`

Nao foi criado app paralelo de assinaturas.

## Models

### Plano

Model:

`billing.Plano`

Planos iniciais:

- Start;
- Growth;
- Pro.

Limites controlados:

- vendedores;
- produtos;
- clientes;
- leads;
- oportunidades;
- pedidos no mes;
- recomendacoes comerciais;
- workspace comercial.

Campos de compatibilidade existentes permanecem:

- `limite_usuarios`;
- `limite_clientes`;
- `limite_produtos`;
- `limite_pedidos_mes`.

Campos SaaS adicionados:

- `limite_vendedores`;
- `limite_leads`;
- `limite_oportunidades`;
- `limite_recomendacoes_comerciais`;
- `permite_workspace_comercial`.

### Assinatura

Model:

`billing.Assinatura`

Campos principais:

- `empresa`;
- `plano`;
- `status`;
- `inicio_em`;
- `fim_trial_em`;
- `gateway_preferido`;
- `gateway_customer_id`;
- `gateway_subscription_id`.

Nenhum campo de gateway dispara cobranca real nesta fase.

## Limites por plano

Os limites iniciais sao configurados por migration:

- Start: uso inicial pequeno;
- Growth: operacao comercial em crescimento;
- Pro: uso amplo.

O helper `billing.services.get_assinatura_empresa()` cria assinatura trial Start quando a empresa ainda nao tem assinatura.

## Helpers

Arquivo:

`billing/services.py`

Helpers principais:

- `get_plano_padrao()`;
- `get_assinatura_empresa(empresa)`;
- `contar_uso(empresa)`;
- `avaliar_limites(empresa)`;
- `pode_criar_recurso(empresa, recurso)`;
- `recurso_disponivel(empresa, recurso)`;
- `assinatura_bloqueada(empresa)`.

`LimiteResultado` informa:

- recurso;
- usado;
- limite;
- percentual;
- limite atingido;
- limite proximo;
- aviso;
- CTA de upgrade.

## Bloqueios suaves

Aviso antes do limite:

- quando o uso atinge pelo menos 80% do limite.

Bloqueio apos limite:

- criacao de produto;
- criacao de cliente;
- criacao de lead;
- criacao de oportunidade.

Controle de acesso por feature:

- workspace comercial pode ser indisponivel por plano.

CTA:

- `Fazer upgrade do plano`.

O layout base exibe avisos e CTA quando `request.billing_limites` ou `request.billing_bloqueio` estao presentes.

## Tela administrativa

Rota:

`/empresas/<empresa_id>/plano/`

View:

`billing.views.PlanoAdminView`

Permite:

- consultar plano atual;
- consultar status da assinatura;
- ver uso dos limites;
- trocar plano;
- alterar status;
- registrar gateway preferido.

Essa tela faz upgrade/downgrade logico apenas. Nao cria cobranca, checkout ou comunicacao com gateway.

## Multiempresa

Regras:

- assinatura pertence a uma unica empresa;
- tela usa `EmpresaRequiredMixin`;
- limites contam apenas dados da empresa atual;
- middleware so carrega billing quando o usuario tem membership ativa;
- empresa sem acesso nao tem assinatura criada pelo middleware;
- nao ha bypass por `is_staff` ou `is_superuser`.

## Fora do escopo

- gateway real;
- checkout;
- webhooks;
- emissao de cobranca;
- bloqueio global duro;
- regras comerciais dentro do billing.

## Testes

Arquivo:

`billing/tests.py`

Cobertura:

- empresa sem assinatura;
- assinatura ativa;
- assinatura suspensa/expirada logicamente;
- limite atingido;
- aviso antes do limite;
- upgrade/downgrade logico;
- isolamento por empresa;
- workspace bloqueado por plano;
- bloqueio de criacao de produto, cliente, lead e oportunidade.

## Validacao

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

# Monetizacao

Data: 2026-06-30

## Objetivo

Preparar a estrutura interna de monetizacao do produto sem integrar gateway de pagamento nesta fase.

## Fora do escopo

- Integracao com Asaas.
- Integracao com Mercado Pago.
- Integracao com Pagar.me.
- Checkout.
- Webhook de pagamento.
- Emissao de cobranca.
- Nota fiscal.
- Bloqueio duro global da aplicacao.

## Apps e modelos

App: `billing`

### Plano

Model: `billing.Plano`

Campos principais:

- `codigo`
- `nome`
- `preco_mensal`
- `limite_usuarios`
- `limite_clientes`
- `limite_produtos`
- `limite_pedidos_mes`
- `ativo`

Planos iniciais criados por migration:

- Start
- Growth
- Pro

### Assinatura

Model: `billing.Assinatura`

Campos principais:

- `empresa`
- `plano`
- `status`
- `inicio_em`
- `fim_trial_em`
- `gateway_preferido`
- `gateway_customer_id`
- `gateway_subscription_id`

Campos de gateway foram deixados como preparacao para Asaas, Mercado Pago ou Pagar.me. Nenhum gateway e chamado nesta fase.

## Status da assinatura

Status disponiveis:

- `trial`
- `ativa`
- `past_due`
- `suspensa`
- `cancelada`

Status que permitem uso:

- `trial`
- `ativa`
- `past_due`

Status bloqueados:

- `suspensa`
- `cancelada`

Nesta fase o bloqueio e suave: o middleware anexa estado de bloqueio ao request e o layout exibe aviso. Fluxos especificos podem consultar helpers para impedir criacao quando necessario.

## Limites por plano

Recursos medidos:

- usuarios ativos da empresa;
- clientes ativos;
- produtos ativos;
- pedidos no mes atual.

Helpers:

- `billing.services.get_assinatura_empresa(empresa)`
- `billing.services.avaliar_limites(empresa)`
- `billing.services.pode_criar_recurso(empresa, recurso)`
- `billing.services.assinatura_bloqueada(empresa)`

## Bloqueios suaves

Os limites sao aplicados de forma inicial nos pontos de criacao existentes:

- criacao de produto;
- criacao de cliente.

Quando o limite esta atingido:

- produto retorna `403` com mensagem JSON;
- cliente retorna o formulario com erro nao relacionado a campo.

O layout base tambem exibe avisos quando `request.billing_limites` indica algum limite atingido ou quando `request.billing_bloqueio` indica assinatura suspensa/cancelada.

## Middleware

Middleware: `billing.middleware.BillingLimitMiddleware`

Responsabilidades:

- detectar `empresa_id` em views escopadas por empresa;
- validar que o usuario tem acesso a empresa antes de carregar billing;
- anexar `request.billing_limites`;
- anexar `request.billing_bloqueio` quando a assinatura nao permite uso.

O middleware nao cria assinatura para empresas sem acesso do usuario.

## Tela administrativa de plano

Rota:

`/empresas/<empresa_id>/plano/`

View:

`billing.views.PlanoAdminView`

Funcionalidades:

- exibe plano atual;
- exibe status da assinatura;
- exibe uso dos limites;
- permite trocar plano;
- permite alterar status;
- permite registrar gateway preferido.

Essa tela e administrativa interna. Ela nao cobra, nao cancela no gateway e nao sincroniza pagamento externo.

## Multiempresa

Assinatura pertence a uma unica empresa.

Regras:

- tela de plano usa `EmpresaRequiredMixin`;
- usuario sem membership ativa recebe `403`;
- limites sao calculados apenas com dados da empresa;
- nao ha bypass por `is_staff` ou `is_superuser`.

## Testes

Arquivo: `billing/tests.py`

Cobertura:

- planos iniciais;
- criacao automatica de assinatura trial Start;
- status suspenso bloqueando uso;
- calculo de limites por empresa;
- helper `pode_criar_recurso`;
- bloqueio suave de produto;
- bloqueio suave de cliente;
- middleware com empresa autorizada;
- middleware sem efeito para empresa sem acesso;
- tela administrativa de plano e atualizacao de assinatura.

## Validacao

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

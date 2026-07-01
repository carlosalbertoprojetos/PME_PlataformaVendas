# CRM comercial centrado em proxima acao

Data: 2026-06-30

## Objetivo

Consolidar o CRM leve existente e tornar `ProximaAcao` o centro da operacao comercial diaria, sem transformar o sistema em um CRM complexo.

## Auditoria dos models existentes

Os models de CRM ja existiam e foram reaproveitados:

- `crm.Cliente`
- `crm.Lead`
- `crm.Oportunidade`
- `crm.HistoricoContato`
- `crm.ProximaAcao`

Nao foram criados models duplicados.

## Padronizacao de ProximaAcao

`ProximaAcao` continua pertencendo obrigatoriamente a uma empresa:

- `empresa`
- `vendedor`
- `descricao`
- `data_prevista`
- `status`

Vinculos comerciais opcionais:

- `cliente`
- `oportunidade`
- `pedido`

Regra de validacao:

- toda proxima acao deve possuir `empresa`;
- a acao deve apontar para pelo menos um contexto comercial: cliente, oportunidade ou pedido;
- cliente, oportunidade e pedido, quando informados, devem pertencer a mesma empresa da acao.

## Recomendacoes e proxima acao

As recomendacoes acionaveis passaram a incluir o botao `Criar proxima acao` quando houver contexto aplicavel.

Links gerados:

- recomendacao por cliente: `?cliente=<id>`;
- recomendacao por oportunidade: `?cliente=<id>&oportunidade=<id>`;
- recomendacao por pedido: `?cliente=<id>&pedido=<id>`.

A tela de criacao de proxima acao le esses parametros e preenche o formulario quando os objetos pertencem a empresa atual.

## Agenda comercial

URL:

`/empresas/<empresa_id>/crm/proximas-acoes/`

A tela existente foi reaproveitada como agenda simples, com quatro blocos:

- acoes de hoje;
- atrasadas;
- proximas;
- concluidas.

Nao ha automacao, Kanban, pipeline visual ou regras complexas de CRM nesta fase.

## Multiempresa

Todas as consultas passam pelo contrato multiempresa existente:

- `EmpresaRequiredMixin`;
- `EmpresaScopedQuerysetMixin`;
- forms com querysets filtrados pela empresa;
- objetos de outro tenant nao aparecem nas opcoes do formulario;
- tentativa de vinculo cruzado invalida o formulario ou a validacao do model.

## Migration

Arquivo:

`crm/migrations/0002_proximaacao_cliente_proximaacao_pedido_and_more.py`

Mudancas:

- adiciona `cliente` opcional em `ProximaAcao`;
- adiciona `pedido` opcional em `ProximaAcao`;
- torna `oportunidade` opcional para permitir acoes diretamente vinculadas a cliente ou pedido.

## Testes

Arquivo principal:

`crm/tests.py`

Cobertura adicionada:

- criacao de proxima acao;
- vinculo com cliente, oportunidade e pedido;
- isolamento por empresa em vinculos do formulario;
- exibicao da agenda comercial;
- criacao de acao a partir de link de recomendacao;
- pre-preenchimento do formulario por parametros de recomendacao.

Arquivo complementar:

`dashboard/test_inteligencia_comercial.py`

Cobertura:

- link de `Criar proxima acao` nas recomendacoes acionaveis.

## Validacao

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

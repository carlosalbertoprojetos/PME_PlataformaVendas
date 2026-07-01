# CRM leve

Data: 2026-06-30

## Objetivo

Adicionar uma camada minima de CRM para apoiar o uso comercial inicial sem transformar o produto em um CRM complexo. O foco desta fase e registrar clientes, leads, oportunidades, proximas acoes e historico simples de contato.

## Escopo implementado

### Cliente

Model: `crm.Cliente`

Campos principais:

- `empresa`
- `nome`
- `email`
- `telefone`
- `documento`
- `observacoes`
- `ativo`

Funcionalidades:

- listagem por empresa;
- cadastro por formulario Django;
- detalhe com oportunidades e historicos do cliente.

### Lead

Model: `crm.Lead`

Campos principais:

- `empresa`
- `nome`
- `email`
- `telefone`
- `origem`
- `status`
- `cliente_convertido`

Funcionalidades:

- listagem por empresa;
- cadastro por formulario Django;
- detalhe com historicos;
- conversao para cliente via POST.

Regras de conversao:

- a conversao cria um `Cliente` na mesma empresa do lead;
- o lead passa para status `convertido`;
- conversoes repetidas retornam o cliente ja vinculado.

### Oportunidade

Model: `crm.Oportunidade`

Campos principais:

- `empresa`
- `cliente`
- `vendedor`
- `titulo`
- `valor_estimado`
- `status`

Funcionalidades:

- listagem por empresa;
- cadastro por formulario Django;
- detalhe com proximas acoes.

Regras:

- a oportunidade pertence sempre a uma empresa;
- o cliente deve pertencer a mesma empresa;
- o vendedor selecionavel vem de memberships ativas da empresa.

### HistoricoContato

Model: `crm.HistoricoContato`

Campos principais:

- `empresa`
- `cliente` ou `lead`
- `vendedor`
- `tipo`
- `resumo`
- `realizado_em`

Funcionalidades:

- registro simples de contato por formulario Django;
- um historico deve apontar para cliente ou lead, nunca ambos;
- cliente/lead devem pertencer a mesma empresa.

### ProximaAcao

Model: `crm.ProximaAcao`

Campos principais:

- `empresa`
- `cliente`
- `oportunidade`
- `pedido`
- `vendedor`
- `descricao`
- `data_prevista`
- `status`

Funcionalidades:

- listagem por empresa;
- cadastro por formulario Django;
- cliente, oportunidade, pedido e vendedor filtrados pela empresa.

## URLs

Todas as URLs seguem o contrato multiempresa existente:

`/empresas/<empresa_id>/crm/...`

Rotas principais:

- `clientes/`
- `clientes/novo/`
- `clientes/<pk>/`
- `leads/`
- `leads/novo/`
- `leads/<pk>/`
- `leads/<pk>/converter/`
- `oportunidades/`
- `oportunidades/novo/`
- `oportunidades/<pk>/`
- `historicos/novo/`
- `proximas-acoes/`
- `proximas-acoes/novo/`

Rotas de workspace comercial:

- `/workspace/<cliente_id>/`
- `/workspace/oportunidade/<id>/`

Essas rotas derivam a empresa do cliente ou oportunidade e validam membership ativa antes de renderizar.

## Isolamento multiempresa

O CRM leve reutiliza o contrato de `docs/multiempresa.md`:

- `EmpresaRequiredMixin` valida empresa ativa e membership ativa;
- `EmpresaScopedQuerysetMixin` filtra detalhes/listagens por empresa;
- forms recebem `empresa` no construtor e limitam querysets de relacionamento;
- objetos de outro tenant retornam `404` quando buscados dentro de uma empresa permitida;
- acesso a empresa sem membership retorna `403`.

Nenhuma view de CRM usa `is_staff` ou `is_superuser` como bypass de tenant.

## Templates

Foram criados templates Django tradicionais e simples:

- `templates/base.html`
- `templates/crm/form.html`
- `templates/crm/cliente_list.html`
- `templates/crm/cliente_detail.html`
- `templates/crm/lead_list.html`
- `templates/crm/lead_detail.html`
- `templates/crm/oportunidade_list.html`
- `templates/crm/oportunidade_detail.html`
- `templates/crm/proxima_acao_list.html`
- `templates/crm/workspace.html`

Nao ha frontend complexo, JavaScript customizado ou IA nesta fase.

As telas de cliente e workspace exibem botoes de WhatsApp leve para mensagem pronta ao cliente e follow-up. Os textos sao configuraveis por empresa em `whatsapp.WhatsAppTemplateConfig`.

## Testes

Arquivo: `crm/tests.py`

Cobertura principal:

- lista clientes apenas da empresa logada;
- bloqueia usuario sem membership;
- bloqueia admin tentando acessar outra empresa;
- retorna `404` para objeto de outro tenant dentro da empresa atual;
- cadastra cliente e lead na empresa do path;
- converte lead em cliente no mesmo tenant;
- impede conversao de lead de outra empresa;
- cria oportunidade com cliente e vendedor da empresa;
- impede oportunidade com cliente de outra empresa;
- registra historico de contato;
- cria proxima acao;
- lista proximas acoes apenas da empresa.
- renderiza workspace por cliente e por oportunidade;
- bloqueia workspace de objetos de outra empresa.

## Fora do escopo desta fase

- pipeline visual ou kanban;
- funil customizavel;
- automacoes;
- IA;
- importacao/exportacao;
- regras avancadas de distribuicao de leads;
- permissao granular por acao alem do tenant/membership;
- edicao/exclusao completa das entidades.

## Comandos de validacao

Executar:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

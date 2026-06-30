# WhatsApp leve

Data: 2026-06-30

## Objetivo

Adicionar compartilhamento comercial via WhatsApp sem integracao paga inicialmente. A implementacao usa links `wa.me` e mensagens configuraveis por empresa.

## Fora do escopo

- API oficial do WhatsApp Business.
- Webhooks.
- Envio automatico.
- Fila de mensagens.
- Templates aprovados pela Meta.
- Armazenamento de status de entrega/leitura.

## Configuracao por empresa

Model: `whatsapp.WhatsAppTemplateConfig`

Campos:

- `empresa`
- `catalogo`
- `produto`
- `pedido`
- `cliente`
- `follow_up`

Se a empresa ainda nao possuir configuracao, `get_whatsapp_config()` cria uma configuracao padrao no primeiro uso.

## Variaveis disponiveis

### Catalogo

- `{empresa_nome}`
- `{catalogo_url}`

### Produto

- `{empresa_nome}`
- `{produto_nome}`
- `{produto_preco}`
- `{produto_url}`

### Pedido

- `{empresa_nome}`
- `{cliente_nome}`
- `{pedido_id}`
- `{pedido_total}`
- `{pedido_status}`

### Cliente e follow-up

- `{empresa_nome}`
- `{cliente_nome}`
- `{cliente_email}`
- `{cliente_telefone}`

## Links entregues

### Compartilhar catalogo

Botao em:

- `templates/catalogo/produto_list.html`

Fonte:

- `whatsapp.services.gerar_link_catalogo()`

### Compartilhar produto

Botoes em:

- `templates/catalogo/produto_list.html`
- `templates/catalogo/produto_detail.html`
- `templates/crm/workspace.html`

Fonte:

- `whatsapp.services.gerar_link_produto()`

### Compartilhar pedido

Botao em:

- `templates/vendas/pedido_detail.html`

Fonte:

- `whatsapp.services.gerar_link_pedido()`

### Mensagem pronta para cliente

Botoes em:

- `templates/crm/cliente_detail.html`
- `templates/crm/workspace.html`

Fonte:

- `whatsapp.services.gerar_link_cliente()`

### Mensagem pronta para follow-up

Botoes em:

- `templates/crm/cliente_detail.html`
- `templates/crm/workspace.html`

Fonte:

- `whatsapp.services.gerar_link_follow_up()`

## Seguranca e multiempresa

Os links sao gerados a partir dos objetos ja escopados pelas views existentes. A configuracao de mensagem e `OneToOne` por empresa.

Regras:

- catalogo e produto usam a empresa validada no endpoint de catalogo;
- cliente usa a empresa do cliente ja escopado por `EmpresaScopedQuerysetMixin`;
- pedido usa a empresa do pedido ja escopado por `PedidoDetailView`;
- nao ha bypass por `is_staff` ou `is_superuser`;
- nao ha envio automatico: o usuario revisa a mensagem no WhatsApp antes de enviar.

## Testes

Arquivo: `whatsapp/tests.py`

Cobertura:

- sanitizacao de telefone;
- encoding da mensagem em `wa.me`;
- geracao de links de catalogo, produto, pedido, cliente e follow-up;
- renderizacao dos botoes de catalogo, produto, pedido e cliente;
- bloqueio de pedido de outra empresa.

## Validacao

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

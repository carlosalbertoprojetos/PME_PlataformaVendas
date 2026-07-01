# Motor de eventos comerciais

Data: 2026-06-30

## Objetivo

Registrar eventos de dominio de forma sincrona e persistente para desacoplar CRM, catalogo, vendas, workspace, dashboard e futuras automacoes. Esta fase nao usa fila externa, RabbitMQ, Kafka, Celery, API de IA ou gateway.

## Componentes

- `eventos.events.DomainEvent`: evento base imutavel com tipo, empresa, entidade relacionada, payload auditavel e vinculos operacionais.
- `eventos.dispatcher`: dispatcher sincrono em memoria com handlers por tipo e handlers globais.
- `eventos.models.EventLog`: registro persistente tenant-scoped por empresa.
- `eventos.receivers`: hooks dos models existentes para publicar eventos sem mudar regras de negocio.
- `eventos.handlers.automation_hook`: ponto vazio e explicito para automacoes futuras.

## Eventos registrados

- `cliente_criado`
- `lead_criado`
- `produto_criado`
- `pedido_criado`
- `pedido_confirmado`
- `oportunidade_criada`
- `oportunidade_atualizada`
- `proxima_acao_criada`
- `proxima_acao_concluida`
- `catalogo_compartilhado`

## Multiempresa

Todo `EventLog` possui `empresa` obrigatoria. A timeline e as consultas usam `EventLog.objects.da_empresa(empresa)` antes de filtrar cliente, oportunidade, pedido, produto ou acao. Eventos nao concedem permissao: as views continuam usando os mixins de tenant existentes.

## Timeline

A workspace comercial passa a buscar eventos em `EventLog` como fonte principal da timeline. Para nao perder contexto transicional de dados antigos, a tela ainda complementa a timeline com historico, pedidos, proximas acoes, WhatsApp e status atual quando nao houver evento equivalente.

## Catalogo compartilhado

O botao de compartilhar catalogo usa uma rota interna rastreavel:

`/empresas/<empresa_id>/catalogo/compartilhar/`

Essa rota registra `catalogo_compartilhado` e redireciona para o link `wa.me` configurado da empresa.

## Automacoes comerciais

O hook `eventos.handlers.automation_hook` agora executa o `AutomationRunner`.

O runner busca regras ativas por empresa e `evento_disparador`, valida condicoes declarativas, executa acoes sincronas e registra `AutomationExecutionLog`. A regra `evento + regra` e unica para evitar duplicidade.

Detalhes da fase estao em `docs/automacoes-comerciais.md`.

## Hooks futuros

Novas automacoes podem assinar eventos com:

```python
from eventos.dispatcher import register_event_handler

register_event_handler("pedido_confirmado", handler)
```

Os handlers executam de forma sincrona. Qualquer evolucao para fila externa deve ser uma fase separada.

# Motor de automacoes comerciais

Data: 2026-06-30

## Objetivo

Transformar eventos de dominio em acoes operacionais simples e auditaveis, sem Celery, RabbitMQ, Kafka, IA ou integracao externa. Tudo executa de forma sincrona a partir do dispatcher de eventos.

## Models

### AutomationRule

Campos:

- `nome`
- `empresa`
- `ativa`
- `evento_disparador`
- `prioridade`
- `conditions`
- `actions`

As regras sao filtradas por empresa e evento antes da execucao. A prioridade define a ordem crescente de execucao.

### AutomationExecutionLog

Registra toda tentativa de execucao:

- `evento`
- `regra`
- `resultado`: sucesso, falha ou ignorada
- `tempo_ms`
- `erro`
- `empresa`

Ha restricao unica para `evento + regra`, evitando execucao duplicada da mesma regra sobre o mesmo evento.

## Runner

Fluxo:

1. Recebe o `DomainEvent`.
2. Localiza o `EventLog` persistido correspondente.
3. Busca regras ativas da mesma empresa e do mesmo evento.
4. Valida condicoes.
5. Executa acoes em ordem.
6. Registra `AutomationExecutionLog`.

## Condicoes suportadas

- `pedido_confirmado`
- `cliente_sem_compra`
- `produto_sem_estoque`
- `lead_sem_contato`
- `oportunidade_parada`

Condicoes sao declaradas em JSON. Exemplo:

```json
[{"type": "cliente_sem_compra", "dias": 45}]
```

## Acoes suportadas

- `criar_proxima_acao`
- `criar_oportunidade`
- `enviar_whatsapp`
- `criar_notificacao`
- `registrar_timeline`
- `criar_tarefa`
- `atualizar_status`

`enviar_whatsapp` nao envia mensagem nem chama API externa nesta fase. A acao apenas registra um evento operacional auditavel.

## Dashboard

O dashboard principal da empresa mostra:

- automacoes executadas hoje;
- sucesso;
- falhas;
- tempo medio.

## Workspace

A workspace comercial mostra as automacoes executadas para o cliente ou oportunidade em exibicao, sempre filtradas por empresa.

## Multiempresa e auditoria

- Toda regra pertence a uma empresa.
- Toda execucao pertence a uma empresa.
- Regras de outra empresa nao sao avaliadas.
- Acoes criadas preservam os vinculos de cliente, oportunidade e pedido do evento.
- A execucao e idempotente por `evento + regra`.

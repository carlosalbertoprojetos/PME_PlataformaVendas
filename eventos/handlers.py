from eventos.models import EventLog


def persist_event_log(event):
    return EventLog.objects.create(
        empresa=event.empresa,
        tipo=event.tipo,
        titulo=event.titulo_final(),
        descricao=event.descricao,
        entidade_tipo=event.entidade_tipo,
        entidade_id=event.entidade_id,
        cliente_id=event.cliente_id,
        lead_id=event.lead_id,
        oportunidade_id=event.oportunidade_id,
        pedido_id=event.pedido_id,
        produto_id=event.produto_id,
        proxima_acao_id=event.proxima_acao_id,
        payload=event.payload,
        ator=event.ator if getattr(event.ator, "is_authenticated", True) else None,
    )


def automation_hook(event):
    from eventos.automation import AutomationRunner

    return AutomationRunner().run(event)

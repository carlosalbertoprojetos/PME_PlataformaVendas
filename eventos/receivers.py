from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from catalogo.models import Produto
from crm.models import Cliente, Lead, Oportunidade, ProximaAcao
from eventos.dispatcher import dispatcher, dispatch_event
from eventos.events import DomainEvent, EventType
from eventos.handlers import automation_hook, persist_event_log
from vendas.models import Pedido


dispatcher.subscribe_all(persist_event_log)
dispatcher.subscribe_all(automation_hook)


def _old_status(model, instance):
    if not instance.pk:
        return None
    return model.objects.filter(pk=instance.pk).values_list("status", flat=True).first()


@receiver(pre_save, sender=Pedido)
@receiver(pre_save, sender=Oportunidade)
@receiver(pre_save, sender=ProximaAcao)
def guardar_status_anterior(sender, instance, **kwargs):
    instance._eventos_status_anterior = _old_status(sender, instance)


@receiver(post_save, sender=Cliente)
def cliente_criado(sender, instance, created, **kwargs):
    if not created:
        return
    dispatch_event(
        DomainEvent(
            tipo=EventType.CLIENTE_CRIADO,
            empresa=instance.empresa,
            descricao=f"Cliente {instance.nome} criado.",
            entidade_tipo="cliente",
            entidade_id=instance.id,
            cliente_id=instance.id,
            payload={"nome": instance.nome},
        )
    )


@receiver(post_save, sender=Lead)
def lead_criado(sender, instance, created, **kwargs):
    if not created:
        return
    dispatch_event(
        DomainEvent(
            tipo=EventType.LEAD_CRIADO,
            empresa=instance.empresa,
            descricao=f"Lead {instance.nome} criado.",
            entidade_tipo="lead",
            entidade_id=instance.id,
            lead_id=instance.id,
            cliente_id=instance.cliente_convertido_id,
            payload={"nome": instance.nome, "status": instance.status},
        )
    )


@receiver(post_save, sender=Produto)
def produto_criado(sender, instance, created, **kwargs):
    if not created:
        return
    dispatch_event(
        DomainEvent(
            tipo=EventType.PRODUTO_CRIADO,
            empresa=instance.empresa,
            descricao=f"Produto {instance.nome} criado.",
            entidade_tipo="produto",
            entidade_id=instance.id,
            produto_id=instance.id,
            payload={"nome": instance.nome, "preco": str(instance.preco)},
        )
    )


@receiver(post_save, sender=Pedido)
def pedido_salvo(sender, instance, created, **kwargs):
    status_anterior = getattr(instance, "_eventos_status_anterior", None)
    if created:
        dispatch_event(
            DomainEvent(
                tipo=EventType.PEDIDO_CRIADO,
                empresa=instance.empresa,
                descricao=f"Pedido #{instance.id} criado.",
                entidade_tipo="pedido",
                entidade_id=instance.id,
                cliente_id=instance.cliente_id,
                oportunidade_id=instance.oportunidade_id,
                pedido_id=instance.id,
                payload={"status": instance.status, "valor_total": str(instance.valor_total)},
            )
        )
    if instance.status == Pedido.Status.CONFIRMADO and status_anterior != Pedido.Status.CONFIRMADO:
        dispatch_event(
            DomainEvent(
                tipo=EventType.PEDIDO_CONFIRMADO,
                empresa=instance.empresa,
                descricao=f"Pedido #{instance.id} confirmado.",
                entidade_tipo="pedido",
                entidade_id=instance.id,
                cliente_id=instance.cliente_id,
                oportunidade_id=instance.oportunidade_id,
                pedido_id=instance.id,
                payload={"valor_total": str(instance.valor_total)},
            )
        )


@receiver(post_save, sender=Oportunidade)
def oportunidade_salva(sender, instance, created, **kwargs):
    if created:
        dispatch_event(
            DomainEvent(
                tipo=EventType.OPORTUNIDADE_CRIADA,
                empresa=instance.empresa,
                descricao=f"Oportunidade {instance.titulo} criada.",
                entidade_tipo="oportunidade",
                entidade_id=instance.id,
                cliente_id=instance.cliente_id,
                oportunidade_id=instance.id,
                payload={"status": instance.status, "valor_estimado": str(instance.valor_estimado)},
            )
        )
        return

    status_anterior = getattr(instance, "_eventos_status_anterior", None)
    dispatch_event(
        DomainEvent(
            tipo=EventType.OPORTUNIDADE_ATUALIZADA,
            empresa=instance.empresa,
            descricao=f"{instance.titulo} - {instance.get_status_display()}",
            entidade_tipo="oportunidade",
            entidade_id=instance.id,
            cliente_id=instance.cliente_id,
            oportunidade_id=instance.id,
            payload={
                "status_anterior": status_anterior,
                "status": instance.status,
                "valor_estimado": str(instance.valor_estimado),
            },
        )
    )


@receiver(post_save, sender=ProximaAcao)
def proxima_acao_salva(sender, instance, created, **kwargs):
    status_anterior = getattr(instance, "_eventos_status_anterior", None)
    if created:
        dispatch_event(
            DomainEvent(
                tipo=EventType.PROXIMA_ACAO_CRIADA,
                empresa=instance.empresa,
                descricao=instance.descricao,
                entidade_tipo="proxima_acao",
                entidade_id=instance.id,
                cliente_id=instance.cliente_id,
                oportunidade_id=instance.oportunidade_id,
                pedido_id=instance.pedido_id,
                proxima_acao_id=instance.id,
                payload={"status": instance.status, "data_prevista": str(instance.data_prevista)},
            )
        )
    if (
        instance.status == ProximaAcao.Status.CONCLUIDA
        and status_anterior != ProximaAcao.Status.CONCLUIDA
    ):
        dispatch_event(
            DomainEvent(
                tipo=EventType.PROXIMA_ACAO_CONCLUIDA,
                empresa=instance.empresa,
                descricao=instance.descricao,
                entidade_tipo="proxima_acao",
                entidade_id=instance.id,
                cliente_id=instance.cliente_id,
                oportunidade_id=instance.oportunidade_id,
                pedido_id=instance.pedido_id,
                proxima_acao_id=instance.id,
                payload={"data_prevista": str(instance.data_prevista)},
            )
        )

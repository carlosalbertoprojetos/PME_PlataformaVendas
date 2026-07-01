from time import perf_counter

from django.db import IntegrityError, transaction
from django.db.models import Avg, Count
from django.utils import timezone

from crm.models import Cliente, HistoricoContato, Lead, Oportunidade, ProximaAcao
from empresas.models import EmpresaMembership
from eventos.events import EventType
from eventos.models import AutomationExecutionLog, AutomationRule, EventLog
from vendas.models import Pedido


ACTION_CRIAR_PROXIMA_ACAO = "criar_proxima_acao"
ACTION_CRIAR_OPORTUNIDADE = "criar_oportunidade"
ACTION_ENVIAR_WHATSAPP = "enviar_whatsapp"
ACTION_CRIAR_NOTIFICACAO = "criar_notificacao"
ACTION_REGISTRAR_TIMELINE = "registrar_timeline"
ACTION_CRIAR_TAREFA = "criar_tarefa"
ACTION_ATUALIZAR_STATUS = "atualizar_status"

CONDITION_PEDIDO_CONFIRMADO = "pedido_confirmado"
CONDITION_CLIENTE_SEM_COMPRA = "cliente_sem_compra"
CONDITION_PRODUTO_SEM_ESTOQUE = "produto_sem_estoque"
CONDITION_LEAD_SEM_CONTATO = "lead_sem_contato"
CONDITION_OPORTUNIDADE_PARADA = "oportunidade_parada"


class AutomationRunner:
    def run(self, event):
        event_log = self._event_log_for(event)
        if event_log is None:
            return []

        regras = AutomationRule.objects.filter(
            empresa=event.empresa,
            ativa=True,
            evento_disparador=event.tipo,
        ).order_by("prioridade", "id")
        execucoes = []
        for regra in regras:
            execucao = self._run_rule(event, event_log, regra)
            if execucao:
                execucoes.append(execucao)
        return execucoes

    def _event_log_for(self, event):
        filtros = {
            "empresa": event.empresa,
            "tipo": event.tipo,
            "entidade_tipo": event.entidade_tipo,
            "entidade_id": event.entidade_id,
        }
        return EventLog.objects.filter(**filtros).order_by("-criado_em", "-id").first()

    def _run_rule(self, event, event_log, regra):
        inicio = perf_counter()
        try:
            with transaction.atomic():
                execucao, criada = AutomationExecutionLog.objects.get_or_create(
                    empresa=event.empresa,
                    evento=event_log,
                    regra=regra,
                    defaults={"resultado": AutomationExecutionLog.Resultado.SUCESSO},
                )
                if not criada:
                    return execucao

                if not self._conditions_match(event, event_log, regra.conditions):
                    execucao.resultado = AutomationExecutionLog.Resultado.IGNORADA
                    execucao.tempo_ms = self._elapsed_ms(inicio)
                    execucao.save(update_fields=["resultado", "tempo_ms"])
                    return execucao

                for action in self._normalize_items(regra.actions):
                    self._execute_action(event, event_log, action)

                execucao.resultado = AutomationExecutionLog.Resultado.SUCESSO
                execucao.tempo_ms = self._elapsed_ms(inicio)
                execucao.save(update_fields=["resultado", "tempo_ms"])
                return execucao
        except Exception as exc:
            return self._registrar_falha(event, event_log, regra, inicio, exc)

    def _registrar_falha(self, event, event_log, regra, inicio, exc):
        try:
            execucao, _ = AutomationExecutionLog.objects.get_or_create(
                empresa=event.empresa,
                evento=event_log,
                regra=regra,
                defaults={"resultado": AutomationExecutionLog.Resultado.FALHA},
            )
            execucao.resultado = AutomationExecutionLog.Resultado.FALHA
            execucao.tempo_ms = self._elapsed_ms(inicio)
            execucao.erro = str(exc)[:1000]
            execucao.save(update_fields=["resultado", "tempo_ms", "erro"])
            return execucao
        except IntegrityError:
            return None

    def _conditions_match(self, event, event_log, conditions):
        for condition in self._normalize_items(conditions):
            if not self._condition_match(event, event_log, condition):
                return False
        return True

    def _condition_match(self, event, event_log, condition):
        tipo = self._item_type(condition)
        if tipo == CONDITION_PEDIDO_CONFIRMADO:
            return event.tipo == EventType.PEDIDO_CONFIRMADO
        if tipo == CONDITION_CLIENTE_SEM_COMPRA:
            return self._cliente_sem_compra(event, condition)
        if tipo == CONDITION_PRODUTO_SEM_ESTOQUE:
            return self._produto_sem_estoque(event, condition)
        if tipo == CONDITION_LEAD_SEM_CONTATO:
            return self._lead_sem_contato(event)
        if tipo == CONDITION_OPORTUNIDADE_PARADA:
            return self._oportunidade_parada(event, condition)
        return True

    def _execute_action(self, event, event_log, action):
        tipo = self._item_type(action)
        if tipo in {ACTION_CRIAR_PROXIMA_ACAO, ACTION_CRIAR_TAREFA}:
            return self._criar_proxima_acao(event, action)
        if tipo == ACTION_CRIAR_OPORTUNIDADE:
            return self._criar_oportunidade(event, action)
        if tipo == ACTION_ENVIAR_WHATSAPP:
            return self._registrar_evento_operacional(event, event_log, action, "automation_whatsapp")
        if tipo == ACTION_CRIAR_NOTIFICACAO:
            return self._registrar_evento_operacional(event, event_log, action, "automation_notificacao")
        if tipo == ACTION_REGISTRAR_TIMELINE:
            return self._registrar_evento_operacional(event, event_log, action, "automation_timeline")
        if tipo == ACTION_ATUALIZAR_STATUS:
            return self._atualizar_status(event, action)
        return None

    def _criar_proxima_acao(self, event, action):
        cliente_id = action.get("cliente_id") or event.cliente_id
        oportunidade_id = action.get("oportunidade_id") or event.oportunidade_id
        pedido_id = action.get("pedido_id") or event.pedido_id
        if not any([cliente_id, oportunidade_id, pedido_id]):
            return None

        vendedor = self._vendedor(event)
        if vendedor is None:
            return None

        descricao = action.get("descricao") or "Acao comercial automatica"
        data_prevista = timezone.localdate() + timezone.timedelta(days=action.get("dias", 0))
        filtros = {
            "empresa": event.empresa,
            "descricao": descricao,
            "data_prevista": data_prevista,
            "status": ProximaAcao.Status.PENDENTE,
            "cliente_id": cliente_id,
            "oportunidade_id": oportunidade_id,
            "pedido_id": pedido_id,
        }
        if ProximaAcao.objects.filter(**filtros).exists():
            return None
        return ProximaAcao.objects.create(
            empresa=event.empresa,
            cliente_id=cliente_id,
            oportunidade_id=oportunidade_id,
            pedido_id=pedido_id,
            vendedor=vendedor,
            descricao=descricao,
            data_prevista=data_prevista,
        )

    def _criar_oportunidade(self, event, action):
        cliente_id = action.get("cliente_id") or event.cliente_id
        if not cliente_id:
            return None
        vendedor = self._vendedor(event)
        if vendedor is None:
            return None
        titulo = action.get("titulo") or "Oportunidade automatica"
        if Oportunidade.objects.filter(
            empresa=event.empresa,
            cliente_id=cliente_id,
            titulo=titulo,
            status=Oportunidade.Status.ABERTA,
        ).exists():
            return None
        return Oportunidade.objects.create(
            empresa=event.empresa,
            cliente_id=cliente_id,
            vendedor=vendedor,
            titulo=titulo,
            valor_estimado=action.get("valor_estimado") or 0,
        )

    def _registrar_evento_operacional(self, event, event_log, action, tipo):
        titulo = action.get("titulo") or "Automacao comercial"
        descricao = action.get("descricao") or f"Automacao executada a partir de {event_log.titulo}."
        return EventLog.objects.create(
            empresa=event.empresa,
            tipo=tipo,
            titulo=titulo,
            descricao=descricao,
            entidade_tipo=event.entidade_tipo,
            entidade_id=event.entidade_id,
            cliente_id=event.cliente_id,
            lead_id=event.lead_id,
            oportunidade_id=event.oportunidade_id,
            pedido_id=event.pedido_id,
            produto_id=event.produto_id,
            proxima_acao_id=event.proxima_acao_id,
            payload={"evento_origem_id": event_log.id, "acao": self._item_type(action)},
        )

    def _atualizar_status(self, event, action):
        entidade = action.get("entidade") or event.entidade_tipo
        status = action.get("status")
        if not status:
            return None
        if entidade == "oportunidade" and event.oportunidade_id:
            oportunidade = Oportunidade.objects.da_empresa(event.empresa).filter(
                pk=event.oportunidade_id
            ).first()
            if oportunidade and oportunidade.status != status:
                oportunidade.status = status
                oportunidade.save(update_fields=["status", "atualizado_em"])
                return oportunidade
        if entidade == "pedido" and event.pedido_id:
            pedido = Pedido.objects.da_empresa(event.empresa).filter(pk=event.pedido_id).first()
            if pedido and pedido.status != status:
                pedido.status = status
                pedido.save(update_fields=["status", "atualizado_em"])
                return pedido
        return None

    def _cliente_sem_compra(self, event, condition):
        if not event.cliente_id:
            return False
        dias = condition.get("dias", 45)
        data_limite = timezone.now() - timezone.timedelta(days=dias)
        return not Pedido.objects.da_empresa(event.empresa).confirmados().filter(
            cliente_id=event.cliente_id,
            criado_em__gte=data_limite,
        ).exists()

    def _produto_sem_estoque(self, event, condition):
        estoque = event.payload.get("estoque", condition.get("estoque"))
        return estoque is not None and int(estoque) <= 0

    def _lead_sem_contato(self, event):
        if not event.lead_id:
            return False
        lead = Lead.objects.da_empresa(event.empresa).filter(pk=event.lead_id).first()
        if lead is None:
            return False
        return not HistoricoContato.objects.da_empresa(event.empresa).filter(lead=lead).exists()

    def _oportunidade_parada(self, event, condition):
        if not event.oportunidade_id:
            return False
        dias = condition.get("dias", 7)
        data_limite = timezone.now() - timezone.timedelta(days=dias)
        return Oportunidade.objects.da_empresa(event.empresa).filter(
            pk=event.oportunidade_id,
            status=Oportunidade.Status.ABERTA,
            atualizado_em__lte=data_limite,
        ).exists()

    def _vendedor(self, event):
        if getattr(event.ator, "is_authenticated", False):
            return event.ator
        membership = EmpresaMembership.objects.filter(
            empresa=event.empresa,
            ativo=True,
        ).select_related("usuario").first()
        return membership.usuario if membership else None

    def _normalize_items(self, items):
        if not items:
            return []
        if isinstance(items, dict):
            return [items]
        return items

    def _item_type(self, item):
        if isinstance(item, str):
            return item
        return item.get("type") or item.get("tipo")

    def _elapsed_ms(self, inicio):
        return max(0, int((perf_counter() - inicio) * 1000))


def metricas_automacoes_empresa(empresa):
    hoje = timezone.localdate()
    logs = AutomationExecutionLog.objects.filter(empresa=empresa, criado_em__date=hoje)
    agregados = logs.aggregate(total=Count("id"), tempo_medio=Avg("tempo_ms"))
    return {
        "executadas_hoje": agregados["total"] or 0,
        "sucesso": logs.filter(resultado=AutomationExecutionLog.Resultado.SUCESSO).count(),
        "falhas": logs.filter(resultado=AutomationExecutionLog.Resultado.FALHA).count(),
        "tempo_medio_ms": int(agregados["tempo_medio"] or 0),
    }

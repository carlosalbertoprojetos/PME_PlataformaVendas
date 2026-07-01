from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Max, Q, Sum
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from catalogo.models import Produto
from billing.services import pode_criar_recurso, recurso_disponivel
from core.mixins import EmpresaRequiredMixin, EmpresaScopedQuerysetMixin
from core.tenant import user_can_access_empresa
from crm.forms import (
    ClienteForm,
    HistoricoContatoForm,
    LeadForm,
    OportunidadeForm,
    ProximaAcaoForm,
)
from crm.models import Cliente, HistoricoContato, Lead, Oportunidade, ProximaAcao
from eventos.models import AutomationExecutionLog
from eventos.models import EventLog
from services.inteligencia_comercial import gerar_recomendacoes_comerciais, score_oportunidade
from vendas.models import Pedido


WORKSPACE_LIMITE_PEDIDOS = 5
WORKSPACE_LIMITE_TIMELINE = 20
WORKSPACE_LIMITE_EVENTOS_POR_TIPO = 10
WORKSPACE_LIMITE_AUTOMACOES = 10


class EmpresaFormMixin(EmpresaRequiredMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = self.empresa
        kwargs["usuario"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context


class ClienteListView(EmpresaScopedQuerysetMixin, ListView):
    model = Cliente
    template_name = "crm/cliente_list.html"
    context_object_name = "clientes"

    def get_queryset(self):
        return super().get_queryset().filter(ativo=True)


class ClienteCreateView(EmpresaFormMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "crm/form.html"

    def form_valid(self, form):
        permitido, limite = pode_criar_recurso(self.empresa, "clientes")
        if not permitido:
            form.add_error(None, limite.aviso + " Faça upgrade do plano.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("crm:cliente-detail", args=[self.empresa.id, self.object.id])


class ClienteDetailView(EmpresaScopedQuerysetMixin, DetailView):
    model = Cliente
    template_name = "crm/cliente_detail.html"
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        context["oportunidades"] = self.object.oportunidades.filter(empresa=self.empresa)
        context["historicos"] = self.object.historicos_contato.filter(empresa=self.empresa)
        return context


class LeadListView(EmpresaScopedQuerysetMixin, ListView):
    model = Lead
    template_name = "crm/lead_list.html"
    context_object_name = "leads"


class LeadCreateView(EmpresaFormMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "crm/form.html"

    def form_valid(self, form):
        permitido, limite = pode_criar_recurso(self.empresa, "leads")
        if not permitido:
            form.add_error(None, limite.aviso + " Faça upgrade do plano.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("crm:lead-detail", args=[self.empresa.id, self.object.id])


class LeadDetailView(EmpresaScopedQuerysetMixin, DetailView):
    model = Lead
    template_name = "crm/lead_detail.html"
    context_object_name = "lead"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        context["historicos"] = self.object.historicos_contato.filter(empresa=self.empresa)
        return context


class LeadConvertView(EmpresaScopedQuerysetMixin, SingleObjectMixin, View):
    model = Lead

    def post(self, request, *args, **kwargs):
        lead = self.get_object()
        cliente = lead.converter_em_cliente()
        messages.success(request, "Lead convertido em cliente.")
        return redirect("crm:cliente-detail", empresa_id=self.empresa.id, pk=cliente.id)


class OportunidadeListView(EmpresaScopedQuerysetMixin, ListView):
    model = Oportunidade
    template_name = "crm/oportunidade_list.html"
    context_object_name = "oportunidades"

    def get_queryset(self):
        return super().get_queryset().select_related("cliente", "vendedor")


class OportunidadeCreateView(EmpresaFormMixin, CreateView):
    model = Oportunidade
    form_class = OportunidadeForm
    template_name = "crm/form.html"

    def form_valid(self, form):
        permitido, limite = pode_criar_recurso(self.empresa, "oportunidades")
        if not permitido:
            form.add_error(None, limite.aviso + " Faça upgrade do plano.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("crm:oportunidade-detail", args=[self.empresa.id, self.object.id])


class OportunidadeDetailView(EmpresaScopedQuerysetMixin, DetailView):
    model = Oportunidade
    template_name = "crm/oportunidade_detail.html"
    context_object_name = "oportunidade"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        context["proximas_acoes"] = self.object.proximas_acoes.filter(empresa=self.empresa)
        return context


class HistoricoContatoCreateView(EmpresaFormMixin, CreateView):
    model = HistoricoContato
    form_class = HistoricoContatoForm
    template_name = "crm/form.html"

    def get_success_url(self):
        cliente = self.object.cliente
        lead = self.object.lead
        if cliente:
            return reverse("crm:cliente-detail", args=[self.empresa.id, cliente.id])
        return reverse("crm:lead-detail", args=[self.empresa.id, lead.id])


class ProximaAcaoListView(EmpresaScopedQuerysetMixin, ListView):
    model = ProximaAcao
    template_name = "crm/proxima_acao_list.html"
    context_object_name = "proximas_acoes"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "cliente",
            "oportunidade",
            "pedido",
            "vendedor",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.localdate()
        acoes = list(context["proximas_acoes"])
        pendentes = [acao for acao in acoes if acao.status == ProximaAcao.Status.PENDENTE]
        context["acoes_hoje"] = [acao for acao in pendentes if acao.data_prevista == hoje]
        context["acoes_atrasadas"] = [acao for acao in pendentes if acao.data_prevista < hoje]
        context["acoes_proximas"] = [acao for acao in pendentes if acao.data_prevista > hoje]
        context["acoes_concluidas"] = [
            acao for acao in acoes if acao.status == ProximaAcao.Status.CONCLUIDA
        ]
        return context


class ProximaAcaoCreateView(EmpresaFormMixin, CreateView):
    model = ProximaAcao
    form_class = ProximaAcaoForm
    template_name = "crm/form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["vendedor"] = self.request.user.id
        initial["data_prevista"] = timezone.localdate()
        cliente_id = self.request.GET.get("cliente")
        oportunidade_id = self.request.GET.get("oportunidade")
        pedido_id = self.request.GET.get("pedido")

        if cliente_id and Cliente.objects.da_empresa(self.empresa).filter(pk=cliente_id).exists():
            initial["cliente"] = cliente_id
        if oportunidade_id:
            oportunidade = Oportunidade.objects.da_empresa(self.empresa).filter(
                pk=oportunidade_id
            ).first()
            if oportunidade:
                initial["oportunidade"] = oportunidade.id
                initial.setdefault("cliente", oportunidade.cliente_id)
        if pedido_id:
            pedido = Pedido.objects.da_empresa(self.empresa).filter(pk=pedido_id).first()
            if pedido:
                initial["pedido"] = pedido.id
                initial.setdefault("cliente", pedido.cliente_id)
                if pedido.oportunidade_id:
                    initial.setdefault("oportunidade", pedido.oportunidade_id)
        return initial

    def form_valid(self, form):
        if form.instance.oportunidade_id and not form.instance.cliente_id:
            form.instance.cliente = form.instance.oportunidade.cliente
        if form.instance.pedido_id and not form.instance.cliente_id:
            form.instance.cliente = form.instance.pedido.cliente
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("crm:proxima-acao-list", args=[self.empresa.id])


class ProximaAcaoUpdateView(EmpresaFormMixin, EmpresaScopedQuerysetMixin, UpdateView):
    model = ProximaAcao
    form_class = ProximaAcaoForm
    template_name = "crm/form.html"

    def get_success_url(self):
        return reverse("crm:proxima-acao-list", args=[self.empresa.id])


class ProximaAcaoConcluirView(EmpresaScopedQuerysetMixin, SingleObjectMixin, View):
    model = ProximaAcao

    def post(self, request, *args, **kwargs):
        acao = self.get_object()
        acao.status = ProximaAcao.Status.CONCLUIDA
        acao.save(update_fields=["status", "atualizada_em"])
        return redirect("crm:proxima-acao-list", empresa_id=self.empresa.id)


class WorkspaceAccessMixin(LoginRequiredMixin):
    raise_exception = True
    empresa = None

    def require_workspace_access(self, empresa):
        if not user_can_access_empresa(self.request.user, empresa):
            raise Http404("Workspace nao encontrada.")
        self.empresa = empresa
        disponivel, mensagem = recurso_disponivel(empresa, "workspace_comercial")
        if not disponivel:
            raise Http404(mensagem)

    def get_workspace_context(self, cliente, oportunidade=None):
        oportunidades = (
            Oportunidade.objects.da_empresa(self.empresa)
            .filter(cliente=cliente)
            .select_related("cliente", "vendedor")
        )
        oportunidade_atual = oportunidade or oportunidades.filter(
            status=Oportunidade.Status.ABERTA
        ).first()
        historicos = HistoricoContato.objects.da_empresa(self.empresa).filter(cliente=cliente)
        pedidos = (
            Pedido.objects.da_empresa(self.empresa)
            .filter(cliente=cliente)
            .select_related("cliente", "oportunidade", "vendedor")
            .prefetch_related("itens__produto")
        )
        pedidos_anteriores = pedidos[:WORKSPACE_LIMITE_PEDIDOS]
        ultima_compra = pedidos.confirmados().aggregate(ultima=Max("criado_em"))["ultima"]
        ticket_medio = pedidos.confirmados().aggregate(media=Avg("valor_total"))["media"]
        ultimo_contato = historicos.aggregate(ultimo=Max("realizado_em"))["ultimo"]
        proximas_acoes = ProximaAcao.objects.da_empresa(self.empresa).filter(
            Q(cliente=cliente) | Q(oportunidade__cliente=cliente) | Q(pedido__cliente=cliente),
            status=ProximaAcao.Status.PENDENTE,
        ).select_related("cliente", "oportunidade", "pedido", "vendedor")
        if oportunidade_atual:
            proximas_acoes = proximas_acoes.filter(
                Q(oportunidade=oportunidade_atual)
                | Q(cliente=cliente)
                | Q(pedido__oportunidade=oportunidade_atual)
            )
        hoje = timezone.localdate()
        proximas_acoes_lista = list(proximas_acoes)
        acoes_hoje = [acao for acao in proximas_acoes_lista if acao.data_prevista == hoje]
        acoes_atrasadas = [acao for acao in proximas_acoes_lista if acao.data_prevista < hoje]
        acoes_agendadas = [acao for acao in proximas_acoes_lista if acao.data_prevista > hoje]
        recomendacoes = gerar_recomendacoes_comerciais(self.empresa)
        recomendacoes_cliente = self._filtrar_recomendacoes_workspace(
            recomendacoes,
            cliente,
            oportunidade_atual,
        )
        produtos_mais_comprados = (
            Produto.objects.da_empresa(self.empresa)
            .filter(pedido_itens__pedido__cliente=cliente)
            .values("id", "nome")
            .annotate(quantidade=Sum("pedido_itens__quantidade"))
            .order_by("-quantidade", "nome")[:5]
        )
        timeline = self._montar_timeline(
            cliente=cliente,
            historicos=historicos,
            pedidos=pedidos,
            proximas_acoes=proximas_acoes_lista,
            oportunidade=oportunidade_atual,
        )

        return {
            "empresa": self.empresa,
            "cliente": cliente,
            "ultimo_contato": ultimo_contato,
            "ultima_compra": ultima_compra,
            "ticket_medio": ticket_medio,
            "produtos": Produto.objects.da_empresa(self.empresa).ativos(),
            "produtos_mais_comprados": produtos_mais_comprados,
            "produtos_sugeridos": (
                recomendacoes["produtos_alta_saida"] + recomendacoes["produtos_risco_ruptura"]
            ),
            "oportunidades": oportunidades,
            "oportunidade": oportunidade_atual,
            "score_comercial": (
                score_oportunidade(oportunidade_atual) if oportunidade_atual else None
            ),
            "probabilidade": "Nao definida",
            "dias_parada": (
                (timezone.now() - oportunidade_atual.atualizado_em).days
                if oportunidade_atual else None
            ),
            "recomendacoes_workspace": recomendacoes_cliente,
            "alertas_workspace": recomendacoes_cliente,
            "historicos": historicos,
            "proximas_acoes": proximas_acoes_lista,
            "acoes_hoje": acoes_hoje,
            "acoes_atrasadas": acoes_atrasadas,
            "acoes_agendadas": acoes_agendadas,
            "carrinho_itens": [],
            "pedidos_anteriores": pedidos_anteriores,
            "timeline": timeline,
            "automacoes_cliente": self._automacoes_cliente(cliente, oportunidade_atual),
            "criar_proxima_acao_url": self._criar_proxima_acao_url(
                cliente=cliente,
                oportunidade=oportunidade_atual,
            ),
        }

    def _criar_proxima_acao_url(self, cliente, oportunidade=None, pedido=None):
        params = [f"cliente={cliente.id}"]
        if oportunidade:
            params.append(f"oportunidade={oportunidade.id}")
        if pedido:
            params.append(f"pedido={pedido.id}")
        return reverse("crm:proxima-acao-create", args=[self.empresa.id]) + "?" + "&".join(params)

    def _filtrar_recomendacoes_workspace(self, recomendacoes, cliente, oportunidade):
        itens = []
        for grupo in recomendacoes.values():
            for item in grupo:
                if item.get("cliente") == cliente:
                    itens.append(item)
                    continue
                if oportunidade and item.get("oportunidade") == oportunidade:
                    itens.append(item)
        vistos = set()
        unicos = []
        for item in itens:
            chave = (item.get("tipo"), item.get("titulo"), item.get("motivo"))
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(item)
        return unicos

    def _montar_timeline(self, cliente, historicos, pedidos, proximas_acoes, oportunidade):
        eventos_logs = EventLog.objects.da_empresa(self.empresa).para_cliente(cliente)
        if oportunidade:
            eventos_logs = eventos_logs | EventLog.objects.da_empresa(self.empresa).para_oportunidade(
                oportunidade
            )
        eventos_logs = eventos_logs.distinct().order_by("-criado_em", "-id")[
            :WORKSPACE_LIMITE_TIMELINE
        ]
        eventos = [
            {
                "data": evento.criado_em,
                "tipo": evento.titulo,
                "texto": evento.descricao,
            }
            for evento in eventos_logs
        ]
        for historico in historicos[:WORKSPACE_LIMITE_EVENTOS_POR_TIPO]:
            eventos.append(
                {
                    "data": historico.realizado_em,
                    "tipo": "Historico",
                    "texto": historico.resumo,
                }
            )
        for pedido in pedidos[:WORKSPACE_LIMITE_EVENTOS_POR_TIPO]:
            eventos.append(
                {
                    "data": pedido.criado_em,
                    "tipo": "Pedido",
                    "texto": f"Pedido #{pedido.id} - {pedido.get_status_display()} - {pedido.valor_total}",
                }
            )
        for acao in proximas_acoes[:WORKSPACE_LIMITE_EVENTOS_POR_TIPO]:
            eventos.append(
                {
                    "data": timezone.make_aware(
                        timezone.datetime.combine(acao.data_prevista, timezone.datetime.min.time())
                    ),
                    "tipo": "Follow-up",
                    "texto": acao.descricao,
                }
            )
        if oportunidade:
            tem_status_evento = any(evento["tipo"] == "Mudanca de status" for evento in eventos)
            if tem_status_evento:
                return sorted(eventos, key=lambda item: item["data"], reverse=True)[
                    :WORKSPACE_LIMITE_TIMELINE
                ]
            eventos.append(
                {
                    "data": oportunidade.atualizado_em,
                    "tipo": "Mudanca de status",
                    "texto": f"{oportunidade.titulo} - {oportunidade.get_status_display()}",
                }
            )
        eventos.append(
            {
                "data": timezone.now(),
                "tipo": "WhatsApp",
                "texto": "Acoes de WhatsApp disponiveis na workspace.",
            }
        )
        return sorted(eventos, key=lambda item: item["data"], reverse=True)[
            :WORKSPACE_LIMITE_TIMELINE
        ]

    def _automacoes_cliente(self, cliente, oportunidade=None):
        eventos = EventLog.objects.da_empresa(self.empresa).para_cliente(cliente)
        if oportunidade:
            eventos = eventos | EventLog.objects.da_empresa(self.empresa).para_oportunidade(
                oportunidade
            )
        return (
            AutomationExecutionLog.objects.filter(
                empresa=self.empresa,
                evento__in=eventos,
            )
            .select_related("regra", "evento")
            .order_by("-criado_em", "-id")[:WORKSPACE_LIMITE_AUTOMACOES]
        )


class ClienteWorkspaceView(WorkspaceAccessMixin, TemplateView):
    template_name = "crm/workspace.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = Cliente.objects.select_related("empresa").filter(
            pk=kwargs["cliente_id"],
            ativo=True,
        ).first()
        if cliente is None:
            raise Http404("Cliente nao encontrado.")
        self.require_workspace_access(cliente.empresa)
        context.update(self.get_workspace_context(cliente))
        return context


class OportunidadeWorkspaceView(WorkspaceAccessMixin, TemplateView):
    template_name = "crm/workspace.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        oportunidade = (
            Oportunidade.objects.select_related("empresa", "cliente", "vendedor")
            .filter(pk=kwargs["id"])
            .first()
        )
        if oportunidade is None:
            raise Http404("Oportunidade nao encontrada.")
        self.require_workspace_access(oportunidade.empresa)
        context.update(self.get_workspace_context(oportunidade.cliente, oportunidade))
        return context

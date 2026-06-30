from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from catalogo.models import Produto
from billing.services import pode_criar_recurso
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
            form.add_error(None, limite.aviso)
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
        return super().get_queryset().select_related("oportunidade", "vendedor")


class ProximaAcaoCreateView(EmpresaFormMixin, CreateView):
    model = ProximaAcao
    form_class = ProximaAcaoForm
    template_name = "crm/form.html"

    def get_success_url(self):
        return reverse("crm:proxima-acao-list", args=[self.empresa.id])


class WorkspaceAccessMixin(LoginRequiredMixin):
    raise_exception = True
    empresa = None

    def require_workspace_access(self, empresa):
        if not user_can_access_empresa(self.request.user, empresa):
            raise Http404("Workspace nao encontrada.")
        self.empresa = empresa

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
        proximas_acoes = ProximaAcao.objects.da_empresa(self.empresa).filter(
            oportunidade__cliente=cliente,
            status=ProximaAcao.Status.PENDENTE,
        ).select_related("oportunidade", "vendedor")
        if oportunidade_atual:
            proximas_acoes = proximas_acoes.filter(oportunidade=oportunidade_atual)

        return {
            "empresa": self.empresa,
            "cliente": cliente,
            "produtos": Produto.objects.da_empresa(self.empresa).ativos(),
            "oportunidades": oportunidades,
            "oportunidade": oportunidade_atual,
            "historicos": historicos,
            "proximas_acoes": proximas_acoes,
            "carrinho_itens": [],
            "pedidos_anteriores": [],
        }


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

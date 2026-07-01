from django.views.generic import TemplateView

from billing.services import avaliar_limites, get_assinatura_empresa
from core.mixins import EmpresaRequiredMixin
from crm.models import ProximaAcao
from dashboard.services import calcular_kpis_comerciais
from eventos.automation import metricas_automacoes_empresa
from services.inteligencia_comercial import (
    gerar_recomendacoes_comerciais,
    listar_recomendacoes_acionaveis,
)
from services.onboarding import gerar_onboarding_empresa

LIMITE_PROXIMAS_ACOES_DASHBOARD = 5


class DashboardEmpresaView(EmpresaRequiredMixin, TemplateView):
    template_name = "dashboard/empresa.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo_dashboard"] = "Dashboard empresa"
        context["kpis"] = calcular_kpis_comerciais(self.empresa)
        context["automacoes"] = metricas_automacoes_empresa(self.empresa)
        context["onboarding"] = gerar_onboarding_empresa(self.empresa)
        context["recomendacoes_acionaveis"] = listar_recomendacoes_acionaveis(self.empresa)
        context["assinatura"] = get_assinatura_empresa(self.empresa)
        context["limites"] = avaliar_limites(self.empresa)
        context["proximas_acoes_executivas"] = (
            ProximaAcao.objects.da_empresa(self.empresa)
            .filter(status=ProximaAcao.Status.PENDENTE)
            .select_related("cliente", "oportunidade", "pedido", "vendedor")
            .order_by("data_prevista", "id")[:LIMITE_PROXIMAS_ACOES_DASHBOARD]
        )
        return context


class DashboardVendedorView(EmpresaRequiredMixin, TemplateView):
    template_name = "dashboard/vendedor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo_dashboard"] = "Dashboard vendedor"
        context["kpis"] = calcular_kpis_comerciais(self.empresa, vendedor=self.request.user)
        return context


class RecomendacoesComerciaisView(EmpresaRequiredMixin, TemplateView):
    template_name = "dashboard/recomendacoes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recomendacoes"] = gerar_recomendacoes_comerciais(self.empresa)
        return context

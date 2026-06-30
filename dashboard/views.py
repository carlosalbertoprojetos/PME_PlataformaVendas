from django.views.generic import TemplateView

from core.mixins import EmpresaRequiredMixin
from dashboard.services import calcular_kpis_comerciais
from services.inteligencia_comercial import gerar_recomendacoes_comerciais


class DashboardEmpresaView(EmpresaRequiredMixin, TemplateView):
    template_name = "dashboard/empresa.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo_dashboard"] = "Dashboard empresa"
        context["kpis"] = calcular_kpis_comerciais(self.empresa)
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

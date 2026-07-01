from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from billing.forms import AssinaturaAdminForm
from billing.services import avaliar_limites, get_assinatura_empresa
from core.mixins import EmpresaRoleRequiredMixin
from empresas.models import EmpresaMembership


class PlanoAdminView(EmpresaRoleRequiredMixin, TemplateView):
    template_name = "billing/plano_admin.html"
    allowed_roles = (EmpresaMembership.Papel.ADMIN,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assinatura = get_assinatura_empresa(self.empresa)
        context["assinatura"] = assinatura
        context["form"] = AssinaturaAdminForm(instance=assinatura)
        context["limites"] = avaliar_limites(self.empresa)
        return context

    def post(self, request, *args, **kwargs):
        self.empresa = self.get_empresa()
        assinatura = get_assinatura_empresa(self.empresa)
        form = AssinaturaAdminForm(request.POST, instance=assinatura)
        if form.is_valid():
            form.save()
            messages.success(request, "Plano atualizado.")
            return redirect("billing:plano-admin", empresa_id=self.empresa.id)
        return self.render_to_response(
            {
                "empresa": self.empresa,
                "assinatura": assinatura,
                "form": form,
                "limites": avaliar_limites(self.empresa),
            }
        )

    def get_empresa(self):
        return self.empresa

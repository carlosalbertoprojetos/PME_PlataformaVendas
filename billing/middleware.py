from billing.services import assinatura_bloqueada, avaliar_limites_leve
from core.tenant import user_can_access_empresa
from empresas.models import Empresa


class BillingLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.billing_limites = {}
        request.billing_bloqueio = None
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        empresa_id = view_kwargs.get("empresa_id")
        if empresa_id and request.user.is_authenticated:
            empresa = Empresa.objects.filter(pk=empresa_id, ativa=True).first()
            if empresa is not None and user_can_access_empresa(request.user, empresa):
                bloqueada, assinatura = assinatura_bloqueada(empresa)
                request.billing_bloqueio = assinatura if bloqueada else None
                request.billing_limites = avaliar_limites_leve(empresa)
        return None

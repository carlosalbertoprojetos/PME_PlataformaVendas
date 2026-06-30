from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from core.tenant import get_empresa_for_user_or_403, get_membership, scoped_queryset_for_user


class EmpresaRequiredMixin(LoginRequiredMixin):
    raise_exception = True
    empresa_url_kwarg = "empresa_id"
    empresa = None

    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_empresa_for_user_or_403(
            request.user,
            kwargs[self.empresa_url_kwarg],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context


class EmpresaScopedQuerysetMixin(EmpresaRequiredMixin):
    empresa_field = "empresa"

    def get_queryset(self):
        queryset = super().get_queryset()
        return scoped_queryset_for_user(queryset, self.request.user, self.empresa)


class EmpresaRoleRequiredMixin(EmpresaRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_empresa_for_user_or_403(
            request.user,
            kwargs[self.empresa_url_kwarg],
        )
        membership = get_membership(request.user, self.empresa)
        if self.allowed_roles and (membership is None or membership.papel not in self.allowed_roles):
            raise PermissionDenied("Papel sem permissao para esta acao.")
        return super(EmpresaRequiredMixin, self).dispatch(request, *args, **kwargs)

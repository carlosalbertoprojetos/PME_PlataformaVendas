from django.core.exceptions import PermissionDenied

from empresas.models import Empresa, EmpresaMembership


def get_membership(usuario, empresa):
    if not usuario.is_authenticated:
        return None

    return (
        EmpresaMembership.objects.select_related("empresa", "usuario")
        .filter(usuario=usuario, empresa=empresa, ativo=True, empresa__ativa=True)
        .first()
    )


def user_can_access_empresa(usuario, empresa):
    return get_membership(usuario, empresa) is not None


def get_empresa_for_user_or_403(usuario, empresa_id):
    empresa = Empresa.objects.filter(pk=empresa_id, ativa=True).first()
    if empresa is None or not user_can_access_empresa(usuario, empresa):
        raise PermissionDenied("Usuario sem acesso a esta empresa.")
    return empresa


def scoped_queryset_for_user(queryset, usuario, empresa):
    if not user_can_access_empresa(usuario, empresa):
        return queryset.none()
    return queryset.filter(empresa=empresa)

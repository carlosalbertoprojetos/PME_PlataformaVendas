from dataclasses import dataclass

from django.utils import timezone

from billing.models import Assinatura, Plano
from catalogo.models import Produto
from crm.models import Cliente
from empresas.models import EmpresaMembership
from vendas.models import Pedido


@dataclass(frozen=True)
class LimiteResultado:
    recurso: str
    usado: int
    limite: int
    atingido: bool
    percentual: int

    @property
    def aviso(self):
        if not self.atingido:
            return ""
        return f"Limite de {self.recurso} atingido ({self.usado}/{self.limite})."


def get_plano_padrao():
    plano = Plano.objects.filter(codigo=Plano.Codigo.START, ativo=True).first()
    if plano:
        return plano
    return Plano.objects.create(
        codigo=Plano.Codigo.START,
        nome="Start",
        preco_mensal="97.00",
        limite_usuarios=2,
        limite_clientes=100,
        limite_produtos=50,
        limite_pedidos_mes=100,
    )


def get_assinatura_empresa(empresa):
    assinatura = getattr(empresa, "assinatura", None)
    if assinatura:
        return assinatura
    return Assinatura.objects.create(
        empresa=empresa,
        plano=get_plano_padrao(),
        status=Assinatura.Status.TRIAL,
    )


def contar_uso(empresa):
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    return {
        "usuarios": EmpresaMembership.objects.filter(empresa=empresa, ativo=True).count(),
        "clientes": Cliente.objects.da_empresa(empresa).filter(ativo=True).count(),
        "produtos": Produto.objects.da_empresa(empresa).filter(ativo=True).count(),
        "pedidos_mes": Pedido.objects.da_empresa(empresa).filter(
            criado_em__date__gte=inicio_mes,
            criado_em__date__lte=hoje,
        ).count(),
    }


def avaliar_limites(empresa):
    assinatura = get_assinatura_empresa(empresa)
    uso = contar_uso(empresa)
    plano = assinatura.plano
    limites = {
        "usuarios": plano.limite_usuarios,
        "clientes": plano.limite_clientes,
        "produtos": plano.limite_produtos,
        "pedidos_mes": plano.limite_pedidos_mes,
    }
    return {
        recurso: _avaliar(recurso, uso[recurso], limite)
        for recurso, limite in limites.items()
    }


def _avaliar(recurso, usado, limite):
    percentual = 0 if limite == 0 else int((usado / limite) * 100)
    return LimiteResultado(
        recurso=recurso,
        usado=usado,
        limite=limite,
        atingido=usado >= limite,
        percentual=percentual,
    )


def pode_criar_recurso(empresa, recurso):
    limites = avaliar_limites(empresa)
    resultado = limites[recurso]
    return not resultado.atingido, resultado


def assinatura_bloqueada(empresa):
    assinatura = get_assinatura_empresa(empresa)
    return not assinatura.permite_uso, assinatura

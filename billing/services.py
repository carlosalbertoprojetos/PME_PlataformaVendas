from dataclasses import dataclass

from django.utils import timezone

from billing.models import Assinatura, Plano
from catalogo.models import Produto
from crm.models import Cliente, Lead, Oportunidade
from empresas.models import EmpresaMembership
from services.inteligencia_comercial import gerar_recomendacoes_comerciais
from vendas.models import Pedido

PERCENTUAL_AVISO_LIMITE = 80


@dataclass(frozen=True)
class LimiteResultado:
    recurso: str
    usado: int
    limite: int
    atingido: bool
    proximo_limite: bool
    percentual: int

    @property
    def aviso(self):
        if self.atingido:
            return f"Limite de {self.recurso} atingido ({self.usado}/{self.limite})."
        if self.proximo_limite:
            return f"Limite de {self.recurso} proximo ({self.usado}/{self.limite})."
        return ""

    @property
    def cta_upgrade(self):
        if self.atingido or self.proximo_limite:
            return "Fazer upgrade do plano"
        return ""


def get_plano_padrao():
    plano = Plano.objects.filter(codigo=Plano.Codigo.START, ativo=True).first()
    if plano:
        return plano
    return Plano.objects.create(
        codigo=Plano.Codigo.START,
        nome="Start",
        preco_mensal="97.00",
        limite_usuarios=2,
        limite_vendedores=2,
        limite_clientes=100,
        limite_leads=100,
        limite_produtos=50,
        limite_oportunidades=50,
        limite_pedidos_mes=100,
        limite_recomendacoes_comerciais=10,
        permite_workspace_comercial=True,
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


def contar_uso(empresa, incluir_recomendacoes=True):
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    return {
        "usuarios": EmpresaMembership.objects.filter(empresa=empresa, ativo=True).count(),
        "vendedores": EmpresaMembership.objects.filter(empresa=empresa, ativo=True).count(),
        "clientes": Cliente.objects.da_empresa(empresa).filter(ativo=True).count(),
        "leads": Lead.objects.da_empresa(empresa).exclude(status=Lead.Status.CONVERTIDO).count(),
        "clientes_leads": (
            Cliente.objects.da_empresa(empresa).filter(ativo=True).count()
            + Lead.objects.da_empresa(empresa).exclude(status=Lead.Status.CONVERTIDO).count()
        ),
        "produtos": Produto.objects.da_empresa(empresa).filter(ativo=True).count(),
        "oportunidades": Oportunidade.objects.da_empresa(empresa).filter(
            status=Oportunidade.Status.ABERTA
        ).count(),
        "pedidos_mes": Pedido.objects.da_empresa(empresa).filter(
            criado_em__date__gte=inicio_mes,
            criado_em__date__lte=hoje,
        ).count(),
        "recomendacoes_comerciais": (
            contar_recomendacoes_comerciais(empresa) if incluir_recomendacoes else 0
        ),
        "workspace_comercial": 1,
    }


def contar_recomendacoes_comerciais(empresa):
    recomendacoes = gerar_recomendacoes_comerciais(empresa)
    return sum(len(itens) for itens in recomendacoes.values())


def avaliar_limites(empresa, incluir_recomendacoes=True):
    assinatura = get_assinatura_empresa(empresa)
    uso = contar_uso(empresa, incluir_recomendacoes=incluir_recomendacoes)
    plano = assinatura.plano
    limites = {
        "usuarios": plano.limite_usuarios,
        "vendedores": plano.limite_vendedores,
        "clientes": plano.limite_clientes,
        "leads": plano.limite_leads,
        "clientes_leads": plano.limite_clientes + plano.limite_leads,
        "produtos": plano.limite_produtos,
        "oportunidades": plano.limite_oportunidades,
        "pedidos_mes": plano.limite_pedidos_mes,
        "recomendacoes_comerciais": plano.limite_recomendacoes_comerciais,
        "workspace_comercial": 1 if plano.permite_workspace_comercial else 0,
    }
    return {
        recurso: _avaliar(recurso, uso[recurso], limite)
        for recurso, limite in limites.items()
    }


def avaliar_limites_leve(empresa):
    return avaliar_limites(empresa, incluir_recomendacoes=False)


def _avaliar(recurso, usado, limite):
    if limite == 0:
        percentual = 100 if usado > 0 else 0
    else:
        percentual = int((usado / limite) * 100)
    return LimiteResultado(
        recurso=recurso,
        usado=usado,
        limite=limite,
        atingido=usado >= limite,
        proximo_limite=percentual >= PERCENTUAL_AVISO_LIMITE and usado < limite,
        percentual=percentual,
    )


def pode_criar_recurso(empresa, recurso):
    limites = avaliar_limites(empresa)
    resultado = limites[recurso]
    return not resultado.atingido, resultado


def recurso_disponivel(empresa, recurso):
    bloqueada, assinatura = assinatura_bloqueada(empresa)
    if bloqueada:
        return False, f"Assinatura {assinatura.get_status_display}. Faça upgrade para continuar."
    if recurso == "workspace_comercial" and not assinatura.plano.permite_workspace_comercial:
        return False, "Workspace comercial indisponivel no plano atual. Faça upgrade do plano."
    return True, ""


def assinatura_bloqueada(empresa):
    assinatura = get_assinatura_empresa(empresa)
    return not assinatura.permite_uso, assinatura

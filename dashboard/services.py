from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from crm.models import Cliente, Oportunidade
from vendas.models import Pedido, PedidoItem


def _month_start(today):
    return today.replace(day=1)


def calcular_kpis_comerciais(empresa, vendedor=None):
    hoje = timezone.localdate()
    inicio_mes = _month_start(hoje)

    pedidos_base = Pedido.objects.da_empresa(empresa)
    if vendedor is not None:
        pedidos_base = pedidos_base.filter(vendedor=vendedor)

    pedidos_confirmados_mes = pedidos_base.confirmados().filter(
        criado_em__date__gte=inicio_mes,
        criado_em__date__lte=hoje,
    )
    pedidos_confirmados_dia = pedidos_base.confirmados().filter(criado_em__date=hoje)

    agregados_mes = pedidos_confirmados_mes.aggregate(
        receita=Coalesce(Sum("valor_total"), Decimal("0.00")),
        ticket_medio=Coalesce(Avg("valor_total"), Decimal("0.00")),
    )

    itens = PedidoItem.objects.filter(
        pedido__in=pedidos_confirmados_mes,
        pedido__empresa=empresa,
    )
    produtos_mais_vendidos = (
        itens.values("produto__nome")
        .annotate(quantidade=Coalesce(Sum("quantidade"), 0))
        .order_by("-quantidade", "produto__nome")[:5]
    )

    vendedores_base = Pedido.objects.da_empresa(empresa).confirmados().filter(
        criado_em__date__gte=inicio_mes,
        criado_em__date__lte=hoje,
    )
    if vendedor is not None:
        vendedores_base = vendedores_base.filter(vendedor=vendedor)

    vendedores_maior_receita = (
        vendedores_base
        .values("vendedor__username")
        .annotate(receita=Coalesce(Sum("valor_total"), Decimal("0.00")))
        .order_by("-receita", "vendedor__username")[:5]
    )

    oportunidades = Oportunidade.objects.da_empresa(empresa).filter(
        status=Oportunidade.Status.ABERTA
    )
    if vendedor is not None:
        oportunidades = oportunidades.filter(vendedor=vendedor)

    return {
        "pedidos_do_dia": pedidos_confirmados_dia.count(),
        "receita_do_mes": agregados_mes["receita"],
        "ticket_medio": agregados_mes["ticket_medio"],
        "produtos_mais_vendidos": list(produtos_mais_vendidos),
        "pedidos_pendentes": pedidos_base.pendentes().count(),
        "clientes_ativos": Cliente.objects.da_empresa(empresa).filter(ativo=True).count(),
        "oportunidades_abertas": oportunidades.count(),
        "vendedores_maior_receita": list(vendedores_maior_receita),
    }

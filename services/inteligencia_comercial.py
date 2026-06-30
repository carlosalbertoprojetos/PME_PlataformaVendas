from datetime import timedelta

from django.db.models import Count, Max, Sum
from django.utils import timezone

from catalogo.models import Produto
from crm.models import Cliente, HistoricoContato, Oportunidade, ProximaAcao
from vendas.models import Pedido, PedidoItem


DIAS_SEM_RECOMPRA = 45
DIAS_FOLLOW_UP = 7
LIMITE_ALTA_SAIDA = 5
LIMITE_RISCO_RUPTURA = 10


def gerar_recomendacoes_comerciais(empresa):
    oportunidades = listar_scores_oportunidades(empresa)
    alta_saida = listar_produtos_alta_saida(empresa)
    risco_ruptura = listar_produtos_risco_ruptura(empresa)
    sem_recompra = listar_clientes_sem_recompra(empresa)
    follow_ups = listar_sugestoes_follow_up(empresa)
    alertas = gerar_alertas_comerciais(
        oportunidades=oportunidades,
        alta_saida=alta_saida,
        risco_ruptura=risco_ruptura,
        sem_recompra=sem_recompra,
        follow_ups=follow_ups,
    )
    return {
        "scores_oportunidade": oportunidades,
        "produtos_risco_ruptura": risco_ruptura,
        "clientes_sem_recompra": sem_recompra,
        "produtos_alta_saida": alta_saida,
        "sugestoes_follow_up": follow_ups,
        "alertas_comerciais": alertas,
    }


def listar_scores_oportunidades(empresa):
    oportunidades = (
        Oportunidade.objects.da_empresa(empresa)
        .filter(status=Oportunidade.Status.ABERTA)
        .select_related("cliente", "vendedor")
        .prefetch_related("proximas_acoes")
    )
    return [score_oportunidade(oportunidade) for oportunidade in oportunidades]


def score_oportunidade(oportunidade):
    score = 0
    motivos = []

    if oportunidade.valor_estimado >= 1000:
        score += 30
        motivos.append("valor estimado acima de 1000")
    elif oportunidade.valor_estimado > 0:
        score += 15
        motivos.append("valor estimado informado")

    if oportunidade.status == Oportunidade.Status.ABERTA:
        score += 25
        motivos.append("oportunidade aberta")

    if oportunidade.proximas_acoes.filter(status=ProximaAcao.Status.PENDENTE).exists():
        score += 25
        motivos.append("possui proxima acao pendente")
    else:
        motivos.append("sem proxima acao pendente")

    if HistoricoContato.objects.da_empresa(oportunidade.empresa).filter(
        cliente=oportunidade.cliente
    ).exists():
        score += 20
        motivos.append("cliente possui historico comercial")
    else:
        motivos.append("cliente sem historico comercial")

    return {
        "tipo": "score_oportunidade",
        "titulo": oportunidade.titulo,
        "score": min(score, 100),
        "motivo": "; ".join(motivos),
        "oportunidade": oportunidade,
        "cliente": oportunidade.cliente,
    }


def listar_produtos_alta_saida(empresa):
    inicio_mes = timezone.localdate().replace(day=1)
    itens = (
        PedidoItem.objects.filter(
            pedido__empresa=empresa,
            pedido__status=Pedido.Status.CONFIRMADO,
            pedido__criado_em__date__gte=inicio_mes,
        )
        .values("produto_id", "produto__nome")
        .annotate(quantidade=Sum("quantidade"))
        .filter(quantidade__gte=LIMITE_ALTA_SAIDA)
        .order_by("-quantidade", "produto__nome")
    )
    return [
        {
            "tipo": "produto_alta_saida",
            "titulo": item["produto__nome"],
            "quantidade": item["quantidade"],
            "motivo": f"vendeu {item['quantidade']} unidades confirmadas no mes",
            "produto_id": item["produto_id"],
        }
        for item in itens
    ]


def listar_produtos_risco_ruptura(empresa):
    inicio_mes = timezone.localdate().replace(day=1)
    itens = (
        PedidoItem.objects.filter(
            pedido__empresa=empresa,
            pedido__status=Pedido.Status.CONFIRMADO,
            pedido__criado_em__date__gte=inicio_mes,
            produto__ativo=True,
        )
        .values("produto_id", "produto__nome")
        .annotate(quantidade=Sum("quantidade"))
        .filter(quantidade__gte=LIMITE_RISCO_RUPTURA)
        .order_by("-quantidade", "produto__nome")
    )
    return [
        {
            "tipo": "risco_ruptura",
            "titulo": item["produto__nome"],
            "quantidade": item["quantidade"],
            "motivo": (
                f"alta saida de {item['quantidade']} unidades no mes e estoque ainda nao e controlado"
            ),
            "produto_id": item["produto_id"],
        }
        for item in itens
    ]


def listar_clientes_sem_recompra(empresa):
    data_limite = timezone.localdate() - timedelta(days=DIAS_SEM_RECOMPRA)
    clientes_com_pedido_recente = Pedido.objects.da_empresa(empresa).filter(
        status=Pedido.Status.CONFIRMADO,
        criado_em__date__gte=data_limite,
    ).values("cliente_id")
    clientes = (
        Cliente.objects.da_empresa(empresa)
        .filter(ativo=True, pedidos__status=Pedido.Status.CONFIRMADO)
        .exclude(id__in=clientes_com_pedido_recente)
        .annotate(ultimo_pedido=Max("pedidos__criado_em"))
        .order_by("ultimo_pedido", "nome")
    )
    return [
        {
            "tipo": "cliente_sem_recompra",
            "titulo": cliente.nome,
            "cliente": cliente,
            "ultimo_pedido": cliente.ultimo_pedido,
            "motivo": f"cliente sem pedido confirmado nos ultimos {DIAS_SEM_RECOMPRA} dias",
        }
        for cliente in clientes
    ]


def listar_sugestoes_follow_up(empresa):
    data_limite = timezone.now() - timedelta(days=DIAS_FOLLOW_UP)
    oportunidades = (
        Oportunidade.objects.da_empresa(empresa)
        .filter(status=Oportunidade.Status.ABERTA, criado_em__lte=data_limite)
        .select_related("cliente", "vendedor")
    )
    sugestoes = []
    for oportunidade in oportunidades:
        tem_acao_pendente = oportunidade.proximas_acoes.filter(
            status=ProximaAcao.Status.PENDENTE
        ).exists()
        if tem_acao_pendente:
            continue
        sugestoes.append(
            {
                "tipo": "follow_up",
                "titulo": oportunidade.titulo,
                "cliente": oportunidade.cliente,
                "oportunidade": oportunidade,
                "motivo": (
                    f"oportunidade aberta ha mais de {DIAS_FOLLOW_UP} dias sem proxima acao pendente"
                ),
            }
        )
    return sugestoes


def gerar_alertas_comerciais(
    oportunidades,
    alta_saida,
    risco_ruptura,
    sem_recompra,
    follow_ups,
):
    alertas = []
    for item in risco_ruptura:
        alertas.append(
            {
                "tipo": "alerta_ruptura",
                "titulo": item["titulo"],
                "severidade": "alta",
                "motivo": item["motivo"],
            }
        )
    for item in follow_ups:
        alertas.append(
            {
                "tipo": "alerta_follow_up",
                "titulo": item["titulo"],
                "severidade": "media",
                "motivo": item["motivo"],
            }
        )
    for item in oportunidades:
        if item["score"] >= 80:
            alertas.append(
                {
                    "tipo": "alerta_oportunidade_quente",
                    "titulo": item["titulo"],
                    "severidade": "alta",
                    "motivo": f"score {item['score']} por: {item['motivo']}",
                }
            )
    if sem_recompra:
        alertas.append(
            {
                "tipo": "alerta_recompra",
                "titulo": "Clientes sem recompra",
                "severidade": "media",
                "motivo": f"{len(sem_recompra)} cliente(s) sem recompra recente",
            }
        )
    if alta_saida:
        alertas.append(
            {
                "tipo": "alerta_alta_saida",
                "titulo": "Produtos com alta saida",
                "severidade": "baixa",
                "motivo": f"{len(alta_saida)} produto(s) acima do limite de saida mensal",
            }
        )
    return alertas

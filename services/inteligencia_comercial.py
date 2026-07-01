from datetime import timedelta
from hashlib import sha256
from urllib.parse import urlencode

from django.core.cache import cache
from django.db.models import Count, Exists, Max, OuterRef, Subquery, Sum
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Produto
from crm.models import Cliente, HistoricoContato, Oportunidade, ProximaAcao
from vendas.models import Pedido, PedidoItem
from whatsapp.services import gerar_link_recomendacao_whatsapp


DIAS_SEM_RECOMPRA = 45
DIAS_FOLLOW_UP = 7
LIMITE_ALTA_SAIDA = 5
LIMITE_RISCO_RUPTURA = 10
RECOMENDACOES_CACHE_TTL = 60


def gerar_recomendacoes_comerciais(empresa):
    cache_key = _cache_key_recomendacoes(empresa)
    recomendacoes_cache = cache.get(cache_key)
    if recomendacoes_cache is not None:
        return recomendacoes_cache

    oportunidades = listar_scores_oportunidades(empresa)
    alta_saida = listar_produtos_alta_saida(empresa)
    risco_ruptura = listar_produtos_risco_ruptura(empresa)
    sem_recompra = listar_clientes_sem_recompra(empresa)
    follow_ups = listar_sugestoes_follow_up(empresa)
    alertas = gerar_alertas_comerciais(
        empresa=empresa,
        oportunidades=oportunidades,
        alta_saida=alta_saida,
        risco_ruptura=risco_ruptura,
        sem_recompra=sem_recompra,
        follow_ups=follow_ups,
    )
    recomendacoes = {
        "scores_oportunidade": oportunidades,
        "produtos_risco_ruptura": risco_ruptura,
        "clientes_sem_recompra": sem_recompra,
        "produtos_alta_saida": alta_saida,
        "sugestoes_follow_up": follow_ups,
        "alertas_comerciais": alertas,
    }
    cache.set(cache_key, recomendacoes, RECOMENDACOES_CACHE_TTL)
    return recomendacoes


def _cache_key_recomendacoes(empresa):
    clientes = Cliente.objects.da_empresa(empresa).aggregate(
        total=Count("id"),
        atualizado=Max("atualizado_em"),
    )
    oportunidades = Oportunidade.objects.da_empresa(empresa).aggregate(
        total=Count("id"),
        atualizado=Max("atualizado_em"),
    )
    historicos = HistoricoContato.objects.da_empresa(empresa).aggregate(
        total=Count("id"),
        criado=Max("criado_em"),
    )
    pedidos = Pedido.objects.da_empresa(empresa).aggregate(
        total=Count("id"),
        atualizado=Max("atualizado_em"),
    )
    produtos = Produto.objects.da_empresa(empresa).aggregate(
        total=Count("id"),
        atualizado=Max("atualizado_em"),
    )
    proximas_acoes = ProximaAcao.objects.da_empresa(empresa).aggregate(
        total=Count("id"),
        atualizado=Max("atualizada_em"),
    )
    assinatura = "|".join(
        str(valor or "")
        for grupo in [clientes, oportunidades, historicos, pedidos, produtos, proximas_acoes]
        for valor in grupo.values()
    )
    assinatura_hash = sha256(assinatura.encode("utf-8")).hexdigest()
    return f"recomendacoes-comerciais:{empresa.id}:{assinatura_hash}"


def listar_recomendacoes_acionaveis(empresa):
    recomendacoes = gerar_recomendacoes_comerciais(empresa)
    return recomendacoes["alertas_comerciais"]


def _url(nome_rota, empresa, objeto_id):
    return reverse(nome_rota, args=[empresa.id, objeto_id])


def _acao(rotulo, url):
    return {"rotulo": rotulo, "url": url}


def _url_criar_proxima_acao(empresa, cliente_id=None, oportunidade_id=None, pedido_id=None):
    parametros = {}
    if cliente_id:
        parametros["cliente"] = cliente_id
    if oportunidade_id:
        parametros["oportunidade"] = oportunidade_id
    if pedido_id:
        parametros["pedido"] = pedido_id
    url = reverse("crm:proxima-acao-create", args=[empresa.id])
    if parametros:
        return f"{url}?{urlencode(parametros)}"
    return url


def _aplicar_acao_principal(item, prioridade, entidade_relacionada, acoes):
    item["prioridade"] = prioridade
    item["entidade_relacionada"] = entidade_relacionada
    item["acoes"] = list(acoes)
    whatsapp_link = gerar_link_recomendacao_whatsapp(item)
    item["whatsapp_link"] = whatsapp_link
    if whatsapp_link and not any(acao["url"] == whatsapp_link for acao in item["acoes"]):
        item["acoes"].append(_acao("Enviar WhatsApp", whatsapp_link))
    if item["acoes"]:
        item["acao_recomendada"] = item["acoes"][0]["rotulo"]
        item["link_acao"] = item["acoes"][0]["url"]
    else:
        item["acao_recomendada"] = ""
        item["link_acao"] = ""
    return item


def listar_scores_oportunidades(empresa):
    historico_cliente = HistoricoContato.objects.da_empresa(empresa).filter(
        cliente_id=OuterRef("cliente_id")
    )
    acao_pendente = ProximaAcao.objects.da_empresa(empresa).filter(
        oportunidade_id=OuterRef("pk"),
        status=ProximaAcao.Status.PENDENTE,
    )
    oportunidades = (
        Oportunidade.objects.da_empresa(empresa)
        .filter(status=Oportunidade.Status.ABERTA)
        .select_related("cliente", "vendedor")
        .annotate(
            tem_historico=Exists(historico_cliente),
            tem_acao_pendente=Exists(acao_pendente),
        )
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

    tem_acao_pendente = getattr(oportunidade, "tem_acao_pendente", None)
    if tem_acao_pendente is None:
        tem_acao_pendente = oportunidade.proximas_acoes.filter(
            status=ProximaAcao.Status.PENDENTE
        ).exists()
    if tem_acao_pendente:
        score += 25
        motivos.append("possui proxima acao pendente")
    else:
        motivos.append("sem proxima acao pendente")

    tem_historico = getattr(oportunidade, "tem_historico", None)
    if tem_historico is None:
        tem_historico = HistoricoContato.objects.da_empresa(oportunidade.empresa).filter(
            cliente=oportunidade.cliente
        ).exists()
    if tem_historico:
        score += 20
        motivos.append("cliente possui historico comercial")
    else:
        motivos.append("cliente sem historico comercial")

    item = {
        "tipo": "score_oportunidade",
        "titulo": oportunidade.titulo,
        "score": min(score, 100),
        "motivo": "; ".join(motivos),
        "oportunidade": oportunidade,
        "cliente": oportunidade.cliente,
    }
    return _aplicar_acao_principal(
        item,
        prioridade="alta" if item["score"] >= 80 else "media",
        entidade_relacionada=f"Oportunidade #{oportunidade.id}",
        acoes=[
            _acao(
                "Criar proxima acao",
                _url_criar_proxima_acao(
                    oportunidade.empresa,
                    cliente_id=oportunidade.cliente_id,
                    oportunidade_id=oportunidade.id,
                ),
            ),
            _acao(
                "Abrir oportunidade",
                _url("crm:oportunidade-detail", oportunidade.empresa, oportunidade.id),
            ),
            _acao(
                "Abrir cliente",
                _url("crm:cliente-detail", oportunidade.empresa, oportunidade.cliente_id),
            ),
        ],
    )


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
        _aplicar_acao_principal(
            {
            "tipo": "produto_alta_saida",
            "titulo": item["produto__nome"],
            "quantidade": item["quantidade"],
            "motivo": f"vendeu {item['quantidade']} unidades confirmadas no mes",
            "produto_id": item["produto_id"],
            },
            prioridade="baixa",
            entidade_relacionada=f"Produto #{item['produto_id']}",
            acoes=[
                _acao(
                    "Abrir produto",
                    _url("catalogo:produto-detail", empresa, item["produto_id"]),
                ),
            ],
        )
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
        _aplicar_acao_principal(
            {
            "tipo": "risco_ruptura",
            "titulo": item["produto__nome"],
            "quantidade": item["quantidade"],
            "motivo": (
                f"alta saida de {item['quantidade']} unidades no mes e estoque ainda nao e controlado"
            ),
            "produto_id": item["produto_id"],
            },
            prioridade="alta",
            entidade_relacionada=f"Produto #{item['produto_id']}",
            acoes=[
                _acao(
                    "Abrir produto",
                    _url("catalogo:produto-detail", empresa, item["produto_id"]),
                ),
            ],
        )
        for item in itens
    ]


def listar_clientes_sem_recompra(empresa):
    data_limite = timezone.localdate() - timedelta(days=DIAS_SEM_RECOMPRA)
    clientes_com_pedido_recente = Pedido.objects.da_empresa(empresa).filter(
        status=Pedido.Status.CONFIRMADO,
        criado_em__date__gte=data_limite,
    ).values("cliente_id")
    ultimo_pedido = (
        Pedido.objects.da_empresa(empresa)
        .filter(cliente_id=OuterRef("pk"), status=Pedido.Status.CONFIRMADO)
        .order_by("-criado_em", "-id")
    )
    clientes = (
        Cliente.objects.da_empresa(empresa)
        .filter(ativo=True, pedidos__status=Pedido.Status.CONFIRMADO)
        .exclude(id__in=clientes_com_pedido_recente)
        .annotate(
            ultimo_pedido=Max("pedidos__criado_em"),
            ultimo_pedido_id=Subquery(ultimo_pedido.values("id")[:1]),
        )
        .order_by("ultimo_pedido", "nome")
    )
    recomendacoes = []
    for cliente in clientes:
        acoes = [
            _acao(
                "Criar proxima acao",
                _url_criar_proxima_acao(empresa, cliente_id=cliente.id),
            ),
            _acao("Abrir cliente", _url("crm:cliente-detail", empresa, cliente.id)),
        ]
        if cliente.ultimo_pedido_id:
            acoes[0] = _acao(
                "Criar proxima acao",
                _url_criar_proxima_acao(
                    empresa,
                    cliente_id=cliente.id,
                    pedido_id=cliente.ultimo_pedido_id,
                ),
            )
            acoes.append(
                _acao(
                    "Abrir ultimo pedido",
                    _url("vendas:pedido-detail", empresa, cliente.ultimo_pedido_id),
                )
            )
        recomendacoes.append(
            _aplicar_acao_principal(
                {
                    "tipo": "cliente_sem_recompra",
                    "titulo": cliente.nome,
                    "cliente": cliente,
                    "ultimo_pedido": cliente.ultimo_pedido,
                    "ultimo_pedido_id": cliente.ultimo_pedido_id,
                    "motivo": f"cliente sem pedido confirmado nos ultimos {DIAS_SEM_RECOMPRA} dias",
                },
                prioridade="media",
                entidade_relacionada=f"Cliente #{cliente.id}",
                acoes=acoes,
            )
        )
    return recomendacoes


def listar_sugestoes_follow_up(empresa):
    data_limite = timezone.now() - timedelta(days=DIAS_FOLLOW_UP)
    acao_pendente = ProximaAcao.objects.da_empresa(empresa).filter(
        oportunidade_id=OuterRef("pk"),
        status=ProximaAcao.Status.PENDENTE,
    )
    oportunidades = (
        Oportunidade.objects.da_empresa(empresa)
        .filter(status=Oportunidade.Status.ABERTA, criado_em__lte=data_limite)
        .select_related("cliente", "vendedor")
        .annotate(tem_acao_pendente=Exists(acao_pendente))
        .filter(tem_acao_pendente=False)
    )
    sugestoes = []
    for oportunidade in oportunidades:
        sugestoes.append(
            _aplicar_acao_principal(
                {
                "tipo": "follow_up",
                "titulo": oportunidade.titulo,
                "cliente": oportunidade.cliente,
                "oportunidade": oportunidade,
                "motivo": (
                    f"oportunidade aberta ha mais de {DIAS_FOLLOW_UP} dias sem proxima acao pendente"
                ),
                },
                prioridade="media",
                entidade_relacionada=f"Oportunidade #{oportunidade.id}",
                acoes=[
                    _acao(
                        "Criar proxima acao",
                        _url_criar_proxima_acao(
                            empresa,
                            cliente_id=oportunidade.cliente_id,
                            oportunidade_id=oportunidade.id,
                        ),
                    ),
                    _acao(
                        "Abrir oportunidade",
                        _url("crm:oportunidade-detail", empresa, oportunidade.id),
                    ),
                    _acao(
                        "Abrir cliente",
                        _url("crm:cliente-detail", empresa, oportunidade.cliente_id),
                    ),
                ],
            )
        )
    return sugestoes


def gerar_alertas_comerciais(
    empresa,
    oportunidades,
    alta_saida,
    risco_ruptura,
    sem_recompra,
    follow_ups,
):
    alertas = []
    for item in risco_ruptura:
        alertas.append(
            _aplicar_acao_principal(
                {
                "tipo": "alerta_ruptura",
                "titulo": item["titulo"],
                "severidade": "alta",
                "motivo": item["motivo"],
                "produto_id": item.get("produto_id"),
                "produto_nome": item["titulo"],
                },
                prioridade="alta",
                entidade_relacionada=item["entidade_relacionada"],
                acoes=item["acoes"],
            )
        )
    for item in follow_ups:
        alertas.append(
            _aplicar_acao_principal(
                {
                "tipo": "alerta_follow_up",
                "titulo": item["titulo"],
                "severidade": "media",
                "motivo": item["motivo"],
                "cliente": item.get("cliente"),
                "oportunidade": item.get("oportunidade"),
                },
                prioridade="media",
                entidade_relacionada=item["entidade_relacionada"],
                acoes=item["acoes"],
            )
        )
    for item in oportunidades:
        if item["score"] >= 80:
            alertas.append(
                _aplicar_acao_principal(
                    {
                    "tipo": "alerta_oportunidade_quente",
                    "titulo": item["titulo"],
                    "severidade": "alta",
                    "motivo": f"score {item['score']} por: {item['motivo']}",
                    "cliente": item.get("cliente"),
                    "oportunidade": item.get("oportunidade"),
                    },
                    prioridade="alta",
                    entidade_relacionada=item["entidade_relacionada"],
                    acoes=item["acoes"],
                )
            )
    if sem_recompra:
        primeiro_item = sem_recompra[0]
        alertas.append(
            _aplicar_acao_principal(
                {
                "tipo": "alerta_recompra",
                "titulo": "Clientes sem recompra",
                "severidade": "media",
                "motivo": f"{len(sem_recompra)} cliente(s) sem recompra recente",
                "cliente": primeiro_item.get("cliente"),
                "ultimo_pedido_id": primeiro_item.get("ultimo_pedido_id"),
                },
                prioridade="media",
                entidade_relacionada=primeiro_item["entidade_relacionada"],
                acoes=primeiro_item["acoes"],
            )
        )
    if alta_saida:
        primeiro_item = alta_saida[0]
        alertas.append(
            _aplicar_acao_principal(
                {
                "tipo": "alerta_alta_saida",
                "titulo": "Produtos com alta saida",
                "severidade": "baixa",
                "motivo": f"{len(alta_saida)} produto(s) acima do limite de saida mensal",
                "produto_id": primeiro_item.get("produto_id"),
                "produto_nome": primeiro_item["titulo"],
                },
                prioridade="baixa",
                entidade_relacionada=primeiro_item["entidade_relacionada"],
                acoes=primeiro_item["acoes"],
            )
        )
    return alertas

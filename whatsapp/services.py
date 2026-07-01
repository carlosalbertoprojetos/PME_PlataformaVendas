from urllib.parse import quote

from django.urls import reverse

from whatsapp.models import WhatsAppTemplateConfig


WHATSAPP_BASE_URL = "https://wa.me/"
MIN_DIGITOS_TELEFONE = 10
MAX_DIGITOS_TELEFONE = 15


def get_whatsapp_config(empresa):
    config, _ = WhatsAppTemplateConfig.objects.get_or_create(empresa=empresa)
    return config


def gerar_wa_me_link(mensagem, telefone=""):
    destino = "".join(ch for ch in str(telefone or "") if ch.isdigit())
    return f"{WHATSAPP_BASE_URL}{destino}?text={quote(str(mensagem))}"


def sanitizar_telefone_whatsapp(telefone):
    return "".join(ch for ch in str(telefone or "") if ch.isdigit())


def telefone_whatsapp_valido(telefone):
    destino = sanitizar_telefone_whatsapp(telefone)
    return MIN_DIGITOS_TELEFONE <= len(destino) <= MAX_DIGITOS_TELEFONE


def render_template(template, contexto):
    valores = {chave: "" if valor is None else valor for chave, valor in contexto.items()}
    return template.format_map(_SafeFormatDict(valores))


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def absolute_url(request, url_name, *args):
    return request.build_absolute_uri(reverse(url_name, args=args))


def gerar_mensagem_recomendacao_whatsapp(recomendacao):
    tipo = recomendacao.get("tipo", "")
    cliente = recomendacao.get("cliente")
    oportunidade = recomendacao.get("oportunidade")
    pedido = recomendacao.get("pedido")
    produto_nome = recomendacao.get("produto_nome") or recomendacao.get("titulo")
    cliente_nome = getattr(cliente, "nome", recomendacao.get("cliente_nome", "cliente"))
    motivo = recomendacao.get("motivo", "")

    if tipo in {"cliente_sem_recompra", "alerta_recompra"}:
        return (
            f"Ola {cliente_nome}, tudo bem? Sentimos sua falta por aqui. "
            f"Podemos te ajudar com uma nova compra? Motivo do contato: {motivo}"
        )
    if tipo in {"follow_up", "alerta_follow_up"}:
        titulo = getattr(oportunidade, "titulo", recomendacao.get("titulo", "sua oportunidade"))
        return (
            f"Ola {cliente_nome}, tudo bem? Estou passando para dar continuidade em {titulo}. "
            f"Motivo do contato: {motivo}"
        )
    if tipo == "pedido_pendente":
        pedido_id = getattr(pedido, "id", recomendacao.get("pedido_id", ""))
        return (
            f"Ola {cliente_nome}, tudo bem? Seu pedido {pedido_id} esta pendente. "
            f"Podemos seguir com ele? Motivo do contato: {motivo}"
        )
    if tipo in {"produto_recomendado", "produto_alta_saida", "risco_ruptura", "alerta_alta_saida", "alerta_ruptura"}:
        return (
            f"Ola {cliente_nome}, tudo bem? Temos uma recomendacao comercial para voce: "
            f"{produto_nome}. Motivo do contato: {motivo}"
        )
    if tipo in {"score_oportunidade", "alerta_oportunidade_quente"}:
        titulo = getattr(oportunidade, "titulo", recomendacao.get("titulo", "sua oportunidade"))
        return (
            f"Ola {cliente_nome}, tudo bem? Vi uma boa oportunidade para seguirmos com {titulo}. "
            f"Motivo do contato: {motivo}"
        )
    return f"Ola {cliente_nome}, tudo bem? Motivo do contato: {motivo}"


def gerar_link_recomendacao_whatsapp(recomendacao, telefone=""):
    cliente = recomendacao.get("cliente")
    pedido = recomendacao.get("pedido")
    destino = telefone or getattr(cliente, "telefone", "") or getattr(getattr(pedido, "cliente", None), "telefone", "")
    if not telefone_whatsapp_valido(destino):
        return ""
    return gerar_wa_me_link(gerar_mensagem_recomendacao_whatsapp(recomendacao), destino)


def gerar_link_catalogo(request, empresa, telefone=""):
    config = get_whatsapp_config(empresa)
    mensagem = render_template(
        config.catalogo,
        {
            "empresa_nome": empresa.nome,
            "catalogo_url": absolute_url(request, "catalogo:produto-list-create", empresa.id),
        },
    )
    return gerar_wa_me_link(mensagem, telefone)


def gerar_link_produto(request, produto, telefone=""):
    config = get_whatsapp_config(produto.empresa)
    mensagem = render_template(
        config.produto,
        {
            "empresa_nome": produto.empresa.nome,
            "produto_nome": produto.nome,
            "produto_preco": produto.preco,
            "produto_url": absolute_url(request, "catalogo:produto-detail", produto.empresa_id, produto.id),
        },
    )
    return gerar_wa_me_link(mensagem, telefone)


def gerar_link_pedido(pedido, telefone=""):
    config = get_whatsapp_config(pedido.empresa)
    mensagem = render_template(
        config.pedido,
        {
            "empresa_nome": pedido.empresa.nome,
            "cliente_nome": pedido.cliente.nome,
            "pedido_id": pedido.id,
            "pedido_total": pedido.valor_total,
            "pedido_status": pedido.get_status_display(),
        },
    )
    return gerar_wa_me_link(mensagem, telefone or pedido.cliente.telefone)


def gerar_link_cliente(cliente, telefone=""):
    config = get_whatsapp_config(cliente.empresa)
    mensagem = render_template(
        config.cliente,
        {
            "empresa_nome": cliente.empresa.nome,
            "cliente_nome": cliente.nome,
            "cliente_email": cliente.email,
            "cliente_telefone": cliente.telefone,
        },
    )
    return gerar_wa_me_link(mensagem, telefone or cliente.telefone)


def gerar_link_follow_up(cliente, telefone=""):
    config = get_whatsapp_config(cliente.empresa)
    mensagem = render_template(
        config.follow_up,
        {
            "empresa_nome": cliente.empresa.nome,
            "cliente_nome": cliente.nome,
            "cliente_email": cliente.email,
            "cliente_telefone": cliente.telefone,
        },
    )
    return gerar_wa_me_link(mensagem, telefone or cliente.telefone)

from urllib.parse import quote

from django.urls import reverse

from whatsapp.models import WhatsAppTemplateConfig


WHATSAPP_BASE_URL = "https://wa.me/"


def get_whatsapp_config(empresa):
    config, _ = WhatsAppTemplateConfig.objects.get_or_create(empresa=empresa)
    return config


def gerar_wa_me_link(mensagem, telefone=""):
    destino = "".join(ch for ch in str(telefone or "") if ch.isdigit())
    return f"{WHATSAPP_BASE_URL}{destino}?text={quote(str(mensagem))}"


def render_template(template, contexto):
    valores = {chave: "" if valor is None else valor for chave, valor in contexto.items()}
    return template.format_map(_SafeFormatDict(valores))


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def absolute_url(request, url_name, *args):
    return request.build_absolute_uri(reverse(url_name, args=args))


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

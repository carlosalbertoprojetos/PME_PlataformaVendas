from django import template

from whatsapp.services import (
    gerar_link_cliente,
    gerar_link_follow_up,
    gerar_link_pedido,
    gerar_link_produto,
)


register = template.Library()


@register.simple_tag
def whatsapp_cliente(cliente):
    return gerar_link_cliente(cliente)


@register.simple_tag
def whatsapp_follow_up(cliente):
    return gerar_link_follow_up(cliente)


@register.simple_tag
def whatsapp_produto(produto):
    return gerar_link_produto(_TemplateRequest(), produto)


@register.simple_tag
def whatsapp_pedido(pedido):
    return gerar_link_pedido(pedido)


class _TemplateRequest:
    def build_absolute_uri(self, path):
        return path

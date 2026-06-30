from django.db import models


class WhatsAppTemplateConfig(models.Model):
    empresa = models.OneToOneField(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="whatsapp_config",
    )
    catalogo = models.TextField(
        default="Ola! Veja nosso catalogo: {catalogo_url}"
    )
    produto = models.TextField(
        default="Ola! Conheca o produto {produto_nome} por R$ {produto_preco}: {produto_url}"
    )
    pedido = models.TextField(
        default="Ola! Segue o resumo do pedido #{pedido_id} no valor de R$ {pedido_total}."
    )
    cliente = models.TextField(
        default="Ola, {cliente_nome}! Posso te ajudar com uma nova cotacao?"
    )
    follow_up = models.TextField(
        default="Ola, {cliente_nome}! Passando para dar continuidade ao nosso atendimento."
    )
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracao de mensagens WhatsApp"
        verbose_name_plural = "Configuracoes de mensagens WhatsApp"

    def __str__(self):
        return f"WhatsApp - {self.empresa}"

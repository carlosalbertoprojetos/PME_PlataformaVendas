from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PedidoQuerySet(models.QuerySet):
    def da_empresa(self, empresa):
        return self.filter(empresa=empresa)

    def confirmados(self):
        return self.filter(status=Pedido.Status.CONFIRMADO)

    def pendentes(self):
        return self.filter(status=Pedido.Status.PENDENTE)


class Pedido(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADO = "confirmado", "Confirmado"
        CANCELADO = "cancelado", "Cancelado"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    cliente = models.ForeignKey(
        "crm.Cliente",
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    oportunidade = models.ForeignKey(
        "crm.Oportunidade",
        on_delete=models.SET_NULL,
        related_name="pedidos",
        blank=True,
        null=True,
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = PedidoQuerySet.as_manager()

    class Meta:
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "status", "criado_em"], name="vend_ped_emp_status_data_idx"),
            models.Index(fields=["empresa", "vendedor", "status"], name="vend_ped_emp_vend_status_idx"),
        ]

    def __str__(self):
        return f"Pedido #{self.pk or 'novo'}"

    def clean(self):
        if self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError("Cliente pertence a outra empresa.")
        if self.oportunidade_id and self.oportunidade.empresa_id != self.empresa_id:
            raise ValidationError("Oportunidade pertence a outra empresa.")


class PedidoItem(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    produto = models.ForeignKey(
        "catalogo.Produto",
        on_delete=models.PROTECT,
        related_name="pedido_itens",
    )
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=["produto"], name="vend_item_produto_idx"),
        ]

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def clean(self):
        if self.pedido_id and self.produto_id:
            if self.produto.empresa_id != self.pedido.empresa_id:
                raise ValidationError("Produto pertence a outra empresa.")

    def __str__(self):
        return f"{self.quantidade} x {self.produto}"

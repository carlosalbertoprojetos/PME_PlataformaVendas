from decimal import Decimal

from django.db import models
from django.utils import timezone


class Plano(models.Model):
    class Codigo(models.TextChoices):
        START = "start", "Start"
        GROWTH = "growth", "Growth"
        PRO = "pro", "Pro"

    codigo = models.CharField(max_length=30, choices=Codigo.choices, unique=True)
    nome = models.CharField(max_length=80)
    preco_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    limite_usuarios = models.PositiveIntegerField()
    limite_vendedores = models.PositiveIntegerField(default=2)
    limite_clientes = models.PositiveIntegerField()
    limite_leads = models.PositiveIntegerField(default=100)
    limite_produtos = models.PositiveIntegerField()
    limite_oportunidades = models.PositiveIntegerField(default=50)
    limite_pedidos_mes = models.PositiveIntegerField()
    limite_recomendacoes_comerciais = models.PositiveIntegerField(default=10)
    permite_workspace_comercial = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["preco_mensal", "nome"]

    def __str__(self):
        return self.nome


class Assinatura(models.Model):
    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ATIVA = "ativa", "Ativa"
        PAST_DUE = "past_due", "Pagamento pendente"
        SUSPENSA = "suspensa", "Suspensa"
        CANCELADA = "cancelada", "Cancelada"

    empresa = models.OneToOneField(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="assinatura",
    )
    plano = models.ForeignKey(Plano, on_delete=models.PROTECT, related_name="assinaturas")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    inicio_em = models.DateField(default=timezone.localdate)
    fim_trial_em = models.DateField(blank=True, null=True)
    gateway_preferido = models.CharField(max_length=30, blank=True)
    gateway_customer_id = models.CharField(max_length=120, blank=True)
    gateway_subscription_id = models.CharField(max_length=120, blank=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["empresa__nome"]

    @property
    def permite_uso(self):
        return self.status in {
            self.Status.TRIAL,
            self.Status.ATIVA,
            self.Status.PAST_DUE,
        }

    def __str__(self):
        return f"{self.empresa} - {self.plano}"

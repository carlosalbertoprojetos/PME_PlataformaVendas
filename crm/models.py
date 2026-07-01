from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class EmpresaScopedQuerySet(models.QuerySet):
    def da_empresa(self, empresa):
        return self.filter(empresa=empresa)


class Cliente(models.Model):
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="clientes",
    )
    nome = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    documento = models.CharField(max_length=30, blank=True)
    observacoes = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = EmpresaScopedQuerySet.as_manager()

    class Meta:
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["empresa", "ativo", "nome"], name="crm_cli_emp_ativo_nome_idx"),
        ]

    def __str__(self):
        return self.nome


class Lead(models.Model):
    class Status(models.TextChoices):
        NOVO = "novo", "Novo"
        EM_CONTATO = "em_contato", "Em contato"
        CONVERTIDO = "convertido", "Convertido"
        PERDIDO = "perdido", "Perdido"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="leads",
    )
    nome = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    origem = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOVO)
    cliente_convertido = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        related_name="leads_convertidos",
        blank=True,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = EmpresaScopedQuerySet.as_manager()

    class Meta:
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "status", "criado_em"], name="crm_lead_emp_status_idx"),
        ]

    def __str__(self):
        return self.nome

    def converter_em_cliente(self):
        if self.cliente_convertido_id:
            return self.cliente_convertido

        cliente = Cliente.objects.create(
            empresa=self.empresa,
            nome=self.nome,
            email=self.email,
            telefone=self.telefone,
            observacoes=f"Convertido do lead #{self.pk}.",
        )
        self.status = self.Status.CONVERTIDO
        self.cliente_convertido = cliente
        self.save(update_fields=["status", "cliente_convertido", "atualizado_em"])
        return cliente


class Oportunidade(models.Model):
    class Status(models.TextChoices):
        ABERTA = "aberta", "Aberta"
        GANHA = "ganha", "Ganha"
        PERDIDA = "perdida", "Perdida"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="oportunidades",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="oportunidades",
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="oportunidades",
    )
    titulo = models.CharField(max_length=160)
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTA)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = EmpresaScopedQuerySet.as_manager()

    class Meta:
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "status", "criado_em"], name="crm_op_emp_status_idx"),
            models.Index(fields=["empresa", "vendedor", "status"], name="crm_op_emp_vend_status_idx"),
        ]

    def __str__(self):
        return self.titulo

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError("Cliente pertence a outra empresa.")


class HistoricoContato(models.Model):
    class Tipo(models.TextChoices):
        TELEFONE = "telefone", "Telefone"
        EMAIL = "email", "Email"
        WHATSAPP = "whatsapp", "WhatsApp"
        REUNIAO = "reuniao", "Reuniao"
        OUTRO = "outro", "Outro"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="historicos_contato",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="historicos_contato",
        blank=True,
        null=True,
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="historicos_contato",
        blank=True,
        null=True,
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="historicos_contato",
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.OUTRO)
    resumo = models.TextField()
    realizado_em = models.DateTimeField(default=timezone.now)
    criado_em = models.DateTimeField(auto_now_add=True)

    objects = EmpresaScopedQuerySet.as_manager()

    class Meta:
        ordering = ["-realizado_em"]
        indexes = [
            models.Index(fields=["empresa", "realizado_em"], name="crm_hist_emp_realizado_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.realizado_em:%d/%m/%Y}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.cliente_id and not self.lead_id:
            raise ValidationError("Informe um cliente ou lead.")
        if self.cliente_id and self.lead_id:
            raise ValidationError("Informe apenas cliente ou lead.")
        if self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError("Cliente pertence a outra empresa.")
        if self.lead_id and self.lead.empresa_id != self.empresa_id:
            raise ValidationError("Lead pertence a outra empresa.")


class ProximaAcao(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONCLUIDA = "concluida", "Concluida"
        CANCELADA = "cancelada", "Cancelada"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="proximas_acoes",
    )
    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name="proximas_acoes",
        blank=True,
        null=True,
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="proximas_acoes",
        blank=True,
        null=True,
    )
    pedido = models.ForeignKey(
        "vendas.Pedido",
        on_delete=models.CASCADE,
        related_name="proximas_acoes",
        blank=True,
        null=True,
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proximas_acoes",
    )
    descricao = models.CharField(max_length=220)
    data_prevista = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    objects = EmpresaScopedQuerySet.as_manager()

    class Meta:
        ordering = ["data_prevista", "id"]
        indexes = [
            models.Index(fields=["empresa", "status", "data_prevista"], name="crm_acao_emp_status_idx"),
        ]

    def __str__(self):
        return self.descricao

    def clean(self):
        if not self.cliente_id and not self.oportunidade_id and not self.pedido_id:
            raise ValidationError("Informe cliente, oportunidade ou pedido.")
        if self.cliente_id and self.cliente.empresa_id != self.empresa_id:
            raise ValidationError("Cliente pertence a outra empresa.")
        if self.oportunidade_id and self.oportunidade.empresa_id != self.empresa_id:
            raise ValidationError("Oportunidade pertence a outra empresa.")
        if self.pedido_id and self.pedido.empresa_id != self.empresa_id:
            raise ValidationError("Pedido pertence a outra empresa.")

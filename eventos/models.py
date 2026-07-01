from django.conf import settings
from django.db import models


class EventLogQuerySet(models.QuerySet):
    def da_empresa(self, empresa):
        return self.filter(empresa=empresa)

    def para_cliente(self, cliente):
        return self.filter(
            models.Q(cliente_id=cliente.id)
            | models.Q(entidade_tipo="cliente", entidade_id=cliente.id)
        )

    def para_oportunidade(self, oportunidade):
        return self.filter(
            models.Q(oportunidade_id=oportunidade.id)
            | models.Q(entidade_tipo="oportunidade", entidade_id=oportunidade.id)
        )


class EventLog(models.Model):
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="event_logs",
    )
    tipo = models.CharField(max_length=80)
    titulo = models.CharField(max_length=160)
    descricao = models.TextField(blank=True)
    entidade_tipo = models.CharField(max_length=80, blank=True)
    entidade_id = models.PositiveIntegerField(blank=True, null=True)
    cliente_id = models.PositiveIntegerField(blank=True, null=True)
    lead_id = models.PositiveIntegerField(blank=True, null=True)
    oportunidade_id = models.PositiveIntegerField(blank=True, null=True)
    pedido_id = models.PositiveIntegerField(blank=True, null=True)
    produto_id = models.PositiveIntegerField(blank=True, null=True)
    proxima_acao_id = models.PositiveIntegerField(blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    ator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="eventos_comerciais",
        blank=True,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    objects = EventLogQuerySet.as_manager()

    class Meta:
        ordering = ["-criado_em", "-id"]
        indexes = [
            models.Index(fields=["empresa", "tipo", "criado_em"], name="evt_log_emp_tipo_data_idx"),
            models.Index(fields=["empresa", "cliente_id", "criado_em"], name="evt_log_emp_cli_data_idx"),
            models.Index(fields=["empresa", "oportunidade_id", "criado_em"], name="evt_log_emp_op_data_idx"),
            models.Index(fields=["empresa", "pedido_id", "criado_em"], name="evt_log_emp_ped_data_idx"),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.empresa}"


class AutomationRule(models.Model):
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="automation_rules",
    )
    nome = models.CharField(max_length=160)
    ativa = models.BooleanField(default=True)
    evento_disparador = models.CharField(max_length=80)
    prioridade = models.PositiveIntegerField(default=100)
    conditions = models.JSONField(default=list, blank=True)
    actions = models.JSONField(default=list, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["prioridade", "nome"]
        indexes = [
            models.Index(
                fields=["empresa", "ativa", "evento_disparador", "prioridade"],
                name="evt_auto_rule_lookup_idx",
            ),
        ]

    def __str__(self):
        return self.nome


class AutomationExecutionLog(models.Model):
    class Resultado(models.TextChoices):
        SUCESSO = "sucesso", "Sucesso"
        FALHA = "falha", "Falha"
        IGNORADA = "ignorada", "Ignorada"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="automation_execution_logs",
    )
    evento = models.ForeignKey(
        EventLog,
        on_delete=models.CASCADE,
        related_name="automation_executions",
    )
    regra = models.ForeignKey(
        AutomationRule,
        on_delete=models.CASCADE,
        related_name="execution_logs",
    )
    resultado = models.CharField(
        max_length=20,
        choices=Resultado.choices,
        default=Resultado.SUCESSO,
    )
    tempo_ms = models.PositiveIntegerField(default=0)
    erro = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "regra"],
                name="unique_execucao_por_evento_regra",
            ),
        ]
        indexes = [
            models.Index(
                fields=["empresa", "resultado", "criado_em"],
                name="evt_auto_exec_emp_result_idx",
            ),
        ]

    def __str__(self):
        return f"{self.regra} - {self.get_resultado_display()}"

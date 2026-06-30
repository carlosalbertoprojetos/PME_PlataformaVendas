from django.conf import settings
from django.db import models


class Empresa(models.Model):
    nome = models.CharField(max_length=160)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class EmpresaMembership(models.Model):
    class Papel(models.TextChoices):
        ADMIN = "admin", "Administrador"
        VENDEDOR = "vendedor", "Vendedor"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="empresa_memberships",
    )
    papel = models.CharField(max_length=20, choices=Papel.choices)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "usuario"],
                name="unique_membership_por_empresa_usuario",
            )
        ]
        indexes = [
            models.Index(
                fields=["empresa", "usuario", "ativo"],
                name="emp_mem_empresa_usuario_idx",
            ),
            models.Index(fields=["usuario", "ativo"], name="emp_mem_usuario_idx"),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.empresa} ({self.papel})"

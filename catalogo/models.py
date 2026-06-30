from django.db import models


class ProdutoQuerySet(models.QuerySet):
    def da_empresa(self, empresa):
        return self.filter(empresa=empresa)

    def ativos(self):
        return self.filter(ativo=True)


class Produto(models.Model):
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="produtos",
    )
    nome = models.CharField(max_length=160)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = ProdutoQuerySet.as_manager()

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "nome"],
                name="unique_produto_nome_por_empresa",
            )
        ]
        indexes = [
            models.Index(fields=["empresa", "ativo", "nome"], name="cat_prod_emp_ativo_nome_idx"),
        ]

    def __str__(self):
        return self.nome

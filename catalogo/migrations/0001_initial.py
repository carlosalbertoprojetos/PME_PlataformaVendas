from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("empresas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Produto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=160)),
                ("descricao", models.TextField(blank=True)),
                ("preco", models.DecimalField(decimal_places=2, max_digits=10)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="produtos", to="empresas.empresa")),
            ],
            options={"ordering": ["nome"]},
        ),
        migrations.AddConstraint(
            model_name="produto",
            constraint=models.UniqueConstraint(fields=("empresa", "nome"), name="unique_produto_nome_por_empresa"),
        ),
        migrations.AddIndex(
            model_name="produto",
            index=models.Index(fields=["empresa", "ativo", "nome"], name="cat_prod_emp_ativo_nome_idx"),
        ),
    ]

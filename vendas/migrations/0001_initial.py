from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalogo", "0001_initial"),
        ("crm", "0001_initial"),
        ("empresas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pendente", "Pendente"), ("confirmado", "Confirmado"), ("cancelado", "Cancelado")], default="pendente", max_length=20)),
                ("valor_total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("criado_em", models.DateTimeField(default=django.utils.timezone.now)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("cliente", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="crm.cliente")),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pedidos", to="empresas.empresa")),
                ("oportunidade", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos", to="crm.oportunidade")),
                ("vendedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-criado_em"]},
        ),
        migrations.CreateModel(
            name="PedidoItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantidade", models.PositiveIntegerField(default=1)),
                ("preco_unitario", models.DecimalField(decimal_places=2, max_digits=10)),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="vendas.pedido")),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedido_itens", to="catalogo.produto")),
            ],
        ),
        migrations.AddIndex(
            model_name="pedido",
            index=models.Index(fields=["empresa", "status", "criado_em"], name="vend_ped_emp_status_data_idx"),
        ),
        migrations.AddIndex(
            model_name="pedido",
            index=models.Index(fields=["empresa", "vendedor", "status"], name="vend_ped_emp_vend_status_idx"),
        ),
        migrations.AddIndex(
            model_name="pedidoitem",
            index=models.Index(fields=["produto"], name="vend_item_produto_idx"),
        ),
    ]

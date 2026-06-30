from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def criar_planos_iniciais(apps, schema_editor):
    Plano = apps.get_model("billing", "Plano")
    planos = [
        {
            "codigo": "start",
            "nome": "Start",
            "preco_mensal": Decimal("97.00"),
            "limite_usuarios": 2,
            "limite_clientes": 100,
            "limite_produtos": 50,
            "limite_pedidos_mes": 100,
        },
        {
            "codigo": "growth",
            "nome": "Growth",
            "preco_mensal": Decimal("197.00"),
            "limite_usuarios": 6,
            "limite_clientes": 500,
            "limite_produtos": 250,
            "limite_pedidos_mes": 500,
        },
        {
            "codigo": "pro",
            "nome": "Pro",
            "preco_mensal": Decimal("397.00"),
            "limite_usuarios": 20,
            "limite_clientes": 2000,
            "limite_produtos": 1000,
            "limite_pedidos_mes": 3000,
        },
    ]
    for dados in planos:
        Plano.objects.update_or_create(codigo=dados["codigo"], defaults=dados)


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("empresas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Plano",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(choices=[("start", "Start"), ("growth", "Growth"), ("pro", "Pro")], max_length=30, unique=True)),
                ("nome", models.CharField(max_length=80)),
                ("preco_mensal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("limite_usuarios", models.PositiveIntegerField()),
                ("limite_clientes", models.PositiveIntegerField()),
                ("limite_produtos", models.PositiveIntegerField()),
                ("limite_pedidos_mes", models.PositiveIntegerField()),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["preco_mensal", "nome"]},
        ),
        migrations.CreateModel(
            name="Assinatura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("trial", "Trial"), ("ativa", "Ativa"), ("past_due", "Pagamento pendente"), ("suspensa", "Suspensa"), ("cancelada", "Cancelada")], default="trial", max_length=20)),
                ("inicio_em", models.DateField(default=django.utils.timezone.localdate)),
                ("fim_trial_em", models.DateField(blank=True, null=True)),
                ("gateway_preferido", models.CharField(blank=True, max_length=30)),
                ("gateway_customer_id", models.CharField(blank=True, max_length=120)),
                ("gateway_subscription_id", models.CharField(blank=True, max_length=120)),
                ("atualizada_em", models.DateTimeField(auto_now=True)),
                ("empresa", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="assinatura", to="empresas.empresa")),
                ("plano", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assinaturas", to="billing.plano")),
            ],
            options={"ordering": ["empresa__nome"]},
        ),
        migrations.RunPython(criar_planos_iniciais, migrations.RunPython.noop),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("empresas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=160)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("telefone", models.CharField(blank=True, max_length=30)),
                ("documento", models.CharField(blank=True, max_length=30)),
                ("observacoes", models.TextField(blank=True)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="clientes", to="empresas.empresa")),
            ],
            options={"ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=160)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("telefone", models.CharField(blank=True, max_length=30)),
                ("origem", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("novo", "Novo"), ("em_contato", "Em contato"), ("convertido", "Convertido"), ("perdido", "Perdido")], default="novo", max_length=20)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("cliente_convertido", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="leads_convertidos", to="crm.cliente")),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="leads", to="empresas.empresa")),
            ],
            options={"ordering": ["-criado_em"]},
        ),
        migrations.CreateModel(
            name="Oportunidade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=160)),
                ("valor_estimado", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("status", models.CharField(choices=[("aberta", "Aberta"), ("ganha", "Ganha"), ("perdida", "Perdida")], default="aberta", max_length=20)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("cliente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="oportunidades", to="crm.cliente")),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="oportunidades", to="empresas.empresa")),
                ("vendedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="oportunidades", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-criado_em"]},
        ),
        migrations.CreateModel(
            name="HistoricoContato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("telefone", "Telefone"), ("email", "Email"), ("whatsapp", "WhatsApp"), ("reuniao", "Reuniao"), ("outro", "Outro")], default="outro", max_length=20)),
                ("resumo", models.TextField()),
                ("realizado_em", models.DateTimeField(default=django.utils.timezone.now)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("cliente", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="historicos_contato", to="crm.cliente")),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="historicos_contato", to="empresas.empresa")),
                ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="historicos_contato", to="crm.lead")),
                ("vendedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="historicos_contato", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-realizado_em"]},
        ),
        migrations.CreateModel(
            name="ProximaAcao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("descricao", models.CharField(max_length=220)),
                ("data_prevista", models.DateField()),
                ("status", models.CharField(choices=[("pendente", "Pendente"), ("concluida", "Concluida"), ("cancelada", "Cancelada")], default="pendente", max_length=20)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                ("atualizada_em", models.DateTimeField(auto_now=True)),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="proximas_acoes", to="empresas.empresa")),
                ("oportunidade", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="proximas_acoes", to="crm.oportunidade")),
                ("vendedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="proximas_acoes", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["data_prevista", "id"]},
        ),
        migrations.AddIndex(
            model_name="cliente",
            index=models.Index(fields=["empresa", "ativo", "nome"], name="crm_cli_emp_ativo_nome_idx"),
        ),
        migrations.AddIndex(
            model_name="lead",
            index=models.Index(fields=["empresa", "status", "criado_em"], name="crm_lead_emp_status_idx"),
        ),
        migrations.AddIndex(
            model_name="oportunidade",
            index=models.Index(fields=["empresa", "status", "criado_em"], name="crm_op_emp_status_idx"),
        ),
        migrations.AddIndex(
            model_name="oportunidade",
            index=models.Index(fields=["empresa", "vendedor", "status"], name="crm_op_emp_vend_status_idx"),
        ),
        migrations.AddIndex(
            model_name="historicocontato",
            index=models.Index(fields=["empresa", "realizado_em"], name="crm_hist_emp_realizado_idx"),
        ),
        migrations.AddIndex(
            model_name="proximaacao",
            index=models.Index(fields=["empresa", "status", "data_prevista"], name="crm_acao_emp_status_idx"),
        ),
    ]

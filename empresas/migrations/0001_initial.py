from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Empresa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=160)),
                ("ativa", models.BooleanField(default=True)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                ("atualizada_em", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="EmpresaMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("papel", models.CharField(choices=[("admin", "Administrador"), ("vendedor", "Vendedor")], max_length=20)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="empresas.empresa")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="empresa_memberships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="empresamembership",
            constraint=models.UniqueConstraint(fields=("empresa", "usuario"), name="unique_membership_por_empresa_usuario"),
        ),
        migrations.AddIndex(
            model_name="empresamembership",
            index=models.Index(fields=["empresa", "usuario", "ativo"], name="emp_mem_empresa_usuario_idx"),
        ),
        migrations.AddIndex(
            model_name="empresamembership",
            index=models.Index(fields=["usuario", "ativo"], name="emp_mem_usuario_idx"),
        ),
    ]

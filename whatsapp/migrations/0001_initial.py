from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("empresas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppTemplateConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("catalogo", models.TextField(default="Ola! Veja nosso catalogo: {catalogo_url}")),
                ("produto", models.TextField(default="Ola! Conheca o produto {produto_nome} por R$ {produto_preco}: {produto_url}")),
                ("pedido", models.TextField(default="Ola! Segue o resumo do pedido #{pedido_id} no valor de R$ {pedido_total}.")),
                ("cliente", models.TextField(default="Ola, {cliente_nome}! Posso te ajudar com uma nova cotacao?")),
                ("follow_up", models.TextField(default="Ola, {cliente_nome}! Passando para dar continuidade ao nosso atendimento.")),
                ("atualizada_em", models.DateTimeField(auto_now=True)),
                ("empresa", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="whatsapp_config", to="empresas.empresa")),
            ],
            options={
                "verbose_name": "Configuracao de mensagens WhatsApp",
                "verbose_name_plural": "Configuracoes de mensagens WhatsApp",
            },
        ),
    ]

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from empresas.models import Empresa, EmpresaMembership


USERNAME = "carlosalberto"
PASSWORD = "@Testando123"
EMPRESA_NOME = "Empresa Demonstração"


class Command(BaseCommand):
    help = "Cria ou atualiza o usuario demo local/staging de forma idempotente."

    def handle(self, *args, **options):
        ambiente = getattr(settings, "DJANGO_ENV", "development")
        if ambiente == "production":
            raise CommandError("Comando bloqueado em producao.")

        User = get_user_model()
        usuario, usuario_criado = User.objects.get_or_create(
            username=USERNAME,
            defaults={
                "is_active": True,
                "first_name": "Carlos",
                "last_name": "Alberto",
            },
        )
        usuario.set_password(PASSWORD)
        usuario.is_active = True
        usuario.save()

        empresa, empresa_criada = Empresa.objects.get_or_create(nome=EMPRESA_NOME)
        membership, membership_criada = EmpresaMembership.objects.get_or_create(
            empresa=empresa,
            usuario=usuario,
            defaults={
                "papel": EmpresaMembership.Papel.ADMIN,
                "ativo": True,
            },
        )
        if membership.papel != EmpresaMembership.Papel.ADMIN or not membership.ativo:
            membership.papel = EmpresaMembership.Papel.ADMIN
            membership.ativo = True
            membership.save(update_fields=["papel", "ativo"])

        self.stdout.write(self.style.SUCCESS("Usuario demo pronto."))
        self.stdout.write(f"Ambiente: {ambiente}")
        self.stdout.write(f"Usuario: {USERNAME}")
        self.stdout.write(f"Senha: {PASSWORD}")
        self.stdout.write(f"Empresa: {empresa.nome}")
        self.stdout.write(
            "Criados agora: "
            f"usuario={usuario_criado}, empresa={empresa_criada}, membership={membership_criada}"
        )

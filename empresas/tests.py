from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from empresas.models import Empresa, EmpresaMembership


class CriarUsuarioDemoCommandTests(TestCase):
    @override_settings(DJANGO_ENV="development")
    def test_cria_usuario_demo_empresa_e_membership_admin(self):
        out = StringIO()

        call_command("criar_usuario_demo", stdout=out)

        usuario = User.objects.get(username="carlosalberto")
        empresa = Empresa.objects.get(nome="Empresa Demonstração")
        membership = EmpresaMembership.objects.get(usuario=usuario, empresa=empresa)
        self.assertTrue(usuario.check_password("@Testando123"))
        self.assertTrue(usuario.is_active)
        self.assertEqual(membership.papel, EmpresaMembership.Papel.ADMIN)
        self.assertTrue(membership.ativo)
        self.assertIn("Usuario demo pronto", out.getvalue())
        self.assertIn("Usuario: carlosalberto", out.getvalue())

    @override_settings(DJANGO_ENV="staging")
    def test_comando_demo_e_idempotente(self):
        call_command("criar_usuario_demo", stdout=StringIO())
        call_command("criar_usuario_demo", stdout=StringIO())

        self.assertEqual(User.objects.filter(username="carlosalberto").count(), 1)
        empresa = Empresa.objects.get(nome="Empresa Demonstração")
        usuario = User.objects.get(username="carlosalberto")
        self.assertEqual(
            EmpresaMembership.objects.filter(empresa=empresa, usuario=usuario).count(),
            1,
        )

    @override_settings(DJANGO_ENV="production")
    def test_comando_demo_bloqueia_producao(self):
        with self.assertRaises(CommandError):
            call_command("criar_usuario_demo", stdout=StringIO())

        self.assertFalse(User.objects.filter(username="carlosalberto").exists())

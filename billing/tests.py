import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from billing.middleware import BillingLimitMiddleware
from billing.models import Assinatura, Plano
from billing.services import (
    assinatura_bloqueada,
    avaliar_limites,
    get_assinatura_empresa,
    pode_criar_recurso,
)
from catalogo.models import Produto
from crm.models import Cliente
from empresas.models import Empresa, EmpresaMembership


class BillingTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa A")
        self.outra_empresa = Empresa.objects.create(nome="Empresa B")
        self.usuario = User.objects.create_user("admin_a", password="senha-segura")
        self.outro_usuario = User.objects.create_user("admin_b", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        EmpresaMembership.objects.create(
            empresa=self.outra_empresa,
            usuario=self.outro_usuario,
            papel=EmpresaMembership.Papel.ADMIN,
        )

    def test_planos_iniciais_existem(self):
        self.assertTrue(Plano.objects.filter(codigo=Plano.Codigo.START).exists())
        self.assertTrue(Plano.objects.filter(codigo=Plano.Codigo.GROWTH).exists())
        self.assertTrue(Plano.objects.filter(codigo=Plano.Codigo.PRO).exists())

    def test_get_assinatura_empresa_cria_trial_start(self):
        assinatura = get_assinatura_empresa(self.empresa)

        self.assertEqual(assinatura.empresa, self.empresa)
        self.assertEqual(assinatura.plano.codigo, Plano.Codigo.START)
        self.assertEqual(assinatura.status, Assinatura.Status.TRIAL)

    def test_assinatura_suspensa_bloqueia_uso(self):
        assinatura = get_assinatura_empresa(self.empresa)
        assinatura.status = Assinatura.Status.SUSPENSA
        assinatura.save(update_fields=["status"])

        bloqueada, assinatura_resultado = assinatura_bloqueada(self.empresa)

        self.assertTrue(bloqueada)
        self.assertEqual(assinatura_resultado, assinatura)

    def test_avaliar_limites_calcula_uso_por_empresa(self):
        plano = Plano.objects.create(
            codigo="teste-limites",
            nome="Teste Limites",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=1,
            limite_clientes=1,
            limite_produtos=2,
            limite_pedidos_mes=10,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        Produto.objects.create(empresa=self.empresa, nome="Produto A", preco="10.00")
        Produto.objects.create(empresa=self.outra_empresa, nome="Produto B", preco="20.00")

        limites = avaliar_limites(self.empresa)

        self.assertTrue(limites["usuarios"].atingido)
        self.assertTrue(limites["clientes"].atingido)
        self.assertFalse(limites["produtos"].atingido)
        self.assertEqual(limites["produtos"].usado, 1)

    def test_pode_criar_recurso_retorna_false_quando_limite_atingido(self):
        plano = Plano.objects.create(
            codigo="teste-clientes",
            nome="Teste Clientes",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_clientes=1,
            limite_produtos=5,
            limite_pedidos_mes=5,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Cliente.objects.create(empresa=self.empresa, nome="Cliente A")

        permitido, limite = pode_criar_recurso(self.empresa, "clientes")

        self.assertFalse(permitido)
        self.assertIn("Limite de clientes atingido", limite.aviso)

    def test_bloqueia_criacao_de_produto_quando_limite_atingido(self):
        plano = Plano.objects.create(
            codigo="teste-produtos",
            nome="Teste Produtos",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_clientes=5,
            limite_produtos=1,
            limite_pedidos_mes=5,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Produto.objects.create(empresa=self.empresa, nome="Produto A", preco="10.00")
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("catalogo:produto-list-create", args=[self.empresa.id]),
            data=json.dumps({"nome": "Produto Novo", "preco": "20.00"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Produto.objects.filter(nome="Produto Novo").exists())

    def test_bloqueia_criacao_de_cliente_quando_limite_atingido(self):
        plano = Plano.objects.create(
            codigo="teste-clientes-view",
            nome="Teste Clientes View",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_clientes=1,
            limite_produtos=5,
            limite_pedidos_mes=5,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("crm:cliente-create", args=[self.empresa.id]),
            data={
                "nome": "Cliente Novo",
                "email": "",
                "telefone": "",
                "documento": "",
                "observacoes": "",
                "ativo": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Limite de clientes atingido")
        self.assertFalse(Cliente.objects.filter(nome="Cliente Novo").exists())

    def test_middleware_anexa_limites_para_empresa_autorizada(self):
        request = RequestFactory().get(reverse("billing:plano-admin", args=[self.empresa.id]))
        request.user = self.usuario
        middleware = BillingLimitMiddleware(lambda req: None)

        middleware(request)
        middleware.process_view(request, None, (), {"empresa_id": self.empresa.id})

        self.assertIn("clientes", request.billing_limites)
        self.assertIsNone(request.billing_bloqueio)

    def test_middleware_nao_cria_assinatura_para_empresa_sem_acesso(self):
        request = RequestFactory().get(reverse("billing:plano-admin", args=[self.outra_empresa.id]))
        request.user = self.usuario
        middleware = BillingLimitMiddleware(lambda req: None)

        middleware(request)
        middleware.process_view(request, None, (), {"empresa_id": self.outra_empresa.id})

        self.assertEqual(request.billing_limites, {})
        self.assertFalse(Assinatura.objects.filter(empresa=self.outra_empresa).exists())

    def test_tela_admin_de_plano_renderiza_e_atualiza_assinatura(self):
        growth = Plano.objects.get(codigo=Plano.Codigo.GROWTH)
        get_assinatura_empresa(self.empresa)
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("billing:plano-admin", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plano da empresa")
        self.assertContains(response, "Start")

        response = self.client.post(
            reverse("billing:plano-admin", args=[self.empresa.id]),
            data={
                "plano": growth.id,
                "status": Assinatura.Status.ATIVA,
                "fim_trial_em": "",
                "gateway_preferido": "asaas",
            },
        )

        self.assertEqual(response.status_code, 302)
        assinatura = Assinatura.objects.get(empresa=self.empresa)
        self.assertEqual(assinatura.plano, growth)
        self.assertEqual(assinatura.status, Assinatura.Status.ATIVA)
        self.assertEqual(assinatura.gateway_preferido, "asaas")
